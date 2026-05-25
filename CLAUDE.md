# Gizmos

This repo is a personal collection of small, unrelated tools and toys.
There's no monorepo build, no shared lockfile, no overarching theme.
Each thing lives in its own folder and stands on its own.

## What's currently in here

**`/` (repo root) — Skill Trails**
A static, vanilla-JS website that displays design/CAD tutorials as an
interactive graph (Cytoscape). No build step. Open `index.html` in a
browser or run `python3 -m http.server`. Data lives in
`data/tutorials.json`. See the root `README.md` for the project's
own write-up.

**`midi-grasshopper/` — MIDI → Ableton → Grasshopper bridge**
Lets you drive Grasshopper parameters in Rhino 8 with a MIDI keyboard
via Ableton Live, OSC, and a pasteable Python script for the GH
ScriptEditor. Completely independent of the Skill Trails app. See
`midi-grasshopper/README.md`.

These two share a repository but otherwise have nothing to do with
each other. If a third gizmo lands, it gets its own top-level folder
the same way.

## Working style

- **Small, verifiable commits.** Each commit should leave the
  subproject in a state that's testable. The midi-grasshopper folder
  followed a chain: OSC encoder → standalone test → GH listener →
  M4L device → demo recipe → README, each independently checkable.
- **No external developer team.** Code is written to be read again in
  a few months by the same person who wrote it. Comments only when
  the *why* isn't obvious from the code; never explaining the *what*.
- **Self-contained subprojects.** Don't introduce shared utilities
  across subprojects. Don't add a root-level `package.json` or
  `requirements.txt`. If two gizmos accidentally share something,
  copy-paste is fine.
- **Honest about platform constraints.** Both Max for Live `.amxd`
  and Grasshopper `.gh` files are binary formats produced by their
  host apps. We ship source-form artefacts (`.maxpat`, recipe `.md`)
  and a short ritual to finalize, rather than pretending to author
  binaries we can't actually produce here.

## Conventions

- Default to lowercase folder names with hyphens.
- A subproject's README is the entry point. Setup time target: under
  10 minutes on a fresh machine. If it can't be that fast, the README
  should say why up front.
- Each subproject's README owns its own troubleshooting section.
  Don't centralize troubleshooting at the repo level — gizmos have
  almost nothing in common.

## Live notes

`WORKING.md` is a running journal — what's in progress, what's
known-broken, what to come back to. It is for the human writing
this; agents reading it should treat it as the latest ground truth
about subproject state, ahead of any individual subproject's docs.
