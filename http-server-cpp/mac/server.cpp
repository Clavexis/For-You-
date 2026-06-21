// HTTP Server from Scratch — a working HTTP/1.1 server with no web libraries.
//
//   - Handles GET (serve static files) and POST (echo submitted data)
//   - Multi-threaded: one thread per connection
//   - Configurable port and document root
//   - Access logging to stdout
//   - Path-traversal protection
//
// Build (Linux/macOS):  g++ -O2 -std=c++17 -pthread -o server server.cpp
// Build (Windows MinGW): g++ -O2 -std=c++17 -o server.exe server.cpp -lws2_32
// Run:                  ./server --port 8080 --root ./www
//
// Built by clavexis — github.com/clavexis

#include <atomic>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_map>

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef SOCKET socket_t;
  #define CLOSESOCK closesocket
#else
  #include <arpa/inet.h>
  #include <netinet/in.h>
  #include <sys/socket.h>
  #include <unistd.h>
  typedef int socket_t;
  #define INVALID_SOCKET (-1)
  #define CLOSESOCK close
#endif

// ---------------------------------------------------------------------------
// Configuration & globals
// ---------------------------------------------------------------------------
static int g_port = 8080;
static std::string g_root = ".";
static std::mutex g_log_mutex;

static void logRequest(const std::string& ip, const std::string& method,
                       const std::string& path, int status) {
    std::lock_guard<std::mutex> lock(g_log_mutex);
    std::time_t t = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&t));
    std::cout << "[" << buf << "] " << ip << " \"" << method << " " << path
              << "\" " << status << std::endl;
}

// ---------------------------------------------------------------------------
// MIME types
// ---------------------------------------------------------------------------
static std::string mimeType(const std::string& path) {
    static const std::unordered_map<std::string, std::string> types = {
        {".html", "text/html"}, {".htm", "text/html"}, {".css", "text/css"},
        {".js", "application/javascript"}, {".json", "application/json"},
        {".png", "image/png"}, {".jpg", "image/jpeg"}, {".jpeg", "image/jpeg"},
        {".gif", "image/gif"}, {".svg", "image/svg+xml"}, {".ico", "image/x-icon"},
        {".txt", "text/plain"}, {".pdf", "application/pdf"},
    };
    auto dot = path.find_last_of('.');
    if (dot != std::string::npos) {
        auto it = types.find(path.substr(dot));
        if (it != types.end()) return it->second;
    }
    return "application/octet-stream";
}

// ---------------------------------------------------------------------------
// Response building
// ---------------------------------------------------------------------------
static const char* statusText(int code) {
    switch (code) {
        case 200: return "OK";
        case 400: return "Bad Request";
        case 403: return "Forbidden";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 500: return "Internal Server Error";
    }
    return "Unknown";
}

static std::string buildResponse(int code, const std::string& contentType,
                                 const std::string& body) {
    std::ostringstream os;
    os << "HTTP/1.1 " << code << " " << statusText(code) << "\r\n"
       << "Server: clawserver/1.0\r\n"
       << "Content-Type: " << contentType << "\r\n"
       << "Content-Length: " << body.size() << "\r\n"
       << "Connection: close\r\n\r\n"
       << body;
    return os.str();
}

static std::string errorPage(int code) {
    std::ostringstream os;
    os << "<!DOCTYPE html><html><head><title>" << code << " " << statusText(code)
       << "</title></head><body><h1>" << code << " " << statusText(code)
       << "</h1><hr><p>clawserver — by clavexis</p></body></html>";
    return os.str();
}

// ---------------------------------------------------------------------------
// Path safety — keep requests inside the document root.
// ---------------------------------------------------------------------------
static bool isSafePath(const std::string& path) {
    // Reject any ".." segment or absolute escape.
    if (path.find("..") != std::string::npos) return false;
    return true;
}

static std::string urlDecode(const std::string& s) {
    std::string out;
    for (size_t i = 0; i < s.size(); i++) {
        if (s[i] == '%' && i + 2 < s.size()) {
            int hi = std::isxdigit((unsigned char)s[i+1]) ? std::stoi(s.substr(i+1, 1), nullptr, 16) : -1;
            int lo = std::isxdigit((unsigned char)s[i+2]) ? std::stoi(s.substr(i+2, 1), nullptr, 16) : -1;
            if (hi >= 0 && lo >= 0) { out += char(hi * 16 + lo); i += 2; continue; }
        }
        if (s[i] == '+') out += ' ';
        else out += s[i];
    }
    return out;
}

// ---------------------------------------------------------------------------
// Request handling
// ---------------------------------------------------------------------------
static void sendAll(socket_t sock, const std::string& data) {
    size_t sent = 0;
    while (sent < data.size()) {
        int n = send(sock, data.data() + sent, (int)(data.size() - sent), 0);
        if (n <= 0) break;
        sent += n;
    }
}

static void handleClient(socket_t sock, std::string ip) {
    char buf[8192];
    std::string request;
    // Read until we have the full header block (\r\n\r\n) or the buffer fills.
    while (request.find("\r\n\r\n") == std::string::npos) {
        int n = recv(sock, buf, sizeof(buf), 0);
        if (n <= 0) break;
        request.append(buf, n);
        if (request.size() > 1 << 20) break; // 1 MB cap
    }
    if (request.empty()) { CLOSESOCK(sock); return; }

    // Parse the request line: "METHOD PATH HTTP/1.1"
    std::istringstream iss(request);
    std::string method, rawPath, version;
    iss >> method >> rawPath >> version;

    if (method.empty() || rawPath.empty()) {
        sendAll(sock, buildResponse(400, "text/html", errorPage(400)));
        logRequest(ip, "?", "?", 400);
        CLOSESOCK(sock);
        return;
    }

    // Strip query string for file lookup.
    std::string path = rawPath;
    auto q = path.find('?');
    if (q != std::string::npos) path = path.substr(0, q);
    path = urlDecode(path);

    if (method == "POST") {
        // Echo the submitted body back as confirmation.
        std::string body;
        auto bodyPos = request.find("\r\n\r\n");
        if (bodyPos != std::string::npos) body = request.substr(bodyPos + 4);
        std::ostringstream os;
        os << "<!DOCTYPE html><html><body><h1>POST received</h1>"
           << "<p>Path: " << path << "</p>"
           << "<pre>" << body << "</pre>"
           << "<hr><p>clawserver — by clavexis</p></body></html>";
        sendAll(sock, buildResponse(200, "text/html", os.str()));
        logRequest(ip, method, path, 200);
        CLOSESOCK(sock);
        return;
    }

    if (method != "GET") {
        sendAll(sock, buildResponse(405, "text/html", errorPage(405)));
        logRequest(ip, method, path, 405);
        CLOSESOCK(sock);
        return;
    }

    // GET — serve a static file.
    if (!isSafePath(path)) {
        sendAll(sock, buildResponse(403, "text/html", errorPage(403)));
        logRequest(ip, method, path, 403);
        CLOSESOCK(sock);
        return;
    }

    std::string fsPath = g_root + path;
    if (!path.empty() && path.back() == '/') fsPath += "index.html"; // directory index

    std::ifstream file(fsPath, std::ios::binary);
    if (!file) {
        sendAll(sock, buildResponse(404, "text/html", errorPage(404)));
        logRequest(ip, method, path, 404);
        CLOSESOCK(sock);
        return;
    }
    std::ostringstream content;
    content << file.rdbuf();
    sendAll(sock, buildResponse(200, mimeType(fsPath), content.str()));
    logRequest(ip, method, path, 200);
    CLOSESOCK(sock);
}

// ---------------------------------------------------------------------------
// main / accept loop
// ---------------------------------------------------------------------------
int main(int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        if (a == "--port" && i + 1 < argc) g_port = std::stoi(argv[++i]);
        else if (a == "--root" && i + 1 < argc) g_root = argv[++i];
        else if (a == "--help") {
            std::cout << "Usage: server [--port N] [--root DIR]\n";
            return 0;
        }
    }

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        std::cerr << "WSAStartup failed\n"; return 1;
    }
#endif

    socket_t listenSock = socket(AF_INET, SOCK_STREAM, 0);
    if (listenSock == INVALID_SOCKET) { std::cerr << "socket() failed\n"; return 1; }

    int opt = 1;
    setsockopt(listenSock, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((unsigned short)g_port);

    if (bind(listenSock, (sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << "bind() failed on port " << g_port << " (in use?)\n";
        CLOSESOCK(listenSock);
        return 1;
    }
    if (listen(listenSock, 64) < 0) {
        std::cerr << "listen() failed\n"; CLOSESOCK(listenSock); return 1;
    }

    std::cout << "clawserver listening on http://localhost:" << g_port
              << "  (root: " << g_root << ")\n";

    for (;;) {
        sockaddr_in clientAddr{};
        socklen_t len = sizeof(clientAddr);
        socket_t client = accept(listenSock, (sockaddr*)&clientAddr, &len);
        if (client == INVALID_SOCKET) continue;

        char ipbuf[INET_ADDRSTRLEN] = {0};
        inet_ntop(AF_INET, &clientAddr.sin_addr, ipbuf, sizeof(ipbuf));

        // One detached thread per connection.
        std::thread(handleClient, client, std::string(ipbuf)).detach();
    }

#ifdef _WIN32
    WSACleanup();
#endif
    CLOSESOCK(listenSock);
    return 0;
}
