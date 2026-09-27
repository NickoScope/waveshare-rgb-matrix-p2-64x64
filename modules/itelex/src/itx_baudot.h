#pragma once
// Baudot-Murray code (ITA2) and its Russian extension MTK-2, as the i-Telex
// wire carries it. Plain C++, no Arduino: tested on the host.
//
// Two facts that are easy to get wrong (docs/38 §4, checked against piTelex
// ece3d43, txDevITelexCommon.py:257 and txCode.py):
//   - i-Telex puts the 5-bit code on the wire BIT-REVERSED against the usual
//     "bit 1 = LSB" ITA2 tables: 'E' is 0x01 in the table, 0x10 on the wire.
//     piTelex builds its codec with flip_bits=True for exactly this.
//   - MTK-2 is ITA2 plus a third register (Russian) selected by code 0x00,
//     which in plain ITA2 is "null" and prints nothing.
//
// The encoder takes Unicode code points (so UTF-8 text in, via utf8Next()) and
// emits wire codes, inserting LTRS / FIGS / RUS shifts only when the register
// changes. The decoder does the reverse and reports WRU ("Wer da?") and BELL
// as distinct values, because a station must answer the first and ring on the
// second.

#include <stddef.h>
#include <stdint.h>

namespace itx {

enum class Coding : uint8_t {
  ITA2,   // international: Latin capitals, digits, a few signs
  MTK2,   // ITA2 + Russian register (code 0x00 selects it)
};

// Special results of BaudotDecoder::decode().
constexpr uint32_t kNone = 0;          // shift or null: nothing to print
constexpr uint32_t kWru  = 0xE000;     // "Wer da?" / WRU, FIGS-D (private use)
constexpr uint32_t kBell = 0x0007;     // FIGS-J in ITA2

// Wire <-> table order (bit 1 <-> bit 5).
uint8_t flip5(uint8_t code);

// Longest output of BaudotEncoder::encode() for one code point:
// a transliteration of up to 4 letters ("ШЩ" -> "SHCH"), each possibly
// preceded by a shift.
constexpr size_t kMaxCodesPerChar = 8;

class BaudotEncoder {
 public:
  explicit BaudotEncoder(Coding coding = Coding::MTK2) : coding_(coding) {}
  void reset() { reg_ = -1; }   // the next printable char sends its shift
  Coding coding() const { return coding_; }

  // Encode one Unicode code point into wire codes. Returns how many were
  // written to out (0 when the code point is dropped, e.g. a control char).
  // Lower case is folded to upper case; what the code cannot carry is
  // substituted (Ё->Е, Ъ->Ь, Ä->AE, ...) or becomes '?'. With Coding::ITA2,
  // Cyrillic is transliterated to Latin, so a Russian text still reaches an
  // ordinary teleprinter readable.
  size_t encode(uint32_t cp, uint8_t out[kMaxCodesPerChar]);

  // The WRU request itself (FIGS-D), for a caller that wants to ask.
  size_t encodeWru(uint8_t out[kMaxCodesPerChar]);

 private:
  size_t emitIndex(uint8_t reg, uint8_t index, uint8_t *out);
  size_t encodeOne(uint32_t cp, uint8_t *out);   // one already-mapped symbol
  Coding coding_;
  int8_t reg_ = -1;   // -1 unknown, 0 LTRS, 1 FIGS, 2 RUS
};

class BaudotDecoder {
 public:
  explicit BaudotDecoder(Coding coding = Coding::MTK2) : coding_(coding) {}
  void reset() { reg_ = 0; }
  // One wire code (0..31) in, one code point out: kNone for a shift or null,
  // kWru, kBell, '\r', '\n' or a printable character.
  uint32_t decode(uint8_t wire);

 private:
  Coding coding_;
  uint8_t reg_ = 0;   // a receiver starts in letters, like a machine after reset
};

// UTF-8 helpers, bounds-checked. utf8Next() returns the code point at s[*i]
// and advances *i; malformed input yields U+FFFD and advances by one byte.
uint32_t utf8Next(const char *s, size_t len, size_t *i);
size_t utf8Put(uint32_t cp, char out[4]);

}  // namespace itx
