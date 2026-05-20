# Working notes

A running log of what's in flight. Newest at top.

## midi-grasshopper (active)

**Goal:** MIDI keyboard → Ableton Live 12 → Max for Live MIDI Effect
→ OSC/UDP (127.0.0.1:7000) → Grasshopper Python 3 ScriptEditor
listener → Rhino 8 viewport. Endpoint: I press a key, GH redraws
with <50ms perceived latency.

**Hardware:** M5 MacBook Pro, Apple Silicon, macOS. Rhino 8 for Mac,
GH ScriptEditor Python 3 (CPython, no pip in the component itself).
Ableton Live 12 Suite (Max for Live included).

**Build order (commits):**

1. OSC parser + encoder (`osc.py`) — pure, dependency-free,
   verifiable in isolation via `python3 osc.py` self-test
2. UDP listener module (`udp_listener.py`) — socket + parser glue,
   runnable standalone
3. GH component (`gh_listener.py`) — single-file script for the
   Grasshopper Python 3 ScriptEditor, inlines parser + listener
4. Fake sender (`test_osc_send.py`) — fires CCs and notes at the
   listener so the GH side is verifiable without Ableton
5. Max for Live device (`ableton/MidiToOSC.maxpat` + helper JS) —
   captures MIDI in Live, maps to OSC, sends to UDP target
6. Demo definition (`example.gh` build guide in README) — twist +
   taper tower driven by two CCs and a note range

**Decisions made so far:**

- OSC over UDP (not raw MIDI via IAC). Named addresses are nicer to
  map and debug than `(status, data1, data2)` triples.
- 30 Hz UI tick on the GH side. Faster makes Rhino chug, slower
  feels laggy on knob sweeps. Background thread drives
  `ExpireSolution(True)` — never touch the GH document from the
  socket thread directly.
- Float arguments only by default. CC values normalized to 0.0–1.0,
  velocity 0.0–1.0, pitch bend -1.0–1.0. Note number sent as int.
  Keeps the GH side from doing scale math.
- IAC Driver path is documented but not built. Switch to it if I
  ever drop M4L.

**Open questions:**

- Does GH ScriptEditor Python 3 reliably keep background threads
  alive across solutions? If not, the tick thread needs to be
  re-entrant.
- M4L `.amxd` is binary and saved from inside Live's device editor.
  I'll ship the `.maxpat` source and the wrapping step in the
  README; can't generate the `.amxd` from outside Live.

**Known gotchas:**

- macOS will silently drop UDP packets if the firewall flags
  `python3` or Rhino on first run. Allow both.
- Two GH listeners on the same port = silent failure. Disable old
  components before enabling new ones, or `lsof -i :7000` to find
  the holder.
- M4L devices have a load order — if the device opens before its
  MIDI source is enabled in Live, no MIDI flows through. Reorder
  the chain.
