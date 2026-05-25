# WORKING

Running journal of what's in progress, what's broken, what to come
back to. Updated as I go. The most recent stuff lives at the top.

---

## midi-grasshopper — first cut landed (2026-05-25)

### What's working

- `test_osc_send.py` — encoder + parser round-trips on the selftest.
  Cross-verified against the listener's decoder on a bunch of edge
  cases including the 4-byte-aligned address bug I hit during the
  encoder build.
- `gh_listener.py` — daemon-threaded UDP socket inside a Rhino 8
  Python 3 ScriptEditor component. Rate-limited ExpireSolution via
  `Rhino.RhinoApp.InvokeOnUiThread`. SO_REUSEADDR so port-in-use
  doesn't bite on restart. Document-removed event handler cleans up
  on close. End-to-end tested headless (sender + decoder) — 118
  messages over 1s sweep, last value 127.0 as expected.
- `ableton/MidiToOSC.maxpat` — hand-authored Max patch. JSON
  validates. Needs the one-time copy/paste/Save-As ritual in M4L
  editor to become `.amxd` — BUILD.md walks through it.
- `example/DEFINITION.md` — recipe for a parametric tower driven by
  two CCs + one note.
- `README.md` — five-step setup, IAC Driver fallback for Standard
  Live users.

### What I haven't verified yet (need the Mac to do it)

- The `.maxpat` actually opens cleanly in the M4L editor. I built it
  by hand from the Max 8 JSON schema; I'm fairly confident it parses
  (it round-trips through `json.load`), but Max may reject specific
  object combinations I didn't get right. First-run check: open the
  patch, look for red boxes (= unrecognized objects) or disconnected
  lines, fix them.
- The `host 127.0.0.1` message box pattern actually initializes
  `udpsend` on first run. There's a folk-wisdom note in the
  troubleshooting section to click it once if no UDP goes out.
  Confirm or remove that note after running it.
- The `live.toggle` LED actually blinks. The patch's blink chain is
  toggle → delay 100 → message "0" → back into toggle. Standard idiom
  but I haven't watched it run.
- The end-to-end <50ms latency budget. Theoretically: MIDI in to
  Live (~1ms) + Live device processing (~1ms) + UDP localhost
  (<1ms) + GH socket receive + ExpireSolution (~1ms) + solve. The
  solve is the variable — Loft is expensive. Demo recommends
  Levels=12; might need to lower for snappy feel.

### Open questions to revisit

- Should the listener emit on EVERY message even if value didn't
  change? Right now it expires the solution only when the value
  changes, which dedupes the steady stream of CCs at rest (M4L
  doesn't emit unchanged CCs anyway, but some controllers do). This
  is the right default but worth a double-check.
- A user-editable CC→OSC-address mapping table is currently
  documented as a manual coll insertion. If I find I'm renaming
  CCs in practice, build a V2 of the patch with the coll wired in
  by default.
- Velocity is emitted separately on `/velocity` but I never use it
  in the demo. Maybe drop the velocity prepend chain if it stays
  unused.

### Known shape decisions

- `.maxpat` instead of `.amxd` is deliberate; .amxd needs Max to
  produce. See `ableton/BUILD.md`.
- Demo ships as a markdown recipe instead of a `.gh` file for the
  same reason — .gh needs Rhino. Recipe is also easier to keep in
  sync with the listener's input shape.

---

## skill-trails — quiet (no recent work)

The static tutorial site. Nothing in progress here. If I come back
to it: data lives in `data/tutorials.json`, no build step.
