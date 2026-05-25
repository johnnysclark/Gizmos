# midi-grasshopper

Play a MIDI keyboard into Ableton Live and have notes/CCs drive
Grasshopper parameters in Rhino 8 in real time. End-to-end target:
press a key or twist a knob → a GH number updates → Rhino redraws,
under 50ms.

```
MIDI keyboard
   ↓
Ableton Live 12
   ↓ (M4L MIDI Effect: MidiToOSC.amxd)
OSC / UDP  ─────  127.0.0.1:7000
   ↓
Grasshopper Python 3 component (gh_listener.py)
   ↓
your GH definition → Rhino viewport
```

## What's in here

- `gh_listener.py` — paste-it-in script for a Rhino 8 ScriptEditor
  Python 3 component. Holds the UDP socket, decodes OSC, exposes a
  list of float outputs.
- `test_osc_send.py` — standalone stdlib OSC sender. Verifies the GH
  side end-to-end without Ableton.
- `ableton/MidiToOSC.maxpat` + `ableton/BUILD.md` — the M4L MIDI
  Effect device source, and the two-minute ritual to turn it into a
  real `.amxd`.
- `example/DEFINITION.md` — recipe to build a demo parametric tower
  driven by your keyboard.

## Setup (under 10 minutes on a fresh machine)

You need: macOS, Rhino 8, Ableton Live 12 Suite (the **Suite** edition
ships M4L; Standard does not — if you're on Standard see the IAC
fallback below).

### 1. Verify the listener works in isolation (1 min)

Open a terminal in this folder:

```sh
python3 test_osc_send.py selftest
```

You should see `selftest passed.`. That confirms the OSC parser is
healthy on your Python.

### 2. Wire the listener into Grasshopper (3 min)

1. Open Rhino 8, type `Grasshopper`.
2. Drop a **C#/Python Script** component on the canvas, switch its
   language to **Python 3**.
3. Right-click → Manage Inputs:
   - `Addresses` (List of Strings)
   - `Port` (Integer)
   - `Reset` (Boolean)
4. Right-click → Manage Outputs:
   - `Values` (List of Numbers)
   - `Status` (String)
5. Open the script editor on the component and paste the entire
   contents of `gh_listener.py` in.
6. Wire a Panel `["/cc/1"]` to `Addresses`, a Number `7000` to
   `Port`, and a Boolean Toggle to `Reset`. The component's `Status`
   should read `":7000 listening — no messages yet"`.

Now from a terminal:

```sh
python3 test_osc_send.py sweep
```

`Status` updates to show `/cc/1 N ms ago`, and `Values` index 0
sweeps from 0 to 127. If you see that, the GH side is done. Ableton
hasn't been touched yet.

### 3. Build and load the M4L device (3 min)

Follow `ableton/BUILD.md`. End state: a `MidiToOSC.amxd` sitting on a
MIDI track in your Live set.

### 4. Route MIDI in Ableton (2 min)

1. On the MIDI track holding the device: set **MIDI From** to your
   keyboard, set the track input monitor to **In**, arm the track.
2. Play a note. The LED on the M4L device should blink and the
   "last message" box should show `/note <pitch>`.
3. In Grasshopper, add `/note` to your Panel and you should see the
   pitch number coming through.

### 5. (Optional) Build the demo tower

Follow `example/DEFINITION.md`. About 5 minutes of clicking once the
listener is wired.

## IAC Driver fallback (no Max for Live needed)

If you're on Ableton Live 12 **Standard** (or Suite without M4L
installed), use macOS's built-in virtual MIDI bus to route MIDI to a
Python process that translates to OSC. This is less elegant than the
M4L device — there's no per-CC mapping UI — but it works.

1. Open **Audio MIDI Setup** (`/Applications/Utilities/`).
2. Window menu → **Show MIDI Studio**.
3. Double-click **IAC Driver**. Tick **Device is online**. Make sure
   there's a port named `Bus 1`.
4. In Ableton: route the MIDI track's **MIDI To** → **IAC Driver
   (Bus 1)**.
5. Run a tiny Python bridge (not included in this repo as a finished
   script — sketch below). You need `python-rtmidi` for MIDI input:

   ```sh
   pip3 install python-rtmidi
   ```

   ```python
   # iac_bridge.py — read MIDI from IAC Bus 1, send OSC to :7000
   import rtmidi, socket, struct, time
   def osc_msg(addr, val):
       def pad4(b): return b + b"\x00" * ((4 - len(b) % 4) % 4)
       return pad4(addr.encode() + b"\x00") + pad4(b",f\x00") + struct.pack(">f", float(val))
   sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   midi = rtmidi.MidiIn(); midi.open_port(0)  # IAC Bus 1
   while True:
       msg = midi.get_message()
       if msg is None: time.sleep(0.001); continue
       (data, _) = msg
       status, a, b = data
       hi = status & 0xF0
       if hi == 0x90 and b > 0:     # note on
           sock.sendto(osc_msg("/note", a), ("127.0.0.1", 7000))
       elif hi == 0xB0:             # CC
           sock.sendto(osc_msg(f"/cc/{a}", b), ("127.0.0.1", 7000))
       elif hi == 0xE0:             # pitch bend (14-bit)
           sock.sendto(osc_msg("/bend", (b << 7) | a), ("127.0.0.1", 7000))
       elif hi == 0xD0:             # channel aftertouch
           sock.sendto(osc_msg("/aftertouch", a), ("127.0.0.1", 7000))
   ```

   The GH listener doesn't change — same OSC, same port. Only the
   sender swaps from M4L to this Python bridge.

## Troubleshooting

**`Status` reads `no messages yet` and never updates.**
The M4L device isn't sending, or it's sending to the wrong port.
Open the device, watch the LED while you play. If LED doesn't
blink, MIDI isn't reaching the device — check the Live track is
armed and has the right MIDI input. If the LED blinks, check the
`port` numbox = 7000 and the GH `Port` input = 7000.

**`could not bind UDP :7000`** in the GH component.
Something else holds the port: another Rhino, another listener, or
a previous run that didn't clean up. Flip `Reset` on the component,
or pick a different `Port` (and match it in the M4L device).

**MIDI keeps passing through the M4L device but no OSC goes out.**
The patch's `udpsend` may not have actually opened a socket — on
some setups it needs a sentinel `host 127.0.0.1` message to
initialize. Click the `host 127.0.0.1` message box once in the M4L
editor to fire it.

**The tower stutters when you sweep a CC.**
The listener already rate-limits ExpireSolution to ~30Hz. The
stutter is downstream — Loft is expensive. Reduce the number of
levels in the demo, or simplify the geometry.

**Restart-order zombies.**
Killing and restarting Rhino while Ableton is still streaming is
fine — `SO_REUSEADDR` on the listener socket means the bind always
succeeds on restart, even before the previous socket's TIME_WAIT
expires. Killing Ableton has no impact on the listener (it just
stops receiving messages).

## Architecture notes

- **OSC over UDP, not OSC over TCP**: UDP suits the low-latency,
  best-effort nature of live performance. Drop a packet, you drop a
  CC sample — the next one arrives 5ms later anyway.
- **Plain messages, no bundles**: M4L's `udpsend` emits plain OSC
  messages. The listener rejects bundles. Keeps the parser tiny.
- **Single-direction**: GH never talks back. If you want Ableton
  Live → display GH state, that's a separate problem (and out of
  scope for this gizmo).
- **No external Python deps in GH**: the ScriptEditor component
  ships with stdlib + pythonnet bridge to .NET. We use stdlib for
  the socket and pythonnet for `Rhino.RhinoApp.InvokeOnUiThread`.
