# 42. Веб-прошивальщик прошивает двойника (ADR-TWIN-03)

**Статус:** работает, проверено 2026-09-29 в браузере на настоящей странице прошивальщика проекта.

**Порядок проверки:**
1. Пустой чип двойника.
2. Connect → «Двойник — USB-Serial/JTAG эмулятора (303A:1001)» → Install AnimatedPixelClock **2.7.4** с «Erase device».
3. Сброс по DTR/RTS в режим загрузки: `rst:0x15 (USB_UART_CHIP_RESET)`, strap 0x3.
4. Запись 1 487 218 байт, затем сброс в прошивку, strap 0xf.
5. «Installation complete!».
6. Шаг Improv «Configure Wi-Fi»: сеть NickoTwin (виртуальная точка двойника), «Device connected to the network!».
7. `twin.py verify`: флэш совпадает с образом везде, кроме раздела NVS, который пишет сама прошивка.

**Как устроено:**
- **Эмулятор.** Канал `/usj` через WebSocket, байты не теряются. Состояния DTR/RTS обрабатываются по TRM ESP32-S3, табл. 33.3-2 и 33.4-3/4. Для esptool есть `--serial-tcp`, RFC 2217. Настоящее ПЗУ и настоящий стаб esptool работают без подмен.
- **Страница.** Шим `navigator.serial` (VID 0x303A, PID 0x1001), `tools/twin/flasher/twin-serial.js`. Копию `docs/` с шимом и ESP Web Tools, закреплённой на версии 10.4.0, `twin.py run --web` собирает в `state/web/`. Публичная страница `docs/` не изменена.
- **esptool.py 4.9.0 через RFC 2217:** `write_flash --verify` полного образа, аппаратный сброс, загрузка прошивки. Выходит 929 кбит/с.

**Независимая проверка:** всё PASS. Замечания:
- **Средняя важность, исправлено:** `--blank` и `--fresh` удаляли `flash.bin` без копии. Теперь старый файл уходит в `state/backup/`.
- **Две мелкие, в бэклог:** событие `release` может теряться при закрытии порта; плашка «USB занят» не доходит до вкладки, открытой посреди прошивки.
- **Подтверждено: установка без стирания тоже сбрасывает Wi-Fi.** В полном образе раздел NVS заполнен 0xFF. Для обновления без потери настроек — OTA (`tools/agent/update.py`). Так живой двойник и обновлён до 2.7.4, подтверждение health пришло через 60 с.

Ниже — проект, по которому это сделано.

---

# Веб-прошивальщик для виртуального двойника: проект реализации

Дата: 2026-09-29. Проект опирается на четыре исследования (usj-hw, esptool-js, ewt, engine). Часть фактов я перепроверил сам по исходникам, результаты ниже.

Опорные версии:
- движок: esp32sim, ветка `nickoscope/twin` @ `b583216`;
- проект: AnimatedPixelClock-twin @ `659e4d8`;
- браузерная часть: ESP Web Tools 10.4.0, esptool-js 0.6.0, improv-wifi-serial-sdk 2.8.0.

Метки статуса: **[П]** проверено по первоисточнику, **[В]** вероятно (вывод из источника), **[Н]** не проверено.

Сокращения источников:
- **TRM**: ESP32-S3 TRM v1.8, локальная текстовая копия `scratchpad/s3trm.txt`.
- **EJS**: esptool-js, тег v0.6.0, `scratchpad/ejsrepo`.
- **EWT**: esp-web-tools, тег 10.4.0, `scratchpad/ewtrepo`.
- **SPEC**: WICG Web Serial, `index.html` @ `600bbf1`.
- **ENG**: esp32sim @ `b583216`.
- **APC**: AnimatedPixelClock-twin @ `659e4d8`.
- **LFS**: esptool-legacy-flasher-stub v1.3.0.

---

## 0. Итог

- **Что увидит владелец.** Он открывает `http://127.0.0.1:8790/flasher/`. Это копия страницы проекта, её собирает `twin.py`, а раздаёт веб-сервер движка. Владелец жмёт Install и выбирает «Двойник». Дальше ESP Web Tools 10.4.0 с esptool-js 0.6.0 сам делает сброс в режим загрузки, загружает stub, стирает и пишет flash. Всё это проходит через настоящий ROM, настоящий stub и модель octal flash. Затем идёт Improv Wi-Fi, и двойник загружается уже с нового образа.
- **Публичная страница не меняется.** На `nickoscope.github.io` шим не попадает. Движок всё равно отвечает 403 на чужой Origin (ENG `esp-soc/src/web.rs:128-143,191-193`) [П].
- **Движок: семь изменений (E1–E7).** Регистровая модель USJ, flash-модель (`spi_mem.rs`) и матрица прерываний не трогаются. Почему это безопасно, объяснено в §3.
- **Главный риск уже в основном снят.** Эксперимент engine прошил двойника через настоящий ROM и stub. Я сверил результат: `flash-after-write.bin` совпадает с `AnimatedPixelClock-waveshare-v2.7.3-Full.bin` везде, кроме 4612 байт в диапазоне `0x9000–0xA5BD`. Это NVS, её прошивка записала при первом старте [П]. Стирание оставило все 32 МБ равными `0xFF` [П].
- **Но stub в том опыте был другой сборки** [П, сверил JSON]:
  - в esptool-js 0.6.0 лежит stub с entry `0x40378A80`, он совпадает с esptool 4.8.1 и LFS v1.3.0 байт в байт;
  - PlatformIO-esptool (версия 4.9.0), на котором шёл эксперимент, использует `stub_flasher/1` с entry `0x40378ADC`.
  - Значит, stub, который реально пришлёт страница, в двойнике ещё не запускался. Это первая проверка в браузере (шаг W5).
- **Объём.** Engine-исследование оценило работу в 2–3 рабочих дня. Это оценка, не измерение.

## 1. Опорные факты

| # | Факт | Источник | Статус |
|---|---|---|---|
| F1 | Пары (RTS, DTR): (0,0) сбрасывает флаг загрузки; (0,1) ставит его; (1,0) сбрасывает чип; (1,1) ничего не делает. Если флаг стоит в момент сброса, чип уходит в режим загрузки, иначе грузится с flash | TRM §33.3.2, табл. 33.3-2, с.1248 | П |
| F2 | Рекомендованные последовательности. В загрузку: (0,0) (0,1) (0,1) (1,1) (1,0) (1,0) (0,0). В загрузку с flash: (0,0) (1,0) «Reset SoC», затем (0,0) «Exit reset» | TRM табл. 33.4-3 и 33.4-4, с.1254 | П |
| F3 | SET_LINE_CODING и SEND_BREAK принимаются и игнорируются. Interrupt-endpoint USJ «никогда не шлёт событий», поэтому скорость порта ничего не значит, а входные сигналы модема всегда нулевые | TRM табл. 33.3-1 и текст §33.3.1, с.1247 | П |
| F4 | У S3 нет регистра, который видит RTS/DTR или запрещает этот сброс, поэтому логику линий надо строить на стороне хоста | usj-hw: IDF 5.5.4 `usb_serial_jtag_struct.h:15-251` | П (исследование) |
| F5 | Код 0x15 «USB (UART) reset» относится к типу Core Reset. Chip Reset бывает только от включения питания, brown-out и SWD | TRM табл. 7.1-1 и прим. 1, с.528 | П |
| F6 | Страпы защёлкиваются только при Chip Reset и держатся до отключения питания | TRM §8.1, с.534 | П |
| F7 | Если в режим загрузки вошли вручную (GPIO0), сброс через USJ из него не выводит: это Core Reset, он не перечитывает страпы | esptool docs, раздел «Leaving Download Mode in USB-Serial/JTAG Mode» (latest, esp32s3), прочитан 2026-09-29 | П |
| F8 | TRM §8.2 утверждает, что USJ умеет «перевести чип в SPI Boot из Joint Download». Это противоречит F7. Для ESP Web Tools разницы нет, пока GPIO0=1 | TRM §8.2, с.536 | Н (противоречие не разрешено) |
| F9 | Чип держится в сбросе, пока линии в состоянии (1,0). Флаг защёлкивается в момент входа в сброс | Вывод из примечаний табл. 33.4-3/4. Модель моста engine так и работала, и сработала | В |
| F10 | Раскладка GPIO_STRAP (0x60004038): bit2 = GPIO46, bit3 = GPIO0, bit4 = GPIO45, bit5 = GPIO3. ROM считает режимом загрузки случай `(v&0xC)==0` | TRM рег. 6.15, с.506; дизассемблер `boot_prepare`/`main` (usj-hw); опыт engine со страпами 00…0f | П |
| F11 | esptool-js выбирает `UsbJtagSerialReset`, только если `getInfo().usbProductId === 0x1001`. Иначе он делает ClassicReset, а тот на USJ приводит к загрузке с flash | EJS `esploader.ts:586-609`; `reset.ts` | П |
| F12 | `setRTS(x)` делает два вызова: `setSignals({requestToSend})`, затем `setSignals({dataTerminalReady: _DTR_state})` | EJS `webserial.ts:434-457` | П |
| F13 | Сама последовательность `UsbJtagSerialReset` | EJS `reset.ts:113-129` | П |
| F14 | Сброс после прошивки: `setRTS(true)`, 100 мс, `HardReset` (100 мс, `setRTS(false)`). По линиям это (1,0), около 200 мс, затем (0,0) | EWT `flash.ts:195-253`; EJS `reset.ts:147-162`, `esploader.ts:1713-1721` | П |
| F15 | Подключение: до 7 попыток; в каждой сброс, `peek()` в поисках баннера (только для диагностики) и до 5 SYNC. Перед каждым SYNC вызывается `flushInput()`, таймаут ответа 100 мс | EJS `esploader.ts:526-577,617-634` | П |
| F16 | S3-класс не переопределяет `getChipRevision`, поэтому READ_REG идут на адреса ESP32 `0x3FF5A00C`, `0x3FF5A014`, `0x3FF6607C`. Это происходит в `main()` и в `runStub()`. В движке такое чтение даёт `Fault::Unmapped`, а ядро поднимает LOAD_PROHIBITED | EJS `targets/esp32.ts:79-99`, `esploader.ts:1242,1307`; ENG `esp32s3/src/bus.rs:640,651`, `xtensa-lx7/src/exec.rs:305` | П |
| F17 | На железе эти чтения прошивку не ломают: страница прошила плату 2026-09-21, включая Improv. Какое значение возвращает кремний, неизвестно | `LED-MATRIX APOLLO/HANDOFF.md:1324-1330` | В |
| F18 | ESP Web Tools читает `"serial" in navigator` и `isSecureContext` один раз, при загрузке модуля. `requestPort()` вызывается без фильтров, `open({baudRate:115200, bufferSize:8192})` | EWT `install-button.ts:6,8`; `connect.ts:7,24` | П |
| F19 | Перед прошивкой диалог закрывает порт. Через 100 мс после конца он открывает тот же объект снова и ждёт Improv `new_install_improv_wait_time`×1000 мс. У нас это 15 с | EWT `install-dialog.ts:993-1013,1047-1061`; APC `docs/flasher.js:50` | П |
| F20 | На USJ ROM записывает в UARTDEV_BUF_NO значение 4, поэтому блок RAM остаётся 0x1800. Значение 3 означает USB-OTG. В сводке ewt сказано «3 (USB)», для USJ это неверно | usj-hw (дизассемблер ROM); EJS `targets/esp32s3.ts:27-29` | П |
| F21 | Где WebSocket-сервер теряет или портит данные: входящих binary-кадров держит не больше 4 (`web.rs:228`); при полной очереди клиента кадр молча выбрасывается (`web.rs:12-16`, очередь 256, `:199`); консоль идёт через `from_utf8_lossy` в JSON (`machine.rs:326-345`, `machine/web.rs:101-102,166-173`) | ENG | П |
| F22 | Ввод от браузера опрашивается раз в push-интервал, по умолчанию 50 Гц, то есть каждые 20 мс эмулированного времени | ENG `esp-soc/src/board.rs:62`, `machine.rs:1019,1028-1030` | П |
| F23 | `reboot()` пересоздаёт периферию, включая USJ, и копирует `gpio.strap` без изменений | ENG `esp32s3/src/soc.rs:122-147` | П |
| F24 | Всё, что трогают ROM и stub в USJ, в модели уже есть: EP1/EP1_CONF, INT_ENA/INT_CLR, бит 2 RECV_PKT, источник прерывания 96 | ENG `usb_serial_jtag.rs:28-65`, `esp32s3/src/periph.rs:40`; LFS `stub_io.c:42-81` | П |
| F25 | Flash-модель декодирует все опкоды stub-пути в режиме octal: 0x9F, 0x05, 0x06, 0x20/0x21, 0xD8/0xDC, 0x12, 0x0C, а также встроенные RDSR/WREN/CE | ENG `spi_mem.rs`; esptool-js-исследование; опыт engine | П |
| F26 | Страница на `http://127.0.0.1` является secure context. Подмена `navigator.serial` через `Object.defineProperty` работает в Chromium 152 | Secure Contexts §3.1 (ewt); ewt, опыт в Chromium 152 | П (Chromium 152) / Н (обычный Chrome) |
| F27 | Improv прошивка поднимает только при первом старте, без сохранённого Wi-Fi. Виртуальная точка доступа у двойника есть, только если существует `state/wifi.txt` | APC `docs/flasher.js:45-49`; `tools/twin/twin.py:62-66` | П |
| F28 | С `--web` движок работает в реальном времени (`m.rt.enabled = true`) и слушает только 127.0.0.1 | ENG `cli/src/lib.rs:478-479`; `web.rs:79` | П |

## 2. Схема

```
Chrome: http://127.0.0.1:8790/flasher/index.html   (копия docs/, собирает twin.py)
  <head>: <script src="/usj-serial.js">   ← шим, классический скрипт, ДО модуля
  esp-web-tools@10.4.0 → esptool-js 0.6.0 / improv-sdk 2.8.0
        │  navigator.serial.requestPort() → UsjSerialPort (VID 0x303A, PID 0x1001)
        │  readable/writable/setSignals
        ▼
  WebSocket ws://127.0.0.1:8790/usj   (binary, эксклюзивный, без потерь)
        ▼
esp32sim: web.rs (Shared.usj_in, неограниченная очередь)
  Machine::usj_service()  (каждую 1 мс эмулированного времени, пока порт занят)
     ├─ Data   → SocBus::serial_input → UsbSerialJtag FIFO → ROM / stub (IRQ 96→17)
     └─ Lines  → SocBus::usj_lines → UsjLines (табл. 33.3-2)
                    └─ вход в (1,0): request_reset(0x15) → reboot() → страп-латч
                                     → hold_in_reset() до выхода из (1,0)
  drain_console: USJ tx_out → кадр 0x00 в /usj (пока порт занят)
  spi_mem → flash[] → persist_flash → ~/twin/state/flash.bin
```

## 3. Изменения движка (esp32sim)

Все изменения делаются в ветке движка. После каждого проверенного шага они экспортируются в `tools/twin/engine/esp32sim-twin.patch` вместе с `HISTORY.txt`.

### E1. Чтения из зарезервированного окна `0x3FF2_0000..=0x3FFF_FFFF` возвращают 0

- **Зачем.** Без этого стоит всё (F16). Страница, скорее всего, валит ROM-обработчик READ_REG ещё до загрузки stub.
- **Где.** `esp32s3/src/bus.rs`, функции `read8_access`, `read16_access`, `read32_access` (строки 629–651). В ветке `None` для адресов из этого окна возвращать `Ok(0)` и печатать один раз на страницу 64 КиБ: `[emu] read of reserved 0x.. -> 0`. Записи и выборка команд из этого окна по-прежнему дают исключение.
- **Граница окна.** DROM у S3 заканчивается на `0x3FF1_FFFF` (TRM табл. 4.3-1, с.403, по esptool-js-исследованию). Все три адреса попадают в окно.
- **Что вернёт кремний** [Н]. Ноль даёт в логе esptool-js «Chip Revision: 0», это косметика. Реальное значение можно узнать одним чтением на панели: `esptool read-mem 0x3ff5a00c`. Это только чтение, но делать его владельцу, потому что нужна плата.
- **Тест.** Юнит-тест шины: `read32(0x3FF5A00C) == Ok(0)`, а `write32` туда же даёт ошибку.

### E2. Состояние линий DTR/RTS по TRM, табл. 33.3-2

Чистая логика кладётся в `esp-periph/src/usb_serial_jtag.rs`, отдельно от регистров. Регистровая модель пересоздаётся при каждом `reboot()`, а линии должны переживать сброс (F4, F23).

```rust
pub struct UsjLines { pub dtr: bool, pub rts: bool, pub flag: bool, pub held: bool, pub latched_dl: bool }
pub enum LineEffect { None, AssertReset { download: bool }, ReleaseReset }
impl UsjLines {
    pub fn set(&mut self, dtr: bool, rts: bool) -> LineEffect {
        let was_reset = self.rts && !self.dtr;
        self.dtr = dtr; self.rts = rts;
        match (rts, dtr) { (false, false) => self.flag = false, (false, true) => self.flag = true, _ => {} }
        let now_reset = rts && !dtr;
        if now_reset && !was_reset { self.held = true; self.latched_dl = self.flag; return LineEffect::AssertReset { download: self.flag }; }
        if was_reset && !now_reset { self.held = false; return LineEffect::ReleaseReset; }
        LineEffect::None
    }
}
```

- **Семантика.** Логика работает по уровням и срабатывает на каждое сообщение, без склейки. Флаг защёлкивается при входе в (1,0) (F9, [В]). Повтор того же состояния ничего не меняет. Поэтому одинаково обрабатываются и пары вызовов из 0.6.0 (F12), и один совместный вызов из 0.7.0, который шим разложит на DTR, затем RTS (SPEC, `setSignals`).
- **Константы.** В `esp-periph/src/rtc_cntl.rs:7-12` добавить `RST_USB_UART_CHIP = 0x15` и `RST_USB_JTAG_CHIP = 0x16`, а в `reset_cause_name` имена `USB_UART_CHIP_RESET` и `USB_JTAG_CHIP_RESET`. Источники: IDF `rom/rtc.h:90-91` и строки ROM (usj-hw, engine). Сейчас `reset_cause_name(0x15)` возвращает `"?"`.
- **Трейт `SocBus`** (`esp-soc/src/soc.rs`, всё с пустой реализацией по умолчанию, так что C3/C6 и wasm не затронуты):
  - `fn usj_lines(&mut self, dtr: bool, rts: bool) -> bool` возвращает true, если запрошен сброс чипа;
  - `fn reset_held(&self) -> bool`;
  - `fn set_usj_reset_enabled(&mut self, on: bool)`.
- **Реализация для S3** (`esp32s3/src/soc.rs`, поля `usj: UsjLines` и `usj_reset_enabled` в `SocBus`, `bus.rs`):
  - `AssertReset` при разрешённом сбросе вызывает `request_reset(0x15)` и возвращает true.
  - При запрещённом сбросе пишется `eprintln!` «line reset ignored», сброса нет.
  - Разрешает сброс CLI: только при `--boot rom`, без `--no-reboot` и без cost-model. Причина: в режиме `--boot app` функция `run_with_reboots` на `SwReset` завершила бы прогон (`cli/src/lib.rs:391-411`).

### E3. Страп: «провода платы» отдельно от защёлки

Поля `SocBus` (S3):
- `strap_pins` берётся из `--strap`. По умолчанию `0x0f`, как сейчас (`gpio.rs:16`), чтобы не менять текущие логи и голдены.
- `strap_latched` хранит значение, защёлкнутое при последнем Chip Reset.

`set_strap(v)` задаёт `strap_pins = v` и пересчитывает защёлку. В `reboot()` (`soc.rs:129`) вместо копирования:

```rust
let gpio0_high = old.gpio.input & 1 != 0;          // уровень пина в момент сброса (BOOT/TSOP/SW, wired-AND)
p.gpio.strap = match cause {
    RST_POWERON => { self.strap_latched = if gpio0_high { self.strap_pins } else { self.strap_pins & !0x08 }; self.strap_latched }
    RST_USB_UART_CHIP => if self.usj.latched_dl { self.strap_latched & !0x0C } else { self.strap_latched },
    _ => old.gpio.strap,                            // Core/System reset: страпы не перечитываются (TRM §8.1)
};
```

- **POWERON (Chip Reset) пересэмплирует GPIO0** (F5, F6). Уровень берётся из `old.gpio.input` до пересоздания периферии. На панели GPIO0 — это wired-AND от TSOP, кнопки энкодера и BOOT (`esp32s3/src/board/panel_inputs.rs:6-11`). Бит 3 в `--strap` работает как «перемычка на землю»: если там 0, режим загрузки включается независимо от кнопки.
- **Сброс 0x15.** С флагом очищаются только биты [3:2]. Это тот же эффект, который TRM документирует для `FORCE_DOWNLOAD_BOOT` («1x → 00», §8.2, с.536). Для USJ регистр в TRM не описан [Н]. ROM такой страп принимает: опыт engine со страпами 00/01/02/03/23.
- **Без флага защёлка не меняется.** Ручной режим загрузки переживает сброс через USJ, как в esptool docs (F7). Утверждение TRM §8.2 (F8) не реализуется и помечается [Н].
- **Прочие сбросы** (SW_SYS, WDT) оставляют регистр как есть, это нынешнее поведение. Для кремния это [Н].
- **Необязательно.** Можно учитывать `RTC_CNTL_OPTION1.FORCE_DOWNLOAD_BOOT` (0x12C бит 0) на не-Chip сбросах (TRM §8.2). Для ESP Web Tools это не нужно.

### E4. Удержание в сбросе

`Machine::hold_in_reset()` живёт в `esp-soc/src/machine.rs`. Её вызывает `run_with_reboots` сразу после `m.reboot()`, если `bus.reset_held()`:

```rust
pub fn hold_in_reset(&mut self) -> Option<Stop> {
    let step = S::CPU_HZ / 1000;
    while self.bus.reset_held() {
        if self.bus.cycles() >= self.max_cycles { return Some(Stop::Halted); }
        self.after_round(step);   // время устройств, скрипты, web push/poll, /usj, rt-пейсинг
    }
    None
}
```

- **Время идёт, ядра стоят.** Это соответствует «Set RTS: Reset SoC … Clear RTS: Exit reset» (F2, F9). Скриптовые события и пейсинг работают без особых случаев (`after_round`, `machine.rs:959-969,1013-1021`). Ядра уже сброшены в `reboot()`, и инструкции не выполняются.
- **Никогда не зависнуть навсегда.** Удержание снимается тремя путями:
  - сообщением `(0,0)` от хоста;
  - отключением клиента /usj, которое движок обрабатывает как `(0,0)`, см. E5;
  - ограничением `max_cycles`.

### E5. Бинарный канал `/usj`

**Протокол.** Только binary-кадры, первый байт задаёт тип:

| Направление | Кадр | Смысл |
|---|---|---|
| хост → эмулятор | `0x00` ‖ байты | Данные хоста в USJ OUT (`UsbSerialJtag::host_input`, там они режутся на пакеты по 64 байта) |
| хост → эмулятор | `0x01` ‖ `b` (bit0 = DTR, bit1 = RTS) | Полное состояние линий после одного изменения |
| эмулятор → хост | `0x00` ‖ байты | USJ IN (`tx_out`) без изменений |
| эмулятор → хост | `0x10` ‖ JSON UTF-8 | События: `hello{proto:1,chip,lines,held}`, `reset{cause,download,strap}`, `release` |

Текстовые кадры и неизвестные типы на `/usj` игнорируются, неизвестный тип один раз пишется в stderr.

**Сервер** (`esp-soc/src/web.rs`):
- Маршрут берётся из пути запроса на upgrade: `/usj` отдельно, всё остальное как сейчас (`panel.html` открывает `/ws`, `web/panel.html:220`).
- Origin проверяется той же `local_origin()`.
- Эксклюзивность: второй клиент получает `409 Conflict` до `101`. Это аналог TIOCEXCL, который выставляет Chrome (ewt: `serial_io_handler_posix.cc`).
- Приём идёт в `Shared.usj_in: VecDeque<UsjIn>` без ограничения размера. Отдача идёт через неограниченный `mpsc::channel`, а не через `sync_channel(256)`, и никогда не отбрасывает кадры (F21).
- Подключение и отключение кладутся в ту же очередь как `Attached` и `Detached`, чтобы порядок сохранялся.
- API: `usj_attached()` (AtomicBool, без мьютекса), `poll_usj()`, `send_usj(&[u8])`, `send_usj_event(&str)`.

**Машина** (`esp-soc/src/machine/web.rs` и `machine.rs`):
- **`usj_service()`** переносит новые сообщения в `ws.usj_pending` и применяет их по порядку:
  - `Data` вызывает `bus.serial_input`;
  - `Lines`: если `bus.usj_lines(..)` вернул true, цикл останавливается. Остаток ждёт до конца `reboot()`, чтобы байты после сброса не попали в старую FIFO, которую сброс уничтожит;
  - `Attached` означает, что порт занят;
  - `Detached` применяет `(0,0)` (снимает удержание) и освобождает порт.
  - В конце вызывается `drain_console()`.
- **Когда вызывается.** Из `web_poll_input` (вход в `run()` и каждые 20 мс) и из `after_round_rest`, если порт занят и прошла 1 мс эмулированного времени.
  - 1 мс — это проектный выбор, а не норма: это период SOF, который модель USJ уже эмулирует (`usb_serial_jtag.rs:11,25-27`).
  - Цель: уложиться с запасом в 100 мс на первый ответ SYNC (F15). С нынешними 20 мс на ввод и ещё 20 мс на вывод выходит до 40 мс эмулированного времени плюс WebSocket.
- **`drain_console()`** (`machine.rs:326`): пока порт занят, поток USB уходит только в `/usj`. Он не попадает в JSON, в бэклог `hello` и в stdout, а UART0 остаётся как есть. Когда порт свободен, всё работает как сейчас.
- **Ввод в USB из `/ws`** (`"serial"`/`"key"` с src usb, `machine/web.rs:166-173`), пока порт занят, отбрасывается. В `/ws` уходит `{"t":"usj","claimed":true|false}`, и `panel.html` может показать «USB занят прошивальщиком» (по желанию).
- **События.** При `AssertReset` и `ReleaseReset` клиенту уходит событие `0x10`, а в stderr строка `[emu] usj: RTS=1 DTR=0 → chip reset 0x15, download=…`. Эта строка — основной журнал для приёмки.

### E6. Мелочи

- **`--web-mount /flasher=DIR`** (`cli/src/lib.rs`, `web.rs::static_file`): второй корень статики с той же защитой через canonicalize. Нужен потому, что `static_file` не пускает симлинки за пределы `web_dir` (`web.rs:145-152`), а класть файлы в `esp32sim/web/` значит засорять git движка.
- **`content_type`**: добавить `jpg`/`jpeg` → `image/jpeg`.
- **Скриптовые глаголы** для безголовых голденов (`load_script`, `machine.rs` около строки 1091): `usj <dtr> <rts>` и `usjhex <hex>`.

### E7. Шим (в движке)

Шим — это `web/usj-serial.js`, и лежит он в движке: протокол и его клиент версионируются вместе. К нему добавляется самотест `web/usj-selftest.html`. Подробности в §4.

### Что не меняем и почему

- **Регистры USJ.** ROM обращается только к EP1 и EP1_CONF, stub дополнительно к INT_ENA/INT_CLR, бит 2. Всё это есть (F24).
- **`spi_mem.rs`.** Все опкоды stub-пути уже есть (F25), опыт engine это подтвердил.
- **RTC WDT после сброса 0x15.** Движок разоружает его (`soc.rs:134`), а кремний сохраняет RTC-домен (F5). Это известное отличие: stub на USJ сам выключает WDT (LFS `stub_flasher.c:110-123`), а esptool-js с хоста этого не делает. Оставляем как есть и документируем.

## 4. Шим `navigator.serial` (`web/usj-serial.js`, около 250 строк)

**Подключение.** Это классический синхронный `<script>` первым в `<head>`. Он должен выполниться до модуля ESP Web Tools: модульные скрипты выполняются после разбора документа (HTML §4.12.1, ewt), а `isSupported` читается при загрузке модуля (F18).

**Условия работы.**
- Шим активен, только если страница пришла с того же сервера, где есть `/usj`, то есть с веб-сервера двойника.
- Оригинал сохраняется: `const native = navigator.serial`.
- Затем `Object.defineProperty(navigator, 'serial', {value: usjSerial, configurable: true, enumerable: true})` (F26).

| Член | Поведение | Основание |
|---|---|---|
| `requestPort(opts)` | Показывает `<dialog>` с тремя кнопками: «Двойник», «Плата по USB», «Отмена». «Двойник» возвращает единственный `UsjSerialPort`. «Плата» синхронно, прямо в обработчике клика, вызывает `native.requestPort(opts)`: клик даёт нужную активацию, и прошивка железа с этой страницы не ломается. «Отмена» отклоняет промис с `DOMException('No port selected by the user.', 'NotFoundError')`, и ESP Web Tools показывает свой диалог «порт не выбран». Параметр `?twin=auto` пропускает выбор (для автотестов). Если фильтры переданы и ни один не подходит под 303A/1001, запрос сразу уходит в native | EWT `connect.ts:7-16`; SPEC `requestPort` |
| `getPorts()` | Двойник, если его уже выбирали, плюс `native.getPorts()` | SPEC. ESP Web Tools не использует |
| `port.getInfo()` | `{usbVendorId: 0x303A, usbProductId: 0x1001}` | F11: без PID 0x1001 сброса в режим загрузки не будет |
| `open(o)` | `InvalidStateError`, если порт не closed. `TypeError` на `baudRate` ≤ 0, `dataBits` ∉ {7,8}, `stopBits` ∉ {1,2}, `bufferSize` 0. Отсутствующие поля получают значения по умолчанию (8/1/none/255/none). Скорость игнорируется (F3). Открывает `ws://<host>/usj` и ждёт событие `hello` с `proto==1`. При 409 или обрыве отклоняет с `NetworkError` «Failed to open serial port.». **Линии не трогает** | SPEC `open()`; esptool-js-исследование: open и close не должны становиться сбросом |
| `readable` | Ленивый геттер. Пока порт открыт и нет фатальной ошибки, создаёт `new ReadableStream({type:'bytes', start, cancel}, {highWaterMark: bufferSize})`. Кадры `0x00` кладутся в поток копией. Если потока нет, байты копятся в буфере до следующего `readable`. `cancel` отбрасывает буфер и обнуляет `[[readable]]` | SPEC `readable`/cancel; ESP Web Tools в консоли делает `pipeThrough(TextDecoderStream)` и после cancel заново читает `port.readable` (ewt) |
| `writable` | Ленивый геттер: `WritableStream` с `ByteLengthQueuingStrategy`. `write(chunk)`: если не BufferSource, `TypeError`; иначе отправка кадра `0x00`, затем ожидание, пока `ws.bufferedAmount` не упадёт ниже 64 КиБ. `abort` и `close` обнуляют `[[writable]]` | SPEC `writable` |
| `setSignals(s)` | `InvalidStateError`, если порт не opened. `TypeError`, если пустой. Сначала DTR, потом RTS: на каждый присутствующий член отдельный кадр `0x01` с полной парой. `break` игнорируется (F3). Промис выполняется после `ws.send` | SPEC `setSignals` (порядок DTR → RTS); F12 |
| `getSignals()` | Все четыре поля false | F3 |
| `close()` | Если какой-то поток заблокирован, `TypeError`. Иначе cancel и abort потоков, закрытие WebSocket с кодом 1000, **без изменения линий**, `state = closed` | SPEC `close()`; EJS `webserial.ts:480-499` |
| Обрыв WS в открытом состоянии | Оба потока получают ошибку `DOMException('The device has been lost.', 'NetworkError')`, ставятся флаги фатальной ошибки, срабатывает событие `disconnect` | SPEC |

Сознательное отличие от Chrome: при переполнении `highWaterMark` шим не выбрасывает `BufferOverrunError`, а продолжает класть данные в поток, без потерь.

Для отладки есть кольцевой журнал событий `window.__usjLog`: линии, события `reset`, `release`, счётчики байт. Его читает автотест во встроенном браузере.

**Самотест `web/usj-selftest.html`.** Страница делает `import {ESPLoader, Transport} from "https://unpkg.com/esptool-js@0.6.0/bundle.js"` (ESM-бандл экспортирует оба класса, я проверил в `ejs060/package/bundle.js`). Затем по кнопке:
1. `requestPort` с `twin=auto`;
2. `new Transport(port)`;
3. `new ESPLoader({transport, baudrate:115200, romBaudrate:115200, terminal})`;
4. `main()`, затем `flashId()`;
5. `after('hard_reset')`, затем `disconnect()`.

Страница проверяет esptool-js, шим и движок без интерфейса ESP Web Tools, и именно со stub 0.6.0.

## 5. Страница прошивальщика для двойника

Её собирает `twin.py` в `~/twin/state/flasher/`. Это вне репозиториев, сборка идёт при каждом запуске, коммитов нет. Движок раздаёт её через `--web-mount /flasher=…`.

- **Что копируется** из `AnimatedPixelClock-twin/docs/`: `index.html`, `flasher.js`, `styles.css`, `img/`, `firmware/latest/*`. `flasher.js` строит URL прошивки относительно `location.href` (`flasher.js:37-40`), так что путь `/flasher/` работает без правок.
- **Что меняется в `index.html`.** Каждый якорь должен найтись ровно один раз, иначе сборка падает: так видно, если оригинал разойдётся с копией.
  1. После `<meta charset="utf-8">` вставляется `<script src="/usj-serial.js"></script>`.
  2. `https://unpkg.com/esp-web-tools@10/` заменяется на `…@10.4.0/`. Сейчас `@10` на unpkg и так отдаёт 10.4.0 (ewt), но закрепление защищает от смены сценария сброса или переоткрытия в следующем 10.x.
  3. К `<title>` дописывается префикс «Двойник · ».
- **`flasher.js` не меняется.** Проверка `'serial' in navigator` (`flasher.js:139,285`) проходит, потому что шим уже установлен.
- **Выбор образа.** По умолчанию берётся `docs/firmware/latest`. `--flasher-image PATH --flasher-version VER` кладёт другой образ под именем `AnimatedPixelClock-waveshare-<VER>-Full.bin` и пишет `VERSION`. Имя образа задаёт `flasher.js:28,38`.
- **Новые ключи `twin.py run`:**
  - `--flasher` включает сборку и `--web-mount` и печатает URL;
  - `--blank`: новый чип стёрт целиком, `--flash-image` не передаётся. `set_flash_size` заполняет flash байтами `0xFF` (`soc.rs:177`), а `--flash-persist` создаёт файл из того, что есть (`cli/src/lib.rs`, `prepare`);
  - `TWIN_ENGINE`: переопределяет путь к движку, чтобы запускать сборку из рабочей ветки.
- **Почему не публичная страница.** Движок отвечает 403 на Origin `https://nickoscope.github.io` (F21). Правила Chrome Local Network Access для WebSocket, по данным ewt, в разработке (M147), и это [Н]. Опасно и для обычных пользователей. Страница двойника той же origin, что и `/usj`, поэтому ни одно из этих ограничений её не касается.

## 6. Порядок работ и приёмка

Правило владельца: коммит и push после каждого проверенного шага. Для движка это коммит в ветке и экспорт patch в APC, затем коммит и push APC.

| Шаг | Работа | Приёмка |
|---|---|---|
| W0 | Ветка движка `nickoscope/usj-flash` от `b583216`. Копия `~/twin/state/flash.bin` в `flash-before-webflash.bin` | `cargo test` зелёный до начала работы, число тестов записано |
| W1 | E1 | Юнит-тест шины. Голден: в режиме загрузки (`--strap 00`, `--serial-hex` с SLIP-кадром READ_REG 0x3FF5A00C) приходит ответ со статусом 0 и без исключения |
| W2 | E2 и E3 | Юнит-тесты `UsjLines` и страпа, перечислены под таблицей |
| W3 | E4 и глаголы скриптов | Три голдена, перечислены под таблицей |
| W4 | E5 и E6 | Тесты `web/tests.rs` и стенд `usj_probe.py`, перечислены под таблицей |
| W5 | E7: шим и самотест во встроенном браузере (Chromium 152) | В логе самотеста: «Chip is ESP32-S3», «Stub running», «Manufacturer: c2, Device: 8039», размер 32MB, затем `reset{download:false}` и `rst:0x15 … SPI_FAST_FLASH_BOOT`. Это **первый запуск stub 0.6.0** в двойнике |
| W6 | Сборка страницы в `twin.py` и новые ключи | На `/flasher/index.html` версия 2.7.3. Отрисована кнопка установки, а не слоты `unsupported`/`not-allowed`. В консоли страницы нет ошибок |
| W7 | Сквозной тест A–C (§7) во встроенном браузере, плюс D и N1–N4 | По §7 |
| W8 | Прогон владельцем в обычном Chrome на Mac | Сценарий A проходит. Это закрывает F26 для обычного Chrome |
| W9 | Экспорт patch и `HISTORY.txt`. Раздел «Веб-прошивальщик» в `tools/twin/README.md`. Раздел в `docs/40-virtual-twin.md` базы знаний. Итог в HANDOFF | Patch воспроизводит ветку (`git apply` на `4ab7e90` даёт то же дерево, как сейчас проверяется). `git diff docs/` в APC пуст |

**W2, юнит-тесты `UsjLines`.** Каждая проверяемая последовательность повторяет вызовы `setSignals` один в один:
- табл. 33.4-3 (TRM) даёт ровно один `AssertReset{download:true}`, затем `ReleaseReset`;
- табл. 33.4-4 даёт ровно один `AssertReset{download:false}`;
- esptool-js 0.6.0 `UsbJtagSerialReset` (F13) даёт то же, что табл. 33.4-3;
- `ClassicReset` из 0.6.0 даёт сброс без флага;
- совместные вызовы 0.7.0, разложенные на DTR, затем RTS, работают так же;
- (1,1) не даёт ничего.

**W2, тесты страпа на уровне `SocBus`:**
- POWERON при GPIO0 = 0 даёт бит 3 = 0;
- 0x15 с флагом даёт `strap_latched & !0xC`;
- 0x15 без флага после ручного режима загрузки оставляет режим загрузки (F7);
- SW_SYS не меняет страп.

**W3, голдены без браузера** (`--board none --boot rom … --console usb --script …`):
1. Скрипт с последовательностью 0.6.0 (паузы 100 мс) и `usjhex` с SYNC. Ожидается:
   - `rst:0x15 (USB_UART_CHIP_RESET),boot:0x3 (DOWNLOAD(USB/UART0))` при страпе `0x0f`, по раскладке F10;
   - `waiting for download`;
   - 8 ответов SYNC вида `c0 01 08 0400 07071220 00000000 c0`, как в опыте engine.
2. Табл. 33.4-4: ожидается `rst:0x15 (USB_UART_CHIP_RESET),boot:0xf (SPI_FAST_FLASH_BOOT)`, затем старт приложения.
3. Пока линии в (1,0), число инструкций core0 не растёт, а баннер ROM появляется только после выхода из (1,0).
4. `--boot app`: печатается предупреждение, прогон продолжается.

**W4, тесты канала.**
- `web/tests.rs`:
  - все 256 значений байта проходят туда и обратно в кадрах `0x00`;
  - 10 000 кадров подряд доходят без потерь;
  - второй клиент `/usj` получает 409;
  - чужой Origin получает 403.
- `tools/twin/usj_probe.py`: простой клиент WebSocket на стандартной библиотеке Python. Он отправляет последовательность сброса и SYNC и получает 8 ответов. Отключение в (1,0) должно снимать удержание.
- Необязательно: esptool.py из PlatformIO (4.9.0) через обработчик pyserial `usj://` (переделка `scratchpad/py/emuhandler`) делает полный `write_flash`. Это нагрузка на канал со stub другой сборки.

**Задержки** (момент выхода из (1,0), первый ответ SYNC, номер попытки connect, время подтверждения каждого блока, полное время прошивки, `stat.speed` и `stat.behind`) записываются справочно. Условием прохождения они не являются. Жёсткие условия задают только внешние таймауты: 7×5 SYNC, 100 мс, 200 мс на MEM_END, 3 с на OHAI и на блок, 15 с на Improv. Порог из одного прогона не выводим (глобальное правило про пороги).

## 7. Сквозной тест: установка, Improv Wi-Fi, загрузка нового образа

**Подготовка.**
- `state/wifi.txt` существует, значит у двойника есть виртуальная точка доступа (F27).
- `check_flash.py IMAGE` — новый скрипт в `tools/twin/`. Он сравнивает `~/twin/state/flash.bin[0:len(IMAGE)]` с образом. Исключаются все data-разделы (type `0x01`) из таблицы разделов самого образа по адресу 0x8000; адреса не зашиваются в скрипт. На выходе список различающихся диапазонов и их принадлежность к разделам.

**A. Чистый чип, стирание, Improv Wi-Fi (основной сценарий).**
1. `tools/twin/twin.py run --fresh --blank --web 8790 --flasher`. В stdout ROM печатает `invalid header: 0xffffffff`, загружать нечего.
2. Встроенный браузер открывает `http://127.0.0.1:8790/flasher/index.html`, затем Install, «Двойник», «Install AnimatedPixelClock», галочку стирания, Install.
3. Порядок событий в stderr и `__usjLog`:
   - `reset{cause:21, download:true}`, затем `release`;
   - баннер `rst:0x15 (USB_UART_CHIP_RESET),boot:0x3 (DOWNLOAD(USB/UART0))`;
   - прогресс до 100 %;
   - `reset{download:false}`, затем `release`;
   - `rst:0x15 … (SPI_FAST_FLASH_BOOT)`, `entry 0x403c98b8`, `Improv: listening on Serial`, как в `bridge-write.log`.
4. «Installation complete». Не позже чем через 15 с ESP Web Tools находит Improv (F19) и показывает «AnimatedPixelClock 2.7.3», это ответ на REQUEST_INFO (опыт engine, Improv).
5. «Connect to Wi-Fi»: SSID и пароль виртуальной точки из `state/wifi.txt`. Диалог доходит до состояния «подключено» без ошибки.
6. Проверки:
   - (a) `check_flash.py` вне data-разделов не показывает различий;
   - (b) виртуальная точка видит ассоциацию (отчёт `[emu] wifi … AP …`), `http://127.0.0.1:8080/` отвечает;
   - (c) после перезапуска `twin.py run --web 8790` без `--fresh` двойник грузится с `flash.bin` и подключается к точке. Это проверка, что запись сохранилась.
   - «До» было «грузить нечего», «после» — версия 2.7.3. Это и доказывает, что работает новый образ.

**B. Обновление поверх работающей прошивки, без стирания.** Двойник с Wi-Fi, Install без стирания. Improv не предлагается, потому что учётные данные есть (F27). `check_flash.py` проходит. После загрузки двойник подключается к той же точке, значит NVS сохранилась.

**C. Сброс из консоли ESP Web Tools** («Logs & Console», затем «Reset Device», EWT `ewt-console.ts:149-158`). Ожидается `reset{download:false}` и `rst:0x15 … SPI_FAST_FLASH_BOOT`, приложение стартует.

**D (по желанию). Ручной режим загрузки.**
1. Скриптом: `boot down`, затем POWERON. Ожидается `rst:0x1 (POWERON),boot:0x… (DOWNLOAD…)`. Для этого бит GPIO46 в `--strap` должен быть 0, см. решение D1.
2. Прошивка со страницы.
3. После сброса ESP Web Tools чип **остаётся** в режиме загрузки (`rst:0x15 … DOWNLOAD`), как в F7.
4. Restart загружает прошивку.

**Негативные проверки.**
- N1: `git diff docs/` пуст, публичная страница не затронута.
- N2: во второй вкладке `open()` отклоняется с `NetworkError`, а первая вкладка продолжает работать.
- N3: пока порт занят, `panel.html` не показывает поток USB и игнорирует ввод. После закрытия диалога консоль работает снова.
- N4: закрыть вкладку, пока линии в (1,0). Двойник выходит из сброса и загружается.

## 8. Не проверено и риски

| Риск | Статус | Как закрыть |
|---|---|---|
| Stub esptool-js 0.6.0 (entry `0x40378A80`) в двойнике ещё не запускался. Опыт engine шёл со stub `0x40378ADC` | П (разные сборки) | W5, самотест |
| Темп. Откалиброванный темп `--cpi 2.45` замедляет всё, кроме Lua, в 2,45 раза (`calibration-2026-09-29.md:44`). Держит ли Mac реальное время во время прошивки, не измерено. Таймауты esptool-js идут по настенным часам | Н | Записать `speed` и `behind` в W5 и W7. Запасной вариант: `twin.py run --flasher --cpi 1` на время прошивки |
| Какое значение кремний возвращает при чтении `0x3FF5A00C/14/6607C` | Н | `esptool read-mem` на панели, делает владелец |
| Удержание в (1,0) и защёлка флага при входе в сброс | В | В браузере это проверит W7. На железе закрыть нельзя, в TRM этого нет |
| Что GPIO_STRAP на кремнии показывает после сброса 0x15 с флагом (очищены ли именно [3:2]); противоречие TRM §8.2 с esptool docs (F8) | Н | Строка загрузки ROM с панели после сброса через USJ |
| Реальный страп панели | Н | Одна строка `rst:…,boot:0x…` с панели по USB, только чтение |
| Подмена `navigator.serial` в обычном Chrome | Н (Chromium 152: П) | W8 |
| RTC WDT: двойник разоружает его при сбросе 0x15, кремний сохраняет | П (отличие) | Документировать. Stub всё равно выключает WDT на USJ |
| Команды ROM внутри `spi_flash_attach` и opiflash-драйвера не опубликованы | Н | Лог `spi1` при W5. Опыт engine с той же ROM прошёл |
| После Improv прошивка может перезагрузиться. Ссылка, которую она отдаёт (`nextUrl`), указывает в сеть двойника, с Mac туда не попасть. Портал доступен на `127.0.0.1:8080` | В | Наблюдение в W7. Сравнить с поведением платы 2026-09-21 |
| Байты хоста, отправленные во время сброса, теряются при `reboot()` | В | esptool-js делает `flushInput` и повторяет SYNC (F15) |
| Нужен интернет: страница грузит unpkg (ESP Web Tools и esptool-js) | П | По желанию: положить dist 10.4.0 локально |
| Баннер ROM приходит после `flushInput`, возможны повторы с «Invalid head of packet» | В | На это есть 5 SYNC на попытку. Число повторов записывается |

## 9. Решения для владельца

- **D1. Страп двойника.** Оставить `0x0f` (сейчас так) или перейти на реальное значение панели.
  - Для ESP Web Tools разницы нет: с флагом получается `0x03`, и ROM входит в режим загрузки.
  - Для сценария D с кнопкой BOOT нужен GPIO46 = 0. По TRM табл. 8.1-1 (с.534) у GPIO46 по умолчанию подтяжка вниз, а в `0x0f` этот бит равен 1, и тогда ROM печатает `UART0_BOOT` (опыт engine со страпом 07).
  - Рекомендация: снять одну строку загрузки с панели и поставить её значение. До этого не менять.
- **D2.** Оставить ли на странице двойника вариант «Плата по USB». По умолчанию да: это ничего не стоит и не прячет железо.
- **D3.** Не пускать публичную страницу к `/usj`. Рекомендация: не пускать, см. §5.
- **D4.** Держать ESP Web Tools 10.4.0 локально, чтобы работать без интернета, или грузить с unpkg.

## 10. Файлы-свидетельства

- Модель моста и логи engine:
  - `/private/tmp/claude-502/-Users-apple-LED-MATRIX-APOLLO/b713b961-29c5-417c-977c-81dddbb4b228/scratchpad/bridge/src/main.rs`
  - `…/scratchpad/bridge-write.log`, `bridge-id.log`, `bridge-erase.log` (строка `rst:0x15 (USB_UART_CHIP_RESET),boot:0x0 (DOWNLOAD(USB/UART0))`), `bridge-improv.log`
  - `…/scratchpad/flash-after-write.bin` (совпадает с Full.bin вне `0x9000–0xA5BD`), `flash-after-erase.bin` (всё `0xFF`)
- Исходники, по которым проверял:
  - `…/scratchpad/ejsrepo` (esptool-js v0.6.0), `…/scratchpad/ewtrepo` (ESP Web Tools 10.4.0)
  - `…/scratchpad/ejs060/package/bundle.js`
  - `…/scratchpad/s3trm.txt`
- Сверка stub:
  - `…/scratchpad/esptool481_s3.json` = `…/scratchpad/lfs130_s3.json` = `ejs060/.../stub_flasher_32s3.json`
  - отличается `~/.platformio/packages/tool-esptoolpy/esptool/targets/stub_flasher/1/esp32s3.json`
- Код для правки:
  - `/Users/apple/twin/esp32sim/esp-periph/src/usb_serial_jtag.rs`
  - `/Users/apple/twin/esp32sim/esp-periph/src/rtc_cntl.rs`
  - `/Users/apple/twin/esp32sim/esp-soc/src/soc.rs`
  - `/Users/apple/twin/esp32sim/esp-soc/src/web.rs`
  - `/Users/apple/twin/esp32sim/esp-soc/src/machine.rs`
  - `/Users/apple/twin/esp32sim/esp-soc/src/machine/web.rs`
  - `/Users/apple/twin/esp32sim/esp32s3/src/soc.rs`
  - `/Users/apple/twin/esp32sim/esp32s3/src/bus.rs`
  - `/Users/apple/twin/esp32sim/cli/src/lib.rs`
  - `/Users/apple/twin/esp32sim/web/` (новые `usj-serial.js`, `usj-selftest.html`)
  - `/Users/apple/AnimatedPixelClock-twin/tools/twin/twin.py` (новые `check_flash.py`, `usj_probe.py`)
  - `/Users/apple/AnimatedPixelClock-twin/tools/twin/engine/esp32sim-twin.patch`
- Страница-источник, не меняется:
  - `/Users/apple/AnimatedPixelClock-twin/docs/index.html`
  - `/Users/apple/AnimatedPixelClock-twin/docs/flasher.js`