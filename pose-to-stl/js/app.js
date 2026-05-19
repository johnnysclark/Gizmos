// app.js — entry point: wires up viewer, loader, exporter, and DOM controls

import * as THREE from 'three';
import { createViewer } from './viewer.js';
import { loadModelFromFile } from './loader.js';
import { bakeSkinnedMesh, bakeStaticMesh, exportSTL } from './exporter.js';

const FPS = 30;

const dom = {
  viewport: document.getElementById('viewport'),
  fileInput: document.getElementById('file-input'),
  resetView: document.getElementById('reset-view'),
  dropOverlay: document.getElementById('drop-overlay'),
  status: document.getElementById('status'),
  playPause: document.getElementById('play-pause'),
  iconPlay: document.getElementById('icon-play'),
  iconPause: document.getElementById('icon-pause'),
  scrubber: document.getElementById('scrubber'),
  timeReadout: document.getElementById('time-readout'),
  scaleInput: document.getElementById('scale-input'),
  presets: document.querySelectorAll('.presets button'),
  bboxReadout: document.getElementById('bbox-readout'),
  exportStl: document.getElementById('export-stl'),
};

const viewer = createViewer(dom.viewport);

const state = {
  root: null,
  skinnedMesh: null,
  mixer: null,
  clip: null,
  playing: false,
  filename: 'model',
};

function setStatus(msg, isError = false) {
  dom.status.textContent = msg;
  dom.status.classList.toggle('error', isError);
}

function updateTimeReadout() {
  if (!state.clip) {
    dom.timeReadout.textContent = '0.000s / 0.000s · frame 0';
    return;
  }
  const t = state.mixer ? state.mixer.time % state.clip.duration : 0;
  const frame = Math.round(t * FPS);
  dom.timeReadout.textContent =
    `${t.toFixed(3)}s / ${state.clip.duration.toFixed(3)}s · frame ${frame}`;
}

function updateBBoxReadout() {
  if (!state.root) {
    dom.bboxReadout.textContent = 'size: —';
    return;
  }
  const scale = parseFloat(dom.scaleInput.value) || 1;
  const box = new THREE.Box3().setFromObject(state.root);
  const size = box.getSize(new THREE.Vector3()).multiplyScalar(scale);
  dom.bboxReadout.textContent =
    `size: ${size.x.toFixed(1)} × ${size.y.toFixed(1)} × ${size.z.toFixed(1)} mm`;
}

function setPlaying(p) {
  state.playing = p;
  viewer.setPlaying(p);
  dom.iconPlay.style.display = p ? 'none' : '';
  dom.iconPause.style.display = p ? '' : 'none';
}

// Drive an rAF loop just to keep the time readout in sync while playing
function tickReadout() {
  requestAnimationFrame(tickReadout);
  if (state.playing && state.clip) {
    const t = state.mixer.time % state.clip.duration;
    dom.scrubber.value = Math.round((t / state.clip.duration) * 1000);
    updateTimeReadout();
  }
}
tickReadout();

async function loadFile(file) {
  setStatus(`Loading ${file.name}…`);
  try {
    if (state.root) viewer.scene.remove(state.root);

    const result = await loadModelFromFile(file);
    state.root = result.root;
    state.skinnedMesh = result.skinnedMesh;
    state.mixer = result.mixer;
    state.clip = result.clip;
    state.filename = file.name.replace(/\.(fbx|glb|gltf)$/i, '');

    viewer.scene.add(state.root);
    viewer.setMixer(state.mixer);
    viewer.fitToObject(state.root);

    const hasAnim = !!state.clip;
    dom.scrubber.disabled = !hasAnim;
    dom.playPause.disabled = !hasAnim;
    dom.resetView.disabled = false;
    dom.exportStl.disabled = false;
    dom.scrubber.value = 0;
    setPlaying(false);

    updateTimeReadout();
    updateBBoxReadout();

    if (!state.skinnedMesh) {
      setStatus(`Loaded ${file.name} — no skinned mesh found; export will use static geometry.`);
    } else if (!hasAnim) {
      setStatus(`Loaded ${file.name} — no animations. Export uses the current pose (likely T-pose).`);
    } else {
      setStatus(`Loaded ${file.name} — ${result.animationCount} animation(s), ${state.clip.duration.toFixed(2)}s.`);
    }
  } catch (err) {
    console.error(err);
    setStatus(`Failed to load ${file.name}: ${err.message}`, true);
  }
}

// === File input ===
dom.fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) loadFile(file);
  e.target.value = '';
});

// === Drag and drop ===
let dragDepth = 0;
window.addEventListener('dragenter', (e) => {
  e.preventDefault();
  dragDepth++;
  dom.dropOverlay.classList.add('active');
});
window.addEventListener('dragleave', (e) => {
  e.preventDefault();
  dragDepth--;
  if (dragDepth <= 0) {
    dragDepth = 0;
    dom.dropOverlay.classList.remove('active');
  }
});
window.addEventListener('dragover', (e) => { e.preventDefault(); });
window.addEventListener('drop', (e) => {
  e.preventDefault();
  dragDepth = 0;
  dom.dropOverlay.classList.remove('active');
  const file = e.dataTransfer.files[0];
  if (file) loadFile(file);
});

// === Play/pause ===
dom.playPause.addEventListener('click', () => {
  if (!state.mixer) return;
  setPlaying(!state.playing);
});

// === Scrubber ===
dom.scrubber.addEventListener('input', () => {
  if (!state.mixer || !state.clip) return;
  setPlaying(false);
  const t = (dom.scrubber.value / 1000) * state.clip.duration;
  state.mixer.setTime(t);
  updateTimeReadout();
});

// === Reset view ===
dom.resetView.addEventListener('click', () => {
  if (state.root) viewer.fitToObject(state.root);
});

// === Scale input + presets ===
dom.scaleInput.addEventListener('input', updateBBoxReadout);
dom.presets.forEach((btn) => {
  btn.addEventListener('click', () => {
    dom.scaleInput.value = btn.dataset.scale;
    updateBBoxReadout();
  });
});

// === Export STL ===
dom.exportStl.addEventListener('click', () => {
  if (!state.root) return;
  const scale = parseFloat(dom.scaleInput.value) || 1;

  let baked;
  if (state.skinnedMesh) {
    baked = bakeSkinnedMesh(state.skinnedMesh, scale);
  } else {
    // Fall back: find the first mesh in the tree
    let mesh = null;
    state.root.traverse((o) => { if (!mesh && o.isMesh) mesh = o; });
    if (!mesh) { setStatus('No exportable mesh found.', true); return; }
    baked = bakeStaticMesh(mesh, scale);
  }

  const frame = state.clip
    ? Math.round((state.mixer.time % state.clip.duration) * FPS)
    : 0;
  const filename = `${state.filename}_frame${String(frame).padStart(4, '0')}.stl`;
  exportSTL(baked, filename);
  setStatus(`Exported ${filename}`);
});
