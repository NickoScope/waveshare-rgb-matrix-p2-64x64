# 23. The MTR-1 presence sensor, in depth

Research done 2026-09-16 at the owner's request, because this sensor is meant to carry a lot of the smart home from here on. Four strands were run in parallel and merged here: the manufacturer's own documents, the community and the software landscape, **our own measurements from his living room**, and what the sensor costs his Home Assistant install.

**How to read it.** Every figure below is labelled by where it comes from. `[DS]` means a datasheet or protocol manual, `[Apollo]` the manufacturer's repository or wiki, `[ESPHome]` the component's source or docs, `[community]` a forum post or a project README, `[measured]` our own data from this house. Anything that could not be established is written as **not verified** rather than filled in. Where a figure rests on fewer than about five independent examples it is marked a **reference figure**: it may be printed, but it must not decide anything on its own.

The device, its entities and the panel integration are in [16](16-presence-radar.md). This document is the background behind those decisions.

---

## 1. What the device is

Apollo Automation **MTR-1**: a Hi-Link **HLK-LD2450** 24 GHz radar, an **LTR-390UV** light and UV sensor, a **DPS310** pressure sensor, and a **socket for an optional SCD40 CO2 module**, on an ESP32-C3 running ESPHome. USB-C from an ordinary 5 V adapter, 49 × 32 × 15 mm `[Apollo, datasheet]`.

**The owner has the base model.** The CO2 entity reads `unknown` and always has: over the entity's whole life there is not a single numeric value, only `unknown` → `unavailable` → `unknown` `[measured]`. The proof that this is a fitment question and not a fault: the DPS310 on the same I²C bus works, so the bus is alive `[measured]`; the SCD40 warm-up in periodic mode is five seconds, not hours `[DS, Sensirion SCD4x v1.7]`; and Apollo sells the module separately, to be pushed onto a mezzanine connector `[Apollo wiki]`. Apollo's firmware declares the sensor unconditionally, so on a board without the module ESPHome marks the component failed and the entity stays `unknown` forever `[ESPHome, scd4x.cpp]`.

**There is no PoE version of this device.** PoE is a different Apollo product `[Apollo]`.

---

## 2. The radar, from the manufacturer's documents

| Property | Value | Source |
|---|---|---|
| Band | 24–24.25 GHz FMCW, 250 MHz sweep | `[DS, HLK-LD2450 manual V1.00]` |
| Range | 6 m | `[DS]` |
| Field | ±60° azimuth, **±35° pitch** | `[DS]` |
| Targets | 3, with coordinates | `[DS]` |
| Module output rate | **10 Hz** | `[DS]` |
| Supply | 5 V, needs >200 mA available, **120 mA average** | `[DS]` |
| UART | 256000 baud, 8N1 | `[Apollo, Core.yaml]` |
| Radar firmware | 2.04.23101915 is the latest Hi-Link names, and it is what this unit runs | `[DS user guide]`, `[measured]` |

**The frame.** `AA FF 03 00` … `55 CC`, little-endian, three fixed 8-byte target slots, ten frames a second. Per target: X int16 mm, Y int16 mm, speed int16, distance resolution uint16 mm `[DS, serial protocol V1.03]`. The sign encoding is unusual and worth knowing if anyone ever parses the wire directly: **the high bit set means positive**, and a negative value is `0 − value` `[DS §6]`. Y is always positive.

**Zones live in the module.** Three rectangles, each two diagonal corners as signed millimetres; type 0 disabled, 1 detect only inside, 2 ignore inside. They survive a power cut, and they take effect immediately `[DS §2.2.12–13]`. **Detection and filtering cannot both be active** — the type is one setting for all three zones `[DS user guide §3.2]`.

**What the manufacturer warns about** `[DS §7.1]`: the enclosure must pass 24 GHz and contain no metal; avoid things that move continuously and are not people (a fan, a curtain in a draught, a large plant in airflow); large reflective surfaces interfere; mount the module rigidly, because "the shaking of the radar itself will affect the detection effect"; **the back lobe detects movement behind the radar**, so a metal backplate is recommended; and never aim two 24 GHz radars at each other. Radome material matters: the manual gives permittivity and half-wavelength for ABS, PC, PMMA, PVC, PE and quartz, and says cover thickness should be a multiple of the half-wavelength in that medium, or else thinner than an eighth of it.

**Mounting height comes from Hi-Link, not Apollo.** Hi-Link says 1.5–2 m on a wall `[DS §7]`. Apollo publishes no height or tilt figure anywhere `[Apollo wiki]`. With ±35° of pitch, the beam covers ±1.40 m at 2 m, ±2.10 m at 3 m and ±2.80 m at 4 m (arithmetic from the spec), so at 1.5 m height the floor only enters the beam from about 2.1 m out.

### Contradictions found in the documents

These matter more than any single number, because each one is a place where following the wrong source produces a wrong system.

1. **Speed units: cm/s or mm/s.** Both Hi-Link documents call the speed field centimetres per second, with a worked example `[DS serial protocol Table 10, user guide §6]`. ESPHome publishes the same field as millimetres per second `[ESPHome, ld2450/sensor.py]`. Our panel divides by ten assuming millimetres. **If Hi-Link is right, the panel is wrong by a factor of ten.** Not resolvable from documents — see the bench test in §7.
2. **Stillness.** Apollo says the LD2450 is "less effective at detecting minimal motion or stillness" and that its sensitivity cannot be tuned, recommending exclusion zones instead `[Apollo wiki]`. Hi-Link's own manual claims the module senses micro-movement `[DS §2.2]`. Our data leans Apollo's way: a seated person was held for 415 s, but the counters called that person "still" about half the time `[measured]`.
3. **Zone limits, three published ranges.** The ESPHome source and the owner's own entities say **X ±4860 mm, Y 0–7560 mm**; Apollo's wiki prints ±7000/0–7000 in one place and ±3000/0–6000 in another `[ESPHome number/__init__.py]`, `[Apollo wiki]`, `[measured]`. The source and the live entities win; the wiki is stale.
4. **"Sees through drywall" is about a different sensor.** That line on Apollo's site describes their MSR-2 with an LD2410B, not this radar `[Apollo wiki]`. Apollo does separately say the LD2450 sees through "light walls", which is why a Filter zone over a shared wall is worth having.

---

## 3. What our own room shows

From one recorded session, 802 one-second frames over 820 s, essentially one person `[measured]`. This is the only strand that describes *this house*, and it disagrees with the folklore in useful places.

| What | Measured | Notes |
|---|---|---|
| Update interval per coordinate | median **1.07 s**, p95 1.24 s | the ESPHome throttle, not the module's 10 Hz |
| **X and Y arrival skew** | median **0.29 s**, p95 0.53 s; only 23 % within 100 ms | **the important one, see below** |
| Cadence while still vs moving | 0.51 s vs 0.43 s | the sensor does **not** go quiet when nobody moves |
| Seconds with no target at all | 28 of 821 (3.4 %), longest run 3 s | longest total silence 4.6 s |
| Slot 1 continuous survival | median 29 s, max 558 s, four dropouts of 2–3 s | reference figure, n=5 |
| Slot reassignment | **never observed**; slot 2 used for 5 s, slot 3 never | one person, so this proves little |
| `people` changes | every 82 s | value 1 lasted a median of 39 s |
| `moving`/`still` changes | **every 2.5 s** | 93 % of it is the speed field touching zero |
| Range | median 0.43 m, **max 1.95 m** | 32 % of the 6 m the radar claims |
| Angle | median 21.6°, p95 45°, max 61.7° | slightly over the ±60° spec |
| \|speed\| | 0 for 57.9 % of the time, exactly 80 for 36.2 %, above 120 only 5.9 % | quantised, see below |
| Position jump in 1 s | median 38 mm, p95 521 mm, max 1421 mm | no impossible jumps |
| Jump vs reported speed | correlation **0.09** | the speed field does not describe the movement |

**The X/Y skew is a real defect, and it is ours.** The radar reports a position, but Home Assistant carries X and Y as two separate entities that arrive a third of a second apart. Anything that reads "the latest X and the latest Y" is mixing two different moments, up to half a second apart, and that is the largest single cause of a dot that stair-steps across a screen. The fix belongs in the publisher: pair the two by their own timestamps, or hold a position until both have refreshed. **Open, not yet fixed.**

**The speed field is nearly useless as a number.** It is quantised: zero, or 80, and almost nothing between. Every threshold from 81 to 160 in those units behaves identically, so tuning the panel's 12 cm/s test would change nothing. Worse, the sign does not tell you approach from retreat: sign agreed with the change in range in 0.49 of 213 intervals, a coin flip. Taking the magnitude and ignoring the sign is the honest treatment, which is what the panel does. A reviewer independently called distance and speed on this module "very jumpy" `[community]`.

**A debounce can be chosen from the data.** Absorbing the moving/still flapping: 2 s removes 64 % of the flips, **3 s removes 82 %**, 4 s removes 92 %. Three seconds sits just above the 90th percentile of a "moving" run, so it kills blips while costing about a third of a session's frames in latency.

**No ghost target was found.** The one suspicious stationary cluster, held for 415 s, turned out to be a seated person: 98 % of the positions inside it were distinct, scattered by about 54 mm.

**What this data cannot support:** anything about several people at once, slot reassignment, stillness beyond about seven minutes, or ranges past 2 m. Several counts above are under five examples and are marked as reference figures.

---

## 3a. The jumping dots, measured 2026-09-16 19:15

The owner reported dots hopping from corner to corner on screen. Twelve minutes of live history for both target slots, 600 rows each, say what is happening, and it is not what I first assumed.

| | Slot 1 | Slot 2 |
|---|---|---|
| Points drawn | 596 | 586 |
| Range, median | 0.44 m | **2.66 m** |
| Points past 2 m | 2 (0 %) | **518 (88 %)** |
| Angle, median | +19° | +3°, spread −45°…+65° |
| Jumps over 1 m between consecutive points | 6 | **19** |
| Absences over 3 s | 1, longest 5 s | **20, longest 513 s** |

**Slot 1 is a person:** close in, a steady track, a median step of 40 mm, one short dropout.

**Slot 2 is not.** It sits almost entirely beyond 2 m, wanders the whole width of the fan, disappears and returns twenty times, and jumps more than a metre nineteen times. It is the module inventing and dropping a weak second target in the far half of its field — the failure the community calls a ghost, and the reason PondEyes splits a track when a target "teleports".

**The X/Y skew is not the cause of these jumps.** Of the 25 jumps over a metre across both slots, **none** happened within 0.35 s of the previous point, which is where a mispaired X and Y would show. The skew is real and worth fixing, but it is a second-order effect; the corner-to-corner hopping is the second slot.

**What follows for the panel:**
1. **Do not draw a slot until it has proved itself** — a minimum lifetime, or a couple of consecutive updates, before a dot appears.
2. **Drop a slot that teleports**, unless it stays at the new place.
3. **A Filter zone over the far region** where these ghosts live is the manufacturer's own remedy, and it costs nothing on the panel side.

## 3b. The ghost is the window, and how big a filter would have to be

The owner was asked what sits 2.5-3 m straight ahead of the sensor. **A window.** That matches the manufacturer's two warnings at once: large strongly reflective surfaces interfere, and a curtain moving in a draught is exactly the kind of continuously moving non-human object to avoid `[DS §7.1]`. Apollo adds that the radar sees through light walls, so people or cars beyond the glass are also candidates.

Sizing a Filter zone against the same twelve minutes of live data:

| Filter over everything beyond | Ghost points removed | Person points lost |
|---|---|---|
| y ≥ 2.2 m | 364 of 586 (62 %) | **0 of 596 (0 %)** |
| y ≥ 2.5 m | 133 (23 %) | 0 |
| y ≥ 2.8 m | 21 (4 %) | 0 |

The ghost cloud beyond 2.2 m spans x from −1.86 m to +1.92 m, median +0.61 m, and reaches 3.75 m out. The person never went past 2.2 m in this window, and never past 1.95 m in the earlier recorded session, so a filter at 2.2 m costs nothing measurable today — **but it is tight**: a guest standing by the window would be erased. At 2.5 m the safety margin doubles and it still removes a quarter of the ghosts.

**A filter alone will not fix the hopping.** The other 38 % of ghost points sit closer than 2.2 m, inside the space a person uses, where no rectangle can separate them. Those need the panel-side rules: confirm a slot before drawing it, and drop one that teleports.

**The simplest lever of all** is the module's own multi-target tracking switch. Turned off, the radar reports one target and invents no second one. The cost is that two people can no longer be counted or drawn. For a room where presence and one person's position are what matter, that removes the whole class of problem in one reversible setting.

## 3c. What was changed at 19:23-19:27, and what it did

- **Multi-target tracking: off** (`switch.apollo_mtr_1_53bc60_multi_target_tracking`), on the owner's word. The module now reports one target.
- **The panel gained `GET /api/presence/mirror?on=0|1`** (`4c31d63`), because the portal's save posts the whole form and reads an absent checkbox as false, so a partial post would clear other settings. With no argument it reports the current value.
- **Mirror X: on.** The owner watched the screen and said the picture was mirrored against the room, which reverses the "совпало" of 18:36. Set through the new route and confirmed in `/api/info`.

**Immediately measured, 19:23:30 to 19:25:06** (the window since the switch, one person in the room):

| | Before, 19:12-19:20 | After |
|---|---|---|
| Second target | present in 134 of 143 rows | **one `unknown` row; gone** |
| Slot 1 clusters | two: 1.09 m and 2.77 m, crossed twice a minute | one cloud, 1.75-3.06 m out |

So the invented target is gone with the switch, as expected. What remains is slot 1 sitting at the **far** distance, around 2.4-2.9 m at about +28°, wandering a few hundred millimetres between samples. Whether that is the people on the sofa or the window reflection now wearing slot 1 cannot be told from the data: it needs the owner to say where he is sitting relative to the sensor. If it is the window, the Filter zone from §3b is the next step; if it is the sofa, the radar is simply tracking them and only the wander remains to be smoothed.

## 4. The software landscape

**ESPHome has an official `ld2450` platform**, merged February 2025 and shipped in 2025.3.0 `[ESPHome]`. It gives per target x, y, speed, angle, distance, resolution and a direction text sensor; globally the presence, moving and still binary sensors, the three counts, version and MAC, switches for Bluetooth and multi-target, selects for baud rate and zone type, and a presence timeout. It requires radar firmware 2.02 or newer.

**The ~1 Hz you see is ESPHome's, not Home Assistant's.** Every sensor carries default filters of `timeout: 1s` and `throttle_with_priority: 1000ms`; binary sensors carry `settle: 1000ms`. Setting `filters: []` removes them `[ESPHome]`. Apollo's own firmware applies no extra filters on top `[Apollo, Core.yaml]`.

**External components worth reading**, by what they teach rather than by stars `[community]`:

| Project | What is worth stealing |
|---|---|
| TillFleisch/ESPHome-HLK-LD2450 | convex **polygon** zones, and hysteresis everywhere: a 25 cm margin, a 5 s target timeout, a tilt-angle margin |
| uncle-yura/esphome-ld2450 | coordinate **rotation** for a sensor mounted in a corner; unlimited software zones, though they do not reach Home Assistant |
| 53l3cu5/ESP32_LD2450 (archived) | six detection plus three exclusion zones and a browser zone editor |
| EverythingSmartHome/everything-presence-lite, `ld2450-base.yaml` | **the most instructive single file**: raw UART parsing, a user-facing "update speed" select from 0.1 to 0.5 s, per-zone `delayed_off`, polygon exclusion zones, an "assume present" timeout and a stale-target reset |
| davidkarnowski/PondEyes | names the failure mode exactly: it splits a track when a target "teleports" because the module reused a slot for a different person |

On the Home Assistant side, **Radar Map Manager** is the strongest general zone editor for this radar: floor-plan polygons typed detect, exclude, entrance or stationary-hold, with anti-ghosting clustering `[community]`. The Everything Presence zone configurator is slicker but documents only its own hardware, and a request to support a generic LD2450 sits unanswered. For a live plot, what people actually use is a Plotly card configuration rather than a dedicated card; the one card named "radar" in the ecosystem plots people and device trackers, not radar coordinates.

---

## 5. Practice that works, and what it rests on

Marked plainly, because most of it is experience rather than measurement, and almost none of it has five independent samples behind it `[community]`.

- **Wall-mount, roughly chest height, aimed across the room.** A user who tested both reported the ceiling giving only about 2 m of useful range against 4–5 m from a wall; another put the honest tracking area at about 5 m inside a 90° cone. Ceiling mounting is for fall detection and narrow zones.
- **Use zones, and use them for their jobs.** Detection on the seating or desk, Filter over the doorway, over a fan, over a window with curtains, and over a shared wall. Three rectangles, no overlap, first corner smaller than the second `[Apollo]`.
- **Automate on zone counts, not on coordinates and never on speed.** The shape people settle on is a trigger on a zone's count with `for: 2s`, and switching off via `delayed_off` rather than by tightening the radar.
- **Let something else turn things on; let the radar hold them on.** The hybrid blueprint author triggers from PIR only and clears on radar-off plus a minute, because the radar "even gets stuck on ON state for days".
- **Assume presence will stick one day and build a watchdog.** There are open reports of values sticking, and one where the presence timeout was ignored in favour of a hardcoded 36 s.
- **Power and EMI are real.** Forum practice asks for under 100 mV of ripple, and one interference case was cured by moving a USB cable away from an LED strip.
- **Pets:** no LD2450 false-positive report was found. The effect people describe is the opposite — aimed at belt height and upward, the radar sees standing and sitting people, and a cat went unnoticed.
- **Fans, curtains, washing machines:** every specific report found was about a *different* sensor. Hi-Link's own warning about continuously moving objects stands `[DS]`, but there is **no LD2450-specific evidence** either way.

---

## 6. What it costs Home Assistant, measured on this install

| Measured | |
|---|---|
| Recorder settings | none configured, so the defaults: 10 days kept |
| Database | 1,101 MB; the states table and its indexes are 85 % of it, at 179 B a row |
| Whole install | 308,131 rows a day |
| **This sensor** | **61,671 rows a day, 20 % of everything**, while present only 2.7 h of the day |
| Of that | 87 % is the three targets' x, y, angle, speed, distance and resolution |
| Growth | at six hours of presence a day, about 24 MB a day, so roughly 240 MB sitting in the ten-day window |

**Excluding an entity from the recorder also denies it long-term statistics** — verified in the source, not the docs. It costs nothing here: of the sensor's entities only five carry a state class at all, and none of the target coordinates do, so they would never have had statistics `[ESPHome]`, `[measured]`.

The policy that follows is in [16](16-presence-radar.md) as pasteable YAML, awaiting the owner. In short: exclude the target coordinates and the moving and still counts; keep presence, the target count, light, air, the diagnostics and the nine zone counters, which become the main signal once zones exist.

**And the finding that was not the radar:** four `nickoscope32` entities — uptime, the two packet counters and a bridge uptime — write **28,650 rows a day each**, more than any entity of this sensor. The same policy is worth having for them. Alongside that, one automation logged "already running" six hundred times and writes 4,728 state rows a day, which looks like the wrong run mode.

---

## 7. What to do with this sensor here

**Settled, and why:**
- **Panel scale 4 m.** Nothing in the recorded session went past 1.95 m, so 6 m wastes two thirds of the fan; 2 m would look better but clips a person already standing at the edge `[measured]`.
- **The 12 cm/s "moving" test stays as it is**, because every threshold in that gap behaves the same on a quantised field `[measured]`.
- **Magnitude of speed, sign ignored** `[measured]`.
- **The radar's Bluetooth is off** since 2026-09-16 16:55. It is the radar module's own radio with its own antenna, and the reason to keep it off is access, not power: with it on, anyone in range can reconfigure the radar from the phone app `[DS]`, `[measured]`.

**Open, in the order worth doing:**
1. **Pair X and Y by timestamp in the publisher.** The largest measurable improvement available, and it is our code.
2. **Define the three zones**, by standing in each corner and reading the coordinates back rather than guessing: stand, wait ten seconds, note the pair, and add 200–300 mm of margin because the measured target resolution is about 360 mm. Detection on the seating, Filter over the doorway and over the window.
3. **Apply the recorder policy**, with the owner's approval.
4. **Debounce the moving/still counters by 3 s** wherever they drive anything.
5. **Bench-test the speed units:** walk a measured distance at a steady pace and compare the reported speed against distance over time. This settles the cm/s versus mm/s contradiction, and it takes a minute.

**Bench tests still open from earlier work:** whether the HUB75 panel disturbs the radar, and whether the module holds a completely motionless person.

---

## 8. Sources

Manufacturer and datasheets: Apollo MTR-1 datasheet and wiki; Apollo's `Core.yaml` and `MTR-1.yaml` at the firmware version this unit runs; Hi-Link HLK-LD2450 instruction manual V1.00 (2023-05-10), serial communication protocol V1.03 (2023-10-17) and user guide; Sensirion SCD4x datasheet v1.7 (April 2025); Lite-On LTR-390UV-01 DS V1.1.

Software: ESPHome `ld2450` component documentation and source, the pull request that added it and the 2025.3.0 and 2025.8.0 release notes; Apollo's issue tracker, including the reports of coordinates going `unknown` on ESPHome 2026.3.x and of zone settings lost on reboot.

Community: the projects named in §4, the Home Assistant community threads on ceiling versus wall mounting and on hybrid PIR plus mmWave automation, and an independent review of the MTR-1. Reddit was not reachable from the research tooling, so nothing here rests on it.

Ours: the recorded session in `~/panel-backups/` (private, never in a repository), and the recorder database read on 2026-09-16.
