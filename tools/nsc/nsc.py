#!/usr/bin/env python3
"""nsc - one way to talk to the LED matrix panel, for a person or for an agent.

Why this exists. An agent currently has three ways to learn what the panel is
doing - read the serial log, curl a route and read the answer, watch the screen
- and every one of them ends in a model reading prose and deciding. That has
cost this project real time: a POST of {"showPage":N} instead of
{"show":{"page":N}} is silently ignored AND answers success:true, and two whole
test sweeps were spent before anyone noticed.

So every command here prints exactly one JSON object and sets an exit code that
means something. The shape and the exit ladder are taken from MicroPixel's
manager (github.com/78/micropixel, tools/manager/micropixel_manager.py), which
solved this for the same reason.

    {"schema_version": 1, "ok": bool, "code": "<symbol>",
     "result": {...}, "error": null|{"code","message"}, "warnings": [...]}

`code` is a SYMBOL for a machine to branch on; the integer below is the exit
status, a coarser class. They are deliberately different things.

    0  ok
    1  execution_failed   - it went wrong; trying again may work
    2  invalid_arguments  - the call was wrong
    3  verification_failed / input_required - a person should look at this
    4  device_unreachable / invalid_response - trying again is pointless

**Two rules that are the whole point, and both are easy to lose.**

1. In --json mode stdout carries one object and nothing else. Everything any
   part of this program prints goes to stderr instead (see `main`). Without
   that, one stray print corrupts the contract for good.

2. A command that CHANGES something reads the state back and compares. An
   exit code that only says "the request was sent" is worth nothing - that is
   exactly the showPage failure above. `page` and `style` exit 3 when the panel
   answered politely and did not change.
"""

import argparse
import contextlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_HOST = "192.168.4.62"   # by IP: the mDNS name costs 5 s a request on this Mac

# How long the panel stands aside for a web client, from the firmware
# (src/network/net_turns.h, NET_TURN_QUIET_MS). Poll faster than this and every
# background fetch - weather, world clock, rail, flight - stops for as long as
# the polling lasts, and the panel then looks broken because of the tool that
# came to measure it.
PANEL_QUIET_MS = 1500


class Failure(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 1):
        super().__init__(message)
        self.code, self.exit_code = code, exit_code


# --- the thresholds, and why they are written down here at all ---------------
#
# The panel reports `largestHeapBlock` but never says what any module NEEDS -
# those are compile-time constants scattered across modules. So this table has
# to exist, and that makes it a second source of truth, which is how a tool
# starts lying confidently. The defence: each row records the file and the
# expression it came from, and `nsc doctor` re-reads the firmware and fails if
# any of them has moved. Verify identity, not presence.
#
# **These numbers are per-BUILD, not per-project**, which this tool learned the
# hard way on its first run: `doctor` reported drift on `rail` because the
# table was written from a branch that had cut that stack from 12 KB to 9, and
# the default checkout still had 12. `budget` would have been optimistic by
# 3,072 B - in exactly the direction that gets a bad build flashed.
#
# The panel cannot settle it for us: /api/info gives `version` and a `build`
# timestamp, but **no git commit and no branch**, so nothing here can work out
# which tree produced what is running. Until the firmware reports its commit,
# a person has to say. That is what --firmware is, and why doctor refuses to
# guess (exit 3, input_required) rather than check the wrong tree quietly.
BLOCK_NEEDS = [
    # name,        bytes,  source file,                        the expression there
    ("flight",     13312,  "src/flightboard/aero_direct.cpp",  "kStackBytes      = 12 * 1024"),
    ("rail",       10240,  "src/railboard/rtt_direct.cpp",     "kStackBytes      = 9 * 1024"),
    ("weather",     9216,  "src/weather/weather.cpp",          "WEATHER_TASK_STACK 8192"),
    ("worldclock",  9216,  "src/worldclock/wc_home.cpp",       '"wcHomeIp", 8192'),
]


def get(host: str, path: str, timeout: float = 6.0) -> tuple[int, str]:
    url = f"http://{host}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as answer:
            return answer.status, answer.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, TimeoutError) as err:
        raise Failure("device_unreachable", f"{url}: {err}", 4) from err


def post(host: str, path: str, payload: dict, timeout: float = 6.0) -> tuple[int, str]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(f"http://{host}{path}", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as answer:
            return answer.status, answer.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, TimeoutError) as err:
        raise Failure("device_unreachable", f"POST {path}: {err}", 4) from err


def get_json(host: str, path: str, timeout: float = 6.0) -> dict:
    status, text = get(host, path, timeout)
    if status != 200:
        raise Failure("execution_failed", f"{path} answered HTTP {status}", 1)
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        # Not "unreachable" and not "try again": the panel said something we
        # cannot act on, which is a 4 - the same class as a corrupt archive.
        raise Failure("invalid_response", f"{path} did not return JSON: {err}", 4) from err


# --- commands ---------------------------------------------------------------

def cmd_status(host: str, _args, warnings: list) -> dict:
    info = get_json(host, "/api/info")
    panel = get_json(host, "/api/panel")
    now = panel.get("now", {})
    if info.get("allocFails"):
        warnings.append({"code": "alloc_failures",
                         "count": info["allocFails"],
                         "last_bytes": info.get("allocFailBytes"),
                         "last_task": info.get("allocFailTask"),
                         "next_command": "nsc budget --json"})
    if info.get("linkRecoveries"):
        warnings.append({"code": "link_recoveries", "count": info["linkRecoveries"]})
    return {
        "firmware": info.get("firmwareVersion") or info.get("version"),
        "page": now.get("page"), "page_name": now.get("name"),
        "style": now.get("style"), "style_name": now.get("styleName"),
        "free_internal": info.get("freeInternalHeap"),
        "largest_block": info.get("largestHeapBlock"),
        "min_free_heap": info.get("minFreeHeap"),
        "alloc_fails": info.get("allocFails"),
        "link_recoveries": info.get("linkRecoveries"),
        "reset_reason": info.get("resetReason"),
        "ota_state": (info.get("ota") or {}).get("state"),
        "net_broker": info.get("netBroker"),
    }


def cmd_budget(host: str, _args, warnings: list) -> dict:
    """The arithmetic that should be done BEFORE flashing, not after.

    On 2026-09-20 a build was flashed that took 12 KB into .bss. It cut the
    largest contiguous internal block from 16,372 B to 9,716 B, below what the
    flight board needs before it will even attempt a fetch - so the flight
    board could not have fetched at all. Every number needed to predict that
    was available beforehand. Nobody subtracted them. This command subtracts
    them, and exits 3 when the answer is negative.
    """
    info = get_json(host, "/api/info")
    largest = info.get("largestHeapBlock")
    if not isinstance(largest, int):
        raise Failure("invalid_response", "/api/info has no largestHeapBlock", 4)
    rows, short = [], []
    for name, need, src, _expr in BLOCK_NEEDS:
        headroom = largest - need
        rows.append({"module": name, "needs_contiguous": need, "headroom": headroom,
                     "ok": headroom >= 0, "source": src})
        if headroom < 0:
            short.append(name)
    worst = min(rows, key=lambda r: r["headroom"])
    result = {"largest_block": largest, "free_internal": info.get("freeInternalHeap"),
              "modules": rows, "tightest": worst["module"],
              "tightest_headroom": worst["headroom"], "short": short}
    if short:
        raise Failure("budget_exceeded",
                      "not enough contiguous internal RAM for: " + ", ".join(short)
                      + f" (largest block {largest} B)", 3)
    if worst["headroom"] < 2048:
        warnings.append({"code": "budget_tight", "module": worst["module"],
                         "headroom": worst["headroom"],
                         "next_command": "nsc status --json"})
    return result


def _verify(host: str, want: dict, field: str) -> dict:
    panel = get_json(host, "/api/panel")
    return panel.get("now", {})


def cmd_page(host: str, args, warnings: list) -> dict:
    """Switch the page AND check that it happened.

    /api/panel answers success:true for a payload it does not understand, so
    the answer alone proves nothing. This is the command that closes that.
    """
    want = args.n
    before = get_json(host, "/api/panel").get("now", {})
    status, text = post(host, "/api/panel", {"show": {"page": want}})
    if status != 200:
        raise Failure("execution_failed", f"/api/panel answered HTTP {status}", 1)
    after = _verify(host, {"page": want}, "page")
    got = after.get("page")
    result = {"requested": want, "was": before.get("page"), "now": got,
              "name": after.get("name"), "panel_said": text.strip()[:120]}
    if got != want:
        raise Failure("verification_failed",
                      f"asked for page {want}, panel reports {got} - it answered "
                      f"politely and did not change", 3)
    if before.get("page") == want:
        warnings.append({"code": "already_in_state", "field": "page", "value": want,
                         "note": "it was already there, so nothing was proved"})
    return result


def cmd_style(host: str, args, warnings: list) -> dict:
    want = args.n
    before = get_json(host, "/api/panel").get("now", {})
    # {"style": N}, NOT {"styleId": N}. The firmware's own header says so -
    # web_panel.cpp:10 - and {"styleId":N} answers HTTP 200 and does nothing,
    # which is how docs/29 came to document the wrong one and how an entire
    # night went by without the weather page ever reaching the screen.
    status, text = post(host, "/api/panel", {"style": want})
    if status != 200:
        raise Failure("execution_failed", f"/api/panel answered HTTP {status}", 1)
    after = _verify(host, {"style": want}, "style")
    got = after.get("style")
    result = {"requested": want, "was": before.get("style"), "now": got,
              "name": after.get("styleName"), "panel_said": text.strip()[:120]}
    if got != want:
        raise Failure("verification_failed",
                      f"asked for style {want}, panel reports {got}", 3)
    # An "ok" that only means "it was already like that" is how a broken
    # command passes for a working one: `nsc style 14` reported success for
    # hours against a panel that happened to be on style 14 already, while the
    # payload it sent did nothing at all. Say which kind of success this is.
    if before.get("style") == want:
        warnings.append({"code": "already_in_state", "field": "style", "value": want,
                         "note": "it was already there, so nothing was proved"})
    return result


def cmd_doctor(host: str, args, warnings: list) -> dict:
    """Is this tool still telling the truth about this firmware?

    Two halves. The routes half asks whether every route the tool uses still
    answers. The thresholds half re-reads the firmware source and checks that
    the numbers baked into BLOCK_NEEDS are still the numbers in the code - the
    defence against this tool becoming a confident liar after someone changes
    a stack size. Modelled on MicroPixel's manager, which checks toolchain
    identity rather than mere presence before it trusts its own lock file.
    """
    routes, bad_routes = [], []
    for path in ("/api/info", "/api/panel"):
        try:
            status, _ = get(host, path, timeout=5.0)
        except Failure as err:
            status = str(err)
        ok = status == 200
        routes.append({"route": path, "status": status, "ok": ok})
        if not ok:
            bad_routes.append(path)

    if not args.firmware:
        raise Failure("input_required",
                      "say which checkout was flashed: the panel reports version and a "
                      "build timestamp but no commit, so this tool cannot tell. "
                      "Re-run with --firmware <path to the checkout that was flashed>", 3)
    thresholds, drifted = [], []
    root = Path(args.firmware)
    for name, need, src, expr in BLOCK_NEEDS:
        path = root / src
        if not path.exists():
            thresholds.append({"module": name, "source": src, "checked": False,
                               "why": "source not found"})
            warnings.append({"code": "firmware_source_missing", "path": str(path),
                             "next_command": f"nsc doctor --firmware <path> --json"})
            continue
        text = path.read_text(errors="replace")
        found = expr in text
        thresholds.append({"module": name, "source": src, "expects": expr,
                           "checked": True, "ok": found, "bytes": need})
        if not found:
            drifted.append(name)

    result = {"host": host, "routes": routes, "thresholds": thresholds,
              "firmware_root": str(root)}
    if bad_routes:
        raise Failure("route_missing",
                      "routes this tool depends on did not answer: " + ", ".join(bad_routes), 4)
    if drifted:
        raise Failure("threshold_drift",
                      "the firmware no longer matches this tool's table for: "
                      + ", ".join(drifted) + " - nsc budget would lie; fix BLOCK_NEEDS", 4)
    return result


COMMANDS = {"status": cmd_status, "budget": cmd_budget, "page": cmd_page,
            "style": cmd_style, "doctor": cmd_doctor}


def build_parser() -> argparse.ArgumentParser:
    # The common flags live on a parent parser so they are accepted BOTH before
    # and after the subcommand. `nsc budget --json` is the order a person types
    # and the order MicroPixel's own examples use; an argparse default that
    # only accepts `nsc --json budget` fails the call rather than the intent.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--host", default=DEFAULT_HOST)
    common.add_argument("--json", action="store_true", help="one JSON object on stdout")

    parser = argparse.ArgumentParser(prog="nsc", parents=[common],
                                     description="talk to the LED matrix panel")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", parents=[common], help="heap, page, link, OTA, broker")
    sub.add_parser("budget", parents=[common],
                   help="contiguous RAM against what each module needs")
    page = sub.add_parser("page", parents=[common],
                          help="switch page and verify it changed")
    page.add_argument("n", type=int)
    style = sub.add_parser("style", parents=[common],
                           help="switch clock style and verify it changed")
    style.add_argument("n", type=int)
    doc = sub.add_parser("doctor", parents=[common],
                         help="are the routes and the baked thresholds still true")
    doc.add_argument("--firmware", help="firmware checkout to check thresholds against")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    warnings: list = []
    result, error, code = {}, None, 0
    try:
        # Rule 1: in --json mode nothing but the envelope reaches stdout.
        with contextlib.redirect_stdout(sys.stderr) if args.json else contextlib.nullcontext():
            result = COMMANDS[args.command](args.host, args, warnings)
    except Failure as failure:
        code, error = failure.exit_code, {"code": failure.code, "message": str(failure)}
        result = getattr(failure, "partial", {}) or {}
    except KeyboardInterrupt:
        code, error = 1, {"code": "interrupted", "message": "interrupted; retry is safe"}
    except Exception as failure:                     # noqa: BLE001 - last resort
        code, error = 1, {"code": "execution_failed", "message": f"{type(failure).__name__}: {failure}"}

    envelope = {"schema_version": SCHEMA_VERSION, "ok": code == 0,
                "code": error["code"] if error else "ok",
                "result": result, "error": error, "warnings": warnings}
    if args.json:
        print(json.dumps(envelope, ensure_ascii=False))
    else:
        for warning in warnings:
            print("nsc: warning: " + warning["code"], file=sys.stderr)
        if error:
            print("nsc: " + error["message"], file=sys.stderr)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
