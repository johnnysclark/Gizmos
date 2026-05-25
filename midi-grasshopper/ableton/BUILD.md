# Building MidiToOSC.amxd from the .maxpat

You have a hand-authored Max patch (`MidiToOSC.maxpat`). To turn it
into a real Max for Live device (`.amxd`) you open it inside Ableton's
M4L editor and save it. Two minutes.

## Steps

1. **Open Ableton Live 12.** Drag a Max MIDI Effect from the Live
   browser onto any MIDI track. (Browser → Max for Live → Max MIDI
   Effect → drag onto track.) You now have a blank `.amxd` on that
   track.

2. **Open the M4L editor** by clicking the small edit (pencil) icon on
   the blank device. Max opens with an empty MIDI Effect template.

3. In Max: **File → Open**, then pick
   `midi-grasshopper/ableton/MidiToOSC.maxpat` from this repo.

4. The patch opens in a normal patcher window — not yet a Live device.
   **Select all** (⌘A), **Copy** (⌘C), then **switch to the empty M4L
   editor window** and **Paste** (⌘V). Everything lands on the M4L
   canvas next to (or replacing) the template `midiin`/`midiout`
   passthrough.

5. The default Max template has `midiin → midiout` wired together so
   MIDI continues down the Live chain. Leave that pair in place; this
   patch taps notes/CCs/bend/touch in parallel via `notein` etc., so
   the chain still passes through.

6. **File → Save As**, navigate to
   `midi-grasshopper/ableton/MidiToOSC.amxd`, save. Max writes the
   `.amxd` (this is the binary M4L container — Max produces it,
   we don't author it by hand).

7. Close the M4L editor. Back in Ableton, the device on the track is
   now your `MidiToOSC.amxd`. You can save it to your User Library
   too — drag the device header to the Live browser.

## What's in the patch

- `notein` → `prepend /note` and `prepend /velocity` → send to UDP
- `ctlin` → `sprintf set /cc/%ld` updates the prepend address; the
  CC value then fires through the `prepend /tmp` box. Result:
  `/cc/<n> <value>` for every CC.
- `bendin` → `prepend /bend`
- `touchin` → `prepend /aftertouch`
- All four streams fanned into a `t l l` that:
  - Sends to `udpsend 127.0.0.1 7000`
  - Updates the "last message" display
  - Blinks the LED for 100ms
- The `port` `live.numbox` (a real Live parameter, mappable!) sends
  `port <n>` to `udpsend` to change the destination port live.
- The `host 127.0.0.1` message box does the same for the host. Edit
  the message text to change destination IP.

## Renaming CC addresses

The default mapping is `CC#n → /cc/n`. To rename (e.g. CC#1 →
`/twist`) inside Max:

1. Disconnect the line from `ctlin`'s second outlet (ctl#) into the
   `sprintf` box.
2. Insert a `coll` object: `ctlin` outlet 1 → `coll mapping` left
   inlet → `coll` outlet → into `sprintf set %s` (with `%s` for a
   symbol, not `%ld`).
3. Double-click the `coll` and add entries:
   ```
   1, /twist;
   2, /taper;
   ```
   Unmapped CCs will produce no output — to keep the default
   fallback, route `coll`'s right outlet (the "not found" bang) back
   to the original `sprintf set /cc/%ld` chain.

A pre-built version of this with a `coll` is a future improvement;
the current patch keeps the default `/cc/n` for simplicity.

## Why we ship a .maxpat instead of a .amxd

`.amxd` is a binary Ableton container; producing one requires Max to
be running. The `.maxpat` is plain JSON, hand-authorable, and easy to
review in a diff. The one-time copy/paste/save in Max above is the
cost of going from text to binary.
