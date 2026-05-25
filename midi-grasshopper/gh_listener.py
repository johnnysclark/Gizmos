"""
gh_listener.py - OSC/UDP listener for a Grasshopper ScriptEditor
                 Python 3 (CPython) component on Rhino 8.

How to use in Grasshopper:
  1. Drop a "C#/Python Script" component, switch language to
     Python 3, paste this whole file into the editor.
  2. Add named inputs (right-click the component → Manage Inputs):
       Addresses  (list of str)        e.g. ["/note", "/cc/1", "/cc/2"]
       Port       (int)                 default 7000
       Reset      (bool)                toggle to force socket rebind
  3. Add named outputs:
       Values     (list of float)       parallel to Addresses
       Status     (str)                 listening state / last message
  4. Hit Run. The component subscribes to UDP packets on Port and
     produces a float per address. Missing addresses read 0.0 until
     the first message arrives.

The listener thread is a daemon, so it dies with Rhino. SO_REUSEADDR
is set before bind, so restarting Rhino or the script won't trip
"Address already in use". On document close the socket is closed too,
belt-and-braces.

No external Python deps. The OSC parser is inlined below.
"""

import socket
import struct
import threading
import time

import scriptcontext as sc

# These come from Rhino's hosted .NET via pythonnet inside Rhino 8
# ScriptEditor Python 3. They are not importable outside Rhino.
import Rhino                          # noqa: F401  (used inside worker)
from System import Action             # noqa: F401  (used inside worker)


# ============================================================
# OSC 1.0 decode (matches test_osc_send.py encoder)
# ============================================================

def _read_string(buf, i):
    end = buf.index(b"\x00", i)
    s = buf[i:end].decode("utf-8", errors="replace")
    j = end + 1
    while j % 4 != 0:
        j += 1
    return s, j


def decode_osc(buf):
    """Decode a single OSC message. Returns (address, [args]) or
    raises ValueError. Bundles are not supported on purpose —
    Ableton/M4L sends plain messages."""
    if buf.startswith(b"#bundle\x00"):
        raise ValueError("OSC bundle received; only plain messages supported")
    address, i = _read_string(buf, 0)
    type_tag, i = _read_string(buf, i)
    if not type_tag.startswith(","):
        raise ValueError("bad type tag")
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
            # Skip unknown types by bailing — keeps the listener honest
            raise ValueError(f"unsupported OSC type char: {t!r}")
    return address, args


# ============================================================
# Listener (daemon thread, owns one UDP socket)
# ============================================================

class Listener:
    def __init__(self, port, component):
        self.port = port
        self.component = component
        self.sock = None
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.state = {}              # {address: float}
        self.last_msg = ("", 0.0)    # (address, monotonic time)
        self.last_expire = 0.0
        self.error = None

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # SO_REUSEADDR prevents "port in use" on rapid restarts. On
        # macOS, SO_REUSEPORT is the right twin for the same effect
        # when multiple processes are involved — we set it if present.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        s.bind(("0.0.0.0", self.port))
        s.settimeout(0.1)
        self.sock = s
        self.thread = threading.Thread(target=self._run, daemon=True,
                                       name=f"osc-listener-{self.port}")
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        if self.thread is not None:
            self.thread.join(timeout=0.5)
            self.thread = None

    def snapshot(self):
        with self.lock:
            return dict(self.state), self.last_msg, self.error

    def _run(self):
        while not self.stop_event.is_set():
            # If the component was removed from the document, stop.
            try:
                if self.component.OnPingDocument() is None:
                    break
            except Exception:
                break
            try:
                buf, _ = self.sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                address, args = decode_osc(buf)
            except Exception as e:
                with self.lock:
                    self.error = f"decode: {e}"
                continue
            if not args:
                continue
            # First numeric arg is the value (matches MIDI mapping).
            value = float(args[0]) if isinstance(args[0], (int, float)) else 0.0
            with self.lock:
                changed = self.state.get(address) != value
                self.state[address] = value
                self.last_msg = (address, time.monotonic())
                self.error = None
            if changed:
                self._maybe_expire()

    def _maybe_expire(self):
        now = time.monotonic()
        if now - self.last_expire < 1.0 / 30.0:
            return  # rate limit to ~30 Hz
        self.last_expire = now
        # ExpireSolution must run on the Rhino UI thread.
        try:
            Rhino.RhinoApp.InvokeOnUiThread(
                Action(lambda: self.component.ExpireSolution(True))
            )
        except Exception:
            # If the component is gone, the next loop iteration's
            # OnPingDocument() check will end the thread cleanly.
            pass


# ============================================================
# Component entry point
# ============================================================

def _sticky_key(component):
    return f"midi_osc_listener_{component.InstanceGuid}"


def _doc_close_handler_installed_key():
    return "midi_osc_listener_doc_close_installed"


def _install_doc_close_handler():
    """Register once: on any GH document removal, close every listener
    socket we know about. Belt-and-braces cleanup."""
    if sc.sticky.get(_doc_close_handler_installed_key()):
        return
    try:
        import Grasshopper
    except ImportError:
        return

    def _on_doc_removed(sender, args):
        for k in list(sc.sticky.keys()):
            if k.startswith("midi_osc_listener_") and k != _doc_close_handler_installed_key():
                listener = sc.sticky.get(k)
                if isinstance(listener, Listener):
                    listener.stop()
                sc.sticky.pop(k, None)

    Grasshopper.Instances.DocumentServer.DocumentRemoved += _on_doc_removed
    sc.sticky[_doc_close_handler_installed_key()] = True


def _ensure_listener(component, port, reset):
    key = _sticky_key(component)
    existing = sc.sticky.get(key)
    needs_restart = (
        existing is None
        or not isinstance(existing, Listener)
        or existing.port != port
        or reset
        or existing.stop_event.is_set()
    )
    if needs_restart:
        if isinstance(existing, Listener):
            existing.stop()
        listener = Listener(port, component)
        try:
            listener.start()
        except OSError as e:
            sc.sticky[key] = None
            raise RuntimeError(
                f"could not bind UDP :{port} — {e}. "
                "Toggle Reset, or pick a different Port."
            )
        sc.sticky[key] = listener
        return listener
    return existing


# Inputs from the component: Addresses, Port, Reset
# (these come in as Python variables of the same names)
_port = int(Port) if Port else 7000
_addresses = [str(a) for a in (Addresses or [])]
_reset = bool(Reset)

_install_doc_close_handler()
_listener = _ensure_listener(ghenv.Component, _port, _reset)

_state, _last, _err = _listener.snapshot()
Values = [float(_state.get(a, 0.0)) for a in _addresses]

if _err:
    Status = f":{_port} listening — last error: {_err}"
elif _last[0]:
    age_ms = int((time.monotonic() - _last[1]) * 1000)
    Status = f":{_port} listening — last {_last[0]} {age_ms}ms ago"
else:
    Status = f":{_port} listening — no messages yet"
