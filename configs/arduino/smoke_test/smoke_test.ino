// Дымовой тест панели Waveshare RGB-Matrix-P2-64x64-B
// на плате Waveshare ESP32-S3-RGB-Matrix (SKU 34422).
//
// Задача: убедиться, что панель живая и все 4096 пикселей отвечают,
// ДО того как что-то собирать в корпус.
//
// Распиновка СВЕРЕНА 2026-09-06 с исходниками Waveshare и с апстримом библиотеки.
// Плата разведена под дефолтный пинаут ESP32-S3 этой библиотеки, отличие ровно одно:
// пин E выведен на GPIO9, в апстриме он не назначен (-1).
// Поэтому явная карта пинов ниже избыточна и приведена только для наглядности —
// достаточно было бы одной строки mxconfig.gpio.e = 9.
//
// ВНИМАНИЕ: скетч не компилировался и не заливался на железо.
//
// Библиотека: ESP32 HUB75 LED MATRIX PANEL DMA Display (mrcodetastic)
// Пакет плат:  esp32 by Espressif Systems, версия 3.3.7 (требование Waveshare)
// Настройки Arduino IDE: ESP32S3 Dev Module, Flash 32MB, PSRAM "OPI PSRAM"

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
    9,   // E  — обязателен для 1/32 scan
    40,  // LAT
    2,   // OE
    41   // CLK
  };

  HUB75_I2S_CFG mxconfig(PANEL_W, PANEL_H, PANEL_CHAIN, pins);

  // Драйвер: руководство Waveshare предписывает Generic (значение по умолчанию).
  // Но их собственный пример 01_SimpleTestShapes ставит FM6126A — похоже на
  // неадаптированный апстрим-пример, он же объявляет панель 64x32.
  // Если экран останется чёрным при исправном питании — раскомментировать.
  // mxconfig.driver = HUB75_I2S_CFG::FM6126A;

  mxconfig.clkphase = false;   // если пиксели съехали на один — поменять на true
  mxconfig.latch_blanking = 1; // при гостинге поднимать до 4
  mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_20M;  // при гостинге снижать до HZ_10M
  mxconfig.min_refresh_rate = 60;

  display = new MatrixPanel_I2S_DMA(mxconfig);
  if (!display->begin()) {
    Serial.println("ОШИБКА: не удалось выделить память под буфер DMA");
    return;
  }

  display->setBrightness8(128);  // половина. Выше не поднимать без запаса по питанию.
  display->clearScreen();
  Serial.printf("Частота обновления: %d Гц\n", display->calculated_refresh_rate);
}

void loop() {
  // Шаг 1. Чистые цвета: ловим перепутанные линии RGB.
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

  // Шаг 2. Рамка и диагонали: ловим потерянные строки и столбцы.
  // Если столбец x=0 не виден — это clkphase.
  display->clearScreen();
  display->drawRect(0, 0, PANEL_W, PANEL_H, display->color565(255, 255, 0));
  display->drawLine(0, 0, PANEL_W - 1, PANEL_H - 1, display->color565(0, 255, 255));
  display->drawLine(PANEL_W - 1, 0, 0, PANEL_H - 1, display->color565(255, 0, 255));
  delay(3000);

  // Шаг 3. Градиент: ловим гостинг и провалы по питанию.
  display->clearScreen();
  for (int y = 0; y < PANEL_H; y++) {
    for (int x = 0; x < PANEL_W; x++) {
      display->drawPixel(x, y, display->color565(x * 4, y * 4, 128));
    }
  }
  delay(3000);
}
