"""UDP socket + OSC decode glue, runnable on its own.

Used as a dev/debug listener and as a reference for the Grasshopper
component (which inlines the same logic so it can run inside the
ScriptEditor with no imports beyond stdlib).

Run as a CLI to spy on incoming OSC:

    python3 udp_listener.py            # listens on 0.0.0.0:7000
    python3 udp_listener.py --port 7001
    python3 udp_listener.py --host 127.0.0.1 --port 7000
"""

import argparse
import socket
import threading
from typing import Callable

import osc


class OscListener:
    """Background-thread UDP listener that decodes OSC into a state dict.

    - Binds a UDP socket on construction. If the port is busy, surfaces
      the OSError so callers can act (don't swallow it — silent failure
      is the worst bug to debug here).
    - `state` is a `{address: [args] or scalar}` dict, guarded by a
      lock so the consumer (GH UI tick) can read without tearing.
    - `start()` spins up the receive loop; `stop()` releases the socket
      and joins the thread. Idempotent so we can call stop() from both
      component-disable and document-close paths.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 7000,
                 on_message: Callable[[str, list], None] | None = None):
        self.host = host
        self.port = port
        self._on_message = on_message
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.state: dict[str, object] = {}
        self.last_error: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # SO_REUSEADDR so a quick restart doesn't hit TIME_WAIT on macOS
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        # 100ms recv timeout so the stop flag is checked promptly
        s.settimeout(0.1)
        self._sock = s
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="OscListener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        s = self._sock
        self._sock = None
        if s is not None:
            try:
                s.close()
            except OSError:
                pass
        t = self._thread
        self._thread = None
        if t is not None and t.is_alive():
            t.join(timeout=1.0)

    def get(self, address: str, default=None):
        with self._lock:
            return self.state.get(address, default)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self.state)

    def _run(self) -> None:
        while not self._stop.is_set():
            sock = self._sock
            if sock is None:
                return
            try:
                data, _addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                # socket closed under us during shutdown
                return
            try:
                address, args = osc.decode(data)
            except Exception as e:  # noqa: BLE001 — record and keep going
                self.last_error = f"decode failed: {e!r}"
                continue
            # Store the scalar if there's exactly one arg, else the list.
            # GH side mostly wants a number, so this avoids unwrapping
            # at every read site.
            value = args[0] if len(args) == 1 else args
            with self._lock:
                self.state[address] = value
            if self._on_message is not None:
                try:
                    self._on_message(address, args)
                except Exception as e:  # noqa: BLE001
                    self.last_error = f"on_message failed: {e!r}"


def _cli() -> None:
    p = argparse.ArgumentParser(description="OSC UDP listener (debug)")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=7000)
    args = p.parse_args()

    def show(addr: str, vals: list) -> None:
        print(f"{addr}  {vals}")

    listener = OscListener(args.host, args.port, on_message=show)
    listener.start()
    print(f"listening on {args.host}:{args.port}  (Ctrl-C to quit)")
    try:
        # Block the main thread without busy-waiting
        while True:
            listener._thread.join(timeout=1.0)  # type: ignore[union-attr]
            if listener._thread is None or not listener._thread.is_alive():
                break
    except KeyboardInterrupt:
        print()
    finally:
        listener.stop()
        print("listener stopped")


if __name__ == "__main__":
    _cli()
