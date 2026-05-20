# Notes for Claude

Quick orientation for any Claude session opened against this repo.

## What lives here

This repo is "Gizmos" — a personal grab-bag of small self-contained
projects. There is no shared build system, no monorepo tooling, no CI
that runs across everything. Each subfolder stands alone.

Current contents:

- **Skill Trails** (root: `index.html`, `css/`, `js/`, `data/`,
  `README.md`) — static interactive tutorial graph. Open
  `index.html` in a browser, that's it. Unrelated to anything below.
- **midi-grasshopper/** — MIDI keyboard → Ableton Live →
  Grasshopper live-parameter control. Active project. See
  `midi-grasshopper/README.md` for setup.

When in doubt, work inside the relevant subfolder and leave the
other gizmos alone.

## Voice / style

I'm not a software engineering team. I'm one person who builds tools
to use. Write commit messages, docs, and code comments accordingly:

- Plain language, not corporate-speak. "Knob sweep is jittery" beats
  "Continuous controller value interpolation exhibits suboptimal
  smoothing characteristics".
- No marketing fluff in READMEs. Setup steps, what to expect, what
  to do when it breaks.
- Comments only when the *why* is non-obvious. Don't restate code.
- Small commits I can revert. Don't pile six unrelated changes into
  one commit just because they touched the same file.

## Working agreement

- See `WORKING.md` for the running journal on the active project.
- Don't push to `main` without me asking. Feature branches only.
- If something is genuinely ambiguous, ask before guessing. If it's
  a 30-second judgement call, just make the call and tell me what
  you picked.
