#include "itx_session.h"

#include <string.h>

namespace itx {

static constexpr uint32_t kAckEveryMs = 1000;       // piTelex: every second while connected
static constexpr uint32_t kClosingMaxMs = 10000;    // give up flushing after this
static constexpr uint8_t kCodesPerPacket = 40;      // piTelex sends ≤ 40 per packet
static constexpr uint32_t kCodingWaitMs = 3000;     // caller: wait this long for the peer's Version

// The WRU request travels through the (UTF-8) send queue as a private-use
// character, so it keeps its place among the text.
static const char kWruUtf8[] = "\xEE\x80\x80";   // U+E000 == kWru

void Session::begin(Role role, bool ascii, const char *ext, const SessionConfig &cfg,
                    const SessionHandlers &h, uint32_t now) {
  cfg_ = cfg;
  h_ = h;
  role_ = role;
  state_ = State::Open;
  ascii_ = -1;
  parser_.setKind(StreamKind::Station);
  enc_ = BaudotEncoder(cfg.coding);
  dec_ = BaudotDecoder(cfg.coding);
  txHead_ = txTail_ = 0;
  outLen_ = 0;
  costHead_ = costTail_ = 0;
  shiftCost_ = 0;
  ackCounter_ = ackSent_ = 0;
  sent_ = peerAck_ = 0;
  havePeerAck_ = false;
  versionSent_ = false;
  codingSettled_ = role == Role::Called;   // a called station hears the caller's Version first
  peerFamily_ = false;
  openedAt_ = now;
  utf8Len_ = utf8Need_ = 0;
  lastRx_ = lastAck_ = now;
  closeReason_ = nullptr;
  ext_[0] = ext_[1] = ext_[2] = 0;
  if (ext) { strncpy(ext_, ext, 2); }

  if (role == Role::Caller) {
    if (!ascii) {
      // The order piTelex's client uses: Version, then Direct Dial.
      uint8_t p[16];
      writeRaw(p, buildVersion(p, cfg_.swId));
      versionSent_ = true;
      writeRaw(p, buildDirectDial(p, ext_));
    }
    open(ascii, now);
  } else if (ascii) {
    // A port that is ASCII by contract (a Minitel, a terminal app): no guessing.
    // Minitel keys start with bytes that look like i-Telex packet types
    // (Envoi = DC3 0x13, accents = SS2 0x19, ESC 0x1B), so detection would fail.
    open(true, now);
  }
}

void Session::open(bool ascii, uint32_t now) {
  ascii_ = ascii ? 1 : 0;
  lastRx_ = now;
  if (h_.onConnected) h_.onConnected(h_.ctx, ascii);
}

void Session::close(const char *reason, bool sendEnd) {
  if (state_ == State::Closed) return;
  if (sendEnd && ascii_ == 0) {
    uint8_t p[4];
    writeRaw(p, buildEnd(p));
  }
  state_ = State::Closed;
  closeReason_ = reason;
  if (h_.onEnd) h_.onEnd(h_.ctx, reason);
}

void Session::transportClosed() { close("closed", false); }

void Session::hangup(const char *reason) {
  if (state_ != State::Open) return;
  state_ = State::Closing;
  closeReason_ = reason;
  closingSince_ = 0;   // stamped by the next poll()
}

// --- receiving ------------------------------------------------------------------

void Session::feed(const uint8_t *d, size_t n, uint32_t now) {
  if (state_ == State::Closed || state_ == State::Idle) return;
  lastRx_ = now;
  for (size_t i = 0; i < n && state_ != State::Closed; i++) {
    const uint8_t b = d[i];
    if (ascii_ == 1) { onAsciiByte(b, now); continue; }
    switch (parser_.feed(b)) {
      case PacketParser::Out::None: break;
      case PacketParser::Out::Packet: onPacket(parser_.packet(), now); break;
      case PacketParser::Out::Ascii:
        if (ascii_ == 0) break;   // stray byte inside a binary call: ignore
        if (!cfg_.acceptAscii) { close("ascii refused", false); break; }
        open(true, now);
        onAsciiByte(parser_.asciiByte(), now);
        break;
    }
  }
}

void Session::onPacket(const Packet &p, uint32_t now) {
  if (ascii_ < 0) open(false, now);
  switch (p.type) {
    case PKT_HEARTBEAT: break;
    case PKT_DIRECT_DIAL:
      if (p.len == 1 && !decodeExtension(p.data[0], ext_)) ext_[0] = 0;
      break;
    case PKT_VERSION:
      onPeerVersion(p);
      if (role_ == Role::Called && !versionSent_) {
        uint8_t v[16];
        writeRaw(v, buildVersion(v, cfg_.swId));
        versionSent_ = true;
      }
      break;
    case PKT_BAUDOT_DATA:
      for (uint8_t i = 0; i < p.len; i++) {
        const uint32_t cp = dec_.decode(p.data[i]);
        if (shiftCost_ < 255) shiftCost_++;
        if (cp == kNone) continue;   // its cost rides on the next character
        const uint8_t cost = shiftCost_;
        shiftCost_ = 0;
        if (cp == kWru) {
          ackCounter_ = (uint8_t)(ackCounter_ + cost);   // nothing to show
          if (h_.onWru) h_.onWru(h_.ctx);
          if (cfg_.answerback && cfg_.answerback[0]) {
            send("\r\n");
            send(cfg_.answerback);
          }
          continue;
        }
        deliver(cp, cost);
      }
      break;
    case PKT_END: close("end", false); break;
    case PKT_REJECT: close("rejected", false); break;
    case PKT_ACKNOWLEDGE:
      if (p.len == 1) { peerAck_ = p.data[0]; havePeerAck_ = true; }
      codingSettled_ = true;   // an answer without a Version: a plain i-Telex peer
      break;
    default: break;   // self test, remote config, reserved: ignore
  }
}

// Version: [protocol version][software id, NUL-padded]. "nk01" is ours, "pi..."
// is piTelex. Only a peer whose id starts with familyTag gets MTK-2.
void Session::onPeerVersion(const Packet &p) {
  bool family = false;
  const char *tag = cfg_.familyTag;
  if (tag && tag[0] && p.len > 1) {
    size_t n = strlen(tag);
    family = (size_t)(p.len - 1) >= n && memcmp(p.data + 1, tag, n) == 0;
  }
  if (!codingSettled_ || family != peerFamily_) {
    peerFamily_ = family;
    const Coding c = family ? cfg_.familyCoding : cfg_.coding;
    enc_ = BaudotEncoder(c);
    dec_ = BaudotDecoder(c);
  }
  codingSettled_ = true;
}

void Session::onAsciiByte(uint8_t b, uint32_t now) {
  (void)now;
  // Telnet negotiation from a terminal app: IAC + command + option.
  if (utf8Need_ == 0 && b == 0xFF) { utf8Need_ = 0xFE; utf8Len_ = 2; return; }
  if (utf8Need_ == 0xFE) { if (--utf8Len_ == 0) utf8Need_ = 0; return; }

  if (utf8Need_ == 0) {
    if (b < 0x80) {
      if (b == '\r' || b == '\n' || b == 0x07 || b >= 0x20) deliver(b, 1);
      return;
    }
    utf8Buf_[0] = b;
    utf8Len_ = 1;
    utf8Need_ = (b & 0xE0) == 0xC0 ? 2 : (b & 0xF0) == 0xE0 ? 3 : (b & 0xF8) == 0xF0 ? 4 : 1;
    if (utf8Need_ == 1) { utf8Need_ = 0; deliver(0xFFFD, 1); }
    return;
  }
  utf8Buf_[utf8Len_++] = b;
  if (utf8Len_ < utf8Need_) return;
  size_t i = 0;
  const uint32_t cp = utf8Next((const char *)utf8Buf_, utf8Len_, &i);
  deliver(cp, utf8Len_);
  utf8Need_ = utf8Len_ = 0;
}

void Session::deliver(uint32_t cp, uint8_t cost) {
  if (autoPrinted_ || ascii_ == 1) {
    ackCounter_ = (uint8_t)(ackCounter_ + cost);
  } else if (((costTail_ + 1) & (kCost - 1)) != costHead_) {
    cost_[costTail_] = cost;
    costTail_ = (uint16_t)((costTail_ + 1) & (kCost - 1));
  } else {
    ackCounter_ = (uint8_t)(ackCounter_ + cost);   // owner far behind: do not stall the peer
  }
  if (h_.onChar) h_.onChar(h_.ctx, cp);
}

void Session::printed(uint16_t chars) {
  while (chars-- && costHead_ != costTail_) {
    ackCounter_ = (uint8_t)(ackCounter_ + cost_[costHead_]);
    costHead_ = (uint16_t)((costHead_ + 1) & (kCost - 1));
  }
}

// --- sending --------------------------------------------------------------------

bool Session::writeRaw(const uint8_t *d, size_t n) {
  if (!h_.write) return false;
  if (outLen_) {   // something older is still waiting: keep order
    if (outLen_ + n > sizeof(out_)) return false;
    memcpy(out_ + outLen_, d, n);
    outLen_ = (uint8_t)(outLen_ + n);
    return false;
  }
  const size_t w = h_.write(h_.ctx, d, n);
  if (w >= n) return true;
  const size_t rest = n - w;
  if (rest > sizeof(out_)) return false;
  memcpy(out_, d + w, rest);
  outLen_ = (uint8_t)rest;
  return false;
}

void Session::flushOut() {
  if (!outLen_ || !h_.write) return;
  const size_t w = h_.write(h_.ctx, out_, outLen_);
  if (w >= outLen_) { outLen_ = 0; return; }
  memmove(out_, out_ + w, outLen_ - w);
  outLen_ = (uint8_t)(outLen_ - w);
}

size_t Session::queueBytes(const uint8_t *b, size_t n) {
  if (kTx - 1 - txCount() < n) return 0;   // all or nothing: never half a character
  for (size_t i = 0; i < n; i++) {
    tx_[txTail_] = b[i];
    txTail_ = (uint16_t)((txTail_ + 1) & (kTx - 1));
  }
  return n;
}

size_t Session::send(const char *s) { return s ? send(s, strlen(s)) : 0; }

size_t Session::send(const char *s, size_t len) {
  if (state_ != State::Open || !s) return 0;
  // Queued as UTF-8 and encoded only when sent: by then the caller knows
  // whether the peer is one of ours (MTK-2) or the wider network (ITA2).
  size_t i = 0;
  while (i < len) {
    const size_t start = i;
    utf8Next(s, len, &i);
    if (!queueBytes((const uint8_t *)s + start, i - start)) return start;
  }
  return len;
}

bool Session::sendWru() {
  if (state_ != State::Open || ascii_ == 1) return false;
  return queueBytes((const uint8_t *)kWruUtf8, 3) == 3;
}

uint8_t Session::inFlight() const {
  if (!havePeerAck_) return sent_;
  const uint8_t d = (uint8_t)(sent_ - peerAck_);
  // A peer that starts its counter below zero (piTelex server: -24 for its own
  // welcome banner) looks like ~230 codes in flight. Treat that as none.
  return d > 200 ? 0 : d;
}

// Length of the UTF-8 sequence that starts with b (1 for a stray byte).
static size_t utf8Len(uint8_t b) {
  return (b & 0xE0) == 0xC0 ? 2 : (b & 0xF0) == 0xE0 ? 3 : (b & 0xF8) == 0xF0 ? 4 : 1;
}

void Session::pumpBinary(uint32_t now) {
  if (!codingSettled_) {
    if (now - openedAt_ < kCodingWaitMs) return;   // the peer's Version decides the code
    codingSettled_ = true;                          // silence: the network's ITA2
  }
  while (txCount() && !outLen_) {
    const uint8_t fl = inFlight();
    if (fl >= cfg_.window) break;
    size_t budget = (size_t)(cfg_.window - fl);
    if (budget > kCodesPerPacket) budget = kCodesPerPacket;
    uint8_t codes[kCodesPerPacket];
    size_t n = 0;
    while (txCount()) {
      char ch[4];
      const size_t L = utf8Len(tx_[txHead_]);
      if (txCount() < L) break;   // cannot happen: whole characters are queued
      for (size_t k = 0; k < L; k++) ch[k] = (char)tx_[(txHead_ + k) & (kTx - 1)];
      size_t i = 0;
      const uint32_t cp = utf8Next(ch, L, &i);
      const BaudotEncoder saved = enc_;
      uint8_t c[kMaxCodesPerChar];
      const size_t m = cp == kWru ? enc_.encodeWru(c) : enc_.encode(cp, c);
      if (n + m > budget) { enc_ = saved; break; }   // next packet, next window
      memcpy(codes + n, c, m);
      n += m;
      txHead_ = (uint16_t)((txHead_ + L) & (kTx - 1));
    }
    if (!n) break;
    uint8_t p[2 + kCodesPerPacket];
    const size_t plen = buildBaudot(p, codes, n);
    sent_ = (uint8_t)(sent_ + n);
    writeRaw(p, plen);
  }
}

void Session::pumpAscii() {
  while (txCount() && !outLen_) {
    uint8_t b[64];
    size_t n = txCount();
    if (n > sizeof(b)) n = sizeof(b);
    for (size_t i = 0; i < n; i++) b[i] = tx_[(txHead_ + i) & (kTx - 1)];
    txHead_ = (uint16_t)((txHead_ + n) & (kTx - 1));
    writeRaw(b, n);   // sendWru() refuses ASCII calls, so no marker reaches here
  }
}

void Session::poll(uint32_t now) {
  if (state_ == State::Idle || state_ == State::Closed) return;
  flushOut();

  const uint32_t idle = ascii_ == 1 ? cfg_.asciiIdleTimeoutMs : cfg_.idleTimeoutMs;
  if (now - lastRx_ > idle) { close("timeout", true); return; }

  if (ascii_ == 0) {
    if (now - lastAck_ >= kAckEveryMs || (uint8_t)(ackCounter_ - ackSent_) >= 8) {
      uint8_t p[4];
      writeRaw(p, buildAck(p, ackCounter_));
      ackSent_ = ackCounter_;
      lastAck_ = now;
    }
    pumpBinary(now);
  } else if (ascii_ == 1) {
    pumpAscii();
  }

  if (state_ == State::Closing) {
    if (!closingSince_) closingSince_ = now ? now : 1;
    // Binary: wait until the peer has acknowledged what we sent, so the
    // telegram is on its paper (or screen) before we ring off.
    const bool drained = sendQueueEmpty() && (ascii_ != 0 || inFlight() == 0);
    if (drained || now - closingSince_ > kClosingMaxMs) close(closeReason_, true);
  }
}

}  // namespace itx
