// app.js — Application entry point

import { createGraph, filterBySearch, clearHighlights } from './graph.js';
import { initSidebar, openSidebar, closeSidebar } from './sidebar.js';
import { initTrails, buildLegend } from './trails.js';

async function init() {
  // Load data
  const res = await fetch('data/tutorials.json');
  const data = await res.json();

  // Build tutorial lookup
  const tutorialMap = {};
  data.tutorials.forEach((t) => (tutorialMap[t.id] = t));

  // Initialize sidebar
  initSidebar({
    onNavigate: (tutorialId) => {
      const tutorial = tutorialMap[tutorialId];
      if (tutorial) {
        openSidebar(tutorial, data);
        // Select node in graph
        cy.nodes().removeClass('selected-node');
        const node = cy.getElementById(tutorialId);
        if (node.length) {
          node.addClass('selected-node');
          cy.animate({ center: { eles: node }, duration: 300 });
        }
      }
    },
  });

  // Initialize graph
  const container = document.getElementById('graph-container');
  const cy = createGraph(container, data, {
    onNodeClick: (nodeId) => {
      const tutorial = tutorialMap[nodeId];
      if (tutorial) {
        openSidebar(tutorial, data);
      }
    },
  });

  // Initialize trails and legend
  initTrails(data, cy);
  buildLegend(data);

  // Search
  const searchInput = document.getElementById('search-input');
  let searchTimeout;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      const query = searchInput.value.trim();
      // Reset trail selector when searching
      document.getElementById('trail-select').value = '';
      clearHighlights(cy);
      filterBySearch(cy, query);
    }, 150);
  });

  // Zoom controls
  document.getElementById('zoom-in').addEventListener('click', () => {
    cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  });

  document.getElementById('zoom-out').addEventListener('click', () => {
    cy.zoom({ level: cy.zoom() / 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  });

  document.getElementById('zoom-fit').addEventListener('click', () => {
    cy.animate({ fit: { padding: 60 }, duration: 300 });
  });
}

init();
