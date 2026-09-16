#!/usr/bin/env python3
"""matrix_presence.py against a fake Home Assistant, a fake broker and a fake clock.

AppDaemon and paho are replaced by stand-ins that record the publishes and the timers,
with the call shapes the app uses (AppDaemon 4.5.13, paho-mqtt 2.1.0). Nothing here talks
to a network, and no recorded room data is used: the states below are made up.

  python3 tools/ha/appdaemon/test_matrix_presence.py
"""
import json
import pathlib
import sys
import types
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class FakeHass:
    def __init__(self, *a, **kw):
        pass

    def log(self, msg, level="INFO"):
        self.logs.append((level, msg))

    def get_state(self, entity_id=None, **kwargs):
        return self.states.get(entity_id)

    def run_every(self, callback, start, interval, **kwargs):
        self.every.append((callback, start, interval))


class FakeClient:
    def __init__(self, api, client_id=""):
        self.client_id = client_id
        self.published = []
        self.user = None

    def username_pw_set(self, user, password=None):
        self.user = (user, password)

    def connect_async(self, host, port, keepalive):
        self.target = (host, port, keepalive)

    def loop_start(self):
        pass

    def loop_stop(self):
        pass

    def disconnect(self):
        pass

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, qos, retain))


hassapi = types.ModuleType("appdaemon.plugins.hass.hassapi")
hassapi.Hass = FakeHass
for name in ("appdaemon", "appdaemon.plugins", "appdaemon.plugins.hass"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["appdaemon.plugins.hass.hassapi"] = hassapi
sys.modules["appdaemon.plugins.hass"].hassapi = hassapi
paho = types.ModuleType("paho")
paho_mqtt = types.ModuleType("paho.mqtt")
paho_client = types.ModuleType("paho.mqtt.client")
paho_client.Client = FakeClient
paho_client.CallbackAPIVersion = types.SimpleNamespace(VERSION2="v2")
sys.modules.update({"paho": paho, "paho.mqtt": paho_mqtt, "paho.mqtt.client": paho_client})

import matrix_presence as mp  # noqa: E402

STEM = "apollo_mtr_1_53bc60"


def states(targets=(None, None, None), p=0, m=0, s=0, lux="12.4", online="on", present="off"):
    st = {
        "sensor.%s_presence_target_count" % STEM: "%.1f" % p,
        "sensor.%s_moving_target_count" % STEM: "%.1f" % m,
        "sensor.%s_still_target_count" % STEM: "%.1f" % s,
        "sensor.%s_ltr390_light" % STEM: lux,
        "binary_sensor.%s_online" % STEM: online,
        "binary_sensor.%s_ld2450_presence" % STEM: present,
    }
    for i, t in enumerate(targets, start=1):
        x, y, v = t if t else ("unknown", "unknown", "unknown")
        st["sensor.%s_target_%d_x" % (STEM, i)] = x
        st["sensor.%s_target_%d_y" % (STEM, i)] = y
        st["sensor.%s_target_%d_speed" % (STEM, i)] = v
    return st


def make_app(st, **args):
    app = mp.MatrixPresence()
    app.args = {"device": STEM, "mqtt_host": "192.0.2.1", "mqtt_user": "u", "mqtt_pass": "p", **args}
    app.states, app.logs, app.every = st, [], []
    app.initialize()
    app._connected.set()
    return app


class Clock:
    def __init__(self, t=1758035712.0):
        self.t = t

    def __call__(self):
        return self.t


class Rules(unittest.TestCase):
    def test_target(self):
        self.assertIsNone(mp.target("unknown", "1200.0", "0.0"))
        self.assertIsNone(mp.target("0.0", "0.0", "180.0"))
        self.assertIsNone(mp.target("nan", "100", "0"))
        self.assertEqual(mp.target("-350.0", "1200.0", "180.0"), [-350, 1200, 180])
        self.assertEqual(mp.target("1203.6", "842.4", "-317.2"), [1204, 842, -317])
        self.assertEqual(mp.target("10", "20", "unavailable"), [10, 20, 0])

    def test_counts_and_lux(self):
        self.assertEqual(mp.count("2.0"), 2)
        self.assertEqual(mp.count("unknown"), 0)
        self.assertEqual(mp.lux("379.558"), 380)
        self.assertIsNone(mp.lux("unknown"))

    def test_payload_shape(self):
        r = mp.read(states([("-350.0", "1200.0", "180.0"), None, None], p=1, m=1).get, STEM)
        body = json.loads(mp.targets_payload(r, 1758035712.9))
        self.assertEqual(list(body), ["t", "p", "m", "s", "lux", "ts"])
        self.assertEqual(body["t"], [[-350, 1200, 180], None, None])
        self.assertEqual((body["p"], body["m"], body["s"], body["lux"], body["ts"]), (1, 1, 0, 12, 1758035712))
        summary = json.loads(mp.summary_payload(r, 1758035712))
        self.assertEqual(list(summary), ["p", "m", "s", "lux", "online", "ts"])
        self.assertIs(summary["online"], True)

    def test_worst_case_size(self):
        worst = ("-4860.0", "7560.0", "-99999.0")
        r = mp.read(states([worst, worst, worst], p=3, m=3, s=3, lux="99999.9").get, STEM)
        size = len(mp.targets_payload(r, 9999999999))
        self.assertLess(size, 160)
        self.assertLess(size, mp.BUFFER_BYTES)

    def test_bad_device(self):
        app = mp.MatrixPresence()
        app.args, app.states, app.logs, app.every = {"device": "Apollo MTR", "mqtt_host": "x"}, {}, [], []
        with self.assertRaises(ValueError):
            app.initialize()


class Timing(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self._real_time = mp.time.time
        mp.time.time = self.clock

    def tearDown(self):
        mp.time.time = self._real_time

    def run_ticks(self, app, seconds):
        for _ in range(seconds):
            app._tick({})
            self.clock.t += 1.0

    def published(self, app, topic):
        return [p for p in app._mq.published if p[0] == topic]

    def test_setup(self):
        app = make_app(states())
        self.assertEqual(app._mq.user, ("u", "p"))
        self.assertEqual(app._mq.target, ("192.0.2.1", 1883, 30))
        self.assertEqual([e[2] for e in app.every], [1, 60])
        self.assertFalse(any("-350" in m for _, m in app.logs))

    def test_present_every_tick_even_when_still(self):
        app = make_app(states([("-350.0", "1200.0", "0.0"), None, None], p=1, s=1, present="on"))
        self.run_ticks(app, 10)
        frames = self.published(app, "nickoscope_matrix/presence/targets")
        self.assertEqual(len(frames), 10)
        self.assertTrue(all(qos == 0 and retain is False for _, _, qos, retain in frames))

    def test_empty_room_every_five_seconds(self):
        app = make_app(states())
        self.run_ticks(app, 21)
        frames = self.published(app, "nickoscope_matrix/presence/targets")
        self.assertEqual(len(frames), 5)          # t = 0, 5, 10, 15, 20
        self.assertEqual(json.loads(frames[0][1])["t"], [None, None, None])

    def test_summary_on_change_and_every_thirty_seconds(self):
        st = states()
        app = make_app(st)
        self.run_ticks(app, 10)
        st["sensor.%s_presence_target_count" % STEM] = "1.0"
        self.run_ticks(app, 50)
        summaries = self.published(app, "nickoscope_matrix/presence")
        # t=0 first, t=10 the change, t=40 the keepalive
        self.assertEqual([json.loads(b)["p"] for _, b, _, _ in summaries], [0, 1, 1])
        self.assertTrue(all(qos == 0 and retain is True for _, _, qos, retain in summaries))

    def test_nothing_while_the_broker_is_down(self):
        app = make_app(states([("1.0", "2.0", "3.0"), None, None], p=1, present="on"))
        app._connected.clear()
        self.run_ticks(app, 5)
        self.assertEqual(app._mq.published, [])
        self.assertEqual(app._skipped, 5)

    def test_reconnect_republishes_the_summary(self):
        app = make_app(states())
        self.run_ticks(app, 2)
        app._on_connect(app._mq, None, None, types.SimpleNamespace(is_failure=False))
        self.run_ticks(app, 1)
        self.assertEqual(len(self.published(app, "nickoscope_matrix/presence")), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
