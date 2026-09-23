# Ideas for later

Things the owner wants some day, written down so they are not lost. Not
planned, not promised; each says what it would take, so picking one up starts
from the notes rather than from zero.

## Brightness that follows the sun and the room's light

**Priority: low, not urgent (owner, 2026-09-23).**

The panel dims and brightens with the sun where it hangs, instead of fixed
"dim from 22:00 to 7:00" times that have to be moved between summer and
winter. And, where a light sensor is available, with the actual light in the
room.

What already exists, so this is mostly assembly:
- **The sun.** The world clock computes the sun's position for any place
  (declination by the cosine approximation, the subsolar point) and draws day,
  night and civil twilight from it: `src/worldclock/worldclock.cpp`.
- **Where the panel is.** The world clock's home city, or the location found by
  IP at boot (the serial log shows "World clock: IP location code 200, ...").
- **Setting the brightness.** `setDisplayBrightnessPercent()`, which since 2.5.4
  rounds both ways and does not drift; the scheduled dimming and the night
  power-off window (`settings.enableScheduledDimming`, `dimStart*`, `dimEnd*`,
  `dimBrightness`, `enableScheduledOff`).
- **The room's light, from Home Assistant** (owner: "датчик освещенности можно
  брать с ХА"). The Apollo MTR-1 carries an LTR-390 whose lux reading is already
  in Home Assistant; the panel already takes the MTR-1's presence targets over
  MQTT for the room radar, and the light level would come the same way.
  The controller board itself has no light sensor: the vendor schematic's GPIO
  table has an "LDR" column, but no pin is assigned to it.

A shape to start from:
- Portal: "Brightness follows the sun" with a day level and a night level;
  optionally "... or the room's light" with the Home Assistant entity.
- Sun mode: full day level above the horizon, night level below civil
  twilight's end (sun at -6 degrees, the standard definition), a smooth ramp in
  between; an offset in minutes for "darker earlier".
- Light mode: brightness from lux through a curve with hysteresis, so a cloud
  does not flicker the panel; the sun mode as the fallback when the reading is
  stale.
- The night power-off window stays as it is.
- Host test: sunrise and sunset from the model against published tables for a
  few cities and dates, the way the time zones are checked against zoneinfo.

Rough size: one session with tests and the gate audit, plus the Home Assistant
side for the light mode.

## The over-the-air update: answers in Russian, and the name question

**From the first live run, 2026-09-23 (owner).**

- Accept Russian answers as well: "да" for yes, "обновить" for update. The
  owner answered "да" to question 1 and the tool, by design, would have
  cancelled; the agent had to ask again rather than translate the answer
  itself.
- At the name step, ask whether to keep the panel's name or change it
  ("изменить или оставить прежним?"), instead of only asking it to be typed.
