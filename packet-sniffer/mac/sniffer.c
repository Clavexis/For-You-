// Packet Sniffer from Scratch (macOS) — capture and decode network packets.
//
// macOS has no AF_PACKET; it uses the Berkeley Packet Filter (BPF) device.
// This opens /dev/bpfN, binds it to an interface, and reads Ethernet frames.
//
//   - Raw BPF capture (no libpcap)
//   - Decodes Ethernet, IP, TCP, UDP, ICMP headers
//   - Filter by protocol (--proto tcp|udp|icmp) or IP (--ip 1.2.3.4)
//   - Coloured terminal output
//
// Build:  clang -O2 -o sniffer sniffer.c
// Run  :  sudo ./sniffer en0            (BPF needs root)
//         sudo ./sniffer en0 --proto tcp
//
// Built by clavexis — github.com/clavexis

#include <arpa/inet.h>
#include <fcntl.h>
#include <net/bpf.h>
#include <net/ethernet.h>
#include <net/if.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#define C_RESET "\033[0m"
#define C_CYAN  "\033[36m"
#define C_GREEN "\033[32m"
#define C_YELL  "\033[33m"
#define C_RED   "\033[31m"
#define C_DIM   "\033[2m"

static volatile int running = 1;
static long packet_count = 0;
static int filter_proto = 0;
static uint32_t filter_ip = 0;

static void on_sigint(int s) { (void)s; running = 0; }

static const char* proto_name(int p) {
    switch (p) {
        case IPPROTO_TCP:  return "TCP";
        case IPPROTO_UDP:  return "UDP";
        case IPPROTO_ICMP: return "ICMP";
    }
    return "OTHER";
}

// Decode one Ethernet frame (starting at the ethernet header).
static void decode(const unsigned char* buf, int len) {
    if (len < (int)sizeof(struct ether_header)) return;
    const struct ether_header* eth = (const struct ether_header*)buf;
    if (ntohs(eth->ether_type) != ETHERTYPE_IP) return;

    const struct ip* ip = (const struct ip*)(buf + sizeof(struct ether_header));
    int ip_hlen = ip->ip_hl * 4;

    if (filter_proto && ip->ip_p != filter_proto) return;
    if (filter_ip && ip->ip_src.s_addr != filter_ip && ip->ip_dst.s_addr != filter_ip) return;

    char src[INET_ADDRSTRLEN], dst[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &ip->ip_src, src, sizeof(src));
    inet_ntop(AF_INET, &ip->ip_dst, dst, sizeof(dst));

    const char* color = C_GREEN;
    char ports[64] = "";
    if (ip->ip_p == IPPROTO_TCP) {
        const struct tcphdr* tcp = (const struct tcphdr*)((const unsigned char*)ip + ip_hlen);
        snprintf(ports, sizeof(ports), ":%d -> :%d", ntohs(tcp->th_sport), ntohs(tcp->th_dport));
        color = C_CYAN;
    } else if (ip->ip_p == IPPROTO_UDP) {
        const struct udphdr* udp = (const struct udphdr*)((const unsigned char*)ip + ip_hlen);
        snprintf(ports, sizeof(ports), ":%d -> :%d", ntohs(udp->uh_sport), ntohs(udp->uh_dport));
        color = C_YELL;
    } else if (ip->ip_p == IPPROTO_ICMP) {
        color = C_RED;
    }

    time_t now = time(NULL);
    char ts[16];
    strftime(ts, sizeof(ts), "%H:%M:%S", localtime(&now));
    printf("%s[%s]%s %s%-4s%s %s -> %s %s%s%s  %s(%d bytes)%s\n",
           C_DIM, ts, C_RESET, color, proto_name(ip->ip_p), C_RESET,
           src, dst, C_DIM, ports, C_RESET, C_DIM, len, C_RESET);
    packet_count++;
}

int main(int argc, char** argv) {
    const char* iface = "en0";
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--proto") && i + 1 < argc) {
            const char* p = argv[++i];
            if (!strcmp(p, "tcp")) filter_proto = IPPROTO_TCP;
            else if (!strcmp(p, "udp")) filter_proto = IPPROTO_UDP;
            else if (!strcmp(p, "icmp")) filter_proto = IPPROTO_ICMP;
        } else if (!strcmp(argv[i], "--ip") && i + 1 < argc) {
            inet_pton(AF_INET, argv[++i], &filter_ip);
        } else if (!strcmp(argv[i], "--help")) {
            printf("Usage: sudo ./sniffer [IFACE] [--proto tcp|udp|icmp] [--ip ADDR]\n");
            return 0;
        } else if (argv[i][0] != '-') {
            iface = argv[i];
        }
    }

    // Open the first available /dev/bpf device.
    int fd = -1;
    char dev[16];
    for (int i = 0; i < 99; i++) {
        snprintf(dev, sizeof(dev), "/dev/bpf%d", i);
        fd = open(dev, O_RDONLY);
        if (fd >= 0) break;
    }
    if (fd < 0) { perror("open /dev/bpf (need root)"); return 1; }

    // Bind the BPF device to the interface.
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, iface, IFNAMSIZ - 1);
    if (ioctl(fd, BIOCSETIF, &ifr) < 0) { perror("BIOCSETIF"); close(fd); return 1; }

    int yes = 1;
    ioctl(fd, BIOCIMMEDIATE, &yes);   // deliver packets immediately

    unsigned int buflen = 0;
    ioctl(fd, BIOCGBLEN, &buflen);    // required read buffer length
    unsigned char* buf = malloc(buflen);
    if (!buf) { perror("malloc"); close(fd); return 1; }

    signal(SIGINT, on_sigint);
    printf("Sniffing on %s... press Ctrl-C to stop.\n\n", iface);

    while (running) {
        ssize_t n = read(fd, buf, buflen);
        if (n <= 0) { if (running) perror("read"); break; }
        // A BPF read returns one or more records; walk them with BPF_WORDALIGN.
        unsigned char* p = buf;
        while (p < buf + n) {
            struct bpf_hdr* bh = (struct bpf_hdr*)p;
            decode(p + bh->bh_hdrlen, bh->bh_caplen);
            p += BPF_WORDALIGN(bh->bh_hdrlen + bh->bh_caplen);
        }
    }

    printf("\nCaptured %ld packet(s).\n", packet_count);
    free(buf);
    close(fd);
    return 0;
}
