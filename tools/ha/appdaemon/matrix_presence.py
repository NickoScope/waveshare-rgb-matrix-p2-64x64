"""Presence radar for the LED panel: the Apollo MTR-1's LD2450 targets from Home Assistant to MQTT.

The contract agreed with the panel on 2026-09-16 (the owner's decision at 17:14):

  <base>/presence/targets   QoS 0, NOT retained. About once a second while anyone is
                            present, once every 5 s while the room is empty.
      {"t":[[x_mm,y_mm,v_mmps] or null, x3],"p":1,"m":1,"s":0,"lux":41,"ts":1758035712}
  <base>/presence           QoS 0, retained. On change, and at least every 30 s.
      {"p":1,"m":1,"s":0,"lux":41,"online":true,"ts":1758035712}

Values go out exactly as Home Assistant holds them, rounded to whole millimetres: x signed
sideways, y forward, v the LD2450's signed speed. A target that is unknown or reads 0/0 is
null. abs(), cm/s, the mirror and the scale all belong to the panel, where the owner can
change them without touching Home Assistant. `p`, `m`, `s` are the presence, moving and
still counts; `lux` is an integer or null; `ts` is unix seconds.

Targets are not retained on purpose: after a panel reboot a retained frame would show
people who have left as if they were still there.

While someone is present a targets frame goes out every tick even when nothing moved: the
panel smooths and ages what it gets, and a gap must mean a dead link, not a still person.
Only an empty room is thinned out.

Why AppDaemon: the owner's decision; a timer that publishes when nothing changed is
Python's job, and publishing straight to the broker with paho keeps a service call every
second out of the recorder (as matrix_media). No token: AppDaemon's HASS plugin reads the
states, and the broker login comes from AppDaemon's secrets.yaml. The log reports counts
and errors, never a coordinate.

Sources (read, not recalled): the entities and units of "Apollo MTR-1 53bc60" in Home
Assistant 2026.9.2 (sensor.<stem>_target_N_x/_y in mm, _speed in mm/s, the three counts,
_ltr390_light in lx, binary_sensor.<stem>_online and _ld2450_presence); matrix_media.py for
the AppDaemon 4.5.13 and paho-mqtt 2.1.0 call shapes; the panel's MQTT_BUS_BUFFER, 2048 B.
"""
import json
import math
import re
import threading
import time

import appdaemon.plugins.hass.hassapi as hass
import paho.mqtt.client as mqtt

BUFFER_BYTES = 2048                      # the panel's MQTT_BUS_BUFFER
STEM_RE = re.compile(r"[a-z0-9_]{1,64}")
SLACK_S = 0.25                           # timer jitter: a 5 s period must not slip to 6


def _num(state):
    try:
        v = float(state)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def target(x_state, y_state, v_state):
    """[x_mm, y_mm, v_mmps] as integers, or None for a target that is not there."""
    x, y = _num(x_state), _num(y_state)
    if x is None or y is None:
        return None
    xi, yi = int(round(x)), int(round(y))
    if xi == 0 and yi == 0:
        return None
    v = _num(v_state)
    return [xi, yi, int(round(v)) if v is not None else 0]


def count(state):
    v = _num(state)
    return max(0, int(round(v))) if v is not None else 0


def lux(state):
    v = _num(state)
    return max(0, int(round(v))) if v is not None else None


def read(get_state, stem):
    """Everything both payloads need, read from Home Assistant's current states."""
    def s(domain, name):
        return get_state("%s.%s_%s" % (domain, stem, name))

    return {
        "t": [target(s("sensor", "target_%d_x" % i), s("sensor", "target_%d_y" % i),
                     s("sensor", "target_%d_speed" % i)) for i in (1, 2, 3)],
        "p": count(s("sensor", "presence_target_count")),
        "m": count(s("sensor", "moving_target_count")),
        "s": count(s("sensor", "still_target_count")),
        "lux": lux(s("sensor", "ltr390_light")),
        "online": s("binary_sensor", "online") == "on",
        "present": s("binary_sensor", "ld2450_presence") == "on",
    }


def occupied(r):
    return r["present"] or r["p"] > 0 or any(t is not None for t in r["t"])


def targets_payload(r, ts):
    return json.dumps({"t": r["t"], "p": r["p"], "m": r["m"], "s": r["s"], "lux": r["lux"], "ts": int(ts)},
                      separators=(",", ":"))


def summary_payload(r, ts):
    return json.dumps({"p": r["p"], "m": r["m"], "s": r["s"], "lux": r["lux"], "online": r["online"], "ts": int(ts)},
                      separators=(",", ":"))


class MatrixPresence(hass.Hass):
    def initialize(self):
        a = self.args
        stem = str(a.get("device", ""))
        if not STEM_RE.fullmatch(stem):
            raise ValueError("matrix_presence: device must be the entity id stem, e.g. apollo_mtr_1_53bc60")
        if not a.get("mqtt_host"):
            raise ValueError("matrix_presence: mqtt_host is required (by IP: this container has no mDNS)")
        base = str(a.get("topic_base", "nickoscope_matrix"))
        self._stem = stem
        self._topic_targets = base + "/presence/targets"
        self._topic_summary = base + "/presence"
        self._period = max(1, int(a.get("period", 1)))
        self._empty_period = max(self._period, int(a.get("empty_period", 5)))
        self._summary_every = max(5, int(a.get("summary_every", 30)))

        self._lock = threading.Lock()
        self._connected = threading.Event()
        self._last_targets_at = 0.0
        self._last_summary = None
        self._last_summary_at = 0.0
        self._sent_targets = 0
        self._sent_summaries = 0
        self._skipped = 0

        self._mq = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="appdaemon-matrix-presence")
        if a.get("mqtt_user"):
            self._mq.username_pw_set(a["mqtt_user"], a.get("mqtt_pass"))
        self._mq.on_connect = self._on_connect
        self._mq.on_disconnect = self._on_disconnect
        self._mq.connect_async(a["mqtt_host"], int(a.get("mqtt_port", 1883)), 30)
        self._mq.loop_start()

        self.run_every(self._tick, "now", self._period)
        self.run_every(self._report, "now+60", 60)
        self.log("presence: %s to %s every %d s (empty room %d s), summary to %s"
                 % (stem, self._topic_targets, self._period, self._empty_period, self._topic_summary))

    def terminate(self):
        try:
            self._mq.loop_stop()
            self._mq.disconnect()
        except Exception:   # shutting down either way
            pass

    # ── MQTT ─────────────────────────────────────────────────────────────────
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if getattr(reason_code, "is_failure", False):
            self.log("presence: broker refused the connection: %s" % reason_code, level="WARNING")
            return
        with self._lock:
            self._last_summary = None      # the retained summary may have gone with the broker
        self._connected.set()

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        self._connected.clear()

    # ── the timer ────────────────────────────────────────────────────────────
    def _tick(self, kwargs):
        now = time.time()
        r = read(self.get_state, self._stem)
        if not self._connected.is_set():
            self._skipped += 1
            return
        with self._lock:
            if occupied(r) or now - self._last_targets_at >= self._empty_period - SLACK_S:
                body = targets_payload(r, now)
                if len(body) < BUFFER_BYTES:
                    self._mq.publish(self._topic_targets, body, qos=0, retain=False)
                    self._last_targets_at = now
                    self._sent_targets += 1
            key = (r["p"], r["m"], r["s"], r["lux"], r["online"])
            if key != self._last_summary or now - self._last_summary_at >= self._summary_every - SLACK_S:
                self._mq.publish(self._topic_summary, summary_payload(r, now), qos=0, retain=True)
                self._last_summary = key
                self._last_summary_at = now
                self._sent_summaries += 1

    def _report(self, kwargs):
        with self._lock:
            sent, summaries, skipped = self._sent_targets, self._sent_summaries, self._skipped
            self._sent_targets = self._sent_summaries = self._skipped = 0
        self.log("presence: last minute %d targets frames, %d summaries, %d ticks skipped with the broker down"
                 % (sent, summaries, skipped))
