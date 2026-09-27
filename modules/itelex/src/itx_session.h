#pragma once
// One i-Telex call, both directions, with no socket in sight: bytes in through
// feed(), bytes out through the write callback, time through the millisecond
// clock the caller passes. That is what lets the same code run on the panel,
// on any other ESP32, and in the host test (two sessions wired back to back).
//
// What the session does for its owner:
//   - tells a binary i-Telex call from a plain ASCII one (a telnet user) by the
//     first bytes, as piTelex does;
//   - decodes Baudot / MTK-2 to Unicode characters and encodes UTF-8 text back;
//   - answers WRU ("Wer da? / КТО ТАМ?") with the station's answerback;
//   - keeps the i-Telex Acknowledge honest: the counter reports what the owner
//     says it has *shown* (printed()), not merely what arrived. That is the
//     telegraph's receipt, and on our panels it means "typed out on screen";
//   - throttles its own sending by the peer's Acknowledge, so a real 50-baud
//     teleprinter at the other end is never flooded;
//   - hangs up cleanly (End), notices a rejection, and times out a dead peer.
//
// Memory: ~1.2 KB per session, all inside the object; no allocation.

#include <stddef.h>
#include <stdint.h>

#include "itx_baudot.h"
#include "itx_packet.h"

namespace itx {

struct SessionConfig {
  Coding coding = Coding::MTK2;
  const char *answerback = "";      // e.g. "10001 KUX NIKOSCOPE", sent on WRU
  const char *swId = "nk01";        // Version packet id, ≤6 chars
  bool acceptAscii = true;          // let telnet users call in
  uint32_t idleTimeoutMs = 30000;   // binary call: silence this long = dead
  uint32_t asciiIdleTimeoutMs = 600000;   // a human typing is slow
  uint8_t window = 16;              // codes in flight before waiting for the peer
};

struct SessionHandlers {
  void *ctx = nullptr;
  // Transport. May accept fewer bytes than offered; the session keeps the rest.
  size_t (*write)(void *ctx, const uint8_t *data, size_t len) = nullptr;
  void (*onConnected)(void *ctx, bool ascii) = nullptr;
  void (*onChar)(void *ctx, uint32_t cp) = nullptr;   // one received character
  void (*onWru)(void *ctx) = nullptr;                 // already answered
  void (*onEnd)(void *ctx, const char *reason) = nullptr;   // exactly once
};

class Session {
 public:
  enum class Role : uint8_t { Caller, Called };
  enum class State : uint8_t { Idle, Open, Closing, Closed };

  // Caller: the TCP connection to the peer is up; `ascii` is the peer's type
  // from the directory, `ext` the direct-dial extension ("" for none).
  // Called: someone connected to us; the kind of call is detected.
  void begin(Role role, bool ascii, const char *ext, const SessionConfig &cfg,
             const SessionHandlers &h, uint32_t nowMs);

  void feed(const uint8_t *data, size_t len, uint32_t nowMs);
  void poll(uint32_t nowMs);          // timers and sending; call often

  size_t send(const char *utf8, size_t len);   // queue text; returns bytes taken
  size_t send(const char *utf8);
  bool sendWru();                     // ask the peer who it is

  // The owner has now shown `chars` more received characters. Without this
  // (autoPrinted), everything counts as shown on arrival.
  void printed(uint16_t chars);
  void setAutoPrinted(bool on) { autoPrinted_ = on; }

  void hangup(const char *reason = "hangup");   // after the queue is sent
  void transportClosed();                        // the socket is gone

  State state() const { return state_; }
  bool ascii() const { return ascii_ == 1; }
  bool sendQueueEmpty() const { return txHead_ == txTail_ && !outLen_; }
  uint8_t inFlight() const;           // codes sent, not yet acknowledged
  const char *extension() const { return ext_; }

 private:
  void open(bool ascii, uint32_t now);
  void close(const char *reason, bool sendEnd);
  void onPacket(const Packet &p, uint32_t now);
  void onAsciiByte(uint8_t b, uint32_t now);
  void deliver(uint32_t cp, uint8_t cost);
  bool writeRaw(const uint8_t *d, size_t n);   // false if it had to be kept
  void flushOut();
  size_t queueCodes(const uint8_t *c, size_t n);
  size_t queueBytes(const uint8_t *b, size_t n);
  size_t txCount() const { return (size_t)((txTail_ - txHead_) & (kTx - 1)); }
  void pumpBinary(uint32_t now);
  void pumpAscii();

  static constexpr size_t kTx = 512;     // outgoing codes (binary) or bytes (ASCII)
  static constexpr size_t kCost = 256;   // received chars not yet shown

  SessionConfig cfg_{};
  SessionHandlers h_{};
  Role role_ = Role::Called;
  State state_ = State::Idle;
  int8_t ascii_ = -1;                    // -1 not yet known
  PacketParser parser_{StreamKind::Station};
  BaudotEncoder enc_;
  BaudotDecoder dec_;
  char ext_[3] = {0, 0, 0};

  uint8_t tx_[kTx];
  uint16_t txHead_ = 0, txTail_ = 0;
  uint8_t out_[64];                      // a packet the transport did not take whole
  uint8_t outLen_ = 0;

  uint8_t cost_[kCost];                  // wire codes behind each unshown char
  uint16_t costHead_ = 0, costTail_ = 0;
  uint8_t shiftCost_ = 0;                // shifts waiting for their character
  uint8_t ackCounter_ = 0;               // what we tell the peer we printed
  uint8_t ackSent_ = 0;
  bool autoPrinted_ = false;

  uint8_t sent_ = 0;                     // codes we sent (mod 256)
  uint8_t peerAck_ = 0;
  bool havePeerAck_ = false;
  bool versionSent_ = false;

  uint8_t utf8Buf_[4];                   // ASCII calls: a character split across reads
  uint8_t utf8Len_ = 0, utf8Need_ = 0;

  uint32_t lastRx_ = 0, lastAck_ = 0, closingSince_ = 0;
  const char *closeReason_ = nullptr;
};

}  // namespace itx
