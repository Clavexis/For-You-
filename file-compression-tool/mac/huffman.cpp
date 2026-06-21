// File Compression Tool — Huffman coding from scratch.
//
//   - Compress and decompress any file (binary-safe)
//   - Huffman tree built from byte frequencies
//   - Reports the compression ratio
//   - Self-describing binary format: a header stores the frequency table so the
//     decompressor can rebuild the exact same tree
//
// Build:  g++ -O2 -std=c++17 -o huff huffman.cpp
// Run  :  ./huff -c input.txt output.huf     (compress)
//         ./huff -d output.huf restored.txt  (decompress)
//
// Built by clavexis — github.com/clavexis

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <queue>
#include <string>
#include <vector>

// A Huffman tree node.
struct Node {
    uint8_t byte = 0;
    uint64_t freq = 0;
    Node* left = nullptr;
    Node* right = nullptr;
    bool leaf() const { return !left && !right; }
};

struct Compare {
    bool operator()(Node* a, Node* b) const { return a->freq > b->freq; }
};

static Node* build_tree(const uint64_t freq[256]) {
    std::priority_queue<Node*, std::vector<Node*>, Compare> pq;
    int distinct = 0;
    for (int i = 0; i < 256; i++) {
        if (freq[i]) {
            Node* n = new Node{(uint8_t)i, freq[i], nullptr, nullptr};
            pq.push(n);
            distinct++;
        }
    }
    if (distinct == 0) return nullptr;
    if (distinct == 1) {
        // Edge case: a single symbol — give it a parent so it gets a 1-bit code.
        Node* only = pq.top(); pq.pop();
        Node* parent = new Node{0, only->freq, only, nullptr};
        return parent;
    }
    while (pq.size() > 1) {
        Node* a = pq.top(); pq.pop();
        Node* b = pq.top(); pq.pop();
        Node* parent = new Node{0, a->freq + b->freq, a, b};
        pq.push(parent);
    }
    return pq.top();
}

static void build_codes(Node* node, std::string code, std::string codes[256]) {
    if (!node) return;
    if (node->leaf()) { codes[node->byte] = code.empty() ? "0" : code; return; }
    build_codes(node->left, code + "0", codes);
    build_codes(node->right, code + "1", codes);
}

static void free_tree(Node* n) {
    if (!n) return;
    free_tree(n->left);
    free_tree(n->right);
    delete n;
}

// --- Bit writer / reader --------------------------------------------------
struct BitWriter {
    std::ofstream& out;
    uint8_t buf = 0;
    int nbits = 0;
    explicit BitWriter(std::ofstream& o) : out(o) {}
    void put(bool bit) {
        buf = (buf << 1) | (bit ? 1 : 0);
        if (++nbits == 8) { out.put((char)buf); buf = 0; nbits = 0; }
    }
    void flush() { if (nbits) { buf <<= (8 - nbits); out.put((char)buf); buf = 0; nbits = 0; } }
};

// ===========================================================================
// Compress
// ===========================================================================
static int compress(const std::string& in_path, const std::string& out_path) {
    std::ifstream in(in_path, std::ios::binary);
    if (!in) { std::cerr << "Cannot open " << in_path << "\n"; return 1; }
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(in)), {});
    in.close();

    uint64_t freq[256] = {0};
    for (uint8_t b : data) freq[b]++;

    Node* root = build_tree(freq);
    std::string codes[256];
    build_codes(root, "", codes);

    std::ofstream out(out_path, std::ios::binary);
    if (!out) { std::cerr << "Cannot write " << out_path << "\n"; free_tree(root); return 1; }

    // Header: magic, original size, frequency table.
    out.write("HUF1", 4);
    uint64_t orig = data.size();
    out.write((char*)&orig, sizeof(orig));
    out.write((char*)freq, sizeof(freq));   // 256 * 8 bytes

    // Body: the encoded bitstream.
    BitWriter bw(out);
    for (uint8_t b : data)
        for (char c : codes[b]) bw.put(c == '1');
    bw.flush();
    out.close();

    free_tree(root);

    // Report.
    std::ifstream check(out_path, std::ios::binary | std::ios::ate);
    uint64_t comp = check.tellg();
    double ratio = orig ? 100.0 * (1.0 - (double)comp / orig) : 0.0;
    printf("Compressed %s (%llu bytes) -> %s (%llu bytes)\n",
           in_path.c_str(), (unsigned long long)orig, out_path.c_str(), (unsigned long long)comp);
    printf("Compression ratio: %.1f%% smaller\n", ratio);
    return 0;
}

// ===========================================================================
// Decompress
// ===========================================================================
static int decompress(const std::string& in_path, const std::string& out_path) {
    std::ifstream in(in_path, std::ios::binary);
    if (!in) { std::cerr << "Cannot open " << in_path << "\n"; return 1; }

    char magic[4];
    in.read(magic, 4);
    if (std::string(magic, 4) != "HUF1") { std::cerr << "Not a HUF1 file.\n"; return 1; }

    uint64_t orig;
    in.read((char*)&orig, sizeof(orig));
    uint64_t freq[256];
    in.read((char*)freq, sizeof(freq));

    Node* root = build_tree(freq);
    std::ofstream out(out_path, std::ios::binary);
    if (!out) { std::cerr << "Cannot write " << out_path << "\n"; free_tree(root); return 1; }

    if (root) {
        Node* node = root;
        uint64_t written = 0;
        int ch;
        while (written < orig && (ch = in.get()) != EOF) {
            for (int bit = 7; bit >= 0 && written < orig; bit--) {
                bool one = (ch >> bit) & 1;
                node = one ? node->right : node->left;
                if (!node) node = root;       // single-symbol tree safety
                if (node->leaf()) {
                    out.put((char)node->byte);
                    written++;
                    node = root;
                }
            }
        }
    }
    out.close();
    free_tree(root);
    printf("Decompressed %s -> %s (%llu bytes)\n",
           in_path.c_str(), out_path.c_str(), (unsigned long long)orig);
    return 0;
}

int main(int argc, char** argv) {
    if (argc != 4 || (std::string(argv[1]) != "-c" && std::string(argv[1]) != "-d")) {
        printf("Usage:\n  huff -c <input> <output.huf>   (compress)\n"
               "  huff -d <output.huf> <restored>  (decompress)\n");
        return 1;
    }
    if (std::string(argv[1]) == "-c") return compress(argv[2], argv[3]);
    return decompress(argv[2], argv[3]);
}
