// trails.js — Trail selector and highlighting

import { highlightTrail, clearHighlights } from './graph.js';

export function initTrails(data, cy) {
  const select = document.getElementById('trail-select');

  // Populate trail options
  data.trails.forEach((trail) => {
    const option = document.createElement('option');
    option.value = trail.id;
    option.textContent = trail.title;
    option.style.color = trail.color;
    select.appendChild(option);
  });

  // Handle trail selection
  select.addEventListener('change', () => {
    const trailId = select.value;
    if (!trailId) {
      clearHighlights(cy);
      return;
    }

    const trail = data.trails.find((t) => t.id === trailId);
    if (trail) {
      highlightTrail(cy, trail, trail.color);
    }
  });
}

export function buildLegend(data) {
  const legend = document.getElementById('legend');
  legend.innerHTML = data.categories
    .map(
      (c) => `<span class="legend-item">
      <span class="legend-dot" style="background: ${c.color}"></span>
      ${c.label}
    </span>`
    )
    .join('');
}
