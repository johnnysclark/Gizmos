# Demo definition: MIDI-controlled tower

Builds a parametric tower (twist + taper) driven by two CCs and one
note from your MIDI keyboard, via the OSC listener.

Open Rhino 8 + Grasshopper. Then follow the recipe below; should take
about 5 minutes once `gh_listener.py` is ready.

## Components to drop

Listed left-to-right, top-to-bottom.

### 1. Listener (the heart)

- **C#/Python Script** component (the new ScriptEditor one) — set the
  language to **Python 3**.
- Right-click the component → **Manage Inputs** and add:
  - `Addresses` — type: List of Strings
  - `Port` — type: Integer
  - `Reset` — type: Boolean
- **Manage Outputs**:
  - `Values` — type: List of Numbers
  - `Status` — type: String (Item Access)
- Open the script editor on the component and **paste the entire
  contents of `gh_listener.py`** into it. Save.
- Wire these in:
  - A **Panel** containing three lines:
    ```
    /note
    /cc/1
    /cc/2
    ```
    Right-click the panel → uncheck "Multiline Data" so each line is
    one item. Wire it to `Addresses`.
  - A **Number** component set to `7000` → `Port`.
  - A **Boolean Toggle** → `Reset` (keep at False; flip momentarily
    if the listener needs to rebind).

You should already see `Status` reading `:7000 listening — no messages
yet`. If you run `python3 ../test_osc_send.py sweep` from a terminal,
`Status` should update and `Values` index 1 should sweep from 0 to
127. That confirms the listener works in isolation.

### 2. Pick the three values out of the list

Three **List Item** components on the `Values` output:
- `i = 0` → `Note` (raw MIDI pitch)
- `i = 1` → `CC1` (0–127)
- `i = 2` → `CC2` (0–127)

### 3. Remap MIDI ranges to useful ranges

Three **Remap Numbers** components:
- `Note` → source `Domain 36 To 84` → target `Domain 10 To 50` → `Height`
- `CC1`  → source `Domain 0 To 127` → target `Domain 0 To 6.2832` → `TwistRad`
  (radians; 0–2π = 0–360°)
- `CC2`  → source `Domain 0 To 127` → target `Domain 0.2 To 1.0` → `TaperTop`

You make a `Domain A To B` with the **Construct Domain** component
(two number inputs).

### 4. Tower geometry

- Two number sliders to taste: `Radius` (default `5`) and `Levels`
  (integer, default `12`).
- A **Range** component: `Domain 0 To 1`, `Steps = Levels` → list of
  `Levels+1` t-values from 0 to 1.
- For each t:
  - `z = t * Height` — **Multiplication** component.
  - `r = Radius * Lerp(1, TaperTop, t)` — easiest as
    `Radius * (1 - t + t*TaperTop)`; build with **Subtraction**,
    **Multiplication**, **Addition**.
  - `angle = t * TwistRad` — **Multiplication**.
  - `plane`: **Construct Plane** with origin `(0, 0, z)` and Z-axis
    rotation by `angle`. Easiest: build a base XY plane (origin at
    `0,0,z`), then **Rotate Plane** about its Z by `angle`.
  - `circle = Circle (plane, r)` — **Circle CNR** with center =
    plane.Origin, normal = plane.ZAxis, radius = r.
- **Loft** the list of circles → tower surface.
- Optionally **Cap Holes** → solid tower.

### 5. Wire it up and play

Hit Run on the listener if it isn't already. In Ableton, drop
`MidiToOSC.amxd` on a MIDI track that receives your keyboard input.
Play:

- **Press C2 (MIDI 36)** → tower goes short (height 10).
- **Press C6 (MIDI 84)** → tower goes tall (height 50).
- **Twist CC#1 knob** → tower twists 0–360°.
- **Twist CC#2 knob** → top tapers from cone to cylinder.

If your knobs aren't CC#1 / CC#2, look in `MidiToOSC.maxpat`'s
last-message display while twisting — that tells you what OSC
addresses your hardware actually sends, and you adjust the panel
strings to match.

## Troubleshooting

- **Status reads `no messages yet`** → either Ableton isn't routing
  MIDI to the M4L device, or the device's port doesn't match (check
  the `port` numbox in M4L = 7000; check the Panel feeding Listener's
  Port = 7000).
- **Values stop updating** → check the M4L device's LED; if it isn't
  blinking on your input, MIDI isn't reaching the device (check
  Live's track input arming, MIDI From settings).
- **Listener errors with "could not bind UDP :7000"** → another
  process holds the port (a stale Rhino, another listener). Flip the
  `Reset` toggle, or change `Port` (and the M4L numbox to match).
- **Tower flickers / stutters on a CC sweep** → expected behaviour;
  the listener rate-limits redraws to ~30 Hz, but the loft is heavy.
  Lower `Levels` to ~8 for smoother sweeps.
