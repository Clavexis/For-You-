#!/usr/bin/env python3
"""
Packet Sniffer (Windows / cross-platform Python) — capture and decode packets
using raw sockets, no libraries.

On Windows, raw sockets capture at the IP layer (no Ethernet header) and need
Administrator privileges plus SIO_RCVALL promiscuous mode. This script also
runs on Linux/macOS as a simpler IP-level sniffer.

  - Decodes IP, TCP, UDP, ICMP headers
  - Filter by protocol (--proto tcp|udp|icmp) or IP (--ip 1.2.3.4)
  - Save to a .pcap file (--write out.pcap)
  - Coloured terminal output

Usage (run as Administrator on Windows):
  python sniffer.py
  python sniffer.py --proto tcp --write capture.pcap

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import socket
import struct
import sys
import time

PROTO = {1: "ICMP", 6: "TCP", 17: "UDP"}
PROTO_NUM = {"icmp": 1, "tcp": 6, "udp": 17}

C_RESET, C_CYAN, C_GREEN, C_YELL, C_RED, C_DIM = (
    "\033[0m", "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[2m")
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C_RESET = C_CYAN = C_GREEN = C_YELL = C_RED = C_DIM = ""


def decode_ip_packet(data: bytes):
    """Parse an IPv4 packet (starting at the IP header). Returns a dict or None."""
    if len(data) < 20:
        return None
    ver_ihl = data[0]
    version = ver_ihl >> 4
    if version != 4:
        return None
    ihl = (ver_ihl & 0x0F) * 4
    proto = data[9]
    src = socket.inet_ntoa(data[12:16])
    dst = socket.inet_ntoa(data[16:20])
    info = {"proto": proto, "src": src, "dst": dst, "sport": None, "dport": None,
            "length": len(data)}
    payload = data[ihl:]
    if proto == 6 and len(payload) >= 4:        # TCP
        info["sport"], info["dport"] = struct.unpack("!HH", payload[:4])
    elif proto == 17 and len(payload) >= 4:     # UDP
        info["sport"], info["dport"] = struct.unpack("!HH", payload[:4])
    return info


def colour_for(proto: int) -> str:
    return {6: C_CYAN, 17: C_YELL, 1: C_RED}.get(proto, C_GREEN)


# --- minimal pcap writer (LINKTYPE_RAW = 101, raw IP) ---------------------
def pcap_global_header() -> bytes:
    return struct.pack("<IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 101)


def pcap_packet_record(data: bytes) -> bytes:
    sec = int(time.time())
    usec = int((time.time() - sec) * 1_000_000)
    return struct.pack("<IIII", sec, usec, len(data), len(data)) + data


def make_socket():
    if os.name == "nt":
        host = socket.gethostbyname(socket.gethostname())
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        s.bind((host, 0))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)  # promiscuous
        return s
    # Linux/macOS fallback: IP-level raw socket (needs root).
    return socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)


def main() -> int:
    ap = argparse.ArgumentParser(description="Raw-socket packet sniffer.")
    ap.add_argument("--proto", choices=["tcp", "udp", "icmp"], help="Filter by protocol.")
    ap.add_argument("--ip", help="Filter by source/destination IP.")
    ap.add_argument("--write", metavar="FILE", help="Save capture to a .pcap file.")
    ap.add_argument("--count", type=int, default=0, help="Stop after N packets (0 = unlimited).")
    args = ap.parse_args()

    filt_proto = PROTO_NUM.get(args.proto) if args.proto else None

    try:
        sock = make_socket()
    except PermissionError:
        sys.stderr.write("Raw sockets need Administrator (Windows) / root privileges.\n")
        return 1
    except OSError as exc:
        sys.stderr.write(f"Could not open raw socket: {exc}\n")
        return 1

    pcap = None
    if args.write:
        pcap = open(args.write, "wb")
        pcap.write(pcap_global_header())
        print(f"Writing capture to {args.write}")

    print("Sniffing... press Ctrl-C to stop.\n")
    seen = 0
    try:
        while True:
            data, _ = sock.recvfrom(65535)
            info = decode_ip_packet(data)
            if not info:
                continue
            if filt_proto and info["proto"] != filt_proto:
                continue
            if args.ip and args.ip not in (info["src"], info["dst"]):
                continue

            col = colour_for(info["proto"])
            pname = PROTO.get(info["proto"], "OTHER")
            ports = ""
            if info["sport"] is not None:
                ports = f":{info['sport']} -> :{info['dport']}"
            ts = time.strftime("%H:%M:%S")
            print(f"{C_DIM}[{ts}]{C_RESET} {col}{pname:<4}{C_RESET} "
                  f"{info['src']} -> {info['dst']} {C_DIM}{ports}{C_RESET} "
                  f"{C_DIM}({info['length']} bytes){C_RESET}")
            if pcap:
                pcap.write(pcap_packet_record(data))
            seen += 1
            if args.count and seen >= args.count:
                break
    except KeyboardInterrupt:
        pass
    finally:
        if os.name == "nt":
            try:
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            except OSError:
                pass
        if pcap:
            pcap.close()
        sock.close()
    print(f"\nCaptured {seen} packet(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
