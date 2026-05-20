# midi-grasshopper

Play a MIDI keyboard into Ableton Live, drive Grasshopper parameters
in real time, watch Rhino redraw. Target: press a key or twist a
knob, GH updates with under 50 ms perceived latency.

## Architecture

```
MIDI keyboard
    ↓ USB
Ableton Live 12  (MIDI Effect on the keyboard's track)
    ↓
MidiToOSC.amxd  (Max for Live device — this repo)
    ↓ UDP/OSC, 127.0.0.1:7000
gh_listener.py  (Grasshopper Python 3 ScriptEditor component)
    ↓ component outputs
your Grasshopper definition
    ↓
Rhino viewport
```

The wire format is OSC over UDP. Addresses are named (`/cc/1`,
`/note/on`, `/pitchbend`, etc.) so the GH side never has to do MIDI
byte math.

## What's in this folder

| File | Role |
|---|---|
| `osc.py` | Pure-Python OSC 1.0 encode/decode. Self-tests via `python3 osc.py`. |
| `udp_listener.py` | UDP-socket-on-a-thread wrapper around `osc.py`. Runnable standalone as a debug spy. |
| `gh_listener.py` | Single-file GH ScriptEditor Python 3 component. Inlines the parser, manages two background threads, drives `ExpireSolution` at 30 Hz. |
| `test_osc_send.py` | Fake OSC sender. One-shot, sweep, or full demo set. Verifies the GH side without Ableton. |
| `ableton/MidiToOSC.maxpat` | Max patcher source for the M4L MIDI Effect device. Wrap into `.amxd` inside Live. |
| `ableton/midi_to_osc.js` | Node-for-Max script the patcher loads. Encodes OSC and does the UDP send. |

## Prerequisites

- macOS, Apple Silicon (built and tested on M5 MacBook Pro)
- Rhino 8 for Mac with Grasshopper (ScriptEditor Python 3 is the
  CPython component — not IronPython)
- Ableton Live 12 Suite (so you have Max for Live). Standard
  without M4L? Skip to the [IAC fallback](#iac-fallback-no-m4l).
- Python 3 on your $PATH for the dev/test scripts. Anything 3.9+.
- No GH plugins. No pip installs.

## Quick start (under 10 min)

### 1. Verify the GH side first (5 min)

This proves Rhino can receive OSC before you touch Ableton.

1. Open Rhino 8. Type `Grasshopper`.
2. Drag a **Python 3 Script** component (ScriptEditor flavour) onto
   the canvas.
3. Right-click → **Edit Component**. Add inputs and outputs:
   - Inputs: `addresses` (list, type Generic),
     `port` (item, type Integer),
     `enable` (item, type Boolean)
   - Outputs: `values`, `status`
4. Open `gh_listener.py` here, paste the whole file into the script
   body.
5. Back on the canvas: feed `addresses` a panel containing one
   address per line, e.g.:
   ```
   /cc/1
   /cc/2
   /note/last
   ```
   Wire a Boolean Toggle (set to `True`) into `enable`. Leave
   `port` empty (defaults to 7000).
6. The `status` output should read `listening on :7000 | 0 pkts`.
7. From a terminal in this folder:
   ```bash
   python3 test_osc_send.py /cc/1 0.5
   python3 test_osc_send.py /note/last 60
   python3 test_osc_send.py --sweep /cc/1 --duration 3
   ```
   You should see the matching `values` outputs update live and
   the packet counter climb.

If that all works, the GH half is done.

### 2. Build the Max for Live device (3 min)

The `.amxd` file is binary and only Live can author it, so we ship
the patcher source. Wrap it like this:

1. In Live, create a new MIDI track on your keyboard's input.
2. Drag a stock **Max MIDI Effect** device onto the track (Max for
   Live → Max MIDI Effect → Max MIDI Effect.amxd).
3. Click the **Edit** (pencil) icon on the device. Max for Live's
   editor opens.
4. **File → Open**, point at `ableton/MidiToOSC.maxpat`. Copy all
   objects (Cmd-A, Cmd-C) into the empty M4L device patcher, paste
   (Cmd-V). Connect the `[midiin]` → `[midiout]` pair if it didn't
   carry the link.
5. Copy `ableton/midi_to_osc.js` next to where you'll save the
   `.amxd` (Live keeps adjacent JS files with the device).
6. **File → Save As** → `MidiToOSC.amxd`. Live will reload the
   device.

Sanity check: open the device, click the **status** message
button. The `target` comment should read `127.0.0.1:7000`. Play a
note or wiggle a knob — the LED next to the displays should pulse
green.

### 3. Wire it together

1. On the MIDI track, arm record / enable monitor so MIDI flows
   into the device.
2. The track's **MIDI From** should be your keyboard. Drop the
   MidiToOSC device above any instrument (or leave the chain
   instrumentless if you only want the OSC).
3. Make sure the GH `gh_listener.py` component is `enable = True`.
4. Press C4 (note number 60). The `status` output should tick up
   packet count. The `/note/last` value should read `60`.

You're done.

## example.gh — twist + taper tower demo

I can't ship a binary `.gh` from outside Rhino. Here's the
30-second build:

1. **Inputs (panels or sliders for testing):**
   - `gh_listener.py` component configured with
     `addresses = ["/cc/1", "/cc/2", "/note/last"]`
   - Three `List Item` components, indices 0/1/2, pulling from
     `values`
2. **CC1 → twist:** `List Item 0` (value 0..1) → multiply by 360 →
   feed into `Rotate` angle.
3. **CC2 → taper:** `List Item 1` (value 0..1) → remap to 0.2..1.0
   → multiply each floor's profile radius by this scalar (lerp
   between top and bottom).
4. **Note → height/floor count:** `List Item 2` (int note number)
   → subtract 48 → clamp 1..36 → use as number of floors.
5. Stack scaled, rotated polygon profiles into a `Loft` →
   `Brep`. Bake when happy.

Test it without your keyboard:

```bash
python3 test_osc_send.py --demo
```

That walks both CCs through smooth sweeps and steps through a note
range, so you can see the tower twist, taper, and grow before
plugging in any hardware.

## Troubleshooting

**`bind failed on :7000: [Errno 48] Address already in use`**
Another process holds the port. Find it:
```bash
lsof -i :7000
```
Usually a stale GH component from a previous Rhino session. Toggle
`enable = False` on that component or close the old document. If
Rhino crashed without releasing the socket, restart Rhino.

**GH `status` shows `listening` but packet count stays at 0**
- macOS firewall is silently dropping packets. System Settings →
  Network → Firewall → allow incoming for `python3` and Rhino.
- Wrong port mismatch. `gh_listener.py` `port` input vs the
  `port 7000` message in the M4L device — they must match.

**M4L device loads but no MIDI gets through**
- The device sits in the MIDI chain. If MIDI source isn't enabled
  (track armed / monitor on), nothing flows. Toggle the track's
  monitor to `In` while testing.
- Load order: M4L devices sometimes init their Node script after
  the first MIDI message. Click the device's `status` message
  button — that forces the script to acknowledge it's alive.

**Restart cycle**
Both orders (restart Rhino first, then Live; restart Live first,
then Rhino) should recover cleanly. The listener uses
`SO_REUSEADDR` so TIME_WAIT doesn't bite. If you hit a stuck port
after a crash, `lsof -i :7000` then `kill <pid>` of the offender.

**Jitter / stutter on knob sweep**
The listener caps ExpireSolution at 30 Hz. If knob sweeps still
feel chunky, check Rhino's solve time — a heavy GH definition
spends >33 ms per solve and starts dropping frames. Profile the
downstream definition, not the listener.

## IAC fallback (no M4L)

If you're on Live Standard without Max for Live, swap the device
half for the macOS IAC Driver and read MIDI directly in
Grasshopper:

1. **macOS** → open `Audio MIDI Setup`. Window → Show MIDI Studio.
   Double-click the IAC Driver, tick **Device is online**, add a
   bus called e.g. `GH`.
2. **Ableton** → on the MIDI track, set **MIDI To → IAC Driver
   (GH)**. Optionally route through a Pitch / Velocity device for
   shaping.
3. **Grasshopper** → in `gh_listener.py`, swap the socket-based
   listener for a `python-rtmidi` listener. This *does* require a
   pip install on the system Python that Rhino's ScriptEditor
   uses, which is annoying enough that I haven't built it yet.
   File an issue here when you actually need it and I'll add a
   `gh_listener_iac.py` variant.

Named OSC addresses are nicer to map and debug than raw MIDI
status bytes, so unless M4L is unavailable, stay on the OSC path.

## Out of scope

- Recording / automation playback in Ableton (handled natively;
  this device just gates MIDI → OSC, no state).
- Bidirectional sync (Rhino → Ableton). One way only.
- Windows / Linux. Tested only on macOS Apple Silicon.
