// sidebar.js — Tutorial detail panel rendering

let currentStep = 0;
let currentTutorial = null;
let onNavigateToTutorial = null;

export function initSidebar({ onNavigate }) {
  onNavigateToTutorial = onNavigate;

  document.getElementById('sidebar-close').addEventListener('click', closeSidebar);

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });
}

export function openSidebar(tutorial, data) {
  currentTutorial = tutorial;
  currentStep = 0;

  const sidebar = document.getElementById('sidebar');
  const content = document.getElementById('sidebar-content');

  const category = data.categories.find((c) => c.id === tutorial.category);
  const categoryColor = category?.color || '#6c8aff';
  const categoryLabel = category?.label || tutorial.category;

  // Find connected tutorials
  const prerequisites = [];
  const nextTutorials = [];
  data.edges.forEach((e) => {
    if (e.target === tutorial.id) {
      const t = data.tutorials.find((t) => t.id === e.source);
      if (t) prerequisites.push(t);
    }
    if (e.source === tutorial.id) {
      const t = data.tutorials.find((t) => t.id === e.target);
      if (t) nextTutorials.push(t);
    }
  });

  content.innerHTML = `
    <div class="tutorial-header">
      <div class="tutorial-meta">
        <span class="badge badge-category" style="background: ${categoryColor}">${categoryLabel}</span>
        <span class="badge badge-difficulty">${tutorial.difficulty}</span>
        ${tutorial.estimatedMinutes ? `<span class="badge badge-time">${tutorial.estimatedMinutes} min</span>` : ''}
      </div>
      <h2 class="tutorial-title">${escapeHtml(tutorial.title)}</h2>
      <p class="tutorial-description">${escapeHtml(tutorial.description)}</p>
    </div>

    ${tutorial.steps.length > 0 ? `
      <div class="step-nav">
        <span class="step-nav-label">Step <span id="step-current">1</span> of ${tutorial.steps.length}: <strong id="step-title">${escapeHtml(tutorial.steps[0].title)}</strong></span>
        <div class="step-nav-buttons">
          <button class="step-btn" id="step-prev" disabled>&larr;</button>
          ${tutorial.steps.map((_, i) => `<button class="step-btn step-dot ${i === 0 ? 'active' : ''}" data-step="${i}">${i + 1}</button>`).join('')}
          <button class="step-btn" id="step-next" ${tutorial.steps.length <= 1 ? 'disabled' : ''}>&rarr;</button>
        </div>
      </div>
      <div class="step-content" id="step-content"></div>
    ` : '<p class="tutorial-description">No steps available yet.</p>'}

    ${prerequisites.length > 0 ? `
      <div class="connected-section">
        <h4>Prerequisites</h4>
        ${prerequisites.map((t) => connectedLinkHtml(t, data)).join('')}
      </div>
    ` : ''}

    ${nextTutorials.length > 0 ? `
      <div class="connected-section">
        <h4>Next Tutorials</h4>
        ${nextTutorials.map((t) => connectedLinkHtml(t, data)).join('')}
      </div>
    ` : ''}
  `;

  // Render first step
  if (tutorial.steps.length > 0) {
    renderStep(tutorial.steps[0]);
  }

  // Wire step navigation
  const prevBtn = document.getElementById('step-prev');
  const nextBtn = document.getElementById('step-next');

  if (prevBtn) prevBtn.addEventListener('click', () => navigateStep(-1));
  if (nextBtn) nextBtn.addEventListener('click', () => navigateStep(1));

  content.querySelectorAll('.step-dot').forEach((btn) => {
    btn.addEventListener('click', () => {
      const step = parseInt(btn.dataset.step);
      goToStep(step);
    });
  });

  // Wire connected tutorial links
  content.querySelectorAll('.connected-link').forEach((link) => {
    link.addEventListener('click', () => {
      const id = link.dataset.tutorialId;
      if (onNavigateToTutorial) onNavigateToTutorial(id);
    });
  });

  sidebar.classList.add('open');
}

export function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  currentTutorial = null;
}

function navigateStep(delta) {
  if (!currentTutorial) return;
  const newStep = currentStep + delta;
  if (newStep < 0 || newStep >= currentTutorial.steps.length) return;
  goToStep(newStep);
}

function goToStep(index) {
  if (!currentTutorial) return;
  currentStep = index;
  const step = currentTutorial.steps[index];

  renderStep(step);

  // Update nav
  const currentLabel = document.getElementById('step-current');
  const titleLabel = document.getElementById('step-title');
  const prevBtn = document.getElementById('step-prev');
  const nextBtn = document.getElementById('step-next');

  if (currentLabel) currentLabel.textContent = index + 1;
  if (titleLabel) titleLabel.textContent = step.title;
  if (prevBtn) prevBtn.disabled = index === 0;
  if (nextBtn) nextBtn.disabled = index === currentTutorial.steps.length - 1;

  // Update dot buttons
  document.querySelectorAll('.step-dot').forEach((btn) => {
    btn.classList.toggle('active', parseInt(btn.dataset.step) === index);
  });
}

function renderStep(step) {
  const container = document.getElementById('step-content');
  if (!container) return;

  let html = '';

  if (step.type === 'video' && step.url) {
    html += `<iframe src="${escapeHtml(step.url)}" allowfullscreen loading="lazy"></iframe>`;
  }

  if (step.content) {
    html += marked.parse(step.content);
  }

  container.innerHTML = html;
}

function connectedLinkHtml(tutorial, data) {
  const cat = data.categories.find((c) => c.id === tutorial.category);
  const color = cat?.color || '#6c8aff';
  return `<div class="connected-link" data-tutorial-id="${tutorial.id}">
    <span class="connected-dot" style="background: ${color}"></span>
    ${escapeHtml(tutorial.title)}
  </div>`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
