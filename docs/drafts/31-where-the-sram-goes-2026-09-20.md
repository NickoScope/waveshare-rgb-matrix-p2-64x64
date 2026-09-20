# Where the internal SRAM actually goes: the cable measurement

2026-09-20, evening, over USB. Run because the council rejected the model this fix had been
built on, and because two of my own "fixes" that day had been built on figures nobody measured.

**Both of my models were wrong. The measurement found the real one.**

## What was measured, and what it says

| Test | Result | Verdict |
|---|---|---|
| 12 TCP connections opened and **nothing sent** | free 35,228 → 33,356 B: **1,872 B for twelve**, ~156 B each | Idle connections are **not** the cost. My "12 × 5,760 B" model was wrong, exactly as the council said: `TCP_SND_BUF` bounds the send queue, it is not allocated per connection in advance. |
| 12 **concurrent** requests for the 21,738 B page | all twelve served in 1.1 s; free 31,892 → 31,612 B | Concurrency is **not** the cost either. The portal on its own is fine. |
| One full page load | about 1 KB | Not the cost. |
| Five minutes idle on the clock, nothing touching it | **loop blocked 0 ms of 300,000** | Nothing is a constant drag. In particular `mqtt took 1001 ms` does **not** appear - it is a symptom of a starved network, not a cause. I had claimed the opposite an hour earlier, on the strength of it appearing in every busy log. |
| Five minutes with the **rail board on screen**, no traffic at all | loop blocked 609 ms of 300,000 (0.2 %), but free internal fell to **13,644 B** and the largest block to **7,668 B**, and the panel reconnected its own Wi-Fi once | **This is the cost.** |

## The chain, finally

The rail board fetches its timetable over HTTPS **every 30 seconds while its page is shown**.
Each fetch costs 12-16 KB of internal RAM - a 12 KB FreeRTOS task stack, plus the TLS client
context and socket. Between fetches the panel sits at about 13 KB free and 7.6 KB contiguous.

From there **any** web traffic tips it over: the Wi-Fi task cannot get its 1,626 B DMA receive
buffers, packets are dropped, and the panel is unreachable although the link is up and the
firmware is running. That is the whole of what the owner has been seeing.

## The one lever that would have been big, and is closed

The council suggested the fetch task's 12 KB stack could live in PSRAM. Checked against the
FreeRTOS source in the SDK rather than assumed:

```c
bool xPortcheckValidStackMem(const void *ptr) {
#ifdef CONFIG_FREERTOS_TASK_CREATE_ALLOW_EXT_MEM
    return esp_ptr_byte_accessible(ptr);
#else
    return esp_ptr_internal(ptr) && esp_ptr_byte_accessible(ptr);
#endif
}
```

`CONFIG_FREERTOS_TASK_CREATE_ALLOW_EXT_MEM` (formerly
`CONFIG_SPIRAM_ALLOW_STACK_EXTERNAL_MEMORY`) is **not set** in this pre-built SDK. A task stack
must be internal. The only way to change that is to rebuild the SDK - which is the ESP-IDF port
the council unanimously advised against. So 12 KB per fetch is a fixed cost here.

## What is left, in order of cost to us

1. **Fetch less often.** 30 s was a choice, not a requirement; trains do not change that fast.
   Two minutes cuts the exposure fourfold and costs nothing but freshness. One constant.
2. **Do not fetch while the web server has a client**, and do not serve the portal's large
   responses while a fetch is on the wire. Half of this is already written on
   `fix/portal-heap`.
3. **Trim the fetch task's stack** - but from a distribution of high-water readings, not from
   the single sample that led me astray this afternoon.
4. **Move the choosing out of the portal** (the owner's idea): if the station and the airport
   are picked on the panel itself, the portal need not be open at all in daily use, and the
   collision has nothing to collide with.

## What was already fixed today and is on the panel

The link watchdog no longer restarts Wi-Fi when the gateway probe could not be **sent** - a
local buffer failure said nothing about the gateway, and reading it as "gateway unreachable"
turned a moment of memory pressure into minutes off the network. Verified: the log now says
"Link probe could not be sent (no buffer): not counted against the gateway" and the link stays up.
