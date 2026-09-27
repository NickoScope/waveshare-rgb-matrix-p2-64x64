#include "itx_baudot.h"

namespace itx {

// Tables in ITA2 "bit 1 = LSB" order, index = code. 0 marks a position with no
// printable meaning in that register (null, the shifts, unassigned).
// Checked against piTelex txCode.py _LUT_BM2A_ITA2 / _LUT_BM2A_MKT2 (ece3d43).
static const uint16_t kLtrs[32] = {
    0,   'E', '\n', 'A', ' ', 'S', 'I', 'U', '\r', 'D', 'R', 'J', 'N', 'F', 'C', 'K',
    'T', 'Z', 'L',  'W', 'H', 'Y', 'P', 'Q', 'O',  'B', 'G', 0,   'M', 'X', 'V', 0};

static const uint16_t kFigsIta2[32] = {
    0,   '3', '\n', '-', ' ', '\'', '8', '7', '\r', 0 /*WRU*/, '4', 0x07 /*BELL*/, ',', 0, ':', '(',
    '5', '+', ')',  '2', 0,   '6',  '0', '1', '9',  '?', 0,   0,   '.', '/', '=', 0};

// MTK-2 figures: four ITA2 positions carry Russian letters instead
// (11 BELL -> Ю, 13 -> Э, 20 -> Щ, 26 -> Ш).
static const uint16_t kFigsMtk2[32] = {
    0,   '3', '\n', '-', ' ', '\'', '8', '7', '\r', 0 /*WRU*/, '4', 0x042E /*Ю*/, ',', 0x042D /*Э*/, ':', '(',
    '5', '+', ')',  '2', 0x0429 /*Щ*/, '6', '0', '1', '9', '?', 0x0428 /*Ш*/, 0, '.', '/', '=', 0};

static const uint16_t kRus[32] = {
    0,      0x0415, '\n',   0x0410, ' ',    0x0421, 0x0418, 0x0423,   // - Е LF А SP С И У
    '\r',   0x0414, 0x0420, 0x0419, 0x041D, 0x0424, 0x0426, 0x041A,   // CR Д Р Й Н Ф Ц К
    0x0422, 0x0417, 0x041B, 0x0412, 0x0425, 0x042B, 0x041F, 0x042F,   // Т З Л В Х Ы П Я
    0x041E, 0x0411, 0x0413, 0,      0x041C, 0x042C, 0x0416, 0};       // О Б Г - М Ь Ж -

constexpr uint8_t kShiftLtrs = 0x1F;
constexpr uint8_t kShiftFigs = 0x1B;
constexpr uint8_t kShiftRus  = 0x00;   // MTK-2 only
constexpr uint8_t kIdxWru    = 9;      // FIGS-D

static const uint8_t kShiftOf[3] = {kShiftLtrs, kShiftFigs, kShiftRus};

uint8_t flip5(uint8_t c) {
  return (uint8_t)(((c & 1) << 4) | ((c & 2) << 2) | (c & 4) | ((c & 8) >> 2) | ((c & 16) >> 4));
}

static const uint16_t *regTable(Coding coding, uint8_t reg) {
  if (reg == 0) return kLtrs;
  if (reg == 1) return coding == Coding::MTK2 ? kFigsMtk2 : kFigsIta2;
  return coding == Coding::MTK2 ? kRus : nullptr;
}

// Space, CR and LF print the same in every register: no shift needed.
static bool isNeutral(uint32_t cp) { return cp == ' ' || cp == '\r' || cp == '\n'; }

// --- normalisation: Unicode -> what a teleprinter can print --------------------

static uint32_t upper(uint32_t cp) {
  if (cp >= 'a' && cp <= 'z') return cp - 32;
  if (cp >= 0x0430 && cp <= 0x044F) return cp - 0x20;         // а..я
  if (cp >= 0x0450 && cp <= 0x045F) return cp - 0x50;         // ѐ..џ
  if (cp >= 0xE0 && cp <= 0xFE && cp != 0xF7) return cp - 32; // à..þ
  return cp;
}

// Substitutions: one code point -> an ASCII/Cyrillic string the code can carry.
// Returns nullptr when the code point needs none.
static const char *substitute(uint32_t cp, Coding coding) {
  switch (cp) {
    case 0x0401: return "\xD0\x95";         // Ё -> Е
    case 0x042A: return "\xD0\xAC";         // Ъ -> Ь
    case 0x0427: return coding == Coding::MTK2 ? "4" : "CH";   // Ч: MTK-2 has no Ч; see README
    case 0xC4: return "AE";  case 0xD6: return "OE";  case 0xDC: return "UE";
    case 0xDF: return "SS";
    case '"': case 0x2018: case 0x2019: case 0x201C: case 0x201D: case 0x201E:
    case 0xAB: case 0xBB: return "'";
    case ';': return ",";
    case '!': return ".";
    case '\t': return " ";
    case '[': case '{': case '<': return "(";
    case ']': case '}': case '>': return ")";
    case '\\': return "/";
    case '_': case 0x2013: case 0x2014: return "-";
    case 0x2026: return "...";
    default: return nullptr;
  }
}

// ITA2 only: Russian to Latin (a readable telegram, not a reversible one).
static const char *translit(uint32_t cp) {
  static const char *const t[32] = {
      "A", "B", "V", "G", "D", "E", "ZH", "Z", "I", "J", "K", "L", "M", "N", "O", "P",
      "R", "S", "T", "U", "F", "H", "C", "CH", "SH", "SHCH", "'", "Y", "'", "E", "JU", "JA"};
  if (cp >= 0x0410 && cp <= 0x042F) return t[cp - 0x0410];
  return nullptr;
}

// --- encoder --------------------------------------------------------------------

size_t BaudotEncoder::emitIndex(uint8_t reg, uint8_t index, uint8_t *out) {
  size_t n = 0;
  if (reg_ != (int8_t)reg) {
    out[n++] = flip5(kShiftOf[reg]);
    reg_ = (int8_t)reg;
  }
  out[n++] = flip5(index);
  return n;
}

size_t BaudotEncoder::encodeOne(uint32_t cp, uint8_t *out) {
  const uint8_t regs = coding_ == Coding::MTK2 ? 3 : 2;
  if (isNeutral(cp)) {
    const uint8_t idx = cp == ' ' ? 4 : (cp == '\r' ? 8 : 2);
    if (reg_ < 0) return emitIndex(0, idx, out);   // first char of all: settle a register
    out[0] = flip5(idx);
    return 1;
  }
  // The current register first, so a run of letters sends one shift.
  for (uint8_t k = 0; k < regs; k++) {
    const uint8_t reg = (uint8_t)(((reg_ < 0 ? 0 : reg_) + k) % regs);
    const uint16_t *tab = regTable(coding_, reg);
    for (uint8_t i = 0; i < 32; i++)
      if (tab[i] && tab[i] == cp) return emitIndex(reg, i, out);
  }
  return 0;
}

size_t BaudotEncoder::encode(uint32_t cp, uint8_t out[kMaxCodesPerChar]) {
  cp = upper(cp);
  if (cp == kBell && coding_ == Coding::MTK2) return 0;   // MTK-2 gave BELL's place to Ю
  const char *sub = substitute(cp, coding_);
  if (!sub && coding_ == Coding::ITA2) sub = translit(cp);
  if (sub) {
    size_t n = 0, i = 0, len = 0;
    while (sub[len]) len++;
    while (i < len && n + 2 <= kMaxCodesPerChar) {
      uint32_t c = utf8Next(sub, len, &i);
      const char *t = coding_ == Coding::ITA2 ? translit(c) : nullptr;   // Ё -> Е -> E
      if (t) {
        for (size_t k = 0; t[k] && n + 2 <= kMaxCodesPerChar; k++) n += encodeOne((uint8_t)t[k], out + n);
        continue;
      }
      n += encodeOne(c, out + n);
    }
    return n;
  }
  if (cp < 0x20 && cp != '\r' && cp != '\n' && cp != kBell) return 0;   // other controls: drop
  size_t n = encodeOne(cp, out);
  if (!n) n = encodeOne('?', out);
  return n;
}

size_t BaudotEncoder::encodeWru(uint8_t out[kMaxCodesPerChar]) {
  return emitIndex(1, kIdxWru, out);
}

// --- decoder --------------------------------------------------------------------

uint32_t BaudotDecoder::decode(uint8_t wire) {
  const uint8_t c = flip5((uint8_t)(wire & 0x1F));
  if (c == kShiftLtrs) { reg_ = 0; return kNone; }
  if (c == kShiftFigs) { reg_ = 1; return kNone; }
  if (c == kShiftRus) {
    if (coding_ == Coding::MTK2) reg_ = 2;
    return kNone;
  }
  if (reg_ == 1 && c == kIdxWru) return kWru;
  const uint16_t *tab = regTable(coding_, reg_);
  return tab ? tab[c] : kNone;
}

// --- UTF-8 ----------------------------------------------------------------------

uint32_t utf8Next(const char *s, size_t len, size_t *i) {
  const uint8_t *p = (const uint8_t *)s;
  const size_t k = *i;
  if (k >= len) { *i = len; return 0; }
  const uint8_t b = p[k];
  uint32_t cp;
  size_t need;
  if (b < 0x80) { *i = k + 1; return b; }
  if ((b & 0xE0) == 0xC0) { cp = b & 0x1F; need = 1; }
  else if ((b & 0xF0) == 0xE0) { cp = b & 0x0F; need = 2; }
  else if ((b & 0xF8) == 0xF0) { cp = b & 0x07; need = 3; }
  else { *i = k + 1; return 0xFFFD; }
  for (size_t j = 1; j <= need; j++) {
    if (k + j >= len || (p[k + j] & 0xC0) != 0x80) { *i = k + 1; return 0xFFFD; }
    cp = (cp << 6) | (p[k + j] & 0x3F);
  }
  *i = k + need + 1;
  return cp;
}

size_t utf8Put(uint32_t cp, char out[4]) {
  if (cp < 0x80) { out[0] = (char)cp; return 1; }
  if (cp < 0x800) {
    out[0] = (char)(0xC0 | (cp >> 6));
    out[1] = (char)(0x80 | (cp & 0x3F));
    return 2;
  }
  if (cp < 0x10000) {
    out[0] = (char)(0xE0 | (cp >> 12));
    out[1] = (char)(0x80 | ((cp >> 6) & 0x3F));
    out[2] = (char)(0x80 | (cp & 0x3F));
    return 3;
  }
  out[0] = (char)(0xF0 | (cp >> 18));
  out[1] = (char)(0x80 | ((cp >> 12) & 0x3F));
  out[2] = (char)(0x80 | ((cp >> 6) & 0x3F));
  out[3] = (char)(0x80 | (cp & 0x3F));
  return 4;
}

}  // namespace itx
