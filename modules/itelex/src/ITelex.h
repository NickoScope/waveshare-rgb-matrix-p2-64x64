#pragma once
// ITelex - a teletype station for any ESP32 (Arduino core), speaking the
// i-Telex protocol. Plug and play: include this header, fill a StationConfig,
// call begin() once and loop() often. Nothing here knows about the LED panel.
//
//   #include <ITelex.h>
//   itx::Station station;
//   station.begin(cfg, events);      // after Wi-Fi is up
//   station.loop();                  // from loop() or a task, often
//   station.dial("10002");           // phonebook, the public TNS, or "host:port"
//   station.send("УЖИН В 8\r\n");
//
// One call at a time, like a teleprinter. A call that arrives while one is in
// progress is turned away with "occ" (occupied), the i-Telex way.
//
// Where the calls come from:
//   - the LAN / tailnet: we listen on StationConfig::listenPort (134);
//   - Centralex (optional): a standing outbound line to a relay, so the public
//     i-Telex network can reach a station with no public IPv4 and no port
//     forwarding. Needs a number registered at the TNS as "dynamic IP", with
//     its PIN, from the i-Telex administrators.
//
// Blocking: dial() and the Centralex (re)connect wait for a TCP connect, at
// most connectTimeoutMs. Everything else in loop() is non-blocking. On a
// device whose loop() must never wait, run the station on its own task.
//
// See README.md for the memory cost and what is not implemented.

#if defined(ARDUINO)

#include <Arduino.h>
#include <WiFi.h>

#include "itx_baudot.h"
#include "itx_packet.h"
#include "itx_session.h"

namespace itx {

struct PhonebookEntry {
  uint32_t number;      // what people dial, e.g. 10001
  const char *host;     // IPv4 or DNS name reachable from this device
  uint16_t port;        // usually 134
  const char *ext;      // direct-dial extension, "" for none
  bool ascii;           // the peer speaks plain ASCII (a telnet-style station)
  const char *name;     // for the display, e.g. "КУХНЯ"
};

struct StationConfig {
  SessionConfig session;              // coding, answerback, timeouts
  uint16_t listenPort = kDefaultStationPort;   // 0: accept no direct calls
  uint32_t connectTimeoutMs = 3000;

  const PhonebookEntry *phonebook = nullptr;   // the family's numbers
  size_t phonebookLen = 0;

  bool useTns = false;                // look up other numbers at a subscriber server
  const char *tnsHost = "tlnserv.teleprinter.net";
  uint16_t tnsPort = kTnsPort;

  bool centralex = false;             // hold a line to a Centralex relay
  uint32_t number = 0;                // our i-Telex number (Centralex login)
  uint16_t pin = 0;                   // its TNS PIN
  const char *centralexHost = "tlnserv2.teleprinter.net";
  uint16_t centralexPort = kCentralexPort;
};

struct StationEvents {
  void *ctx = nullptr;
  // peer: the caller's IP for an incoming call, the dialled target otherwise
  void (*onCallStart)(void *ctx, bool incoming, bool ascii, const char *peer) = nullptr;
  void (*onChar)(void *ctx, uint32_t cp) = nullptr;
  void (*onWru)(void *ctx) = nullptr;
  void (*onCallEnd)(void *ctx, const char *reason) = nullptr;
  void (*onStatus)(void *ctx, const char *status) = nullptr;   // log line, optional
};

class Station {
 public:
  bool begin(const StationConfig &cfg, const StationEvents &ev);
  void end();
  void loop();

  // "10002" (phonebook, then the TNS if enabled) or "host" / "host:port".
  bool dial(const char *target);
  size_t send(const char *utf8) { return inCall_ ? session_.send(utf8) : 0; }
  bool sendWru() { return inCall_ && session_.sendWru(); }
  void printed(uint16_t chars) { session_.printed(chars); }
  void setAutoPrinted(bool on) { autoPrinted_ = on; session_.setAutoPrinted(on); }
  void hangup() { if (inCall_) session_.hangup(); }

  bool inCall() const { return inCall_; }
  bool centralexReady() const { return cx_ == Cx::Standby; }
  const char *peer() const { return peer_; }
  Session &session() { return session_; }

 private:
  enum class Cx : uint8_t { Off, WaitConfirm, Standby };

  bool lookup(const char *target, char *host, size_t hostCap, uint16_t *port,
              char ext[3], bool *ascii);
  bool queryTns(uint32_t number, PeerInfo *out);
  void startCall(Session::Role role, bool ascii, const char *ext, const char *peer);
  void pumpCall(uint32_t now);
  void pumpCentralex(uint32_t now);
  void acceptDirect();
  void cxDrop(const char *why, uint32_t now);
  void status(const char *s) { if (ev_.onStatus) ev_.onStatus(ev_.ctx, s); }

  static size_t tWrite(void *ctx, const uint8_t *d, size_t n);
  static void tConnected(void *ctx, bool ascii);
  static void tChar(void *ctx, uint32_t cp);
  static void tWru(void *ctx);
  static void tEnd(void *ctx, const char *reason);

  StationConfig cfg_{};
  StationEvents ev_{};
  WiFiServer *server_ = nullptr;
  WiFiClient call_;
  WiFiClient cxClient_;
  Session session_;
  PacketParser cxParser_{StreamKind::Centralex};

  bool started_ = false;
  bool inCall_ = false;
  bool incoming_ = false;
  bool callViaCx_ = false;
  bool autoPrinted_ = false;
  char peer_[48] = {0};

  Cx cx_ = Cx::Off;
  uint32_t cxNextTry_ = 0, cxLastRx_ = 0, cxLastTx_ = 0, cxSince_ = 0;
};

}  // namespace itx

#endif  // ARDUINO
