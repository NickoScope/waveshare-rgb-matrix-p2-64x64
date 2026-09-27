// Host tests for the i-Telex module: no Arduino, no network.
//   modules/itelex/test/run_host_tests.sh
//
// Reference vectors:
//   - Baudot: produced by piTelex ece3d43, txCode.BaudotMurrayCode(False,
//     coding, True) - the codec its i-Telex device uses on the wire. piTelex
//     starts every text with a LTRS shift even when the first character needs
//     another register; our encoder does not, so those vectors lose that one
//     leading 0x1F. Both decode to the same text.
//   - Packets: the worked examples of the i-Telex Communication Specification
//     (telexforum.de lexicon entry 74): Connect Remote for 5478221/PIN 46113,
//     Client_update and Peer_query for 3451414.

#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "itx_baudot.h"
#include "itx_packet.h"
#include "itx_session.h"

using namespace itx;

static int g_fail = 0, g_pass = 0;
#define CHECK(cond)                                                                  \
  do {                                                                               \
    if (cond) g_pass++;                                                              \
    else { g_fail++; std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); }   \
  } while (0)

static std::string hex(const std::vector<uint8_t> &v) {
  std::string s;
  char b[4];
  for (size_t i = 0; i < v.size(); i++) {
    std::snprintf(b, sizeof b, i ? " %02X" : "%02X", v[i]);
    s += b;
  }
  return s;
}

static std::vector<uint8_t> encodeText(const char *utf8, Coding c) {
  BaudotEncoder e(c);
  std::vector<uint8_t> out;
  size_t i = 0, len = std::strlen(utf8);
  while (i < len) {
    uint32_t cp = utf8Next(utf8, len, &i);
    uint8_t codes[kMaxCodesPerChar];
    size_t n = e.encode(cp, codes);
    out.insert(out.end(), codes, codes + n);
  }
  return out;
}

static std::string decodeCodes(const std::vector<uint8_t> &v, Coding c) {
  BaudotDecoder d(c);
  std::string s;
  for (uint8_t b : v) {
    uint32_t cp = d.decode(b);
    if (cp == kNone) continue;
    if (cp == kWru) { s += "<WRU>"; continue; }
    char u[4];
    s.append(u, utf8Put(cp, u));
  }
  return s;
}

static void expectCodes(const char *text, Coding c, const char *want) {
  std::string got = hex(encodeText(text, c));
  if (got != want) std::printf("  encode %s\n    got  %s\n    want %s\n", text, got.c_str(), want);
  CHECK(got == want);
}

static void testBaudot() {
  CHECK(flip5(0x01) == 0x10);
  CHECK(flip5(0x1F) == 0x1F);
  CHECK(flip5(0x1B) == 0x1B);
  CHECK(flip5(0x03) == 0x18);

  // Identical to piTelex (the text starts with a Latin letter):
  expectCodes("RY 123", Coding::ITA2, "1F 0A 15 04 1B 1D 19 10");
  expectCodes("HELLO, WORLD", Coding::ITA2, "1F 05 10 09 09 03 1B 06 04 1F 19 03 0A 09 12");
  expectCodes("ABC АБВ", Coding::MTK2, "1F 18 13 0E 04 00 18 13 19");
  // piTelex minus its leading 1F:
  expectCodes("ПРИВЕТ МИР", Coding::MTK2, "00 0D 0A 0C 19 10 01 04 07 0C 0A");
  expectCodes("ЭТО ЮГ 42", Coding::MTK2, "1B 16 00 01 03 04 1B 1A 00 0B 04 1B 0A 19");
  // lower case folds, Ё and Ъ are substituted
  CHECK(encodeText("привет", Coding::MTK2) == encodeText("ПРИВЕТ", Coding::MTK2));
  CHECK(decodeCodes(encodeText("Ёлка съел", Coding::MTK2), Coding::MTK2) == "ЕЛКА СЬЕЛ");

  // Round trips
  CHECK(decodeCodes(encodeText("ПРИВЕТ МИР", Coding::MTK2), Coding::MTK2) == "ПРИВЕТ МИР");
  CHECK(decodeCodes(encodeText("ЭТО ЮГ 42", Coding::MTK2), Coding::MTK2) == "ЭТО ЮГ 42");
  CHECK(decodeCodes(encodeText("Hello, world 1+1=2?", Coding::ITA2), Coding::ITA2) == "HELLO, WORLD 1+1=2?");
  CHECK(decodeCodes(encodeText("Line1\r\nLine2", Coding::ITA2), Coding::ITA2) == "LINE1\r\nLINE2");
  // piTelex's own vector decodes too (with its redundant leading LTRS)
  CHECK(decodeCodes({0x1F, 0x00, 0x0D, 0x0A, 0x0C, 0x19, 0x10, 0x01, 0x04, 0x07, 0x0C, 0x0A},
                    Coding::MTK2) == "ПРИВЕТ МИР");

  // ITA2 transliterates Russian so a plain teleprinter still reads it
  CHECK(decodeCodes(encodeText("Щука и ёж", Coding::ITA2), Coding::ITA2) == "SHCHUKA I EZH");
  // What neither code has becomes '?', emoji included
  CHECK(decodeCodes(encodeText("A\xF0\x9F\x98\x80" "B", Coding::MTK2), Coding::MTK2) == "A?B");

  // WRU is FIGS-D and decodes as WRU, not as a character
  {
    BaudotEncoder e(Coding::MTK2);
    uint8_t c[kMaxCodesPerChar];
    size_t n = e.encodeWru(c);
    CHECK(n == 2 && c[0] == 0x1B && c[1] == flip5(9));
    CHECK(decodeCodes(std::vector<uint8_t>(c, c + n), Coding::MTK2) == "<WRU>");
  }
  // In plain ITA2 code 0 is null, not a shift to Russian
  CHECK(decodeCodes({0x1F, 0x18, 0x00, 0x18}, Coding::ITA2) == "AA");

  // UTF-8 edge cases
  {
    const char bad[] = "\xD0";   // truncated two-byte sequence
    size_t i = 0;
    CHECK(utf8Next(bad, 1, &i) == 0xFFFD && i == 1);
  }
}

static std::vector<uint8_t> bytes(const uint8_t *p, size_t n) { return std::vector<uint8_t>(p, p + n); }

static void testPackets() {
  uint8_t b[128];
  CHECK(hex(bytes(b, buildConnectRemote(b, 5478221, 46113))) == "81 06 4D 97 53 00 21 B4");
  CHECK(hex(bytes(b, buildClientUpdate(b, 3451414, 4660, 134))) == "01 08 16 AA 34 00 34 12 86 00");
  CHECK(hex(bytes(b, buildPeerQuery(b, 3451414))) == "03 05 16 AA 34 00 01");
  CHECK(hex(bytes(b, buildAck(b, 0x2A))) == "06 01 2A");
  CHECK(hex(bytes(b, buildEnd(b))) == "03 00");
  CHECK(hex(bytes(b, buildReject(b, "occ"))) == "04 03 6F 63 63");
  CHECK(hex(bytes(b, buildVersion(b, "nk01"))) == "07 06 01 6E 6B 30 31 00");
  CHECK(hex(bytes(b, buildAcceptCall(b))) == "84 00");

  // Direct-dial extensions (spec r874 table)
  CHECK(encodeExtension("") == 0);
  CHECK(encodeExtension("01") == 1);
  CHECK(encodeExtension("99") == 99);
  CHECK(encodeExtension("00") == 100);
  CHECK(encodeExtension("1") == 101);
  CHECK(encodeExtension("9") == 109);
  CHECK(encodeExtension("0") == 110);
  char e[3];
  CHECK(decodeExtension(7, e) && std::string(e) == "07");
  CHECK(decodeExtension(105, e) && std::string(e) == "5");
  CHECK(decodeExtension(110, e) && std::string(e) == "0");
  CHECK(!decodeExtension(111, e));

  // Peer_reply_v1
  {
    uint8_t r[2 + 100] = {0x05, 0x64};
    uint8_t *p = r + 2;
    p[0] = 0x16; p[1] = 0xAA; p[2] = 0x34; p[3] = 0x00;      // 3451414
    std::memcpy(p + 4, "KUX NIKOSCOPE", 13);
    p[46] = 5;                                              // dynamic IP, Baudot
    p[87] = 192; p[88] = 168; p[89] = 1; p[90] = 57;
    p[91] = 134; p[92] = 0;
    p[93] = 105;                                            // extension "5"
    PeerInfo pi;
    CHECK(parsePeerReply(r, 50, &pi) == PeerReply::Incomplete);
    CHECK(parsePeerReply(r, sizeof r, &pi) == PeerReply::Found);
    CHECK(pi.number == 3451414);
    CHECK(std::string(pi.name) == "KUX NIKOSCOPE");
    CHECK(std::string(pi.host) == "192.168.1.57");
    CHECK(pi.port == 134);
    CHECK(std::string(pi.ext) == "5");
    CHECK(!pi.ascii);
    p[46] = 3;                                              // ASCII, hostname
    std::memcpy(p + 47, "panel.example", 13);
    CHECK(parsePeerReply(r, sizeof r, &pi) == PeerReply::Found);
    CHECK(pi.ascii && std::string(pi.host) == "panel.example");
    p[46] = 6;
    CHECK(parsePeerReply(r, sizeof r, &pi) == PeerReply::Unusable);
    const uint8_t nf[] = {0x04, 0x00};
    CHECK(parsePeerReply(nf, 2, &pi) == PeerReply::NotFound);
  }

  // Parser: packets split anywhere, ASCII told apart, telnet IAC skipped
  {
    PacketParser ps(StreamKind::Station);
    const uint8_t s[] = {0x07, 0x02, 0x01, 0x00, 0x06, 0x01, 0x2A};
    int packets = 0;
    for (uint8_t x : s)
      if (ps.feed(x) == PacketParser::Out::Packet) {
        packets++;
        if (ps.packet().type == PKT_ACKNOWLEDGE) CHECK(ps.packet().data[0] == 0x2A);
      }
    CHECK(packets == 2);

    PacketParser pa(StreamKind::Station);
    const uint8_t t[] = {0xFF, 0xFB, 0x01, 'H', 'i'};
    std::string text;
    for (uint8_t x : t)
      if (pa.feed(x) == PacketParser::Out::Ascii) text += (char)pa.asciiByte();
    CHECK(text == "Hi");

    PacketParser pc(StreamKind::Centralex);
    CHECK(pc.feed(0x82) == PacketParser::Out::None);
    CHECK(pc.feed(0x00) == PacketParser::Out::Packet && pc.packet().type == PKT_REMOTE_CONFIRM);
  }
}

// --- two sessions wired back to back ---------------------------------------------

struct End {
  explicit End(const char *n) : name(n) {}
  const char *name;
  std::vector<uint8_t> wire;   // what this side wrote, not yet read by the other
  std::string text;            // what this side received
  std::string endReason;
  int connected = 0, wrus = 0, ends = 0;
  bool ascii = false;
  size_t maxWrite = 1u << 30;  // simulate a transport that takes little at a time
};

static size_t writeCb(void *ctx, const uint8_t *d, size_t n) {
  End *e = (End *)ctx;
  if (n > e->maxWrite) n = e->maxWrite;
  e->wire.insert(e->wire.end(), d, d + n);
  return n;
}
static void connCb(void *ctx, bool ascii) { End *e = (End *)ctx; e->connected++; e->ascii = ascii; }
static void charCb(void *ctx, uint32_t cp) {
  End *e = (End *)ctx;
  char u[4];
  e->text.append(u, utf8Put(cp, u));
}
static void wruCb(void *ctx) { ((End *)ctx)->wrus++; }
static void endCb(void *ctx, const char *r) { End *e = (End *)ctx; e->ends++; e->endReason = r; }

static SessionHandlers handlers(End &e) {
  SessionHandlers h;
  h.ctx = &e; h.write = writeCb; h.onConnected = connCb; h.onChar = charCb;
  h.onWru = wruCb; h.onEnd = endCb;
  return h;
}

static uint32_t g_now = 1000;

static void pump(Session &a, End &ea, Session &b, End &eb, int rounds = 50, uint32_t stepMs = 10) {
  for (int i = 0; i < rounds; i++) {
    g_now += stepMs;
    a.poll(g_now);
    b.poll(g_now);
    if (!ea.wire.empty()) { std::vector<uint8_t> w; w.swap(ea.wire); b.feed(w.data(), w.size(), g_now); }
    if (!eb.wire.empty()) { std::vector<uint8_t> w; w.swap(eb.wire); a.feed(w.data(), w.size(), g_now); }
  }
}

static void testBinaryCall() {
  End ea("A"), eb("B");
  ea.maxWrite = 5;   // partial writes on the caller's side
  SessionConfig ca; ca.answerback = "10001 KUX NIKOSCOPE";
  SessionConfig cb; cb.answerback = "10002 GAR NIKOSCOPE";
  Session a, b;
  b.begin(Session::Role::Called, false, nullptr, cb, handlers(eb), g_now);
  a.begin(Session::Role::Caller, false, "", ca, handlers(ea), g_now);
  b.setAutoPrinted(true);
  a.setAutoPrinted(true);
  pump(a, ea, b, eb, 5);
  CHECK(ea.connected == 1 && !ea.ascii);
  CHECK(eb.connected == 1 && !eb.ascii);

  CHECK(a.send("Ужин в 8, не опаздывай.\r\n") > 0);
  pump(a, ea, b, eb, 200);
  CHECK(eb.text == "УЖИН В 8, НЕ ОПАЗДЫВАЙ.\r\n");
  CHECK(a.inFlight() == 0);

  // WRU: B asks, A answers with its answerback on its own
  CHECK(b.sendWru());
  pump(a, ea, b, eb, 200);
  CHECK(ea.wrus == 1);
  CHECK(eb.text.find("\r\n10001 KUX NIKOSCOPE") != std::string::npos);

  // Hang up: A rings off once everything is acknowledged
  a.hangup();
  pump(a, ea, b, eb, 50);
  CHECK(a.state() == Session::State::Closed && ea.endReason == "hangup" && ea.ends == 1);
  CHECK(b.state() == Session::State::Closed && eb.endReason == "end" && eb.ends == 1);
}

// A peer of the wider network (piTelex says "pi..."): ITA2, Russian transliterated.
// One of ours ("nk..."): MTK-2, Russian as is. Nobody configures this per call.
static void testCodingByPeer() {
  {
    End ea("A"), eb("B");
    SessionConfig ca;
    SessionConfig cb; cb.swId = "pi0.9";   // plays a piTelex station
    Session a, b;
    b.begin(Session::Role::Called, false, nullptr, cb, handlers(eb), g_now);
    a.begin(Session::Role::Caller, false, "", ca, handlers(ea), g_now);
    a.setAutoPrinted(true); b.setAutoPrinted(true);
    CHECK(a.send("Привет 1") > 0);
    pump(a, ea, b, eb, 100);
    CHECK(!a.peerIsFamily() && a.coding() == Coding::ITA2);
    CHECK(eb.text == "PRIVET 1");
  }
  {
    End ea("A"), eb("B");
    SessionConfig c;
    Session a, b;
    b.begin(Session::Role::Called, false, nullptr, c, handlers(eb), g_now);
    a.begin(Session::Role::Caller, false, "", c, handlers(ea), g_now);
    a.setAutoPrinted(true); b.setAutoPrinted(true);
    CHECK(a.send("Привет 1") > 0);
    pump(a, ea, b, eb, 100);
    CHECK(a.peerIsFamily() && a.coding() == Coding::MTK2);
    CHECK(b.peerIsFamily() && b.coding() == Coding::MTK2);
    CHECK(eb.text == "ПРИВЕТ 1");
  }
  {
    // A peer that never sends Version: after the wait, ITA2
    End ea("A");
    SessionConfig c;
    Session a;
    a.begin(Session::Role::Caller, false, "", c, handlers(ea), g_now);
    ea.wire.clear();
    CHECK(a.send("Да") > 0);
    a.poll(g_now + 100);
    CHECK(ea.wire.empty());                    // still waiting for the Version
    a.poll(g_now + 3001);
    const uint8_t fed[] = {PKT_ACKNOWLEDGE, 1, 0};
    a.feed(fed, 3, g_now + 3001);
    a.poll(g_now + 3002);
    CHECK(a.coding() == Coding::ITA2 && !ea.wire.empty());
  }
}

static void testFlowControl() {
  End ea("A"), eb("B");
  SessionConfig cfg;
  Session a, b;
  b.begin(Session::Role::Called, false, nullptr, cfg, handlers(eb), g_now);
  a.begin(Session::Role::Caller, false, "", cfg, handlers(ea), g_now);
  a.setAutoPrinted(true);
  // B shows nothing yet: A must stop at the window
  std::string longText(100, 'E');
  CHECK(a.send(longText.c_str()) == 100);
  pump(a, ea, b, eb, 100);
  CHECK(eb.text.size() <= cfg.window);
  CHECK(a.inFlight() == cfg.window);
  // B shows what it has; A continues
  for (int k = 0; k < 20; k++) {
    b.printed((uint16_t)eb.text.size());
    pump(a, ea, b, eb, 150);
  }
  CHECK(eb.text == longText);
}

static void testAsciiCall() {
  End eb("B");
  SessionConfig cfg;
  Session b;
  b.begin(Session::Role::Called, false, nullptr, cfg, handlers(eb), g_now);
  // A phone's telnet app: some negotiation, then UTF-8 text split mid-character
  const uint8_t part1[] = {0xFF, 0xFD, 0x03, 'H', 'i', ' ', 0xD0};
  const uint8_t part2[] = {0x9C, 0xD0, 0xB0, 0xD0, 0xBC, 0xD0, 0xB0, '\r', '\n'};   // "Мама"
  b.feed(part1, sizeof part1, g_now);
  b.feed(part2, sizeof part2, g_now);
  CHECK(eb.connected == 1 && eb.ascii);
  CHECK(eb.text == "Hi Мама\r\n");
  CHECK(b.send("Привет!") == std::strlen("Привет!"));
  b.poll(g_now);
  CHECK(std::string(eb.wire.begin(), eb.wire.end()) == "Привет!");   // UTF-8 as is
  // A person may be slow: no timeout at 5 min, timeout after the ASCII limit
  b.poll(g_now + 5 * 60000);
  CHECK(b.state() == Session::State::Open);
  b.poll(g_now + cfg.asciiIdleTimeoutMs + 1);
  CHECK(b.state() == Session::State::Closed && eb.endReason == "timeout");
}

// A Minitel on an ASCII-only port: its Envoi key (DC3 0x13) and an accent
// (SS2 0x19 ...) must not be taken for i-Telex packets.
static void testAsciiPort() {
  End eb("B");
  SessionConfig cfg;
  Session b;
  b.begin(Session::Role::Called, true, nullptr, cfg, handlers(eb), g_now);
  CHECK(eb.connected == 1 && eb.ascii);
  const uint8_t minitel[] = {'O', 'U', 'I', 0x13, 0x41};   // "OUI" + Envoi
  b.feed(minitel, sizeof minitel, g_now);
  CHECK(b.state() == Session::State::Open && b.ascii());
  CHECK(eb.text.substr(0, 3) == "OUI");
  // the same bytes on an auto-detecting port are (wrongly, but as piTelex does)
  // read as a packet when a control byte comes first
  End ec("C");
  Session c;
  c.begin(Session::Role::Called, false, nullptr, cfg, handlers(ec), g_now);
  const uint8_t envoiFirst[] = {0x13, 0x41, 'O'};
  c.feed(envoiFirst, sizeof envoiFirst, g_now);
  CHECK(!c.ascii());
}

static void testRefusalsAndTimeouts() {
  {
    End eb("B");
    SessionConfig cfg; cfg.acceptAscii = false;
    Session b;
    b.begin(Session::Role::Called, false, nullptr, cfg, handlers(eb), g_now);
    const uint8_t t[] = {'h', 'i'};
    b.feed(t, 2, g_now);
    CHECK(b.state() == Session::State::Closed && eb.endReason == "ascii refused");
  }
  {
    End eb("B");
    SessionConfig cfg;
    Session b;
    b.begin(Session::Role::Called, false, nullptr, cfg, handlers(eb), g_now);
    uint8_t v[16];
    size_t n = buildVersion(v, "pi0");
    b.feed(v, n, g_now);
    CHECK(eb.connected == 1 && !eb.ascii);
    b.poll(g_now + cfg.idleTimeoutMs + 1);
    CHECK(b.state() == Session::State::Closed && eb.endReason == "timeout");
    // it said End on its way out
    CHECK(eb.wire.size() >= 2 && eb.wire[eb.wire.size() - 2] == PKT_END);
  }
  {
    End ea("A");
    SessionConfig cfg;
    Session a;
    a.begin(Session::Role::Caller, false, "", cfg, handlers(ea), g_now);
    uint8_t r[8];
    size_t n = buildReject(r, "occ");
    a.feed(r, n, g_now);
    CHECK(a.state() == Session::State::Closed && ea.endReason == "rejected");
  }
}

int main() {
  testBaudot();
  testPackets();
  testBinaryCall();
  testCodingByPeer();
  testFlowControl();
  testAsciiCall();
  testAsciiPort();
  testRefusalsAndTimeouts();
  std::printf("%s: %d passed, %d failed\n", g_fail ? "FAIL" : "PASS", g_pass, g_fail);
  return g_fail ? 1 : 0;
}
