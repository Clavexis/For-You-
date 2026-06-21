// Packet Sniffer from Scratch (Linux) — capture and decode network packets.
//
//   - Raw AF_PACKET socket capture (no libpcap)
//   - Decodes Ethernet, IP, TCP, UDP, ICMP headers
//   - Filter by protocol (--proto tcp|udp|icmp) or IP (--ip 1.2.3.4)
//   - Save captures to a .pcap file (--write out.pcap) — readable by Wireshark
//   - Coloured terminal output
//
// Build:  gcc -O2 -o sniffer sniffer.c
// Run  :  sudo ./sniffer            (raw sockets need root / CAP_NET_RAW)
//         sudo ./sniffer --proto tcp --write capture.pcap
//
// Built by clavexis — github.com/clavexis

#include <arpa/inet.h>
#include <linux/if_packet.h>
#include <net/ethernet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/ip_icmp.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

// ANSI colours
#define C_RESET "\033[0m"
#define C_CYAN  "\033[36m"
#define C_GREEN "\033[32m"
#define C_YELL  "\033[33m"
#define C_RED   "\033[31m"
#define C_DIM   "\033[2m"

static volatile int running = 1;
static long packet_count = 0;
static FILE* pcap_file = NULL;

// --- filters --------------------------------------------------------------
static int filter_proto = 0;        // 0 = any, else IPPROTO_*
static uint32_t filter_ip = 0;      // 0 = any (network byte order)

static void on_sigint(int sig) { (void)sig; running = 0; }

// --- pcap file format -----------------------------------------------------
struct pcap_global_header {
    uint32_t magic;        // 0xa1b2c3d4
    uint16_t version_major, version_minor;
    int32_t  thiszone;
    uint32_t sigfigs, snaplen, network;
};
struct pcap_packet_header {
    uint32_t ts_sec, ts_usec, incl_len, orig_len;
};

static void pcap_write_global(FILE* f) {
    struct pcap_global_header h = {0xa1b2c3d4, 2, 4, 0, 0, 65535, 1 /*LINKTYPE_ETHERNET*/};
    fwrite(&h, sizeof(h), 1, f);
    fflush(f);
}
static void pcap_write_packet(FILE* f, const unsigned char* data, int len) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct pcap_packet_header h = {(uint32_t)tv.tv_sec, (uint32_t)tv.tv_usec,
                                   (uint32_t)len, (uint32_t)len};
    fwrite(&h, sizeof(h), 1, f);
    fwrite(data, 1, len, f);
    fflush(f);
}

// --- decoding -------------------------------------------------------------
static const char* proto_name(int p) {
    switch (p) {
        case IPPROTO_TCP:  return "TCP";
        case IPPROTO_UDP:  return "UDP";
        case IPPROTO_ICMP: return "ICMP";
    }
    return "OTHER";
}

static void decode(const unsigned char* buf, int len) {
    if (len < (int)sizeof(struct ethhdr)) return;
    const struct ethhdr* eth = (const struct ethhdr*)buf;
    if (ntohs(eth->h_proto) != ETH_P_IP) return;  // only IPv4 here

    const struct iphdr* ip = (const struct iphdr*)(buf + sizeof(struct ethhdr));
    int ip_hlen = ip->ihl * 4;

    // Apply filters.
    if (filter_proto && ip->protocol != filter_proto) return;
    if (filter_ip && ip->saddr != filter_ip && ip->daddr != filter_ip) return;

    char src[INET_ADDRSTRLEN], dst[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &ip->saddr, src, sizeof(src));
    inet_ntop(AF_INET, &ip->daddr, dst, sizeof(dst));

    const char* color = C_GREEN;
    char ports[64] = "";
    const char* pname = proto_name(ip->protocol);

    if (ip->protocol == IPPROTO_TCP) {
        const struct tcphdr* tcp = (const struct tcphdr*)((const unsigned char*)ip + ip_hlen);
        snprintf(ports, sizeof(ports), ":%d -> :%d", ntohs(tcp->source), ntohs(tcp->dest));
        color = C_CYAN;
    } else if (ip->protocol == IPPROTO_UDP) {
        const struct udphdr* udp = (const struct udphdr*)((const unsigned char*)ip + ip_hlen);
        snprintf(ports, sizeof(ports), ":%d -> :%d", ntohs(udp->source), ntohs(udp->dest));
        color = C_YELL;
    } else if (ip->protocol == IPPROTO_ICMP) {
        color = C_RED;
    }

    time_t now = time(NULL);
    char ts[16];
    strftime(ts, sizeof(ts), "%H:%M:%S", localtime(&now));

    printf("%s[%s]%s %s%-4s%s %s -> %s %s%s%s  %s(%d bytes)%s\n",
           C_DIM, ts, C_RESET, color, pname, C_RESET, src, dst,
           C_DIM, ports, C_RESET, C_DIM, len, C_RESET);

    if (pcap_file) pcap_write_packet(pcap_file, buf, len);
    packet_count++;
}

int main(int argc, char** argv) {
    const char* pcap_path = NULL;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--proto") && i + 1 < argc) {
            const char* p = argv[++i];
            if (!strcmp(p, "tcp")) filter_proto = IPPROTO_TCP;
            else if (!strcmp(p, "udp")) filter_proto = IPPROTO_UDP;
            else if (!strcmp(p, "icmp")) filter_proto = IPPROTO_ICMP;
        } else if (!strcmp(argv[i], "--ip") && i + 1 < argc) {
            inet_pton(AF_INET, argv[++i], &filter_ip);
        } else if (!strcmp(argv[i], "--write") && i + 1 < argc) {
            pcap_path = argv[++i];
        } else if (!strcmp(argv[i], "--help")) {
            printf("Usage: sudo ./sniffer [--proto tcp|udp|icmp] [--ip ADDR] [--write file.pcap]\n");
            return 0;
        }
    }

    // Raw socket capturing every Ethernet frame.
    int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (sock < 0) {
        perror("socket (need root / CAP_NET_RAW)");
        return 1;
    }

    if (pcap_path) {
        pcap_file = fopen(pcap_path, "wb");
        if (!pcap_file) { perror("fopen pcap"); close(sock); return 1; }
        pcap_write_global(pcap_file);
        printf("Writing capture to %s\n", pcap_path);
    }

    signal(SIGINT, on_sigint);
    printf("Sniffing... press Ctrl-C to stop.\n\n");

    unsigned char buf[65536];
    while (running) {
        ssize_t n = recvfrom(sock, buf, sizeof(buf), 0, NULL, NULL);
        if (n < 0) {
            if (running) perror("recvfrom");
            break;
        }
        decode(buf, (int)n);
    }

    printf("\nCaptured %ld packet(s).\n", packet_count);
    if (pcap_file) fclose(pcap_file);
    close(sock);
    return 0;
}
