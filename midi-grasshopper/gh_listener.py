"""Grasshopper Python 3 (ScriptEditor) OSC listener component.

Drop the body of this file into a GH ScriptEditor Python 3 component.

Inputs (rename the input params on the component to match):
    addresses : list of OSC addresses to expose, e.g.
                ["/cc/1", "/cc/2", "/note/last"]
    port      : UDP port to listen on (int, default 7000)
    enable    : toggle (bool, default True). Set False to release the
                socket cleanly before closing the document.

Outputs:
    values : list of latest values, parallel to `addresses`.
             Missing addresses come out as None until a packet arrives.
    status : short string with bind state + last error + packet count.

How it works:
- Spins up a UDP socket on a background thread.
- Each incoming packet is decoded as OSC and stashed in a thread-safe
  dict keyed by OSC address.
- A second tiny thread debounces redraws: any time a packet lands it
  asks Grasshopper to recompute, capped at ~30 Hz so a fast knob
  sweep doesn't drown Rhino in solutions.
- State is attached to `ghenv.Component` so it survives across
  solves. Toggling `enable` False (or closing the doc) releases the
  socket and joins the threads.

The OSC parser is inlined (no external deps). If you change the
parser, change the same code in `osc.py` so the dev tests still
match.
"""

import socket
import struct
import threading
import time


# ---------------------------------------------------------------------------
# OSC decode (inlined from osc.py — keep in sync if you edit either)
# ---------------------------------------------------------------------------

def _read_osc_string(buf, off):
    end = buf.index(b"\x00", off)
    s = buf[off:end].decode("utf-8")
    nxt = end + 1
    nxt += (-nxt) % 4
    return s, nxt


def osc_decode(data):
    address, off = _read_osc_string(data, 0)
    type_tags, off = _read_osc_string(data, off)
    if not type_tags.startswith(","):
        raise ValueError("invalid OSC type tag string")
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
            raise ValueError("unsupported OSC type tag: " + repr(t))
    return address, args


# ---------------------------------------------------------------------------
# Listener — socket thread + redraw-tick thread
# ---------------------------------------------------------------------------

class GhOscListener(object):
    """UDP/OSC listener with a debounced GH redraw tick."""

    def __init__(self, port, expire_callback, host="0.0.0.0", tick_hz=30.0):
        self.host = host
        self.port = int(port)
        self._expire = expire_callback
        self._tick_period = 1.0 / max(1.0, float(tick_hz))

        self._sock = None
        self._sock_thread = None
        self._tick_thread = None
        self._stop = threading.Event()
        self._dirty = threading.Event()
        self._lock = threading.Lock()

        self.state = {}
        self.packets = 0
        self.last_error = None
        self.bound = False

    def start(self):
        if self.bound:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.settimeout(0.1)
        self._sock = s
        self._stop.clear()
        self._dirty.clear()

        self._sock_thread = threading.Thread(
            target=self._recv_loop, name="GhOscListener.recv", daemon=True)
        self._tick_thread = threading.Thread(
            target=self._tick_loop, name="GhOscListener.tick", daemon=True)
        self._sock_thread.start()
        self._tick_thread.start()
        self.bound = True

    def stop(self):
        self._stop.set()
        self._dirty.set()  # wake the tick thread so it can exit
        s = self._sock
        self._sock = None
        if s is not None:
            try:
                s.close()
            except OSError:
                pass
        for t in (self._sock_thread, self._tick_thread):
            if t is not None and t.is_alive():
                t.join(timeout=1.0)
        self._sock_thread = None
        self._tick_thread = None
        self.bound = False

    def snapshot(self):
        with self._lock:
            return dict(self.state)

    def _recv_loop(self):
        while not self._stop.is_set():
            sock = self._sock
            if sock is None:
                return
            try:
                data, _addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                address, args = osc_decode(data)
            except Exception as e:
                self.last_error = "decode: " + repr(e)
                continue
            value = args[0] if len(args) == 1 else args
            with self._lock:
                self.state[address] = value
                self.packets += 1
            self._dirty.set()

    def _tick_loop(self):
        while not self._stop.is_set():
            self._dirty.wait()
            if self._stop.is_set():
                return
            self._dirty.clear()
            try:
                self._expire()
            except Exception as e:
                self.last_error = "expire: " + repr(e)
            time.sleep(self._tick_period)


# ---------------------------------------------------------------------------
# UI-thread-safe ExpireSolution
# ---------------------------------------------------------------------------

def _make_expire_callback(component):
    """Return a callable that asks GH to recompute, marshalled to the UI
    thread where possible. Falls back to a direct call if the canvas is
    unavailable (e.g. during shutdown)."""
    try:
        import Grasshopper  # only importable inside Rhino/GH
        canvas = Grasshopper.Instances.ActiveCanvas

        def expire():
            try:
                if canvas is not None and canvas.InvokeRequired:
                    canvas.Invoke(lambda: component.ExpireSolution(True))
                else:
                    component.ExpireSolution(True)
            except Exception:
                # last resort — calling from a non-UI thread sometimes
                # works on Mac Rhino 8 even without the marshalling
                component.ExpireSolution(True)
        return expire
    except Exception:
        return lambda: component.ExpireSolution(True)


# ---------------------------------------------------------------------------
# Component body — runs every solve
# ---------------------------------------------------------------------------

# Inputs (will be None if the param is empty)
_addresses = addresses if isinstance(addresses, (list, tuple)) and addresses else []
_port = int(port) if port is not None else 7000
_enable = True if enable is None else bool(enable)

_component = ghenv.Component
_listener = getattr(_component, "_osc_listener", None)

# Tear down if config changed or user disabled the component
if _listener is not None and (not _enable or _listener.port != _port):
    _listener.stop()
    _component._osc_listener = None
    _listener = None

# Stand up a fresh listener when needed
if _enable and _listener is None:
    try:
        _listener = GhOscListener(
            port=_port,
            expire_callback=_make_expire_callback(_component),
        )
        _listener.start()
        _component._osc_listener = _listener
    except OSError as e:
        # Most often: another process holds the port. Surface it on the
        # status output rather than crashing the whole document.
        _listener = None
        _component._osc_listener = None
        _bind_error = repr(e)
    else:
        _bind_error = None
else:
    _bind_error = None

# Read current values for the requested addresses
if _listener is not None:
    _snap = _listener.snapshot()
    values = [_snap.get(a) for a in _addresses]
    if _bind_error:
        status = "bind failed: " + _bind_error
    elif _listener.last_error:
        status = "port {p} | {n} pkts | err: {e}".format(
            p=_listener.port, n=_listener.packets, e=_listener.last_error)
    else:
        status = "listening on :{p} | {n} pkts".format(
            p=_listener.port, n=_listener.packets)
else:
    values = [None] * len(_addresses)
    if _bind_error:
        status = "bind failed on :{p}: {e}".format(p=_port, e=_bind_error)
    elif not _enable:
        status = "disabled"
    else:
        status = "idle"
