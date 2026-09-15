# The board's temperature and humidity sensor, and the weather screen

**Owner's decision, 2026-09-15 19:10: variant B, split "outside | inside".** Being implemented on `feat/onboard-climate`. Variants A and C stay in `tools/climate/preview/` for reference.

**2026-09-15.**

| Stage | Where it stands |
|---|---|
| Design | done |
| Previews | done |
| Driver and data plumbing | built |
| Weather-screen code | not written: the owner picks a design first |
| Panel | nothing flashed, nothing measured |

Firmware: branch `feat/onboard-climate` in the worktree
`AnimatedPixelClock-climate`, off `feature/market-dashboard` 776fc04.

Owner's request (18:24): «разработать модуль температурного/влажностного
датчика нашей платы и красиво встроить в экран погоды». Keralots named the SHTC3
as the one onboard peripheral he would take upstream: local temperature for
the weather clock ([09](09-upstream-contributions.md)).

## 0. Summary

- **Part and bus.** A Sensirion **SHTC3** (schematic U6) at **0x70**, with SDA on
  **GPIO47** and SCL on **GPIO48** [1][3][4][6].
  - On this module GPIO47/48 work at 1.8 V [7][8].
  - The schematic puts a MOSFET level shifter, M2 (NDC7002N), between them and
    the sensor's 3.3 V bus, with 4.7 k pull-ups on each side [2].
  - The same bus carries the PCF85063 RTC, the QMI8658 IMU and both audio
    codecs. This firmware uses none of them, and nothing in it called
    `Wire.begin` before.
- **Where it sits.** The photo shows a 2 mm part with a centred opening in the
  board's top-right corner. It stands on a peninsula cut free by an L-shaped
  milled slot, beside the POWER USB-C socket. That is the thermal decoupling
  Sensirion's design guide draws [9]. The marking is not readable, so this is
  "very likely the SHTC3", not confirmed.
- **Driver.** A state machine in `loop()`, one I2C transaction per pass:
  - normal-mode measurement with clock stretching off;
  - both CRCs checked, the ID register checked;
  - soft reset after repeated failures;
  - states absent, stale and ok.
- **Self-heating.** The sensor shares the board with an ESP32-S3 whose radio never
  sleeps, so it will read warm. The firmware has:
  - a user temperature offset;
  - the humidity recomputed at the corrected temperature, with Sensirion's own
    Magnus parameters [10], as their design guide asks [9];
  - smoothing.

  A load-dependent correction stays an idea until it is measured.
- **What it feeds.**
  - `/api/info`;
  - an Indoor sensor card in the portal;
  - on request, two Home Assistant sensors by MQTT discovery.
- **Weather screen.** Three designs are drawn pixel for pixel in
  `tools/climate/preview/`: A an indoor line, B split, C a badge. No weather-screen
  code yet.
- **To measure on the panel:**
  - an I2C scan and the ID;
  - the offset against a reference thermometer after 30 minutes of normal display
    use (plan in section 5.4).

## 1. Hardware and bus

### 1.1 The part

| Fact | Source |
|---|---|
| U6 "SHTC3": pin 1 VDD on 3V3 with C41 100 nF, 2 SCL on `I2C_SCL`, 3 SDA on `I2C_SDA`, 4 VSS and 5 EP on GND | schematic [2] |
| The datasheet asks for 100 nF between VDD and VSS, close to the sensor; the drawing has it | datasheet §4 [5] |
| I2C address 0x70 (111'0000) | datasheet Table 8 [5]; `SHTC3_I2C_ADDR 0x70` in the driver the BSP uses [11] |
| The vendor BSP depends on `pedrominatel/shtc3` ^1.4.0, and its `06_Matrix_SHTC3` example reads it every 500 ms | [03](03-firmware.md), [3] |
| The Arduino `08_Sensor_Test` reads it with Adafruit_SHTC3 | [4] |

### 1.2 Pins and levels

| Fact | Source |
|---|---|
| `BSP_I2C_SDA GPIO_NUM_47`, `BSP_I2C_SCL GPIO_NUM_48` | vendor BSP `config.h` [1] |
| `I2C_SDA_PIN 47`, `I2C_SCL_PIN 48`, `Wire.setClock(400000)` | `08_Sensor_Test.ino` [4] |
| The ESP-IDF middleware adds the SHTC3 to that bus at **40 kHz** with `scl_wait_us` 10 000 | `middle_sensor.c` [3] |
| On ESP32-S3R8V and S3R16V, "the working voltage for pins SPICLK_N and SPICLK_P (GPIO47 and GPIO48) would also be 1.8 V". The N32R16V module carries an S3R16V ([02](02-controller.md)) | ESP32-S3 datasheet §2.2 [7]; WROOM-2 datasheet Table 3-1 note 2 [8] |
| **M2, NDC7002N**, a dual N-channel MOSFET wired as the usual bidirectional level shifter. Pins:<br>• gates G1 (pin 1) and G2 (pin 3) on **1V8**;<br>• sources S1 (pin 5) on `IO47` and S2 (pin 2) on `IO48`, pulled to 1V8 by R10 and R13 (4.7 k each);<br>• drains D1 (pin 6) on `I2C_SDA` and D2 (pin 4) on `I2C_SCL`, pulled to 3V3 by R11 and R12 (4.7 k each).<br>Read at 600 dpi on 2026-09-15 | schematic [2] |

**Open question 6 of the bring-up** ([12](12-bringup.md)) asked whether GPIO47/48
run at 1.8 V. It is **answered from sources, not measured.** The datasheet says
yes, and the board shifts them to 3.3 V for the sensors. Anything 3.3 V added to
this bus belongs on the `I2C_SDA`/`I2C_SCL` side of M2.

Waveshare's two examples disagree on speed (40 kHz and 400 kHz) and neither
says why. The sensor takes 0-1000 kHz (datasheet Table 6 [5]). The firmware uses
**100 kHz**, a conservative choice through the level shifter, not a measurement.

### 1.3 What else is on the bus

| Device | Address | Source |
|---|---|---|
| PCF85063ATL RTC (U2) | 0x51 | [02](02-controller.md) |
| QMI8658 IMU (U5) | probed at its high and low addresses, WHO_AM_I 0x05 | `08_Sensor_Test.ino` [4] |
| ES8311 codec (U9), ES7210 ADC | not read from the vendor source | [2], [17](17-media-player.md) |

**The firmware today.** A grep on 2026-09-15 finds no `Wire` anywhere in
`src/`, and GPIO47/48 are unused. Nothing collides with:
- HUB75 (4-9, 15, 16, 18, 2, 3, 40-42);
- the TF card (1, 44, 17);
- the encoder (45, 46, 0);
- I2S (11, 12, 21, 38, 39, 43);
- the planned IR receiver on IO14 ([11](11-control-and-pins.md)).

**The media player will share this bus** for the ES8311 ([17](17-media-player.md)).
`TwoWire::begin` returns true if the bus is already up (Wire.cpp:300-303 [12]),
so a second user can call it again. The datasheet recommends no bus traffic
while the SHTC3 measures, for best repeatability (§5.5 [5]). That matters once
the codec talks on the bus too.

### 1.4 Where the part sits

`photos/2026-09-14-arrival/controller-front.jpg`: in the top-right corner, next
to the POWER USB-C socket and above the RTC header, stands a black 2 mm square
part with a round centred opening. The SHTC3 is a 2 x 2 mm DFN with its humidity
opening centred on top (datasheet §7 [5]). An L-shaped slot is milled through
the board around it, leaving it on a peninsula.

That is Sensirion's Figure 8b: "milled slits (white lines) around the sensor
decrease the thermal conduction through the PCB" [9]. The laser marking is not
readable in the photo: **not confirmed** that this part is U6.

## 2. The sensor, from its datasheet [5]

### Commands (§5, Tables 9-14)

| Command | Code |
|---|---|
| Wake-up | 0x3517 |
| Sleep | 0xB098 |
| Soft reset | 0x805D |
| Read ID | 0xEFC8 |
| Measure, normal mode, T first / RH first, clock stretching **on** | 0x7CA2 / 0x5C24 |
| Measure, normal mode, T first / RH first, clock stretching **off** | 0x7866 / 0x58E0 |
| Measure, low power, T first / RH first, stretching **on** | 0x6458 / 0x44DE |
| Measure, low power, T first / RH first, stretching **off** | 0x609C / 0x401A |
| Reset by I2C general call | 0x0006 at address 0x00. It resets every device on the bus that supports it, so it is not used here |

**The measurement sequence** (§5.4): wake-up, measurement command, read-out,
sleep.
- **Stretching on:** the sensor ACKs the read header and holds SCL until the
  result is ready.
- **Stretching off:** it NACKs the read header until the measurement is done.

**The read-out** (§5.6): two bytes and a CRC, then two bytes and a CRC.

**The ID** (§5.9, Table 15): a 16-bit ID and a CRC. Bits 11 and 5:0 carry the
product code, `xxxx'1xxx'xx00'0111`; the other bits may differ from sensor to
sensor.

### Timing (Table 5; max values measured at -40 °C)

| | Typ | Max |
|---|---|---|
| Power-up tPU, soft reset tSR | 180 µs | 240 µs |
| Measurement, normal mode | 10.8 ms | 12.1 ms |
| Measurement, low power | 0.7 ms | 0.8 ms |

### CRC and conversion (§5.10, §5.11)

- **CRC-8:** polynomial 0x31 (x^8 + x^5 + x^4 + 1), init 0xFF, no reflection,
  final XOR 0x00. Examples: CRC(0x00) = 0xAC, CRC(0xBEEF) = 0x92.
- **Conversion:** RH = 100 · S_RH / 2^16 %RH, and T = -45 + 175 · S_T / 2^16 °C.
- **Worked example, Figure 7:** humidity bytes A1 33 with CRC 1C, temperature
  64 8B with CRC C7, "63 %RH and 23.7 °C". The host test checks all of it
  (section 8).

### Accuracy (Tables 1, 2)

The typ, max and repeatability figures apply to normal mode (footnotes 1-3).

| | Humidity | Temperature |
|---|---|---|
| Accuracy, typical | ±2.0 %RH (max: Figure 2) | ±0.2 °C (max: Figure 3) |
| Repeatability (3σ) | 0.1 %RH | 0.1 °C |
| Resolution | 0.01 %RH | 0.01 °C |
| Hysteresis | ±1 %RH | — |
| Response time, 63 % | 8 s | <5 to 30 s, depending on the design-in |
| Long-term drift | <0.25 %RH/y | <0.02 °C/y |

**Recommended operating range** (§1.2): 5-60 °C and 20-80 %RH.

### Current (Table 3, 25 °C, 3.3 V)

| State | Typ | Max |
|---|---|---|
| Idle | 45 µA | 70 µA |
| Sleep | 0.3 µA | 0.6 µA |
| Measuring, normal mode | 430 µA | 900 µA |
| Measuring, low power | 270 µA | 570 µA |
| Average at one measurement per second, normal mode | 4.9 µA | — |
| Average at one measurement per second, low power | 0.5 µA | — |

The datasheet recommends putting the sensor to sleep after power-up (§5.2).

**The sensor's own heating.** At one reading per 10 s in normal mode the
datasheet's figures give about 0.5 µA average. That is derived from the 1 Hz
figure, assuming the average scales with the rate. It is negligible next to
what the board around it dissipates.

## 3. The weather screen and the patterns it lives with

### The weather clock today

It is clock style 14, `displayClockWithWeather()` in
`src/clocks/clock_weather.cpp`.

| Row | Content |
|---|---|
| y 2 | the time at size 2 |
| y 24 | a 24 px animated icon at x 10 (sun, part cloud, cloud, fog, rain, snow, storm) |
| y 27 | the temperature at size 3 at x 52, with a radius-2 `drawCircle` degree and the unit letter at size 1 |
| y 55 | a details row that alternates every 5 s: max↑ min↓ and RH, or sunrise and sunset |

**Other states:** "Weather not set up" and "Fetching weather...". The no-WiFi icon
sits at 0,0 and AM/PM at x 112.

**Colours** are the user's sprite slots: icon yellow 0xFFE0, accent light blue
0x551F, temperature white. The data boards use the house colours (amber
255/150/0, white, dim 110/122/128); the weather clock does not.

**Data** comes from Open-Meteo: current temperature, RH, weather code, wind,
today's max/min, sunrise and sunset. It is fetched in a one-shot task, every
10 min, only while the page is on screen (`src/weather/weather.cpp`).

### MQTT

One PubSubClient (`src/mqtt/mqtt_bus.cpp`) with a 2048 B buffer, and tables of 8
subscriptions and 8 handlers. **Seven of each are taken** with every page built
in:
- cards 3;
- flight board, rail board, media and market 1 each.

The media player's topics are `nickoscope_matrix/<mac3>/media/…`. **No Home
Assistant discovery existed in the firmware before this module.**

### The portal

- One static gzipped page, filled by `/api/portal`.
- `data-need` removes a part whose feature the build does not list.
- `tools/web_assets_gen.py --check` refuses a form control that
  `handlePortalValues()` does not fill.

## 4. Driver design

The code lives in `src/climate/` and has three layers:

| File | Contents | Tested on the host |
|---|---|---|
| `shtc3.h` | the datasheet: commands, timing, CRC, ID mask, conversions | yes |
| `climate_model.h` | smoothing, offsets, the humidity compensation, staleness, the settings' bounds | yes |
| `climate.cpp` | the reader, `/api/info`, the discovery | — |

### 4.1 The cycle

One transaction per `loop()` pass:

| Step | Bus | Wait |
|---|---|---|
| due | wake-up 0x3517 | 1 ms (tPU max 240 µs) |
| after a third failure in a row | soft reset 0x805D | 1 ms (tSR max 240 µs) |
| first contact, after a reset | read ID 0xEFC8 (3 bytes): CRC and product code | — |
| measure | 0x7866: normal mode, T first, **stretching off** | 15 ms (tMEAS max 12.1 ms) |
| read | 6 bytes. A NACK means still measuring: 3 more tries, 5 ms apart | — |
| check | both CRCs | — |
| sleep | 0xB098 | the interval, default 10 s |

**Why `loop()` and not a task.**
- The weather needs a task because a TLS fetch blocks for seconds.
- Here every step is a few bytes, about a millisecond at 100 kHz (estimated from
  the bit rate; to be measured as `loopSlowPart`).
- There is no stack to hold, and no lock: the web handlers and the MQTT bus run
  in `loop()` too.

**Why stretching off.** A too-early read gets a NACK and the reader comes back
later. With stretching on, the sensor would hold SCL for up to 12 ms inside
`Wire.requestFrom()`, blocking `loop()`.

**Why normal mode.** The accuracy and repeatability figures are specified in
normal mode. Its 10.8 ms cost nothing here, because `loop()` never waits for
them.

**Timeouts.** A transaction that is not answered in 20 ms fails. Wire's default
is 50 ms (Wire.cpp:48 [12]). `endTransmission` returns 0 when sent, 2 for a NACK,
5 on timeout and 4 otherwise (Wire.cpp:465-470 [12]).

**Logging.** Neither `CORE_DEBUG_LEVEL` nor any log level is set in
`platformio.ini`. A NACK makes `requestFrom` log through `log_e` (Wire.cpp:512),
which this build level does not print. **Not verified on the panel.**

### 4.2 Auto-detect and failures

| Case | What happens |
|---|---|
| Nothing answers at 0x70 | three looks 2 s apart, then **absent**, looked for again once a minute (one NACKed address) |
| Something answers with a foreign ID | **absent**, left alone except for that look once a minute; `foreignDevice` in `/api/info` |
| A found sensor stops answering, or its CRC fails | retried in 2 s; every third failure in a row starts with a soft reset and a new ID check; after that, once an interval. Counters `i2cErrors`, `crcErrors`, `softResets` |
| No good reading for three intervals (never less than 30 s) | **stale**: the value is kept but marked, the panel shows dashes, Home Assistant's `expire_after` runs out |
| The bus hangs | each transaction ends after 20 ms, so a fault costs at most that per pass, every 2 s at first and then once an interval |
| `Wire.begin` fails | absent, and one line on the serial port |
| Switched off in the portal | the sensor is put to sleep, the reading dropped, the Home Assistant entities removed |

A failure after a successful wake-up sends the sensor back to sleep, so it does
not idle at 45 µA (Table 3).

**Upstream** needs no flag. The module is built for the Waveshare env, and the ID
check is the auto-detect. **In the fork** `-DCLIMATE_ENABLED` (in
`matrix-waveshare-rgb`) follows the house convention. It needs
`BOARD_WAVESHARE_RGB_MATRIX`, or `CLIMATE_I2C_SDA` and `CLIMATE_I2C_SCL`;
without them the build fails with `#error`.

## 5. Self-heating

### 5.1 What the sources say

Sensirion, *Design Guide for Humidity and Temperature Sensors*, Version 2,
March 2024 [9]:

- **§3.** "External heat sources close to the sensor will cause increased
  temperature (and thus decreased RH) readings. In extreme cases such as at
  90 %RH, a deviation of 1 °C will result in a deviation of the humidity signal
  of 5 %RH."
- **§3.** "Heat conduction from nearby heat sources (power electronics,
  microprocessors, displays, etc.) is the more severe and most common source of
  temperature deviations. Mostly it occurs through the PCB and can be mitigated
  by sufficient distances and removal of unnecessary metal around the sensor
  (e.g. trough milling or etching slits…)"
- **§3.1.** Self-heating "depends on the used components, the build, and the mode
  in which it is operated", for example maximal screen brightness. It "can
  easily be overcome by smart thermal design-in, potentially coupled with an
  algorithmic compensation of the residual offset". Also: "subsequent
  compensation of temperature also requires a compensation of the RH signal as
  the RH is strongly temperature dependent."

### 5.2 On this board

**Heat sources:**
- the ESP32-S3 module, with Wi-Fi modem sleep off (`WiFi.setSleep(false)` in
  `main.cpp`);
- the 3V3 buck;
- the POWER USB-C input next to the sensor;
- the HUB75 buffers on the back (photo `controller-back.jpg`).

**Power path.** In the bench setup the panels take power from their own supply
([12](12-bringup.md)), so the board carries only its own current. Record the
power path in every measurement.

**Decoupling.** Waveshare's slot (1.4) is the decoupling the guide recommends.
How much heat still arrives is unknown. No number is taken from anywhere else.

### 5.3 What the firmware does

The order matters: `climate::correct()` in `climate_model.h`.

1. **Smoothing.** A first-order filter with a 60 s time constant, on the sensor's
   own values. The 60 s is a choice for a steady last digit, not a sourced figure.
   It is reset after a stale spell. Because smoothing comes before the offsets,
   a new offset shows at once.
2. **Temperature offset.** Tenths of a °C, ±20.0, default 0.
3. **Humidity at the corrected temperature** (on by default). Air warmed by the
   board gains heat, not water, so its vapour pressure *e* is the room's. By the
   definition RH = *e* / *e_w*(*t*) (*Introduction to Humidity* eq. (7) [10]):

   RH_room = RH_sensor · *e_w*(t_sensor) / *e_w*(t_room)

   with the Magnus formula *e_w*(*t*) = 6.112 hPa · exp(17.62 *t* / (243.12 + *t*)),
   Table 1 "above water", valid -45 to 60 °C (eq. (3) [10]). The host test checks
   it against the guide's statement. At 90 %RH, 1 °C gives a 5.0-5.4 %RH change
   between 15 and 30 °C; the guide gives "5 %RH" and names no temperature.
4. **Humidity offset.** Tenths of a %RH, ±20.0, default 0, for what remains.

**An idea, not built, no source:** an offset that follows the load. Candidates
are display brightness (`settings.displayBrightness`), the page (the Lua effects
load a core), and Wi-Fi traffic. Sensirion says an algorithmic compensation is
possible but gives no model. By the project's rule a threshold comes from a
distribution: **it stays a reference idea until at least five independent
sessions** (5.4) show the offset changing with load by more than the sensor's
±0.2 °C typ plus the reference's uncertainty.

### 5.4 Measurement plan (on the panel)

**Kit and placement:**
- A reference thermometer-hygrometer whose stated accuracy is written down.
- Place it at the panel's height, about 30 cm to the side, out of the air rising
  from the panel and the board.
- Write down whether the board is bare or in its case, and the power path.

**Steps:**
1. **Cold start.** Leave the panel unpowered for at least an hour, then power it
   and show the usual page (the weather clock) at the usual brightness.
2. **Log for 60 minutes, once a minute:**
   - from `/api/info`: `climate.sensorTempC`, `climate.sensorHumidity`, and
     `loopSlowPart` / `loopSlowPartMs`;
   - the reference's temperature and humidity.
3. **Temperature offset.** Once the sensor's temperature moves less than 0.1 °C in
   10 minutes (not before 30 min), take the mean of sensor minus reference over
   the remaining minutes. Enter its negative as the temperature offset.
4. **Humidity.** With "Correct the humidity with the temperature" on, compare the
   corrected humidity with the reference. Enter only the residual as the humidity
   offset, and only if it is larger than both instruments' stated accuracy
   together.
5. **Repeat with other loads:**
   - night brightness;
   - maximum brightness;
   - a Lua effect page (CPU load);
   - on another day and room temperature.

   Five sessions or more decide whether one offset is enough, or whether 5.3's
   load idea earns a model.
6. **Record per session:** date, room temperature, page, brightness, power path,
   case, offset found.

## 6. What it feeds

### 6.1 `/api/info`

It gets a `climate` object:

| Field | |
|---|---|
| `state` | `off`, `probing`, `ok`, `stale`, `absent` |
| `intervalS` | seconds |
| `tempC`, `humidity` | what the panel reports (smoothed, offsets, compensation), while a reading exists |
| `sensorTempC`, `sensorHumidity` | smoothed, before the offsets: the numbers the measurement plan logs |
| `ageS` | since the last good reading |
| `reads`, `crcErrors`, `i2cErrors`, `softResets` | counters since boot. `i2cErrors` counts only once the sensor has been found, so an absent part's once-a-minute look does not add to it |
| `foreignDevice` | only when something that is not an SHTC3 answered |
| `ha`, `haPublishes` | with the MQTT bus |

The portal's diagnostics text shows a line with the state, the reading and the
error counters.

### 6.2 Portal: the Indoor sensor card on the Clock page

The card is shown only in builds whose `/api/portal` lists `climate`.

| Field | Key | NVS | Default | Bounds |
|---|---|---|---|---|
| Read the board's sensor | `climateEnabled` | `climEn` | on | |
| Temperature offset, °C | `climateTempOffset` (tenths) | `climTOff` | 0 | ±20.0 |
| Humidity offset, %RH | `climateHumOffset` (tenths) | `climHOff` | 0 | ±20.0 |
| Correct the humidity with the temperature | `climateRhFollowsT` | `climRhT` | on | |
| Read every, seconds | `climateIntervalS` | `climIvl` | 10 | 5-300 |
| On the weather screen | `climateShow` | `climShow` | 0 off | 1 indoor line, 2 badge, 3 split. Stored, not drawn yet |
| Publish to Home Assistant | `climateHa` | `climHa` | **off** | only with the bus |

**Where they live.**
- In the main `Settings` struct: seven more keys in the `pcmonitor` namespace,
  so `saveSettings()` writes 136.
- In `/api/export` and `/api/import`, with the same bounds.
- A live line under the switch, from the 5 s `/api/info` poll: "Now 23.4 °C and
  45 %RH; the sensor itself reads 25.1 °C and 40 %RH (7 s ago)".

**Units.** The unit on the panel follows the weather's Fahrenheit switch. The
offsets are entered in °C.

**Why the interval is 5-300 s, default 10.** Faster than the sensor's response
(8 s humidity, 5-30 s temperature) adds nothing.

### 6.3 Home Assistant, over the MQTT bus

Sources [13][14].

**Default off,** so no entities appear in anyone's Home Assistant until the
switch is on.

**Discovery.** `homeassistant/sensor/nickoscope_matrix_<mac3>/indoor_temperature/config`
and `…/indoor_humidity/config`, with:
- `device_class` temperature (°C) and humidity (%);
- `state_class` measurement;
- `suggested_display_precision` 1 and 0;
- `expire_after` = 3 × max(interval, 60 s);
- `value_template {{ value_json.t }}` / `{{ value_json.rh }}`;
- one device: name `settings.deviceName`, model ESP32-S3-RGB-Matrix,
  manufacturer Waveshare, sw_version the firmware's.

**Configs are retained** and sent again on every connect. Home Assistant's docs
prefer re-sending on its birth message [14]. That costs a subscription and a
handler, and the bus has one of each left. Sending an empty config removes the
entity [14]; the firmware does that whenever the switch or the sensor is off.
The configs go out only after the sensor has been found.

**State.** `nickoscope_matrix/<mac3>/climate/state`, payload
`{"t":23.4,"rh":45.0}`, not retained. It is sent when the value moves 0.1 °C or
1 %RH, and at least once a minute while readings arrive. In °C always: Home
Assistant converts.

## 7. The weather screen: three designs (previews)

`tools/climate/render.py` draws today's screen from the firmware's own
constants, colours and draw calls. It adds the indoor reading three ways.
Pictures and the details are in `tools/climate/preview/` and its README.
Indoor values are 23.4 °C and 45 %.

| | What changes | For | Against |
|---|---|---|---|
| **A indoor line** | time up 1 row, icon and big temperature up 6, details row up 8. A 5x7 line at row 56: amber house, white 23.4 with a thin dot and degree mark, dim humidity | the most legible indoor reading; outdoor keeps size and colours | two text lines at the bottom make it a list; every row of today's screen moves |
| **B split** | icon to x 1, big temperature to x 28, a dim rule at x 89. An indoor column from x 92: house and 5x7 temperature, humidity under it | reads "outside \| inside" at a glance; indoor stays 5x7 | the weather block leaves the centre. A three-character outdoor temperature (-10 °C and below, 100 °F and above) drops its unit letter |
| **C badge** | nothing moves. Two Picopixel lines at x 104-126, rows 37-47, beside the big temperature | the least intrusive; today's screen untouched | the smallest text; may be taken for a "feels like"; cramped beside a three-digit temperature |

**States.**
- **Stale:** a dim house and dashes.
- **Absent or switched off:** all three fall back to today's screen, so A leaves
  no empty line.

**Shared rules.**
- Indoor temperature: one decimal from -9.9 to 99.9, whole degrees beyond.
- Humidity in whole percent (±2 %RH typ).

**Layout budget.** 1792 cases with the widest strings, every icon at every
animation phase. No two parts within one pixel, nothing off the panel: clean.

**The owner chooses.** Then the firmware copies the chosen `CL_*` block, and
`climateShow` selects it.

## 8. Checks run

| Check | Result |
|---|---|
| `python3 tools/climate/check_climate.py`: CRC examples (Table 16), Figure 7 to 63 %RH and 23.7 °C, conversion ends, ID mask, Magnus against the guide's 5 %RH, offsets, clamps, smoothing, staleness across the `millis()` wrap | 56 checks, 0 failed |
| `python3 tools/climate/render.py` layout budget | clean, 1792 cases |
| `pio run -e matrix-waveshare-rgb` | SUCCESS, no warnings from the new or touched files |
| `python3 tools/web_assets_gen.py --check` | OK |
| `PORTAL_JS`, taken from `web_pages.h`, through JavaScriptCore's `checkSyntax` | parses; `climateStatus()` defined and called |
| `tools/flightboard/check_portal_js.py`, `tools/media/check_media.py` (the Panel script) | passed |
| pre-commit hook (climate test, portal assets, clock styles) | passed on every commit |
| `python3 tools/flag_matrix.py`, rows "climate + bus" and "climate without MQTT", and CLIMATE_ENABLED in "everything" | 41/41 behaved as intended, the bring-up images included |

## 9. Memory and CPU

**Build, whole env `matrix-waveshare-rgb`:**

| | Static RAM | Flash |
|---|---|---|
| 776fc04 | 100 576 B | 2 146 893 B |
| this branch with `CLIMATE_ENABLED` unset | 100 584 B (+8) | 2 151 569 B (+4 676) |
| with the module | 101 104 B (+528) | 2 178 189 B (+31 296) |

**Where the growth comes from.**
- The portal card, the settings and the import/export are built into every
  build: +4 676 B of flash.
- The module itself: +520 B of static RAM and +26 620 B of flash. That includes
  `Wire` and ESP-IDF's I2C driver, which the firmware did not link before. It
  was not broken down further.

**Heap.**
- Wire allocates its receive and transmit buffers when the bus starts
  (`I2C_BUFFER_LENGTH` 128 B, Wire.h [12]).
- The legacy driver's `i2c_driver_install()` adds its own objects; that source
  was not read. **Measure** `freeInternalHeap` in `/api/info` with the sensor
  switched on and off.
- The discovery builds a small `JsonDocument` for a moment, on each connect.

**CPU.**
- At most one transaction per `loop()` pass: about four per reading, every 10 s.
- At 100 kHz a transaction of three to seven bytes is about a millisecond
  (estimated from the bit rate).
- **Measure** `loopSlowPart` / `loopSlowPartMs`: "climate" should never be the
  slowest part.

## 10. Upstream

Keralots' rules ([09](09-upstream-contributions.md)):
- one PR off `main`;
- Conventional Commits;
- no flags;
- all three envs build;
- the `matrix-s3` size in the description;
- a README when setup is needed.

**Goes upstream:**
- `shtc3.h`, `climate_model.h`, the reader;
- the settings and portal card;
- `/api/info`;
- the weather-screen design once chosen.

Built for his `matrix-waveshare` env with the pins taken from his
`src/display/hub75_pins.h` pattern, no flag, found by the ID check.

**Stays in the fork:**
- the Home Assistant discovery (the MQTT bus is fork-only);
- `-DCLIMATE_ENABLED`;
- the flag-matrix rows.

**Not verified:** whether upstream `main`'s `clock_weather.cpp` still matches the
fork's layout. Check it before drafting.

## 11. Not verified

- That the SHTC3 answers at 0x70 on our board, and its ID. Do an I2C scan.
- That the corner part in the photo is U6.
- Clean signals at 100 kHz through M2. Waveshare's own choices are 40 and 400 kHz.
- The level on GPIO47/48 (1.8 V per the datasheet; question 6 of doc 12 wanted a
  meter).
- The self-heating offset, and whether it depends on load.
- The heap the I2C driver takes, and the time in `loop()`.
- Whether `log_e` from a NACK stays silent in this build.
- Home Assistant picking up the discovery. Nothing was sent to a broker.
- That the SOT-23-6 marked `02N` beside the IMU in the photo is M2. It is
  consistent with an NDC7002N, but its marking code was not looked up.

## 12. Sources

1. waveshareteam/ESP32-S3-RGB-Matrix, commit 4047e4e — `example/idf_v5.5.2/components/bsp/esp32_s3_matrix/include/bsp/config.h`, and `.../esp32_s3_matrix.c` (`bsp_i2c_init`)
2. Same repository, `hardware/schematics/ESP32-S3-RGB-Matrix-Schematics.pdf`; local copy `reference-drawings/controller/ESP32-S3-RGB-Matrix-Schematics.pdf` (U6, U2, U5, U9, M2, R10-R13, the pin table)
3. Same repository — `example/idf_v5.5.2/components/Middleware/Sensor/middle_sensor.c`, `example/idf_v5.5.2/main/examples/06_Matrix_SHTC3/matrix_shtc3.c`
4. Same repository — `example/arduino_v3.3.7/08_Sensor_Test/08_Sensor_Test.ino`
5. Sensirion, *Datasheet SHTC3*, Version 4, December 2022 — https://sensirion.com/media/documents/643F9C8E/63A5A436/Datasheet_SHTC3.pdf
6. [02-controller.md](02-controller.md) — device addresses on the bus
7. Espressif, *ESP32-S3 Series Datasheet*, §2.2 Pin Overview, note 2 — https://documentation.espressif.com/esp32-s3_datasheet_en.html
8. Espressif, *ESP32-S3-WROOM-2 Datasheet*, Table 3-1, note 2 — https://documentation.espressif.com/esp32-s3-wroom-2_datasheet_en.html
9. Sensirion, *Design Guide for Humidity and Temperature Sensors*, Version 2, March 2024, §3, §3.1, §3.3, Figures 8, 10, 11 — https://sensirion.com/media/documents/FC5BED84/662B494D/Sensirion_Humidity_Temperature_Design_Guide.pdf
10. Sensirion, *Introduction to Humidity*, Version 2.0, August 2009, eq. (3), (7), Table 1 — https://sensirion.com/media/documents/8AB2AD38/61642ADD/Sensirion_AppNotes_Humidity_Sensors_Introduction_to_Relative_Humidit.pdf
11. pedrominatel/esp-components, `shtc3` 1.4.2, commit edfcf35 — `shtc3/include/shtc3.h`, `shtc3/shtc3.c`
12. arduino-esp32 2.0.17 as PlatformIO installs it (framework-arduinoespressif32 3.20017.241212) — `libraries/Wire/src/Wire.cpp`, `Wire.h`, `cores/esp32/esp32-hal-i2c.c`
13. Home Assistant, *MQTT Sensor* — https://www.home-assistant.io/integrations/sensor.mqtt/
14. Home Assistant, *MQTT*, discovery — https://www.home-assistant.io/integrations/mqtt/
15. `photos/2026-09-14-arrival/controller-front.jpg` — the corner part and its slot
16. AnimatedPixelClock fork, `feature/market-dashboard` 776fc04 — `src/clocks/clock_weather.cpp`, `src/weather/weather.cpp`, `src/mqtt/mqtt_bus.cpp`, `src/media/media_ha.cpp`, `src/web/web.cpp`, `tools/web_assets_gen.py`
