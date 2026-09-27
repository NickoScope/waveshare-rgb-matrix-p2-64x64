#if defined(ARDUINO)

#include "ITelex.h"

#include <string.h>

namespace itx {

static constexpr uint32_t kCxConfirmMs = 10000;     // login must be confirmed by then
static constexpr uint32_t kCxHeartbeatMs = 15000;   // piTelex: send one every 15 s
static constexpr uint32_t kCxSilenceMs = 35000;     // and gives up after 35 s of silence
static constexpr uint32_t kCxRetryMs = 15000;       // after an error
static constexpr uint32_t kCxRedialMs = 2000;       // after a call through the relay

// --- session callbacks ------------------------------------------------------------

size_t Station::tWrite(void *ctx, const uint8_t *d, size_t n) {
  Station *s = (Station *)ctx;
  if (!s->call_.connected()) return n;   // swallow: the call is ending anyway
  return s->call_.write(d, n);
}
void Station::tConnected(void *ctx, bool ascii) {
  Station *s = (Station *)ctx;
  if (s->ev_.onCallStart) s->ev_.onCallStart(s->ev_.ctx, s->incoming_, ascii, s->peer_);
}
void Station::tChar(void *ctx, uint32_t cp) {
  Station *s = (Station *)ctx;
  if (s->ev_.onChar) s->ev_.onChar(s->ev_.ctx, cp);
}
void Station::tWru(void *ctx) {
  Station *s = (Station *)ctx;
  if (s->ev_.onWru) s->ev_.onWru(s->ev_.ctx);
}
void Station::tEnd(void *ctx, const char *reason) {
  Station *s = (Station *)ctx;
  if (s->ev_.onCallEnd) s->ev_.onCallEnd(s->ev_.ctx, reason);
}

// --- life cycle ------------------------------------------------------------------

bool Station::begin(const StationConfig &cfg, const StationEvents &ev) {
  end();
  cfg_ = cfg;
  ev_ = ev;
  if (cfg_.listenPort) {
    server_ = new WiFiServer(cfg_.listenPort);
    server_->begin();
    server_->setNoDelay(true);
  }
  if (cfg_.asciiListenPort) {
    asciiServer_ = new WiFiServer(cfg_.asciiListenPort);
    asciiServer_->begin();
    asciiServer_->setNoDelay(true);
  }
  cx_ = Cx::Off;
  cxNextTry_ = millis();
  started_ = true;
  status(cfg_.listenPort ? "itx: listening" : "itx: started, not listening");
  return true;
}

void Station::end() {
  if (inCall_) { session_.transportClosed(); call_.stop(); inCall_ = false; }
  if (server_) { server_->end(); delete server_; server_ = nullptr; }
  if (asciiServer_) { asciiServer_->end(); delete asciiServer_; asciiServer_ = nullptr; }
  cxClient_.stop();
  cx_ = Cx::Off;
  started_ = false;
}

void Station::loop() {
  if (!started_) return;
  const uint32_t now = millis();
  acceptDirect();
  if (inCall_) pumpCall(now);
  if (cfg_.centralex && !(inCall_ && callViaCx_)) pumpCentralex(now);
}

// --- calls -----------------------------------------------------------------------

void Station::startCall(Session::Role role, bool ascii, const char *ext, const char *peer) {
  incoming_ = role == Session::Role::Called;
  strncpy(peer_, peer ? peer : "", sizeof(peer_) - 1);
  peer_[sizeof(peer_) - 1] = 0;
  call_.setNoDelay(true);
  SessionHandlers h;
  h.ctx = this;
  h.write = tWrite;
  h.onConnected = tConnected;
  h.onChar = tChar;
  h.onWru = tWru;
  h.onEnd = tEnd;
  inCall_ = true;
  session_.begin(role, ascii, ext, cfg_.session, h, millis());
  session_.setAutoPrinted(autoPrinted_);
}

void Station::acceptDirect() {
  acceptOn(server_, false);
  acceptOn(asciiServer_, true);
}

void Station::acceptOn(WiFiServer *srv, bool ascii) {
  if (!srv || !srv->hasClient()) return;
  WiFiClient c = srv->available();
  if (!c) return;
  if (inCall_) {
    if (ascii) {
      c.print("occ\r\n");
    } else {
      uint8_t r[8];
      c.write(r, buildReject(r, "occ"));
    }
    c.stop();
    status("itx: second caller turned away (occ)");
    return;
  }
  call_ = c;
  callViaCx_ = false;
  const String ip = c.remoteIP().toString();
  startCall(Session::Role::Called, ascii, nullptr, ip.c_str());
}

void Station::pumpCall(uint32_t now) {
  uint8_t buf[128];
  int budget = 4;   // bounded work per loop()
  while (budget-- && call_.available() > 0) {
    const int n = call_.read(buf, sizeof(buf));
    if (n <= 0) break;
    session_.feed(buf, (size_t)n, now);
  }
  session_.poll(now);
  if (session_.state() != Session::State::Closed && !call_.connected() && !call_.available())
    session_.transportClosed();
  if (session_.state() == Session::State::Closed) {
    call_.flush();
    call_.stop();
    inCall_ = false;
    if (callViaCx_) {   // the relay line was used for the call: log in again
      callViaCx_ = false;
      cx_ = Cx::Off;
      cxNextTry_ = now + kCxRedialMs;
    }
  }
}

bool Station::dial(const char *target) {
  if (!started_ || inCall_ || !target || !*target) return false;
  char host[64];
  uint16_t port = kDefaultStationPort;
  char ext[3] = {0, 0, 0};
  bool ascii = false;
  if (!lookup(target, host, sizeof(host), &port, ext, &ascii)) {
    status("itx: number not found");
    return false;
  }
  WiFiClient c;
  if (!c.connect(host, port, (int32_t)cfg_.connectTimeoutMs)) {
    status("itx: no answer from the number");
    return false;
  }
  call_ = c;
  callViaCx_ = false;
  startCall(Session::Role::Caller, ascii, ext, target);
  return true;
}

bool Station::lookup(const char *t, char *host, size_t cap, uint16_t *port, char ext[3],
                     bool *ascii) {
  bool digits = true;
  for (const char *p = t; *p; p++) digits = digits && *p >= '0' && *p <= '9';
  if (!digits) {   // "host" or "host:port"
    const char *colon = strrchr(t, ':');
    size_t n = colon ? (size_t)(colon - t) : strlen(t);
    if (n >= cap) return false;
    memcpy(host, t, n);
    host[n] = 0;
    if (colon) *port = (uint16_t)atoi(colon + 1);
    return true;
  }
  const uint32_t number = (uint32_t)strtoul(t, nullptr, 10);
  for (size_t i = 0; i < cfg_.phonebookLen; i++) {
    const PhonebookEntry &e = cfg_.phonebook[i];
    if (e.number != number) continue;
    strncpy(host, e.host, cap - 1);
    host[cap - 1] = 0;
    *port = e.port ? e.port : kDefaultStationPort;
    strncpy(ext, e.ext ? e.ext : "", 2);
    *ascii = e.ascii;
    return true;
  }
  if (!cfg_.useTns) return false;
  PeerInfo pi;
  if (!queryTns(number, &pi)) return false;
  strncpy(host, pi.host, cap - 1);
  host[cap - 1] = 0;
  *port = pi.port;
  memcpy(ext, pi.ext, 3);
  *ascii = pi.ascii;
  return true;
}

bool Station::queryTns(uint32_t number, PeerInfo *out) {
  WiFiClient c;
  if (!c.connect(cfg_.tnsHost, cfg_.tnsPort, (int32_t)cfg_.connectTimeoutMs)) return false;
  uint8_t q[8];
  c.write(q, buildPeerQuery(q, number));
  uint8_t r[2 + 0x64];
  size_t got = 0;
  const uint32_t t0 = millis();
  PeerReply res = PeerReply::Incomplete;
  while (millis() - t0 < cfg_.connectTimeoutMs) {
    while (c.available() > 0 && got < sizeof(r)) r[got++] = (uint8_t)c.read();
    res = parsePeerReply(r, got, out);
    if (res != PeerReply::Incomplete) break;
    if (!c.connected()) break;
    delay(5);
  }
  c.stop();
  return res == PeerReply::Found;
}

// --- Centralex -------------------------------------------------------------------

void Station::cxDrop(const char *why, uint32_t now) {
  cxClient_.stop();
  cx_ = Cx::Off;
  cxNextTry_ = now + kCxRetryMs;
  status(why);
}

void Station::pumpCentralex(uint32_t now) {
  switch (cx_) {
    case Cx::Off: {
      if ((int32_t)(now - cxNextTry_) < 0) return;
      if (!cfg_.number || !cfg_.pin) { cxNextTry_ = now + 60000; status("itx: centralex needs number and pin"); return; }
      if (!cxClient_.connect(cfg_.centralexHost, cfg_.centralexPort, (int32_t)cfg_.connectTimeoutMs)) {
        cxDrop("itx: centralex unreachable", now);
        return;
      }
      cxClient_.setNoDelay(true);
      uint8_t p[8];
      cxClient_.write(p, buildConnectRemote(p, cfg_.number, cfg_.pin));
      cxParser_.setKind(StreamKind::Centralex);
      cx_ = Cx::WaitConfirm;
      cxSince_ = cxLastRx_ = cxLastTx_ = now;
      return;
    }
    case Cx::WaitConfirm:
    case Cx::Standby:
      break;
  }

  if (!cxClient_.connected()) { cxDrop("itx: centralex line lost", now); return; }
  int budget = 64;
  while (budget-- > 0 && cxClient_.available() > 0) {
    const uint8_t b = (uint8_t)cxClient_.read();
    cxLastRx_ = now;
    if (cxParser_.feed(b) != PacketParser::Out::Packet) continue;
    const Packet &p = cxParser_.packet();
    if (p.type == PKT_REMOTE_CONFIRM && cx_ == Cx::WaitConfirm) {
      cx_ = Cx::Standby;
      status("itx: centralex ready");
    } else if (p.type == PKT_REJECT || p.type == PKT_ERROR) {
      cxDrop("itx: centralex refused the login (number/pin/dyn-ip?)", now);
      return;
    } else if (p.type == PKT_REMOTE_CALL && cx_ == Cx::Standby) {
      uint8_t a[4];
      if (inCall_) {   // busy with a direct call
        cxClient_.write(a, buildReject(a, "occ"));
        cxDrop("itx: centralex call turned away (occ)", now);
        cxNextTry_ = now + kCxRedialMs;
        return;
      }
      cxClient_.write(a, buildAcceptCall(a));
      // From here the relay line *is* the call.
      call_ = cxClient_;
      cxClient_ = WiFiClient();
      callViaCx_ = true;
      cx_ = Cx::Off;
      startCall(Session::Role::Called, false, nullptr, "centralex");
      return;   // the session reads whatever follows
    }
    // heartbeats and anything else just keep the line alive
  }

  if (cx_ == Cx::WaitConfirm && now - cxSince_ > kCxConfirmMs) {
    cxDrop("itx: centralex did not confirm", now);
    return;
  }
  if (cx_ == Cx::Standby) {
    if (now - cxLastRx_ > kCxSilenceMs) { cxDrop("itx: centralex silent", now); return; }
    if (now - cxLastTx_ >= kCxHeartbeatMs) {
      uint8_t h[2];
      cxClient_.write(h, buildHeartbeat(h));
      cxLastTx_ = now;
    }
  }
}

}  // namespace itx

#endif  // ARDUINO
