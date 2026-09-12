# What the Ulanzi pixel clocks got right

Studied 2026-09-12. The Ulanzi TC001 and TC002 are the best-known consumer
version of what we are building, and the TC001's community firmware — AWTRIX 3
— is the best-known open one. Neither runs on our hardware. Both are worth
reading for what they decided.

## The devices

| | Ulanzi TC002 | Ours |
|---|---|---|
| Matrix | 16 × 52 = **832** addressable LEDs | 128 × 64 = **8192** |
| Type | WS2812-class, one LED per pixel | HUB75, multiplexed 1/32 |
| Power | 3.7 V 3600 mAh battery, ~2 h at full brightness | mains, 8 A for two panels |
| Radio | Wi-Fi 2.4 GHz + BLE 5.2 | Wi-Fi only |
| Control | **rotary knob: turn to navigate, press to open, hold for settings**, plus volume and a BUSY button | one rotary encoder |
| Price | €129.99–249.99 | roughly a third of that in parts |

Source: the [TC002 product page](https://www.ulanzi.de/en/products/tc002-smart-pixel-uhr-i008).

Two things stand out. The first is scale: we have **ten times the pixels** for
less money, because a multiplexed HUB75 panel is a fundamentally cheaper way to
buy area than individually-addressed LEDs. The second is that a shipping
consumer product arrived at **the same control scheme we did** — one knob,
turn/press/hold. That is worth knowing: our gesture map is not a compromise, it
is what this class of device converges on.

Their mapping differs from ours in one place: TC002 uses *press to open* and
*hold for settings*, while we use *press to toggle the page's second axis* and
*hold to leave for the next page*. Theirs is a menu; ours is a carousel.

## Can we just run AWTRIX 3?

**No.** It is built for a 32 × 8 WS2812 matrix, the geometry is baked into the
layout, and it drives the LEDs through `FastLED_NeoMatrix`. HUB75 is not
supported and other resolutions are "not supported at this time". It also does
not support the TC002's own 16 × 52.

So this is an ideas read, not a port. What follows is what AWTRIX decided, and
what it would mean here.

## The idea worth taking: pages are dumb, the logic lives outside

AWTRIX's central decision is that **apps do not run their own logic**. They
render data that either comes from the firmware (time, date, temperature) or is
pushed in from outside. Everything clever happens in Home Assistant.

We already follow this for the flight board — Home Assistant does the API
calls, the merging and the time maths, and the panel renders a digested
payload. What AWTRIX does that we do not is make it **generic**:

```
[PREFIX]/custom/[appname]     ← create, update or replace a page, by name
[PREFIX]/notify               ← a temporary overlay
[PREFIX]/settings             ← change settings
```

A page is created by publishing to a name that did not exist before. No
firmware change, no new build, no flash cycle. Home Assistant can invent a page
for the laundry, the bin day, the electricity price, and the panel just shows
it.

Payload vocabulary, the parts worth copying:

| Field | What it does | Why it matters |
|---|---|---|
| `text` | string, or an array of fragments each with its own colour | one field covers both plain and rich text |
| `icon` | a file in `/ICONS/`, or base64 in the payload | no firmware rebuild to add an icon |
| `progress` | 0–100 bar | the single most-wanted widget, and free |
| `duration` | seconds in the carousel | per-page, set by the sender |
| **`lifetime`** | drop the page if no update arrives in N seconds | **a stale page removes itself** |
| `draw` | an array of low-level drawing instructions | a display list in JSON |

`lifetime` is the quiet good one. Our flight board shows an age, but a page
whose source has died stays on screen forever. Auto-expiry costs a timestamp
and a comparison.

There is also a placeholder mechanism: a page's text can reference an MQTT
topic, and the firmware subscribes to it, so the page updates itself without
the sender re-publishing the whole payload.

## Notifications, which we have nothing like

Notifications are separate from pages: a temporary overlay that interrupts
whatever is showing, with `hold` (stay until dismissed), `stack` (queue several)
and `wakeup` (turn the matrix on for this). For a panel on a wall this is the
obvious missing feature — a doorbell, an alarm, a washing machine finishing.

## `draw` versus Lua

AWTRIX's `draw` array is a declarative display list in JSON: safe, no
interpreter, bounded by construction, and limited to what the firmware
implements. We chose a Lua interpreter instead: far more expressive, but it
costs 91 KB, a sandbox, an instruction budget and a dedicated task with its own
C stack.

They are not competitors. `draw` is right for *show me this number, in this
colour, with a bar*. Lua is right for *draw me a world*. Having both would
suit this panel: JSON for data pages that Home Assistant invents, Lua for the
effects and games we write ourselves.

## What not to take

- **The battery.** A wall panel is on mains. Two hours at full brightness is a
  desk toy's constraint.
- **The closed half of their ecosystem.** TC002 ships with Ulanzi's own
  PixelGrid and Studio apps and an app marketplace. TC001's value came from the
  *open* firmware the community wrote instead.
- **8 × 8 icons.** Sized for a 32 × 8 display. At 128 × 64 we have room for
  something better, and reusing their gallery would mean adopting their pitch.

## What this suggests for the fork

In rough order of value for effort. All of it reuses what already exists here —
the MQTT client, the LittleFS store, the page dispatch.

1. **Generic MQTT pages.** One page type that renders a JSON payload, created
   and named by whoever publishes it. This is the single biggest idea on this
   page, and the smallest change: our MQTT client already runs on every page.
2. **`lifetime`.** A page whose data stopped arriving should remove itself.
3. **Notifications.** A temporary overlay with hold and duration.
4. **Per-page duration and a carousel.** Upstream already has a custom rotation
   for clock styles; extending it to data pages is the same mechanism.
5. **An icon store on LittleFS.** The custom-animation store is already there
   and is the pattern to copy.

Items 1, 3 and 4 would suit upstream as well as us — they are generic, and they
do not depend on anything about this house. Items in
[09](09-upstream-contributions.md) are the roadmap for offering that.
