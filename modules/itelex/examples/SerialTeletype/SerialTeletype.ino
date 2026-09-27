// SerialTeletype - the smallest i-Telex station: the serial monitor is the
// teleprinter. Works on any ESP32 with Wi-Fi; nothing panel-specific.
//
// Serial commands (end with Enter):
//   /dial 10002        call a number from the phonebook (or host:port)
//   /wru               ask the other side who it is
//   /bye               hang up
//   anything else      is sent as text while in a call
//
// Call it from a phone: any telnet / TCP terminal app to <this device's IP>:134,
// type, and the text appears here. Over Tailscale, use the house's subnet route.

#include <WiFi.h>
#include <ITelex.h>

#ifndef WIFI_SSID
#define WIFI_SSID "your-ssid"
#define WIFI_PASS "your-password"
#endif

// The family's numbers. Hosts are whatever this device can reach: a LAN IP,
// or across houses the address the Tailscale subnet router gives it.
static const itx::PhonebookEntry kPhonebook[] = {
    {10001, "192.168.1.57", 134, "", false, "KUX"},
    {10002, "192.168.1.58", 134, "", false, "GAR"},
};

static itx::Station station;
static String line;

static void onCallStart(void *, bool incoming, bool ascii, const char *peer) {
  Serial.printf("\r\n--- %s call %s %s ---\r\n", incoming ? "incoming" : "outgoing",
                ascii ? "(ascii)" : "(i-telex)", peer);
}
static void onChar(void *, uint32_t cp) {
  char u[4];
  Serial.write((const uint8_t *)u, itx::utf8Put(cp, u));
}
static void onWru(void *) { Serial.print("<WRU answered>"); }
static void onCallEnd(void *, const char *why) { Serial.printf("\r\n--- end: %s ---\r\n", why); }
static void onStatus(void *, const char *s) { Serial.println(s); }

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(200);
  Serial.printf("Wi-Fi up, %s:134\r\n", WiFi.localIP().toString().c_str());

  itx::StationConfig cfg;
  cfg.session.coding = itx::Coding::MTK2;
  cfg.session.answerback = "10001 KUX NIKOSCOPE";
  cfg.phonebook = kPhonebook;
  cfg.phonebookLen = sizeof(kPhonebook) / sizeof(kPhonebook[0]);

  itx::StationEvents ev;
  ev.onCallStart = onCallStart;
  ev.onChar = onChar;
  ev.onWru = onWru;
  ev.onCallEnd = onCallEnd;
  ev.onStatus = onStatus;

  station.setAutoPrinted(true);   // the serial monitor "prints" instantly
  station.begin(cfg, ev);
}

void loop() {
  station.loop();
  while (Serial.available()) {
    const char c = (char)Serial.read();
    if (c != '\n' && c != '\r') { line += c; continue; }
    if (!line.length()) continue;
    if (line.startsWith("/dial ")) station.dial(line.substring(6).c_str());
    else if (line == "/wru") station.sendWru();
    else if (line == "/bye") station.hangup();
    else { station.send(line.c_str()); station.send("\r\n"); }
    line = "";
  }
}
