// DNS Resolver from Scratch — query and parse DNS over raw UDP sockets.
//
//   - Builds DNS query packets by hand
//   - Parses responses, including compressed names (0xC0 pointers)
//   - Supports A, AAAA, CNAME, MX, NS records
//   - Recursion-desired queries via a recursive resolver (default 8.8.8.8)
//   - In-memory cache (resolve repeated names from cache within a run)
//
// Build:  gcc -O2 -o dns dns.c
// Run  :  ./dns example.com
//         ./dns example.com MX --server 1.1.1.1
//         ./dns google.com google.com   (second query is a cache hit)
//
// Built by clavexis — github.com/clavexis

#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#define T_A 1
#define T_NS 2
#define T_CNAME 5
#define T_MX 15
#define T_AAAA 28

// --- DNS header (12 bytes) ------------------------------------------------
struct dns_header {
    uint16_t id, flags, qd, an, ns, ar;
};

static int qtype_from_string(const char* s) {
    if (!strcasecmp(s, "A")) return T_A;
    if (!strcasecmp(s, "AAAA")) return T_AAAA;
    if (!strcasecmp(s, "CNAME")) return T_CNAME;
    if (!strcasecmp(s, "MX")) return T_MX;
    if (!strcasecmp(s, "NS")) return T_NS;
    return T_A;
}
static const char* type_name(int t) {
    switch (t) {
        case T_A: return "A"; case T_AAAA: return "AAAA"; case T_CNAME: return "CNAME";
        case T_MX: return "MX"; case T_NS: return "NS";
    }
    return "?";
}

// Encode "www.example.com" -> 3www7example3com0 into buf. Returns length.
static int encode_name(const char* host, uint8_t* buf) {
    int len = 0;
    const char* p = host;
    while (*p) {
        const char* dot = strchr(p, '.');
        int seg = dot ? (int)(dot - p) : (int)strlen(p);
        buf[len++] = (uint8_t)seg;
        memcpy(buf + len, p, seg);
        len += seg;
        p += seg;
        if (*p == '.') p++;
    }
    buf[len++] = 0;
    return len;
}

// Parse a (possibly compressed) name starting at offset `pos` in `msg`.
// Writes the dotted name into `out`; returns the offset just past the name
// in the *original* stream (not following the compression pointer).
static int parse_name(const uint8_t* msg, int pos, char* out, int outsz) {
    int oi = 0, jumped = 0, orig_next = -1;
    int safety = 0;
    while (msg[pos] != 0) {
        if (++safety > 128) break;
        if ((msg[pos] & 0xC0) == 0xC0) {           // compression pointer
            int ptr = ((msg[pos] & 0x3F) << 8) | msg[pos + 1];
            if (!jumped) orig_next = pos + 2;
            pos = ptr;
            jumped = 1;
            continue;
        }
        int len = msg[pos++];
        for (int i = 0; i < len && oi < outsz - 1; i++) out[oi++] = msg[pos++];
        if (msg[pos] != 0 && oi < outsz - 1) out[oi++] = '.';
    }
    out[oi] = 0;
    if (!jumped) orig_next = pos + 1;
    return orig_next;
}

// --- a tiny in-memory cache ----------------------------------------------
struct cache_entry { char name[256]; int type; char value[256]; time_t expires; int used; };
#define CACHE_SIZE 64
static struct cache_entry cache[CACHE_SIZE];

static const char* cache_get(const char* name, int type) {
    time_t now = time(NULL);
    for (int i = 0; i < CACHE_SIZE; i++)
        if (cache[i].used && cache[i].type == type &&
            !strcasecmp(cache[i].name, name) && cache[i].expires > now)
            return cache[i].value;
    return NULL;
}
static void cache_put(const char* name, int type, const char* value, int ttl) {
    for (int i = 0; i < CACHE_SIZE; i++) {
        if (!cache[i].used || cache[i].expires <= time(NULL)) {
            cache[i].used = 1; cache[i].type = type;
            snprintf(cache[i].name, sizeof(cache[i].name), "%s", name);
            snprintf(cache[i].value, sizeof(cache[i].value), "%s", value);
            cache[i].expires = time(NULL) + (ttl > 0 ? ttl : 60);
            return;
        }
    }
}

// --- query + parse --------------------------------------------------------
static int resolve(const char* server, const char* host, int qtype) {
    const char* cached = cache_get(host, qtype);
    if (cached) {
        printf("%s %-5s %s  %s(from cache)%s\n", host, type_name(qtype), cached,
               "\033[2m", "\033[0m");
        return 0;
    }

    uint8_t pkt[512];
    struct dns_header* h = (struct dns_header*)pkt;
    memset(h, 0, sizeof(*h));
    h->id = htons(0x1234);
    h->flags = htons(0x0100); // recursion desired
    h->qd = htons(1);

    int len = sizeof(struct dns_header);
    len += encode_name(host, pkt + len);
    *(uint16_t*)(pkt + len) = htons(qtype); len += 2;
    *(uint16_t*)(pkt + len) = htons(1);     len += 2; // class IN

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in srv = {0};
    srv.sin_family = AF_INET;
    srv.sin_port = htons(53);
    inet_pton(AF_INET, server, &srv.sin_addr);

    struct timeval tv = {5, 0};
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    if (sendto(sock, pkt, len, 0, (struct sockaddr*)&srv, sizeof(srv)) < 0) {
        perror("sendto"); close(sock); return 1;
    }

    uint8_t resp[1024];
    int n = recv(sock, resp, sizeof(resp), 0);
    close(sock);
    if (n < (int)sizeof(struct dns_header)) {
        fprintf(stderr, "no response from %s\n", server);
        return 1;
    }

    struct dns_header* rh = (struct dns_header*)resp;
    int ancount = ntohs(rh->an);
    int pos = sizeof(struct dns_header);

    // Skip the question section.
    char tmp[256];
    pos = parse_name(resp, pos, tmp, sizeof(tmp));
    pos += 4; // qtype + qclass

    if (ancount == 0) {
        printf("%s: no %s records found.\n", host, type_name(qtype));
        return 0;
    }

    for (int i = 0; i < ancount; i++) {
        char name[256];
        pos = parse_name(resp, pos, name, sizeof(name));
        int type = ntohs(*(uint16_t*)(resp + pos)); pos += 2;
        pos += 2; // class
        uint32_t ttl = ntohl(*(uint32_t*)(resp + pos)); pos += 4;
        int rdlen = ntohs(*(uint16_t*)(resp + pos)); pos += 2;
        int rdpos = pos;

        char value[256] = "";
        if (type == T_A && rdlen == 4) {
            inet_ntop(AF_INET, resp + rdpos, value, sizeof(value));
        } else if (type == T_AAAA && rdlen == 16) {
            inet_ntop(AF_INET6, resp + rdpos, value, sizeof(value));
        } else if (type == T_CNAME || type == T_NS) {
            parse_name(resp, rdpos, value, sizeof(value));
        } else if (type == T_MX) {
            int pref = ntohs(*(uint16_t*)(resp + rdpos));
            char mx[200];
            parse_name(resp, rdpos + 2, mx, sizeof(mx));
            snprintf(value, sizeof(value), "%d %.200s", pref, mx);
        } else {
            snprintf(value, sizeof(value), "(%d bytes)", rdlen);
        }
        printf("%-30s %-6s %-6u %s\n", name, type_name(type), ttl, value);
        cache_put(host, type, value, ttl);
        pos = rdpos + rdlen;
    }
    return 0;
}

int main(int argc, char** argv) {
    const char* server = "8.8.8.8";
    int qtype = T_A;
    const char* names[16];
    int name_count = 0;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--server") && i + 1 < argc) {
            server = argv[++i];
        } else if (!strcmp(argv[i], "--help")) {
            printf("Usage: dns <name>... [A|AAAA|CNAME|MX|NS] [--server IP]\n");
            return 0;
        } else if (!strcasecmp(argv[i], "A") || !strcasecmp(argv[i], "AAAA") ||
                   !strcasecmp(argv[i], "CNAME") || !strcasecmp(argv[i], "MX") ||
                   !strcasecmp(argv[i], "NS")) {
            qtype = qtype_from_string(argv[i]);
        } else if (name_count < 16) {
            names[name_count++] = argv[i];
        }
    }

    if (name_count == 0) {
        fprintf(stderr, "Usage: dns <name>... [TYPE] [--server IP]\n");
        return 1;
    }

    printf("Resolving via %s:\n", server);
    printf("%-30s %-6s %-6s %s\n", "NAME", "TYPE", "TTL", "VALUE");
    for (int i = 0; i < name_count; i++)
        resolve(server, names[i], qtype);

    return 0;
}
