#!/usr/bin/env python3
"""
test_osc_send.py - standalone OSC sender for testing the GH listener.

No external dependencies. Pure stdlib. Speaks the same OSC 1.0 wire
format that Ableton/M4L sends, so if this drives the GH listener
correctly, the GH side is verified before any Ableton work.

Usage:
    python3 test_osc_send.py                # interactive REPL
    python3 test_osc_send.py sweep          # sweep /cc/1 0..127 over 5s
    python3 test_osc_send.py sweep /cc/2 3  # sweep /cc/2 over 3s
    python3 test_osc_send.py note 60        # send /note 60.0
    python3 test_osc_send.py send /foo 1.5  # send arbitrary float message
    python3 test_osc_send.py selftest       # encode+decode round-trip check

Default target is 127.0.0.1:7000. Override with TEST_OSC_HOST /
TEST_OSC_PORT env vars.
"""

import os
import socket
import struct
import sys
import time


# ---------- OSC 1.0 wire format ----------
# Address pattern + type tag string + args, each section 4-byte aligned.
# Strings are null-terminated and padded with nulls to the next 4-byte
# boundary (if the length is already a multiple of 4, four nulls are
# still appended). Floats and ints are big-endian.

def _pad4(b: bytes) -> bytes:
    return b + b"\x00" * (4 - (len(b) % 4))


def _enc_string(s: str) -> bytes:
    return _pad4(s.encode("utf-8") + b"\x00")


def encode_message(address: str, *args) -> bytes:
    type_tag = ","
    payload = b""
    for a in args:
        if isinstance(a, bool):
            # OSC has T/F type tags but Ableton/M4L won't send them; map
            # to int 1/0 so the listener sees a numeric value.
            type_tag += "i"
            payload += struct.pack(">i", 1 if a else 0)
        elif isinstance(a, int):
            type_tag += "i"
            payload += struct.pack(">i", a)
        elif isinstance(a, float):
            type_tag += "f"
            payload += struct.pack(">f", a)
        elif isinstance(a, str):
            type_tag += "s"
            payload += _enc_string(a)
        else:
            raise TypeError(f"unsupported OSC arg type: {type(a).__name__}")
    return _enc_string(address) + _enc_string(type_tag) + payload


def _read_string(buf: bytes, i: int):
    end = buf.index(b"\x00", i)
    s = buf[i:end].decode("utf-8")
    # advance past the null and any padding to next 4-byte boundary
    j = end + 1
    while j % 4 != 0:
        j += 1
    return s, j


def decode_message(buf: bytes):
    """Decode one OSC message. Returns (address, [args]). Bundles not
    supported on purpose — Ableton/M4L sends plain messages."""
    if buf.startswith(b"#bundle\x00"):
        raise ValueError("OSC bundles not supported")
    address, i = _read_string(buf, 0)
    type_tag, i = _read_string(buf, i)
    if not type_tag.startswith(","):
        raise ValueError(f"bad OSC type tag: {type_tag!r}")
    args = []
    for t in type_tag[1:]:
        if t == "f":
            args.append(struct.unpack(">f", buf[i:i + 4])[0])
            i += 4
        elif t == "i":
            args.append(struct.unpack(">i", buf[i:i + 4])[0])
            i += 4
        elif t == "s":
            s, i = _read_string(buf, i)
            args.append(s)
        else:
            raise ValueError(f"unsupported OSC type tag char: {t!r}")
    return address, args


# ---------- send helpers ----------

def _target():
    host = os.environ.get("TEST_OSC_HOST", "127.0.0.1")
    port = int(os.environ.get("TEST_OSC_PORT", "7000"))
    return host, port


def send(address: str, *args, sock=None):
    s = sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(encode_message(address, *args), _target())
    if sock is None:
        s.close()


# ---------- modes ----------

def cmd_sweep(address="/cc/1", duration=5.0):
    duration = float(duration)
    host, port = _target()
    print(f"sweep {address} 0..127 over {duration}s → {host}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start = time.monotonic()
    last_print = start
    while True:
        t = time.monotonic() - start
        if t >= duration:
            send(address, 127.0, sock=sock)
            break
        v = (t / duration) * 127.0
        send(address, float(v), sock=sock)
        if time.monotonic() - last_print > 0.5:
            print(f"  t={t:4.2f}s  {address} = {v:6.2f}")
            last_print = time.monotonic()
        time.sleep(1 / 120)  # 120 Hz update; M4L will run slower IRL
    print("done.")


def cmd_note(pitch="60"):
    p = float(pitch)
    send("/note", p)
    print(f"sent /note {p}")


def cmd_send(address, value):
    send(address, float(value))
    print(f"sent {address} {value}")


def cmd_repl():
    host, port = _target()
    print(f"interactive OSC sender → {host}:{port}")
    print("type:  <address> <float>     e.g.  /cc/1 64")
    print("       sweep [addr] [secs]   e.g.  sweep /cc/2 3")
    print("       note <pitch>")
    print("       quit")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            break
        parts = line.split()
        try:
            if parts[0] == "sweep":
                cmd_sweep(*(parts[1:] or ["/cc/1", "5"]))
            elif parts[0] == "note":
                cmd_note(parts[1])
            elif parts[0].startswith("/"):
                send(parts[0], float(parts[1]), sock=sock)
                print(f"sent {parts[0]} {parts[1]}")
            else:
                print("unknown command")
        except Exception as e:
            print(f"error: {e}")


def cmd_selftest():
    """Encode → decode round-trip. Exercises every supported type."""
    cases = [
        ("/cc/1", [64.0]),
        ("/note", [60.0]),
        ("/foo", [1, 2, 3]),
        ("/bar", ["hello"]),
        ("/mix", [1, 2.5, "x"]),
        ("/", [0.0]),
    ]
    for addr, args in cases:
        buf = encode_message(addr, *args)
        assert len(buf) % 4 == 0, f"not 4-byte aligned: {addr}"
        decoded_addr, decoded_args = decode_message(buf)
        assert decoded_addr == addr, (decoded_addr, addr)
        # float comparison tolerant of float32 quantization
        for a, b in zip(args, decoded_args):
            if isinstance(a, float):
                assert abs(a - b) < 1e-5, (a, b)
            else:
                assert a == b, (a, b)
        print(f"  ok  {addr} {args}")
    print("selftest passed.")


def main(argv):
    if len(argv) <= 1:
        cmd_repl()
        return
    cmd = argv[1]
    if cmd == "sweep":
        cmd_sweep(*(argv[2:] or ["/cc/1", "5"]))
    elif cmd == "note":
        cmd_note(argv[2] if len(argv) > 2 else "60")
    elif cmd == "send":
        cmd_send(argv[2], argv[3])
    elif cmd == "selftest":
        cmd_selftest()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
