// graph.js — Cytoscape.js graph initialization and rendering

const DIFFICULTY_SIZE = {
  beginner: 40,
  intermediate: 50,
  advanced: 55,
};

const DIFFICULTY_BORDER = {
  beginner: 2,
  intermediate: 3,
  advanced: 4,
};

export function createGraph(container, data, { onNodeClick }) {
  const categoryMap = {};
  data.categories.forEach((c) => (categoryMap[c.id] = c));

  const nodes = data.tutorials.map((t) => ({
    data: {
      id: t.id,
      label: t.title,
      category: t.category,
      color: categoryMap[t.category]?.color || '#6c8aff',
      difficulty: t.difficulty,
      size: DIFFICULTY_SIZE[t.difficulty] || 45,
      borderWidth: DIFFICULTY_BORDER[t.difficulty] || 2,
    },
    position: t.position ? { x: t.position.x * 1.2, y: t.position.y * 1.2 } : undefined,
  }));

  const edges = data.edges.map((e, i) => ({
    data: {
      id: `e${i}`,
      source: e.source,
      target: e.target,
    },
  }));

  const cy = cytoscape({
    container,
    elements: { nodes, edges },
    style: [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          width: 'data(size)',
          height: 'data(size)',
          'background-color': 'data(color)',
          'background-opacity': 0.15,
          'border-width': 'data(borderWidth)',
          'border-color': 'data(color)',
          color: '#e4e6f0',
          'font-size': '11px',
          'font-family': "'Inter', -apple-system, sans-serif",
          'font-weight': 500,
          'text-valign': 'bottom',
          'text-halign': 'center',
          'text-margin-y': 8,
          'text-wrap': 'wrap',
          'text-max-width': '90px',
          'text-outline-color': '#0f1117',
          'text-outline-width': 2,
          'text-outline-opacity': 0.8,
          'transition-property': 'background-opacity, border-color, opacity, width, height',
          'transition-duration': '0.2s',
          'overlay-padding': 6,
        },
      },
      {
        selector: 'node:active',
        style: {
          'overlay-opacity': 0,
        },
      },
      {
        selector: 'node.hover',
        style: {
          'background-opacity': 0.3,
          width: (ele) => ele.data('size') + 6,
          height: (ele) => ele.data('size') + 6,
        },
      },
      {
        selector: 'node.selected-node',
        style: {
          'background-opacity': 0.4,
          'border-width': 4,
          width: (ele) => ele.data('size') + 8,
          height: (ele) => ele.data('size') + 8,
        },
      },
      {
        selector: 'node.dimmed',
        style: {
          opacity: 0.15,
        },
      },
      {
        selector: 'node.trail-highlighted',
        style: {
          opacity: 1,
          'background-opacity': 0.3,
          'border-width': 4,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#2e3348',
          'target-arrow-color': '#2e3348',
          'target-arrow-shape': 'triangle',
          'arrow-scale': 0.8,
          'curve-style': 'bezier',
          opacity: 0.6,
          'transition-property': 'line-color, target-arrow-color, opacity, width',
          'transition-duration': '0.2s',
        },
      },
      {
        selector: 'edge.dimmed',
        style: {
          opacity: 0.08,
        },
      },
      {
        selector: 'edge.trail-highlighted',
        style: {
          opacity: 1,
          width: 2.5,
          'line-color': '#6c8aff',
          'target-arrow-color': '#6c8aff',
        },
      },
    ],
    layout: {
      name: 'preset',
      fit: true,
      padding: 60,
    },
    minZoom: 0.3,
    maxZoom: 3,
    wheelSensitivity: 0.3,
    boxSelectionEnabled: false,
  });

  // If any nodes lack positions, run a force-directed layout on them
  const unpositioned = cy.nodes().filter((n) => !n.position() || (n.position().x === 0 && n.position().y === 0 && n.data('id') !== 'rhino-basics'));
  if (unpositioned.length > 0) {
    cy.layout({
      name: 'cose',
      fit: true,
      padding: 60,
      nodeRepulsion: () => 8000,
      idealEdgeLength: () => 120,
      animate: false,
    }).run();
  }

  // Fit with padding
  cy.fit(undefined, 60);

  // Node hover
  cy.on('mouseover', 'node', (e) => {
    e.target.addClass('hover');
    container.style.cursor = 'pointer';
  });

  cy.on('mouseout', 'node', (e) => {
    e.target.removeClass('hover');
    container.style.cursor = 'grab';
  });

  // Node click
  cy.on('tap', 'node', (e) => {
    const nodeId = e.target.data('id');
    cy.nodes().removeClass('selected-node');
    e.target.addClass('selected-node');
    onNodeClick(nodeId);
  });

  // Click background to deselect
  cy.on('tap', (e) => {
    if (e.target === cy) {
      cy.nodes().removeClass('selected-node');
    }
  });

  return cy;
}

export function highlightTrail(cy, trail, trailColor) {
  const tutorialSet = new Set(trail.tutorials);

  cy.batch(() => {
    // Dim everything
    cy.nodes().addClass('dimmed').removeClass('trail-highlighted');
    cy.edges().addClass('dimmed').removeClass('trail-highlighted');

    // Highlight trail nodes
    trail.tutorials.forEach((tid) => {
      const node = cy.getElementById(tid);
      if (node.length) {
        node.removeClass('dimmed').addClass('trail-highlighted');
      }
    });

    // Highlight edges between trail nodes
    cy.edges().forEach((edge) => {
      if (tutorialSet.has(edge.data('source')) && tutorialSet.has(edge.data('target'))) {
        edge.removeClass('dimmed').addClass('trail-highlighted');
        edge.style({
          'line-color': trailColor,
          'target-arrow-color': trailColor,
        });
      }
    });
  });
}

export function clearHighlights(cy) {
  cy.batch(() => {
    cy.nodes().removeClass('dimmed trail-highlighted');
    cy.edges().removeClass('dimmed trail-highlighted');
    cy.edges().removeStyle();
  });
}

export function filterBySearch(cy, query) {
  if (!query) {
    cy.nodes().removeClass('dimmed');
    cy.edges().removeClass('dimmed');
    return;
  }

  const q = query.toLowerCase();
  cy.batch(() => {
    cy.nodes().forEach((node) => {
      const label = node.data('label').toLowerCase();
      const cat = node.data('category').toLowerCase();
      if (label.includes(q) || cat.includes(q)) {
        node.removeClass('dimmed');
      } else {
        node.addClass('dimmed');
      }
    });

    cy.edges().forEach((edge) => {
      const src = cy.getElementById(edge.data('source'));
      const tgt = cy.getElementById(edge.data('target'));
      if (src.hasClass('dimmed') || tgt.hasClass('dimmed')) {
        edge.addClass('dimmed');
      } else {
        edge.removeClass('dimmed');
      }
    });
  });
}
