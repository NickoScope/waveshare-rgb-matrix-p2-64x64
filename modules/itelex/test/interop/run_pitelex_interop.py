#!/usr/bin/env python3
"""
Interoperability test: our station (itx::Session over TCP, built from
itx_tcp.cpp) against piTelex's own i-Telex code, in both directions.

    test/interop/run_pitelex_interop.py --pitelex /path/to/piTelex

piTelex (GPL-3, https://github.com/fablab-wue/piTelex) is not part of this
repository: point --pitelex at a clone. The script imports only its i-Telex
modules (txDevITelexClient / txDevITelexSrv and what they import) and plays
the part of its MCP and teleprinter, through the same read()/write()
escape-sequence interface its real devices use:
  ESC A        printer start requested  -> we answer ESC AA (started)
  ESC I        welcome banner wanted    -> we answer ESC WELCOME
  ESC ~n       printer buffer length    -> we send ESC ~0 (nothing pending)
  ESC Z        end the call
  '@' / '#'    WRU (sent as '@'; a received WRU reads as '#')

Scenarios:
  1. piTelex calls us: text in, our reply out, WRU -> our answerback, piTelex hangs up.
  2. We call piTelex: text in, its reply out, our WRU -> its answerback, we hang up.
Exit status 0 only if every check passes.
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "src"))


def build(tmp):
    exe = os.path.join(tmp, "itx_tcp")
    cmd = [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-Wall", "-Wextra", "-Werror",
           "-I" + SRC, os.path.join(HERE, "itx_tcp.cpp"),
           os.path.join(SRC, "itx_baudot.cpp"), os.path.join(SRC, "itx_packet.cpp"),
           os.path.join(SRC, "itx_session.cpp"), "-o", exe]
    subprocess.run(cmd, check=True)
    return exe


class Printer:
    """The MCP + teleprinter side of a piTelex device, for a test."""

    def __init__(self, dev, name):
        self.dev, self.name, self.rx, self.events = dev, name, "", []
        self._run = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def _loop(self):
        last_feedback = 0.0
        while self._run:
            a = self.dev.read()
            if a is None:
                now = time.monotonic()
                if now - last_feedback > 0.5:
                    self.dev.write("\x1b~0", "MCP")   # printer buffer empty: all printed
                    self.dev.idle2Hz()                # lets it send its Acknowledge
                    last_feedback = now
                time.sleep(0.01)
                continue
            if a.startswith("\x1b"):
                self.events.append(a)
                if a == "\x1bA":
                    self.dev.write("\x1bAA", "MCP")
                elif a == "\x1bI":
                    self.dev.write("\x1bWELCOME", "MCP")
                continue
            if a in "<>":          # piTelex shows LTRS/FIGS shifts as '<' and '>'
                continue
            self.rx += a

    def type(self, text):
        for ch in text:
            self.dev.write(ch, "MCP")

    def stop(self):
        self._run = False


def wait_for(cond, timeout):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if cond():
            return True
        time.sleep(0.05)
    return False


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (("  " + detail) if detail else ""))
    return ok


def scenario_pitelex_calls_us(exe, tmp, port):
    import txDevITelexClient
    ours = subprocess.Popen([exe, "listen", str(port), "--expect", "HELLO FROM PITELEX",
                             "--reply", "RY RY NIKOSCOPE", "--answerback", "10101 NIKOSCOPE"],
                            stdout=subprocess.PIPE, text=True)
    time.sleep(0.3)
    book = os.path.join(tmp, "userlist.csv")
    with open(book, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Nick", "TNum", "ENum", "Type", "Host", "Port", "Name"])
        w.writerow(["NKTX", "10101", "-", "I", "127.0.0.1", str(port), "NikoScope"])
    txDevITelexClient.TelexITelexClient.USERLIST = []
    dev = txDevITelexClient.TelexITelexClient(userlist=book)
    pr = Printer(dev, "pitelex-client")
    dev.write("\x1b#10101", "MCP")                      # dial
    ok = check("1a piTelex connects to our station", wait_for(lambda: "\x1bA" in pr.events, 10))
    time.sleep(0.5)
    pr.type("HELLO FROM PITELEX\r\n")
    ok &= check("1b our reply prints at piTelex", wait_for(lambda: "RY RY NIKOSCOPE" in pr.rx, 15),
                repr(pr.rx))
    pr.type("@")                                        # WRU
    ok &= check("1c WRU answered with our answerback",
                wait_for(lambda: "10101 NIKOSCOPE" in pr.rx, 15), repr(pr.rx))
    time.sleep(1.5)
    dev.write("\x1bZ", "MCP")                           # hang up
    out, _ = ours.communicate(timeout=20)
    print("   ours: " + out.strip().replace("\n", "\n   ours: "))
    ok &= check("1d our station saw the text", "RX HELLO FROM PITELEX" in out)
    ok &= check("1e our station saw piTelex's End", "END end" in out)
    ok &= check("1f our station exited PASS", ours.returncode == 0)
    pr.stop()
    dev.exit()
    return ok


def scenario_we_call_pitelex(exe, port):
    import txDevITelexSrv
    dev = txDevITelexSrv.TelexITelexSrv(port=port, block_ascii=True, tns_pin=1)   # no TNS use; a pin is mandatory
    pr = Printer(dev, "pitelex-server")

    def answer():
        if wait_for(lambda: "HELLO FROM NIKOSCOPE" in pr.rx, 20):
            pr.type("ROGER\r\n")
        if wait_for(lambda: "#" in pr.rx, 20):          # our WRU arrives as '#'
            pr.type("\r\n4711 PITELEX\r\n")
    threading.Thread(target=answer, daemon=True).start()

    ours = subprocess.run([exe, "call", "127.0.0.1", str(port), "--send", "HELLO FROM NIKOSCOPE",
                           "--wru", "--expect", "4711 PITELEX"], capture_output=True, text=True,
                          timeout=60)
    print("   ours: " + ours.stdout.strip().replace("\n", "\n   ours: "))
    ok = check("2a piTelex printed our text", "HELLO FROM NIKOSCOPE" in pr.rx, repr(pr.rx))
    ok &= check("2b piTelex saw our WRU", "#" in pr.rx)
    ok &= check("2c its reply reached us", "RX ROGER" in ours.stdout)
    ok &= check("2d its answerback reached us", "4711 PITELEX" in ours.stdout)
    ok &= check("2e we hung up cleanly", ours.returncode == 0 and "END hangup" in ours.stdout)
    ok &= check("2f piTelex noticed the end", wait_for(lambda: "\x1bST" in pr.events, 10))
    pr.stop()
    dev.exit()
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pitelex", required=True, help="path to a piTelex clone")
    ap.add_argument("--port", type=int, default=21340)
    args = ap.parse_args()
    sys.path.insert(0, os.path.abspath(args.pitelex))
    import logging
    logging.basicConfig(level=logging.WARNING)
    with tempfile.TemporaryDirectory() as tmp:
        exe = build(tmp)
        ok = scenario_pitelex_calls_us(exe, tmp, args.port)
        ok &= scenario_we_call_pitelex(exe, args.port + 1)
    print("INTEROP " + ("PASS" if ok else "FAIL"))
    os._exit(0 if ok else 1)   # piTelex leaves non-daemon threads behind


if __name__ == "__main__":
    main()
