"""Fire fake OSC at the GH listener so the Rhino side can be verified
without Ableton in the picture.

Examples:

    # one-shot: send a single value
    python3 test_osc_send.py /cc/1 0.5

    # mixed args
    python3 test_osc_send.py /note/on 60 0.8

    # smoothly sweep a CC over a few seconds
    python3 test_osc_send.py --sweep /cc/1 --duration 3 --rate 60

    # exercise the whole demo set the GH definition expects
    python3 test_osc_send.py --demo

By default sends to 127.0.0.1:7000. Override with --host/--port.

Args are auto-typed: 'true'/'false' → bool, integers → int, anything
else parseable as float → float, otherwise string. Force a float by
adding a decimal point (`60` is int, `60.0` is float).
"""

import argparse
import math
import socket
import sys
import time

import osc


def coerce(token: str):
    low = token.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("none", "null", "nil"):
        return None
    # int only if no decimal point or scientific notation
    if "." not in token and "e" not in low:
        try:
            return int(token)
        except ValueError:
            pass
    try:
        return float(token)
    except ValueError:
        return token


def send_one(sock, host, port, address, args):
    pkt = osc.encode(address, *args)
    sock.sendto(pkt, (host, port))
    print(f"-> {host}:{port}  {address}  {list(args)}")


def sweep(sock, host, port, address, duration, rate):
    n = max(2, int(duration * rate))
    period = 1.0 / rate
    print(f"sweeping {address} for {duration:.1f}s @ {rate:.0f} Hz "
          f"({n} packets)")
    t0 = time.time()
    for i in range(n):
        # cosine-eased 0..1..0 sweep so you can see direction reverse
        phase = i / (n - 1)
        v = 0.5 - 0.5 * math.cos(2 * math.pi * phase)
        send_one(sock, host, port, address, (float(v),))
        # busy-tight enough to keep timing tight without burning CPU
        target = t0 + (i + 1) * period
        rem = target - time.time()
        if rem > 0:
            time.sleep(rem)


def demo(sock, host, port):
    """Hit every channel the example.gh definition uses."""
    print("demo: walking through CC1, CC2 sweeps and a note range")
    # CC1 sweep — tower twist
    sweep(sock, host, port, "/cc/1", duration=2.0, rate=60)
    time.sleep(0.2)
    # CC2 sweep — tower taper
    sweep(sock, host, port, "/cc/2", duration=2.0, rate=60)
    time.sleep(0.2)
    # Notes across a small range — picks "current pitch"
    for note in [60, 62, 64, 65, 67, 69, 71, 72]:
        send_one(sock, host, port, "/note/last", (note,))
        send_one(sock, host, port, "/note/on", (note, 0.8))
        time.sleep(0.12)
        send_one(sock, host, port, "/note/off", (note, 0.0))
        time.sleep(0.06)
    print("demo complete")


def main():
    p = argparse.ArgumentParser(description="Fake OSC sender")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7000)
    p.add_argument("--sweep", metavar="ADDR",
                   help="sweep a value 0..1..0 on the given OSC address")
    p.add_argument("--duration", type=float, default=2.0,
                   help="sweep duration in seconds (default 2.0)")
    p.add_argument("--rate", type=float, default=60.0,
                   help="sweep packet rate in Hz (default 60)")
    p.add_argument("--demo", action="store_true",
                   help="run the demo sequence the example.gh expects")
    p.add_argument("address", nargs="?", help="OSC address e.g. /cc/1")
    p.add_argument("args", nargs="*", help="OSC arguments")
    ns = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if ns.demo:
            demo(sock, ns.host, ns.port)
            return
        if ns.sweep:
            sweep(sock, ns.host, ns.port, ns.sweep, ns.duration, ns.rate)
            return
        if not ns.address:
            p.error("address required (or use --sweep / --demo)")
        typed = tuple(coerce(a) for a in ns.args)
        send_one(sock, ns.host, ns.port, ns.address, typed)
    finally:
        sock.close()


if __name__ == "__main__":
    sys.exit(main() or 0)
