# Skill Trails

An interactive skills tutorials website inspired by [GSAPP Skill Trails](https://skilltrails.gsapp.org/). Tutorials are shown as interconnected nodes on a visual graph, organized into curated learning paths ("trails").

## Features

- **Interactive node graph** — Pan, zoom, click tutorials on a visual map
- **Tutorial detail panel** — Step-by-step content with Markdown and video support
- **Curated trails** — Select a learning path to highlight related tutorials
- **Search** — Filter tutorials by name or category
- **Category legend** — Color-coded by skill area
- **Fully static** — No build step, just HTML/CSS/JS

## Getting Started

Open `index.html` in a browser, or serve locally:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Customizing Content

Edit `data/tutorials.json` to add your own tutorials, edges, trails, and categories. The data model is:

- **categories** — Skill areas with colors
- **tutorials** — Nodes with title, description, steps (markdown or video), position
- **edges** — Connections between tutorials (prerequisite relationships)
- **trails** — Curated sequences of tutorials

## Tech Stack

- Vanilla HTML/CSS/JS (ES modules)
- [Cytoscape.js](https://js.cytoscape.org/) for the interactive graph
- [marked.js](https://marked.js.org/) for Markdown rendering
