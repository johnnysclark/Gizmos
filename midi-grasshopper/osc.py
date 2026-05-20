"""Minimal OSC 1.0 encode/decode. No external deps.

Supports the subset we need for MIDI → Grasshopper:
  - addresses: any "/foo/bar" string
  - args: int32 ('i'), float32 ('f'), string ('s'), True/False/None
          ('T'/'F'/'N')
  - non-bundled messages only (bundles are unused on this path)

Both sides of the wire live in this repo, so we don't need to handle
every weird OSC corner case — just round-trip cleanly with ourselves
and accept what TouchOSC / Max-style senders typically emit.

Run `python3 osc.py` for a self-test.
"""

import struct


def _osc_string(s: str) -> bytes:
    """OSC-string: UTF-8 bytes, one null terminator, then pad to 4."""
    b = s.encode("utf-8") + b"\x00"
    pad = (-len(b)) % 4
    return b + b"\x00" * pad


def _read_osc_string(buf: bytes, off: int) -> tuple[str, int]:
    end = buf.index(b"\x00", off)
    s = buf[off:end].decode("utf-8")
    nxt = end + 1
    nxt += (-nxt) % 4
    return s, nxt


def encode(address: str, *args) -> bytes:
    """Encode a single OSC message. Returns bytes ready for UDP send."""
    if not address.startswith("/"):
        raise ValueError("OSC address must start with '/'")
    type_tags = ","
    payload = b""
    for a in args:
        if a is True:
            type_tags += "T"
        elif a is False:
            type_tags += "F"
        elif a is None:
            type_tags += "N"
        elif isinstance(a, bool):
            # covered above, but defensive
            type_tags += "T" if a else "F"
        elif isinstance(a, int):
            type_tags += "i"
            payload += struct.pack(">i", a)
        elif isinstance(a, float):
            type_tags += "f"
            payload += struct.pack(">f", a)
        elif isinstance(a, str):
            type_tags += "s"
            payload += _osc_string(a)
        else:
            raise TypeError(f"unsupported OSC arg type: {type(a).__name__}")
    return _osc_string(address) + _osc_string(type_tags) + payload


def decode(data: bytes) -> tuple[str, list]:
    """Decode a single OSC message. Returns (address, [args])."""
    address, off = _read_osc_string(data, 0)
    type_tags, off = _read_osc_string(data, off)
    if not type_tags.startswith(","):
        raise ValueError(f"invalid OSC type tag string: {type_tags!r}")
    args = []
    for t in type_tags[1:]:
        if t == "i":
            args.append(struct.unpack(">i", data[off:off + 4])[0])
            off += 4
        elif t == "f":
            args.append(struct.unpack(">f", data[off:off + 4])[0])
            off += 4
        elif t == "s":
            s, off = _read_osc_string(data, off)
            args.append(s)
        elif t == "T":
            args.append(True)
        elif t == "F":
            args.append(False)
        elif t == "N":
            args.append(None)
        else:
            # Unknown tag — bail loudly so we notice in dev. The wire
            # we control should never produce these.
            raise ValueError(f"unsupported OSC type tag: {t!r}")
    return address, args


def _selftest() -> None:
    cases = [
        ("/x", ()),
        ("/cc/1", (0.5,)),
        ("/note/on", (60, 0.8)),
        ("/label", ("hello",)),
        ("/mixed", (1, 2.5, "three", True, False, None)),
        # padding edge cases — string lengths that land on 4-byte
        # boundaries before adding the null are the gnarly ones
        ("/abcd", (1.0,)),       # address ends exactly on boundary
        ("/abcdefg", (2.0,)),    # 7 chars + null = 8, no pad needed
        ("/abcdefgh", (3.0,)),   # 8 chars + null = 9 → pad to 12
    ]
    for addr, args in cases:
        packet = encode(addr, *args)
        assert len(packet) % 4 == 0, f"packet not 4-aligned: {addr}"
        out_addr, out_args = decode(packet)
        assert out_addr == addr, f"addr mismatch: {out_addr!r} != {addr!r}"
        assert len(out_args) == len(args), f"arg count mismatch on {addr}"
        for got, want in zip(out_args, args):
            if isinstance(want, float):
                assert abs(got - want) < 1e-6, f"float drift on {addr}"
            else:
                assert got == want, f"arg mismatch on {addr}: {got!r} != {want!r}"
        print(f"ok  {addr}  ->  {len(packet):3d} bytes  {out_args}")
    print("all OSC round-trips passed")


if __name__ == "__main__":
    _selftest()
