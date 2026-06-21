# Packet Sniffer from Scratch

Capture and inspect live network packets — Ethernet, IP, TCP, UDP, and ICMP — using raw sockets, **no libpcap**. Save captures to `.pcap` files you can open in Wireshark.

## Demo

```text
$ sudo ./sniffer --proto tcp
Sniffing... press Ctrl-C to stop.

[14:22:01] TCP  192.168.1.20 -> 142.250.80.14 :51234 -> :443  (74 bytes)
[14:22:01] TCP  142.250.80.14 -> 192.168.1.20 :443 -> :51234  (66 bytes)
[14:22:02] UDP  192.168.1.20 -> 1.1.1.1 :54123 -> :53  (60 bytes)
[14:22:02] ICMP 192.168.1.1 -> 192.168.1.20  (98 bytes)

Captured 4 packet(s).
```

(TCP cyan, UDP yellow, ICMP red, other green.)

## Features

- **Raw packet capture** with zero packet-parsing libraries.
  - Linux: `AF_PACKET` raw socket
  - macOS: Berkeley Packet Filter (`/dev/bpf`)
  - Windows: Python raw socket with `SIO_RCVALL` promiscuous mode
- **Header decoding** — Ethernet, IPv4, TCP, UDP, ICMP (source/destination IPs and ports).
- **Filters** — by protocol (`--proto tcp|udp|icmp`) or IP (`--ip 1.2.3.4`).
- **`.pcap` export** (`--write capture.pcap`) — opens in Wireshark/tcpdump.
- **Coloured terminal output.**

## Build & run

> ⚠️ Raw packet capture requires **root** (Linux/macOS) or **Administrator** (Windows).

### Linux
```bash
cd linux
make                     # or ./build.sh
sudo ./sniffer
sudo ./sniffer --proto tcp --write capture.pcap
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh               # uses clang
sudo ./sniffer en0       # specify your interface
sudo ./sniffer en0 --proto udp
```

### Windows
```powershell
cd windows
# Run an elevated (Administrator) terminal:
python sniffer.py --proto tcp --write capture.pcap
```

## Usage

```bash
sudo ./sniffer                          # capture everything
sudo ./sniffer --proto tcp              # only TCP
sudo ./sniffer --ip 8.8.8.8             # only packets to/from this IP
sudo ./sniffer --write out.pcap         # save to a pcap (Wireshark-compatible)
```

## How it works

```text
raw socket / BPF ──▶ recv frame ──▶ parse Ethernet ──▶ parse IP
                                                        ├── TCP  → ports
                                                        ├── UDP  → ports
                                                        └── ICMP
                                          └──▶ print + (optional) write to .pcap
```

The `.pcap` writer emits the standard global header + per-packet records, so captures load directly in Wireshark.

## Tech stack

- **C** (Linux `AF_PACKET`, macOS BPF) and **Python** (Windows raw sockets)
- Manual header parsing, hand-written pcap file writer

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
