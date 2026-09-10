# What AnimatedPixelClock does well, and what of it NickoScope32 actually needs

A read of [Keralots/AnimatedPixelClock](https://github.com/Keralots/AnimatedPixelClock)
(76 files, ~26 000 lines) made on 2026-09-10, after a day of working inside it.

The useful answer turned out not to be "copy these patterns". Checking each one
against the NickoScope32 V1b sources showed that most are **already there, and
in two cases done better**. What follows is therefore a comparison, and the
transferable list at the end is short on purpose.

---

## 1. The network stack — their strongest work

`src/network/network.cpp`, 860 lines. The premise is stated in the header:

```c
// WiFi.status() stays WL_CONNECTED even when the stack moves no traffic at all,
// so the association record and a gateway ping decide instead.
```

Three levels of evidence rather than one:

| Level | How |
|---|---|
| Stack flag | `WiFi.status()` — **not trusted** |
| Association | `esp_wifi_sta_get_ap_info()` |
| Actual traffic | ICMP to the gateway |

**Traffic is counted, not assumed.** `netMarkInbound()` from the UDP handler,
`netMarkOutboundOk()` on a successful send, `netMarkHttp()` on a served
request. The probe fires **only after 120 s of silence**, so a working link
costs nothing to monitor.

**Escalation has hysteresis and a ceiling:**

```
120 s silent          -> async gateway ping (3 packets, 1 s timeout)
2 consecutive fails   -> restart WiFi, NOT a reboot
60 s cooling          -> do not hammer recovery
6 min still bad       -> ESP.restart(), last resort
```

Note the order: **a reboot is the fourth answer, not the first.** And plain
Wi-Fi loss triggers none of it — `NOTE: Auto-reboot removed - device continues
as clock-only`. The device degrades rather than dies.

**The probe is asynchronous.** `esp_ping` with callbacks, `volatile` flags, the
result collected on a later tick. `loop()` never blocks — which is worth noting
against the fact that today's audit found two blocking network calls in code
written for this project, either of which would have tripped the watchdog.

**Recovery rebuilds everything holding a descriptor:**

```c
udp.stop(); udp.begin(UDP_PORT);    // old fd is stale
initMDNS();                          // re-register
ntpSynced = false; applyTimezone();  // restart SNTP
```

with a neat trick: `netRecover()` sets `wifiDisconnectTime = now` so the
*reconnect* branch performs all of it. One copy of the rebuild logic, not two.

**The failure reason survives.** `netLastRecoveryReason()` and
`netRecoveryCount()` reach the diagnostics endpoint, so afterwards you read
"gateway unreachable, 4 recoveries" rather than "the link was flaky".

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

## The two gaps that are real

**1. No heap fragmentation signal.** Searched across the S3 firmware:

| Symbol | Files |
|---|---|
| `heap_caps_get_largest_free_block` | **0** |
| `minimum_free` / `heap_caps_get_minimum_free_size` | 0 / 1 |

Free heap alone cannot distinguish "memory is tight" from "memory is
fragmented", and the second is the documented STORM heap-exhaustion class in
the debug ladder. Two extra fields in whatever the device already publishes:

```c
heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)
heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)   // the low-water mark since boot
```

The low-water mark matters as much as the current value: it survives the dip
that a poll will always miss.

**2. Wi-Fi liveness on the S3 is still the flag.** `WiFi.status()` appears in
11 files; `esp_ping` and `esp_wifi_sta_get_ap_info` in none. The NSP link is
measured properly and the Wi-Fi link is not — the same zombie-connection the
bridge already defends against, undefended one layer up.

The idle-then-probe shape transfers directly, and the "probe only after
silence" rule means it costs nothing while traffic flows.

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
