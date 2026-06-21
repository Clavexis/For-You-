// Ray Tracer from Scratch — a software ray tracer that renders 3D scenes to PNG.
//
//   - Ray-sphere and ray-plane intersection
//   - Shadows, recursive reflections, and refractions (Snell + Schlick Fresnel)
//   - Anti-aliasing (configurable samples per pixel)
//   - Scene defined in a simple config file (or a built-in default scene)
//   - Writes a real PNG (hand-written PNG encoder — no image libraries)
//
// Build:  g++ -O2 -std=c++17 -o raytracer raytracer.cpp
// Run  :  ./raytracer -o out.png --width 800 --height 600 --samples 4
//         ./raytracer --scene scene.txt -o out.png
//
// Built by clavexis — github.com/clavexis

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

// ===========================================================================
// Vector math
// ===========================================================================
struct Vec3 {
    double x = 0, y = 0, z = 0;
    Vec3() {}
    Vec3(double a, double b, double c) : x(a), y(b), z(c) {}
    Vec3 operator+(const Vec3& v) const { return {x + v.x, y + v.y, z + v.z}; }
    Vec3 operator-(const Vec3& v) const { return {x - v.x, y - v.y, z - v.z}; }
    Vec3 operator*(double s) const { return {x * s, y * s, z * s}; }
    Vec3 operator*(const Vec3& v) const { return {x * v.x, y * v.y, z * v.z}; }
    double dot(const Vec3& v) const { return x * v.x + y * v.y + z * v.z; }
    double length() const { return std::sqrt(dot(*this)); }
    Vec3 normalized() const { double l = length(); return l > 0 ? *this * (1.0 / l) : *this; }
};

static Vec3 reflect(const Vec3& d, const Vec3& n) { return d - n * (2 * d.dot(n)); }

// ===========================================================================
// Scene objects
// ===========================================================================
struct Material {
    Vec3 color{0.8, 0.8, 0.8};
    double reflectivity = 0.0;   // 0..1
    double transparency = 0.0;   // 0..1
    double ior = 1.5;            // index of refraction
    double specular = 32.0;
};

struct Hit {
    double t = std::numeric_limits<double>::max();
    Vec3 point, normal;
    Material material;
    bool hit = false;
};

struct Object {
    enum Type { SPHERE, PLANE } type;
    Vec3 center;         // sphere center / point on plane
    double radius = 1;   // sphere radius
    Vec3 normal{0, 1, 0};// plane normal
    Material material;

    bool intersect(const Vec3& orig, const Vec3& dir, double& t) const {
        if (type == SPHERE) {
            Vec3 oc = orig - center;
            double b = oc.dot(dir);
            double c = oc.dot(oc) - radius * radius;
            double disc = b * b - c;
            if (disc < 0) return false;
            double sq = std::sqrt(disc);
            double t0 = -b - sq, t1 = -b + sq;
            t = (t0 > 1e-4) ? t0 : t1;
            return t > 1e-4;
        } else { // PLANE
            double denom = normal.dot(dir);
            if (std::fabs(denom) < 1e-6) return false;
            t = (center - orig).dot(normal) / denom;
            return t > 1e-4;
        }
    }
};

struct Light { Vec3 position; double intensity = 1.0; };

struct Scene {
    std::vector<Object> objects;
    std::vector<Light> lights;
    Vec3 background{0.5, 0.7, 1.0};
    Vec3 camera{0, 1, 5};
};

// ===========================================================================
// Ray tracing
// ===========================================================================
static Hit closestHit(const Scene& scene, const Vec3& orig, const Vec3& dir) {
    Hit hit;
    for (const auto& obj : scene.objects) {
        double t;
        if (obj.intersect(orig, dir, t) && t < hit.t) {
            hit.t = t; hit.hit = true;
            hit.point = orig + dir * t;
            hit.material = obj.material;
            if (obj.type == Object::SPHERE)
                hit.normal = (hit.point - obj.center).normalized();
            else
                hit.normal = obj.normal.dot(dir) < 0 ? obj.normal : obj.normal * -1;
        }
    }
    return hit;
}

static bool inShadow(const Scene& scene, const Vec3& point, const Vec3& lightDir, double dist) {
    for (const auto& obj : scene.objects) {
        double t;
        if (obj.intersect(point, lightDir, t) && t < dist) return true;
    }
    return false;
}

static Vec3 trace(const Scene& scene, const Vec3& orig, const Vec3& dir, int depth) {
    if (depth > 5) return {0, 0, 0};
    Hit hit = closestHit(scene, orig, dir);
    if (!hit.hit) return scene.background;

    Vec3 color{0, 0, 0};
    Vec3 n = hit.normal;
    Vec3 viewDir = (dir * -1).normalized();

    // Phong shading with shadows.
    for (const auto& light : scene.lights) {
        Vec3 toLight = light.position - hit.point;
        double dist = toLight.length();
        Vec3 lightDir = toLight.normalized();
        Vec3 shadowOrig = hit.point + n * 1e-3;
        if (inShadow(scene, shadowOrig, lightDir, dist)) continue;

        double diff = std::max(0.0, n.dot(lightDir));
        color = color + hit.material.color * (diff * light.intensity);

        Vec3 r = reflect(lightDir * -1, n);
        double spec = std::pow(std::max(0.0, r.dot(viewDir)), hit.material.specular);
        color = color + Vec3{1, 1, 1} * (spec * light.intensity * 0.5);
    }
    // Ambient term.
    color = color + hit.material.color * 0.1;

    // Reflection.
    if (hit.material.reflectivity > 0) {
        Vec3 refl = reflect(dir, n).normalized();
        Vec3 reflColor = trace(scene, hit.point + n * 1e-3, refl, depth + 1);
        color = color * (1 - hit.material.reflectivity) + reflColor * hit.material.reflectivity;
    }

    // Refraction (Snell's law) with Schlick's Fresnel approximation.
    if (hit.material.transparency > 0) {
        double eta = hit.material.ior;
        double cosi = std::max(-1.0, std::min(1.0, dir.dot(n)));
        Vec3 normal = n;
        double etai = 1, etat = eta;
        if (cosi < 0) { cosi = -cosi; }
        else { std::swap(etai, etat); normal = n * -1; }
        double ratio = etai / etat;
        double k = 1 - ratio * ratio * (1 - cosi * cosi);
        if (k >= 0) {
            Vec3 refrDir = (dir * ratio + normal * (ratio * cosi - std::sqrt(k))).normalized();
            Vec3 refrColor = trace(scene, hit.point - normal * 1e-3, refrDir, depth + 1);
            // Schlick approximation for the reflectance.
            double r0 = (etai - etat) / (etai + etat); r0 = r0 * r0;
            double fresnel = r0 + (1 - r0) * std::pow(1 - cosi, 5);
            color = color * (1 - hit.material.transparency)
                  + refrColor * (hit.material.transparency * (1 - fresnel));
        }
    }
    return color;
}

// ===========================================================================
// PNG writer (from scratch — uncompressed zlib "stored" blocks)
// ===========================================================================
static uint32_t crc_table[256];
static void init_crc() {
    for (uint32_t n = 0; n < 256; n++) {
        uint32_t c = n;
        for (int k = 0; k < 8; k++) c = (c & 1) ? 0xedb88320 ^ (c >> 1) : c >> 1;
        crc_table[n] = c;
    }
}
static uint32_t crc32(const std::vector<uint8_t>& data) {
    uint32_t c = 0xffffffff;
    for (uint8_t b : data) c = crc_table[(c ^ b) & 0xff] ^ (c >> 8);
    return c ^ 0xffffffff;
}
static void put32(std::vector<uint8_t>& v, uint32_t x) {
    v.push_back(x >> 24); v.push_back(x >> 16); v.push_back(x >> 8); v.push_back(x);
}
static void writeChunk(std::ofstream& f, const char* type, std::vector<uint8_t> data) {
    std::vector<uint8_t> chunk(type, type + 4);
    chunk.insert(chunk.end(), data.begin(), data.end());
    std::vector<uint8_t> lenb; put32(lenb, (uint32_t)data.size());
    f.write((char*)lenb.data(), 4);
    f.write((char*)chunk.data(), chunk.size());
    std::vector<uint8_t> crcb; put32(crcb, crc32(chunk));
    f.write((char*)crcb.data(), 4);
}
static void writePNG(const std::string& path, int w, int h, const std::vector<uint8_t>& rgb) {
    init_crc();
    std::ofstream f(path, std::ios::binary);
    const uint8_t sig[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    f.write((char*)sig, 8);
    // IHDR
    std::vector<uint8_t> ihdr;
    put32(ihdr, w); put32(ihdr, h);
    ihdr.push_back(8);   // bit depth
    ihdr.push_back(2);   // colour type 2 = RGB
    ihdr.push_back(0); ihdr.push_back(0); ihdr.push_back(0);
    writeChunk(f, "IHDR", ihdr);
    // Raw image data with a filter byte (0) per scanline.
    std::vector<uint8_t> raw;
    for (int y = 0; y < h; y++) {
        raw.push_back(0);
        for (int x = 0; x < w; x++) {
            int i = (y * w + x) * 3;
            raw.push_back(rgb[i]); raw.push_back(rgb[i + 1]); raw.push_back(rgb[i + 2]);
        }
    }
    // zlib stream: 2-byte header, stored deflate blocks, adler32 checksum.
    std::vector<uint8_t> zlib;
    zlib.push_back(0x78); zlib.push_back(0x01);
    size_t pos = 0;
    while (pos < raw.size()) {
        size_t block = std::min<size_t>(65535, raw.size() - pos);
        zlib.push_back(pos + block >= raw.size() ? 1 : 0); // final flag
        zlib.push_back(block & 0xff); zlib.push_back((block >> 8) & 0xff);
        zlib.push_back(~block & 0xff); zlib.push_back((~block >> 8) & 0xff);
        zlib.insert(zlib.end(), raw.begin() + pos, raw.begin() + pos + block);
        pos += block;
    }
    // Adler-32 over the raw data.
    uint32_t a = 1, b = 0;
    for (uint8_t byte : raw) { a = (a + byte) % 65521; b = (b + a) % 65521; }
    put32(zlib, (b << 16) | a);
    writeChunk(f, "IDAT", zlib);
    writeChunk(f, "IEND", {});
}

// ===========================================================================
// Scene loading
// ===========================================================================
static Scene defaultScene() {
    Scene s;
    // Ground plane
    Object ground; ground.type = Object::PLANE; ground.center = {0, -1, 0};
    ground.normal = {0, 1, 0}; ground.material.color = {0.3, 0.3, 0.35};
    ground.material.reflectivity = 0.2; s.objects.push_back(ground);
    // Red reflective sphere
    Object a; a.type = Object::SPHERE; a.center = {-1.2, 0, -1}; a.radius = 1;
    a.material.color = {0.9, 0.2, 0.2}; a.material.reflectivity = 0.4;
    s.objects.push_back(a);
    // Glass sphere
    Object b; b.type = Object::SPHERE; b.center = {1.2, 0, 0}; b.radius = 1;
    b.material.color = {0.9, 0.9, 0.9}; b.material.transparency = 0.8; b.material.ior = 1.5;
    s.objects.push_back(b);
    // Small green sphere
    Object c; c.type = Object::SPHERE; c.center = {0, -0.5, 1.5}; c.radius = 0.5;
    c.material.color = {0.2, 0.8, 0.3}; s.objects.push_back(c);

    s.lights.push_back({{-3, 5, 5}, 0.8});
    s.lights.push_back({{3, 3, 2}, 0.5});
    return s;
}

static Scene loadScene(const std::string& path) {
    Scene s = defaultScene();
    std::ifstream f(path);
    if (!f) { fprintf(stderr, "Could not open scene '%s', using default.\n", path.c_str()); return s; }
    s.objects.clear(); s.lights.clear();
    std::string line;
    while (std::getline(f, line)) {
        std::istringstream is(line);
        std::string kind; is >> kind;
        if (kind == "sphere") {
            Object o; o.type = Object::SPHERE;
            is >> o.center.x >> o.center.y >> o.center.z >> o.radius
               >> o.material.color.x >> o.material.color.y >> o.material.color.z
               >> o.material.reflectivity >> o.material.transparency;
            s.objects.push_back(o);
        } else if (kind == "plane") {
            Object o; o.type = Object::PLANE;
            is >> o.center.x >> o.center.y >> o.center.z
               >> o.normal.x >> o.normal.y >> o.normal.z
               >> o.material.color.x >> o.material.color.y >> o.material.color.z
               >> o.material.reflectivity;
            s.objects.push_back(o);
        } else if (kind == "light") {
            Light l; is >> l.position.x >> l.position.y >> l.position.z >> l.intensity;
            s.lights.push_back(l);
        } else if (kind == "camera") {
            is >> s.camera.x >> s.camera.y >> s.camera.z;
        }
    }
    return s;
}

static uint8_t toByte(double c) {
    if (c < 0) c = 0;
    if (c > 1) c = 1;
    return (uint8_t)(std::pow(c, 1 / 2.2) * 255 + 0.5); // gamma correction
}

int main(int argc, char** argv) {
    int width = 640, height = 480, samples = 2;
    std::string out = "render.png", scenePath;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        if (a == "-o" && i + 1 < argc) out = argv[++i];
        else if (a == "--width" && i + 1 < argc) width = std::stoi(argv[++i]);
        else if (a == "--height" && i + 1 < argc) height = std::stoi(argv[++i]);
        else if (a == "--samples" && i + 1 < argc) samples = std::stoi(argv[++i]);
        else if (a == "--scene" && i + 1 < argc) scenePath = argv[++i];
        else if (a == "--help") { printf("Usage: raytracer [-o out.png] [--width W] [--height H] [--samples N] [--scene file]\n"); return 0; }
    }

    Scene scene = scenePath.empty() ? defaultScene() : loadScene(scenePath);
    Vec3 cam = scene.camera;

    std::vector<uint8_t> image(width * height * 3);
    double aspect = (double)width / height;
    double fov = 1.0; // ~53 degrees

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            Vec3 color{0, 0, 0};
            for (int sy = 0; sy < samples; sy++) {
                for (int sx = 0; sx < samples; sx++) {
                    double px = (2 * ((x + (sx + 0.5) / samples) / width) - 1) * aspect * fov;
                    double py = (1 - 2 * ((y + (sy + 0.5) / samples) / height)) * fov;
                    Vec3 dir = Vec3{px, py, -1}.normalized();
                    color = color + trace(scene, cam, dir, 0);
                }
            }
            color = color * (1.0 / (samples * samples));
            int idx = (y * width + x) * 3;
            image[idx] = toByte(color.x);
            image[idx + 1] = toByte(color.y);
            image[idx + 2] = toByte(color.z);
        }
        if (y % 64 == 0) fprintf(stderr, "\rRendering... %d%%", (int)(100.0 * y / height));
    }
    fprintf(stderr, "\rRendering... done.   \n");

    writePNG(out, width, height, image);
    printf("Saved %s (%dx%d, %d spp)\n", out.c_str(), width, height, samples * samples);
    return 0;
}
