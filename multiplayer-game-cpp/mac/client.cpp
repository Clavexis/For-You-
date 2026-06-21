// client.cpp — SDL2 client for the multiplayer game.
//
//   - Connects to the UDP server, sends movement input (arrow keys / WASD).
//   - Receives the broadcast game state and renders every player.
//   - Up to 4 players, each a different colour.
//
// Build:  g++ -O2 -std=c++17 client.cpp -o client $(pkg-config --cflags --libs sdl2)
// Run  :  ./client [server_ip]
//
// Built by clavexis — github.com/clavexis

#include "protocol.h"

#include <SDL2/SDL.h>
#include <arpa/inet.h>
#include <cstring>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstdio>

struct PlayerView { int id; int16_t x, y; uint8_t score, alive; };

static const SDL_Color COLORS[MAX_PLAYERS] = {
    {230, 60, 60, 255}, {60, 160, 230, 255}, {80, 200, 100, 255}, {230, 200, 60, 255},
};

int main(int argc, char** argv) {
    const char* server_ip = argc > 1 ? argv[1] : "127.0.0.1";

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in srv{};
    srv.sin_family = AF_INET;
    srv.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, server_ip, &srv.sin_addr);

    // Join.
    uint8_t join = MSG_JOIN;
    sendto(sock, &join, 1, 0, (sockaddr*)&srv, sizeof(srv));
    uint8_t buf[64];
    ssize_t n = recvfrom(sock, buf, sizeof(buf), 0, nullptr, nullptr);
    if (n < 2 || buf[0] != MSG_WELCOME) { fprintf(stderr, "no welcome from server\n"); return 1; }
    int my_id = buf[1];
    printf("Joined as player %d\n", my_id);

    // Non-blocking socket so rendering isn't stalled.
    fcntl(sock, F_SETFL, fcntl(sock, F_GETFL, 0) | O_NONBLOCK);

    if (SDL_Init(SDL_INIT_VIDEO) != 0) { fprintf(stderr, "SDL_Init: %s\n", SDL_GetError()); return 1; }
    SDL_Window* win = SDL_CreateWindow("Multiplayer — clavexis",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, FIELD_W, FIELD_H, 0);
    SDL_Renderer* ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);

    PlayerView players[MAX_PLAYERS];
    int player_count = 0;
    bool running = true;

    while (running) {
        SDL_Event e;
        while (SDL_PollEvent(&e))
            if (e.type == SDL_QUIT) running = false;

        // Read keyboard -> input.
        const Uint8* keys = SDL_GetKeyboardState(nullptr);
        int8_t dx = 0, dy = 0;
        if (keys[SDL_SCANCODE_LEFT]  || keys[SDL_SCANCODE_A]) dx = -1;
        if (keys[SDL_SCANCODE_RIGHT] || keys[SDL_SCANCODE_D]) dx = 1;
        if (keys[SDL_SCANCODE_UP]    || keys[SDL_SCANCODE_W]) dy = -1;
        if (keys[SDL_SCANCODE_DOWN]  || keys[SDL_SCANCODE_S]) dy = 1;
        uint8_t in[5] = {MSG_INPUT, (uint8_t)my_id, (uint8_t)dx, (uint8_t)dy, 0};
        sendto(sock, in, 5, 0, (sockaddr*)&srv, sizeof(srv));

        // Drain state packets (keep the latest).
        while ((n = recvfrom(sock, buf, sizeof(buf), 0, nullptr, nullptr)) > 0) {
            if (buf[0] != MSG_STATE) continue;
            int count = buf[1], pos = 2;
            player_count = 0;
            for (int i = 0; i < count && i < MAX_PLAYERS; i++) {
                PlayerView& p = players[player_count++];
                p.id = buf[pos++];
                memcpy(&p.x, buf + pos, 2); pos += 2;
                memcpy(&p.y, buf + pos, 2); pos += 2;
                p.score = buf[pos++];
                p.alive = buf[pos++];
            }
        }

        // Render.
        SDL_SetRenderDrawColor(ren, 25, 25, 35, 255);
        SDL_RenderClear(ren);
        for (int i = 0; i < player_count; i++) {
            const SDL_Color& c = COLORS[players[i].id % MAX_PLAYERS];
            SDL_SetRenderDrawColor(ren, c.r, c.g, c.b, 255);
            SDL_Rect rect = {players[i].x - 12, players[i].y - 12, 24, 24};
            SDL_RenderFillRect(ren, &rect);
            // Outline your own player.
            if (players[i].id == my_id) {
                SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
                SDL_RenderDrawRect(ren, &rect);
            }
        }
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }

    uint8_t leave[2] = {MSG_LEAVE, (uint8_t)my_id};
    sendto(sock, leave, 2, 0, (sockaddr*)&srv, sizeof(srv));
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
    close(sock);
    return 0;
}
