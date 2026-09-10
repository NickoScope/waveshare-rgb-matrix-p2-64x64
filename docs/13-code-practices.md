# What AnimatedPixelClock does well, and what of it NickoScope32 actually needs

A read of [Keralots/AnimatedPixelClock](https://github.com/Keralots/AnimatedPixelClock)
(76 files, ~26 000 lines) made on 2026-09-10, after a day of working inside it.

The useful answer turned out not to be "copy these patterns". Checking each one
against the NickoScope32 V1b sources showed that most are **already there, and
in two cases done better**. What follows is therefore a comparison, and the
transferable list at the end is short on purpose.

---

## 1. The two network stacks, side by side

Read from the sources, not summarised from memory:
`AnimatedPixelClock/src/network/network.cpp` (860 lines) against
`NickoScope32-v1B-Main-S3-v33.58.0/src/netgate.{h,cpp}` (139 + 437) plus
`src/net/`.

| | AnimatedPixelClock | NickoScope32 NetGate (ADD-62) |
|---|---|---|
| Where network calls run | in `loop()`; only the probe is async | **one `netTask` on core 0**; `loop()` never blocks |
| Concurrency limit | none | **one in-flight per owner** — the STORM rule made structural |
| TLS heap | unbounded | **one TLS at a time firmware-wide → deterministic heap peak** |
| What triggers a health check | **silence** — 120 s with no traffic | **failure** — 2 consecutive connect/DNS errors, or an explicit report |
| What the probe is | ICMP to the gateway, `esp_ping`, asynchronous | DNS resolve, `WiFi.hostByName`, blocking — but inside `netTask`, so nothing stalls |
| Probe period | 60 s | 30 s |
| Association checked | `esp_wifi_sta_get_ap_info()` | not checked |
| Escalation | WiFi restart → cooling → `ESP.restart()` after 6 min | latch OFFLINE, rehabilitate by probe; a separate **loop watchdog** restarts on a stalled loop |
| Failure reason kept | `netLastRecoveryReason()` + count, in diagnostics | logged, and `who` passed to `note_external_fail()` |
| Sockets rebuilt on recovery | UDP fd, mDNS, SNTP — explicitly | not applicable: no long-lived fds in the gateway |

### Where NetGate is plainly stronger

The header states the contract, and it is a stronger one than the other project
has anywhere:

```c
// ВСЕ request/response HTTP(S)-обмены S3 идут через ОДНУ задачу netTask
// (core 0). Модули в loop() (core 1) кладут заявку в очередь и читают
// результат из своего mailbox'а. loop() НИКОГДА не блокируется сетью.
//
// ИНВАРИАНТЫ (§3.3):
//   1. Один in-flight на owner (submit → false, если уже занят) —
//      STORM RULE встроен архитектурно.
//   2. Один TLS на всю прошивку единовременно → heap peak детерминирован.
```

Invariant 2 deserves emphasis, because it is the problem this project's own
yacht radar has unsolved: a TLS session's heap cost is the largest unmeasured
allocation in that firmware, and it is unmeasured because nothing bounds how
many can exist at once. NetGate bounds it by construction.

Invariant 1 is the same story for concurrency. AnimatedPixelClock has no
equivalent because it makes few enough outbound requests not to need one.

And the exception list is reasoned rather than convenient:

```c
//   * ha_mqtt (ADD-68): свой сокет к ЛОКАЛЬНОМУ брокеру, отдельная задача
//     на ядре 0. netgate_note_external_fail() для него НЕ вызывается
//     намеренно: падение локального брокера иначе залатчило бы весь шлюз
//     в OFFLINE и убило Telegram с оракулом, syncTask NTP/погода, urri-сервер.
```

A local broker outage must not be evidence about the internet. That distinction
is absent from the other project entirely, which has only one notion of "up".

### Where AnimatedPixelClock's shape is different, and why it matters

**Health is failure-driven here, silence-driven there.** NetGate learns the link
is down when something asks and fails. AnimatedPixelClock learns it from 120 s
of quiet, before anyone asks.

This is not a hypothetical difference — the closed loop it creates has already
been paid for, and the fix is recorded in place:

```c
// v33.21.0 (инцидент 21:03): health питался ТОЛЬКО фейлами NetGate. При
// outage с полным AQ-кэшем и радаром вне fx31 заявок нет — OFFLINE не
// латчится, а tg/oracle (loop-сайд исключения §10.1) проверяют флаг, но не
// кормят его, и блокируют loop на DNS по 14 c КАЖДЫЙ полл. Замкнутый круг.
```

The repair — requiring the loop-side exceptions to report their own failures —
closes it for the paths that exist today. A silence-driven probe would close it
by construction instead, for paths that do not exist yet. That is the whole of
what the other design offers here, and it is a real difference in kind: one
approach needs every new caller to remember something, the other does not.

**The probe conflates three failures into one.** `WiFi.hostByName` returning 0
can mean no association, no DHCP, no DNS server, or no internet. Checking
`esp_wifi_sta_get_ap_info()` first separates "not on the network at all" from
"on it but nothing answers", and those want different responses: the first is
worth restarting the radio for, the second is not.

**Nothing restarts the radio on a link fault.** `ESP.restart()` exists on the S3
but is reached through the loop watchdog — a stalled loop — not through link
health. A zombie association (`WL_CONNECTED`, no traffic) therefore probes DNS
every 30 s indefinitely without ever resetting the stack that is stuck. The
other project restarts the radio after two failed probes and reboots only after
six further minutes; the ordering — radio before reboot — is the part worth
taking.

## 2. Compile-time guards on index arithmetic

Colour slots are indexed as `COL_TET_I + pieceIndex`, and the invariant that
allows it is held by the compiler:

```c
static_assert(COL_TET_L - COL_TET_I == 6,
              "Tetris piece color slots must stay contiguous in I,O,T,S,Z,J,L order");
```

with the matching note at the enum: *"MUST stay contiguous ... A static_assert
guards it."*

## 3. Migration inside the parser

`parseCycleConfig` accepts historical 12- and 13-entry sets, preserves their
order and durations, and appends newly introduced styles disabled:

```c
// Accept complete historical sets (12 or 13 styles), preserving their
// order and durations. Append newly introduced styles as disabled.
```

No schema version, no migration script — compatibility lives where the data is
read.

## 4. Diagnostics built by someone who debugged remotely

`/api/diagnostics` returns, among others:

```
freeHeap  minFreeHeap  largestHeapBlock  freeInternalHeap
resetReason  animationFailureCode  lastAnimationError
```

`largestHeapBlock` **separately from** `freeHeap` is the fragmentation signal:
plenty free, no contiguous block left.

## 5. Comments name the failure being prevented

```c
// Callers pass either an already-sanitized settings value or an intentional 0
// (forced off / 0%): sanitizing here would turn that 0 into 1, leaving the
// panel faintly lit instead of off.
```

Not what the code does — what breaks if you do the obvious thing instead.

---

# Checked against NickoScope32 V1b

Every item above was verified against `NickoScope32-v1B-H743-v46.78.0`,
`-Main-S3-v33.58.0` and the bridge sources before being called transferable.
Most were not.

## Already there, and stricter

**Link liveness.** The initial reading of this — that the bridge's
`link.link_up()` is a bare flag like `WiFi.status()` — was wrong.
`NickoBridge/deploy/app/link.py`:

```python
self.last_rx_ms = 0.0   # monotonic последнего ВАЛИДНОГО кадра

def link_up(self, timeout_s: float = 3.0) -> bool:
    return self.last_rx_ms > 0 and (time.monotonic() - self.last_rx_ms) < timeout_s
```

Time since the last **valid, parsed** frame — a stricter test than "bytes
arrived", and stricter than what AnimatedPixelClock applies to Wi-Fi.

**Recovery with a recorded reason** exists too — `_drop_port(why)` — and the
reopen path is better than theirs, because it resets the *parser* as well as
the buffers, with the incident that taught it written down:

```python
# Чистим ОБА буфера при открытии. После выдёргивания кабеля в приёмном
# буфере остаётся хвост оборванного кадра, и парсер начинает разбирать
# поток со сдвига: 2026-08-26 команда SHOW дошла до H743 как «ZSHOW»,
# link висел False при растущем tx, и лечилось только перезапуском
# сервиса. Переоткрытие порта обязано начинать с чистого листа.
```

Date, symptom, diagnosis, rule. That is better documentation than anything in
AnimatedPixelClock.

**`static_assert` is already used** — 7 in the H743 firmware, 8 on the S3 — and
on higher-value invariants than theirs, because they guard the **wire format**:

```
"nsp_vessel_record_t must be exactly 20 bytes"
"nsp_aircraft_record_t must be exactly 20 bytes"
"ring: power of two"
"ring: whole L/R pairs"
```

A struct that silently gains a padding byte desynchronises three codebases at
once. That is exactly where the compiler should be standing.

**`esp_reset_reason()` is captured and published**, with a comment recording
the subtlety that it describes the *start*, not the present moment.

**NetGate (ADD-62)** — a single serialised network gateway on core 0 through
which all HTTP must pass — has no counterpart in AnimatedPixelClock at all.

## The gaps that survived a code-level read

**1. Health is driven by failure, not by silence.** Section 1 above, with the
v33.21.0 incident that already demonstrated the failure mode. The repair works
for today's callers; a probe fired by quiet would work for tomorrow's too.

**2. Association is never checked.** `esp_wifi_sta_get_ap_info` appears in zero
files across 100 in the S3 firmware; `WiFi.status()` in eleven. A DNS probe
cannot tell "we are not associated" from "DNS is down", and only the first is
worth restarting the radio for.

**3. Nothing restarts the radio on a link fault.** Verified: `WiFi.disconnect`
appears once in `main.cpp`, guarded by a comment about not killing ESP-NOW, and
`ESP.restart()` is reached from the loop watchdog. A stuck association is
therefore probed forever and never reset.

**4. No heap fragmentation signal.** Searched across the same 100 files:

| Symbol | Files |
|---|---|
| `heap_caps_get_largest_free_block` | **0** |
| `heap_caps_get_minimum_free_size` | **0** |

Free heap alone cannot separate "tight" from "fragmented", and the second is
the documented STORM exhaustion class in the debug ladder. Two fields added to
whatever the device already publishes:

```c
heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)
heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)   // low-water mark since boot
```

The low-water mark matters as much as the instantaneous value: it survives the
dip that any poll will miss.

## Verdict: do one of the four

Weighed against the cost of touching a working multi-MCU system.

| Gap | Do it? | Why |
|---|---|---|
| Heap fragmentation metric | **Yes** | Two read-only calls into an existing publish. No behaviour change, no risk, and it maps to a documented incident class |
| Silence-driven probe | No, not now | The v33.21.0 incident is already patched. The residual case is a caller that does not exist yet |
| Association check | No | Only useful if the answer changes something, and the only thing it would change is contraindicated below |
| Restart the radio before rebooting | **No — actively wrong here** | See below |

### Why the radio restart must not be copied

AnimatedPixelClock restarts Wi-Fi after two failed probes, six minutes before
it will consider a reboot. On that device the radio does nothing else. On the
S3 it does, and the cost is already measured and written down:

```c
// Плановый sync (24h NTP / 15min weather) при ЖИВОМ WiFi не должен
// рвать радио: WiFi.disconnect(true) гасит RF целиком → ESP-NOW
// (M5Dial) мёртв до ~15 c. Полный цикл подключения — только когда
// линка реально нет.
```

Adopting the pattern would kill the M5Dial link for fifteen seconds every time
the internet hiccuped. The existing design already reached the opposite
conclusion deliberately, and the backstop it chose instead is sound: a loop
watchdog with a cause recorded into an RTC ring that survives the reboot, and
an audit note about not flushing LittleFS from core 0 during recovery because
`scene_lib` shares it and `open()` could deadlock the recovery itself.

That is a more careful piece of engineering than the thing it would be replaced
by.

### The one to do

```c
heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)
heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)
```

Added to whatever the device already publishes. Both are reads; neither changes
behaviour; the second is a low-water mark that survives the dip any poll would
miss. `esp_reset_reason()` and `set_reboot_cause()` already exist, so this is
the missing third of a diagnostic set rather than a new idea.

## What should not be copied

`NSP_FX_COUNT` consistency is currently held by a grep in the ship-check and by
the habit of noting it in commit comments. Turning it into a `static_assert`
would be in the spirit of the four that already exist — but only if the count
and the table are visible in one translation unit. **A `static_assert` that has
to be kept in sync by hand is worse than the grep**, because it looks like a
guarantee.

More broadly: their project structure should not be borrowed. It is one MCU and
one screen. NickoScope32 is five MCUs, a bridge, a protocol and an analogue
chain, and its structure is more complex because the problem is.

## What NickoScope32 has that they do not

Worth stating, since the comparison ran one way for most of this page:

- **The emulator harness** — a 1:1 twin of the render engine in a browser.
  AnimatedPixelClock edits effects by flashing hardware.
- **ADD architectural documents** with review gates. They have none.
- **Wire-format assertions**, as above.

The borrowing is therefore narrow: two diagnostic fields and one probing
pattern. That is the honest size of it.
