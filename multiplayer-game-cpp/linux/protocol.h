// protocol.h — shared wire protocol for the multiplayer game (server + client).
//
// A tiny binary UDP protocol. All multi-byte integers are little-endian.
//
//   Client -> Server:
//     JOIN   : [0x01]
//     INPUT  : [0x02][id:u8][dx:i8][dy:i8][shoot:u8]
//     LEAVE  : [0x03][id:u8]
//   Server -> Client:
//     WELCOME: [0x10][assigned_id:u8]
//     STATE  : [0x11][count:u8] then count * { id:u8, x:i16, y:i16, score:u8, alive:u8 }
//
// Built by clavexis — github.com/clavexis
#pragma once
#include <cstdint>

enum : uint8_t {
    MSG_JOIN    = 0x01,
    MSG_INPUT   = 0x02,
    MSG_LEAVE   = 0x03,
    MSG_WELCOME = 0x10,
    MSG_STATE   = 0x11,
};

static const int MAX_PLAYERS = 4;
static const int FIELD_W = 800;
static const int FIELD_H = 600;
static const int PLAYER_SPEED = 4;
static const int SERVER_PORT = 9999;
