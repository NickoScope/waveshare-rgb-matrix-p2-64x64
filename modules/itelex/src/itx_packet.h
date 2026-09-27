#pragma once
// i-Telex packets: building them, and a streaming parser that tells packets
// from plain ASCII text. Plain C++, no Arduino.
//
// Every packet is [type][length][length bytes]. Sources:
//   - the i-Telex Communication Specification (telexforum.de lexicon entry 74,
//     "Protokoll-Spezifikation"), incl. its worked examples, which are the
//     host test vectors;
//   - piTelex ece3d43, txDevITelexCommon.py (what the real network accepts).
//
// Three kinds of stream use this format:
//   Station    a call between two stations (types 0x00-0x09; 0x10-0x1F are
//              reserved and pass as packets). Any other first byte means the
//              caller speaks plain ASCII (a telnet user). 0xFF is a telnet IAC
//              there, never a packet.
//   Centralex  the standing line to a Centralex relay (0x81-0x84, 0x04, 0xFF,
//              plus the station types once a call is put through).
//   Directory  one query/answer with a subscriber server (TNS, port 11811).

#include <stddef.h>
#include <stdint.h>

namespace itx {

enum PacketType : uint8_t {
  PKT_HEARTBEAT     = 0x00,
  PKT_DIRECT_DIAL   = 0x01,
  PKT_BAUDOT_DATA   = 0x02,
  PKT_END           = 0x03,
  PKT_REJECT        = 0x04,
  PKT_ACKNOWLEDGE   = 0x06,
  PKT_VERSION       = 0x07,
  PKT_SELF_TEST     = 0x08,
  PKT_REMOTE_CONFIG = 0x09,
  // Centralex (the relay for stations without a public IPv4 address)
  PKT_CONNECT_REMOTE = 0x81,
  PKT_REMOTE_CONFIRM = 0x82,
  PKT_REMOTE_CALL    = 0x83,
  PKT_ACCEPT_CALL    = 0x84,
  PKT_ERROR          = 0xFF,
};

constexpr uint8_t kProtocolVersion = 1;
constexpr uint8_t kMaxBaudotPerPacket = 50;   // receivers reject more (piTelex: 1..50)
constexpr uint16_t kDefaultStationPort = 134; // the i-Telex convention; piTelex uses 2342
constexpr uint16_t kTnsPort = 11811;
constexpr uint16_t kCentralexPort = 49491;

// --- builders: each returns the packet length written to out -------------------

size_t buildHeartbeat(uint8_t *out);                            // 2 B
size_t buildEnd(uint8_t *out, const char *reason = nullptr);    // 2 B + reason
size_t buildReject(uint8_t *out, const char *reason);           // 2 B + reason (≤20)
size_t buildAck(uint8_t *out, uint8_t printed);                 // 3 B
size_t buildVersion(uint8_t *out, const char *swId);            // 3 B + id (≤6) + NUL
size_t buildDirectDial(uint8_t *out, const char *ext);          // 3 B
size_t buildBaudot(uint8_t *out, const uint8_t *codes, size_t n);   // n ≤ 50
size_t buildConnectRemote(uint8_t *out, uint32_t number, uint16_t pin);   // 8 B
size_t buildAcceptCall(uint8_t *out);                           // 2 B

// Direct-dial extension, as dialled ("", "0".."9", "00".."99") <-> wire byte.
uint8_t encodeExtension(const char *ext);
// Writes "" for none, else 1-2 digits into out[3]. Returns false if invalid.
bool decodeExtension(uint8_t wire, char out[3]);

// --- streaming parser -----------------------------------------------------------

enum class StreamKind : uint8_t { Station, Centralex };

struct Packet {
  uint8_t type;
  uint8_t len;
  uint8_t data[255];
};

class PacketParser {
 public:
  enum class Out : uint8_t {
    None,      // byte consumed, nothing complete yet
    Packet,    // packet() holds a complete packet
    Ascii,     // asciiByte() holds one byte of plain text
  };

  explicit PacketParser(StreamKind kind = StreamKind::Station) : kind_(kind) {}
  void reset() { st_ = St::Type; telnetSkip_ = 0; }
  void setKind(StreamKind k) { kind_ = k; reset(); }

  Out feed(uint8_t b);
  const Packet &packet() const { return pkt_; }
  uint8_t asciiByte() const { return ascii_; }

 private:
  bool isPacketType(uint8_t b) const;
  enum class St : uint8_t { Type, Len, Data };
  StreamKind kind_;
  St st_ = St::Type;
  uint8_t got_ = 0;
  uint8_t telnetSkip_ = 0;
  uint8_t ascii_ = 0;
  Packet pkt_{};
};

// --- subscriber server (TNS) ----------------------------------------------------

enum class PeerType : uint8_t {
  Deleted = 0, BaudotHost = 1, BaudotIp = 2, AsciiHost = 3, AsciiIp = 4,
  BaudotDynIp = 5, Email = 6,
};

struct PeerInfo {
  uint32_t number;
  char name[41];
  PeerType type;
  char host[41];     // hostname for types 1/3, dotted IPv4 otherwise
  uint16_t port;
  char ext[3];       // direct-dial extension, "" for none
  bool ascii;        // types 3/4 speak plain ASCII
};

size_t buildPeerQuery(uint8_t *out, uint32_t number);                        // 7 B
size_t buildClientUpdate(uint8_t *out, uint32_t number, uint16_t pin, uint16_t port);   // 10 B

enum class PeerReply : uint8_t { Found, NotFound, Unusable, Incomplete, Invalid };
// Parse the server's answer to a peer query. Incomplete: feed more bytes.
PeerReply parsePeerReply(const uint8_t *buf, size_t len, PeerInfo *out);

}  // namespace itx
