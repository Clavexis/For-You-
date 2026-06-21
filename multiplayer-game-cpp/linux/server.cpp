// server.cpp — authoritative UDP game server for the multiplayer game.
//
//   - Up to 4 players, each on a UDP "connection" (address).
//   - Receives JOIN / INPUT / LEAVE; runs the game simulation at a fixed tick.
//   - Broadcasts the full game state to all connected clients.
//   - No graphics — this is the headless authority. Clients render with SDL2.
//
// Build:  g++ -O2 -std=c++17 -o server server.cpp
// Run  :  ./server
//
// Built by clavexis — github.com/clavexis

#include "protocol.h"

#include <arpa/inet.h>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <chrono>
#include <thread>
#include <vector>

struct Client {
    bool active = false;
    sockaddr_in addr{};
    int16_t x = 0, y = 0;
    int8_t dx = 0, dy = 0;
    uint8_t score = 0;
    uint8_t alive = 1;
};

static bool same_addr(const sockaddr_in& a, const sockaddr_in& b) {
    return a.sin_addr.s_addr == b.sin_addr.s_addr && a.sin_port == b.sin_port;
}

int main() {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) { perror("socket"); return 1; }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(SERVER_PORT);
    if (bind(sock, (sockaddr*)&addr, sizeof(addr)) < 0) { perror("bind"); return 1; }

    // Non-blocking receive so we can run the simulation on a clock.
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    std::vector<Client> players(MAX_PLAYERS);
    printf("Game server listening on UDP %d (max %d players).\n", SERVER_PORT, MAX_PLAYERS);

    auto tick = std::chrono::milliseconds(33); // ~30 Hz
    auto next = std::chrono::steady_clock::now();

    while (true) {
        // --- drain incoming packets ---
        uint8_t buf[64];
        sockaddr_in from{};
        socklen_t flen = sizeof(from);
        ssize_t n;
        while ((n = recvfrom(sock, buf, sizeof(buf), 0, (sockaddr*)&from, &flen)) > 0) {
            uint8_t type = buf[0];
            if (type == MSG_JOIN) {
                // Assign the first free slot.
                int id = -1;
                for (int i = 0; i < MAX_PLAYERS; i++)
                    if (!players[i].active) { id = i; break; }
                if (id >= 0) {
                    players[id] = Client{};
                    players[id].active = true;
                    players[id].addr = from;
                    players[id].x = (int16_t)(100 + id * 150);
                    players[id].y = (int16_t)(FIELD_H / 2);
                    uint8_t reply[2] = {MSG_WELCOME, (uint8_t)id};
                    sendto(sock, reply, 2, 0, (sockaddr*)&from, flen);
                    printf("Player %d joined.\n", id);
                }
            } else if (type == MSG_INPUT && n >= 5) {
                uint8_t id = buf[1];
                if (id < MAX_PLAYERS && players[id].active &&
                    same_addr(players[id].addr, from)) {
                    players[id].dx = (int8_t)buf[2];
                    players[id].dy = (int8_t)buf[3];
                    // buf[4] = shoot flag (scoring kept simple here)
                }
            } else if (type == MSG_LEAVE && n >= 2) {
                uint8_t id = buf[1];
                if (id < MAX_PLAYERS) { players[id].active = false; printf("Player %d left.\n", id); }
            }
        }

        // --- simulate ---
        for (auto& p : players) {
            if (!p.active) continue;
            p.x += p.dx * PLAYER_SPEED;
            p.y += p.dy * PLAYER_SPEED;
            if (p.x < 0) p.x = 0;
            if (p.y < 0) p.y = 0;
            if (p.x > FIELD_W) p.x = FIELD_W;
            if (p.y > FIELD_H) p.y = FIELD_H;
        }

        // --- broadcast state ---
        uint8_t out[2 + MAX_PLAYERS * 7];
        int pos = 0;
        out[pos++] = MSG_STATE;
        int count_pos = pos++;
        uint8_t count = 0;
        for (int i = 0; i < MAX_PLAYERS; i++) {
            if (!players[i].active) continue;
            out[pos++] = (uint8_t)i;
            memcpy(out + pos, &players[i].x, 2); pos += 2;
            memcpy(out + pos, &players[i].y, 2); pos += 2;
            out[pos++] = players[i].score;
            out[pos++] = players[i].alive;
            count++;
        }
        out[count_pos] = count;
        for (auto& p : players) {
            if (p.active)
                sendto(sock, out, pos, 0, (sockaddr*)&p.addr, sizeof(p.addr));
        }

        // --- pace the loop ---
        next += tick;
        std::this_thread::sleep_until(next);
    }

    close(sock);
    return 0;
}
