#include "itx_packet.h"

#include <string.h>

namespace itx {

static void putLe16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void putLe32(uint8_t *p, uint32_t v) {
  for (int i = 0; i < 4; i++) p[i] = (uint8_t)(v >> (8 * i));
}
static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t le32(const uint8_t *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static size_t withText(uint8_t *out, uint8_t type, const char *text, size_t max) {
  out[0] = type;
  size_t n = 0;
  if (text)
    while (text[n] && n < max) { out[2 + n] = (uint8_t)text[n]; n++; }
  out[1] = (uint8_t)n;
  return 2 + n;
}

size_t buildHeartbeat(uint8_t *out) { out[0] = PKT_HEARTBEAT; out[1] = 0; return 2; }
size_t buildEnd(uint8_t *out, const char *reason) { return withText(out, PKT_END, reason, 20); }
size_t buildReject(uint8_t *out, const char *reason) { return withText(out, PKT_REJECT, reason, 20); }
size_t buildAck(uint8_t *out, uint8_t printed) {
  out[0] = PKT_ACKNOWLEDGE; out[1] = 1; out[2] = printed; return 3;
}

size_t buildVersion(uint8_t *out, const char *swId) {
  out[0] = PKT_VERSION;
  out[2] = kProtocolVersion;
  size_t n = 0;
  if (swId)
    while (swId[n] && n < 6) { out[3 + n] = (uint8_t)swId[n]; n++; }
  if (n < 6) out[3 + n++] = 0;   // piTelex pads a short id with one NUL
  out[1] = (uint8_t)(1 + n);
  return 3 + n;
}

size_t buildDirectDial(uint8_t *out, const char *ext) {
  out[0] = PKT_DIRECT_DIAL; out[1] = 1; out[2] = encodeExtension(ext); return 3;
}

size_t buildBaudot(uint8_t *out, const uint8_t *codes, size_t n) {
  if (n > kMaxBaudotPerPacket) n = kMaxBaudotPerPacket;
  out[0] = PKT_BAUDOT_DATA;
  out[1] = (uint8_t)n;
  memcpy(out + 2, codes, n);
  return 2 + n;
}

size_t buildConnectRemote(uint8_t *out, uint32_t number, uint16_t pin) {
  out[0] = PKT_CONNECT_REMOTE; out[1] = 6;
  putLe32(out + 2, number);
  putLe16(out + 6, pin);
  return 8;
}

size_t buildAcceptCall(uint8_t *out) { out[0] = PKT_ACCEPT_CALL; out[1] = 0; return 2; }

// Spec r874: 0 none; 1..99 -> "01".."99"; 100 -> "00"; 101..109 -> "1".."9";
// 110 -> "0"; above that invalid.
uint8_t encodeExtension(const char *ext) {
  if (!ext || !ext[0]) return 0;
  const size_t len = strlen(ext);
  if (len > 2 || ext[0] < '0' || ext[0] > '9' || (len == 2 && (ext[1] < '0' || ext[1] > '9')))
    return 0;
  const int v = len == 1 ? ext[0] - '0' : (ext[0] - '0') * 10 + (ext[1] - '0');
  if (len == 1) return (uint8_t)(v == 0 ? 110 : 100 + v);
  return (uint8_t)(v == 0 ? 100 : v);
}

bool decodeExtension(uint8_t w, char out[3]) {
  out[0] = out[1] = out[2] = 0;
  if (w == 0) return true;
  if (w <= 99) { out[0] = (char)('0' + w / 10); out[1] = (char)('0' + w % 10); return true; }
  if (w == 100) { out[0] = '0'; out[1] = '0'; return true; }
  if (w <= 109) { out[0] = (char)('0' + (w - 100)); return true; }
  if (w == 110) { out[0] = '0'; return true; }
  return false;
}

// --- parser ---------------------------------------------------------------------

bool PacketParser::isPacketType(uint8_t b) const {
  if (b <= 0x09 || (b >= 0x10 && b <= 0x1F)) return true;   // station types
  if (kind_ == StreamKind::Centralex)
    return (b >= PKT_CONNECT_REMOTE && b <= PKT_ACCEPT_CALL) || b == PKT_ERROR;
  return false;
}

PacketParser::Out PacketParser::feed(uint8_t b) {
  switch (st_) {
    case St::Type:
      if (telnetSkip_) { telnetSkip_--; return Out::None; }
      if (kind_ == StreamKind::Station && b == 0xFF) {   // telnet IAC + 2 bytes
        telnetSkip_ = 2;
        return Out::None;
      }
      if (!isPacketType(b)) { ascii_ = b; return Out::Ascii; }
      pkt_.type = b;
      st_ = St::Len;
      return Out::None;
    case St::Len:
      pkt_.len = b;
      got_ = 0;
      if (b == 0) { st_ = St::Type; return Out::Packet; }
      st_ = St::Data;
      return Out::None;
    case St::Data:
      pkt_.data[got_++] = b;
      if (got_ == pkt_.len) { st_ = St::Type; return Out::Packet; }
      return Out::None;
  }
  return Out::None;
}

// --- subscriber server ----------------------------------------------------------

size_t buildPeerQuery(uint8_t *out, uint32_t number) {
  out[0] = 0x03; out[1] = 0x05;
  putLe32(out + 2, number);
  out[6] = 0x01;   // highest reply version we understand
  return 7;
}

size_t buildClientUpdate(uint8_t *out, uint32_t number, uint16_t pin, uint16_t port) {
  out[0] = 0x01; out[1] = 0x08;
  putLe32(out + 2, number);
  putLe16(out + 6, pin);
  putLe16(out + 8, port);
  return 10;
}

static void copyZ(char *dst, const uint8_t *src, size_t n) {
  size_t i = 0;
  for (; i < n && src[i]; i++) dst[i] = (char)src[i];   // ISO 8859-1, kept as bytes
  dst[i] = 0;
}

// Peer_reply_v1 (0x05, length 0x64): number 4, name 40, flags 2, type 1,
// hostname 40, IPv4 4, port 2, extension 1, pin 2, date 4.
PeerReply parsePeerReply(const uint8_t *buf, size_t len, PeerInfo *out) {
  if (len < 2) return PeerReply::Incomplete;
  if (buf[0] == 0x04) return PeerReply::NotFound;
  if (buf[0] != 0x05 || buf[1] != 0x64) return PeerReply::Invalid;
  if (len < 2 + 0x64) return PeerReply::Incomplete;
  const uint8_t *p = buf + 2;
  memset(out, 0, sizeof(*out));
  out->number = le32(p);
  copyZ(out->name, p + 4, 40);
  out->type = (PeerType)p[46];
  const uint8_t *ip = p + 87;
  out->port = le16(p + 91);
  if (!decodeExtension(p[93], out->ext)) out->ext[0] = 0;
  switch (out->type) {
    case PeerType::BaudotHost: case PeerType::AsciiHost:
      copyZ(out->host, p + 47, 40);
      break;
    case PeerType::BaudotIp: case PeerType::AsciiIp: case PeerType::BaudotDynIp: {
      char *h = out->host;
      for (int i = 0; i < 4; i++) {
        unsigned v = ip[i];
        char tmp[4]; int k = 0;
        do { tmp[k++] = (char)('0' + v % 10); v /= 10; } while (v);
        while (k) *h++ = tmp[--k];
        if (i < 3) *h++ = '.';
      }
      *h = 0;
      break;
    }
    default:
      return PeerReply::Unusable;   // deleted, e-mail
  }
  out->ascii = out->type == PeerType::AsciiHost || out->type == PeerType::AsciiIp;
  return PeerReply::Found;
}

}  // namespace itx
