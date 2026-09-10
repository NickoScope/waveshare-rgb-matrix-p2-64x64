// Smoke test for the Waveshare RGB-Matrix-P2-64x64-B panel
// on the Waveshare ESP32-S3-RGB-Matrix board (SKU 34422).
//
// Purpose: prove the panel is alive and all 4096 pixels respond,
// BEFORE building anything around it.
//
// Pin assignments VERIFIED 2026-09-06 against Waveshare's own sources and against the
// library upstream. The board is laid out on this library's default ESP32-S3 pinout;
// the single difference is pin E, routed to GPIO9 where upstream leaves it unassigned.
// The explicit pin map below is therefore redundant and included only for clarity --
// one line, mxconfig.gpio.e = 9, would do.
//
// NOTE: this sketch has not been compiled or flashed.
//
// Library:       ESP32 HUB75 LED MATRIX PANEL DMA Display (mrcodetastic)
// Board package: esp32 by Espressif Systems, version 3.3.7 (Waveshare's requirement)
// Arduino IDE:   ESP32S3 Dev Module, Flash 32MB, PSRAM "OPI PSRAM"

#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

#define PANEL_W 64
#define PANEL_H 64
#define PANEL_CHAIN 1

MatrixPanel_I2S_DMA *display = nullptr;

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("HUB75 smoke test");

  HUB75_I2S_CFG::i2s_pins pins = {
    4,   // R1
    5,   // G1
    6,   // B1
    7,   // R2
    15,  // G2
    16,  // B2
    18,  // A
    8,   // B
    3,   // C
    42,  // D
    9,   // E  -- mandatory for 1/32 scan
    40,  // LAT
    2,   // OE
    41   // CLK
  };

  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);

  // Shift driver: Waveshare's user guide and ESP-IDF config indicate Generic (the
  // default), but 7 of their 10 Arduino examples set FM6126A, and the AnimatedPixelClock
  // author verified FM6126A on real Waveshare P2.5 64x64 panels. Ours is the P2 GOB, so
  // start on Generic. If the screen stays black on known-good power, uncomment this.
  // mxconfig.driver = HUB75_I2S_CFG::FM6126A;

  mxconfig.clkphase = false;   // if pixels are offset by one, flip this to true
  mxconfig.latch_blanking = 1; // raise towards 4 if you see ghosting
  mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_20M;  // drop to HZ_10M if you see ghosting
  mxconfig.min_refresh_rate = 60;

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) {
    Serial.println("ERROR: failed to allocate the DMA buffer");
    return;
  }

  display->setBrightness8(128);  // 50%. Do not raise without power headroom.
  display->clearScreen();
  Serial.printf("Refresh rate: %d Hz\n", display->calculated_refresh_rate);
}

void loop() {
  // Step 1. Flat colours: catches swapped RGB lines.
  const uint16_t colors[] = {
    display->color565(255, 0, 0),
    display->color565(0, 255, 0),
    display->color565(0, 0, 255),
    display->color565(255, 255, 255)
  };
  const char *names[] = {"RED", "GREEN", "BLUE", "WHITE"};

  for (int i = 0; i < 4; i++) {
    display->fillScreen(colors[i]);
    Serial.println(names[i]);
    delay(1500);
  }

  // Step 2. Border and diagonals: catches missing rows and columns.
  // An invisible x=0 column means clkphase.
  display->clearScreen();
  display->drawRect(0, 0, PANEL_W, PANEL_H, display->color565(255, 255, 0));
  display->drawLine(0, 0, PANEL_W - 1, PANEL_H - 1, display->color565(0, 255, 255));
  display->drawLine(PANEL_W - 1, 0, 0, PANEL_H - 1, display->color565(255, 0, 255));
  delay(3000);

  // Step 3. Gradient: catches ghosting and supply droop.
  display->clearScreen();
  for (int y = 0; y < PANEL_H; y++) {
    for (int x = 0; x < PANEL_W; x++) {
      display->drawPixel(x, y, display->color565(x * 4, y * 4, 128));
    }
  }
  delay(3000);
}
