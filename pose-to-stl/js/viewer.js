// viewer.js — Three.js scene, camera, renderer, controls, render loop

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function createViewer(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x14171c);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
  camera.position.set(150, 150, 250);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  const hemi = new THREE.HemisphereLight(0xffffff, 0x404048, 0.9);
  scene.add(hemi);

  const key = new THREE.DirectionalLight(0xffffff, 0.8);
  key.position.set(200, 300, 200);
  scene.add(key);

  const grid = new THREE.GridHelper(400, 20, 0x2a2f37, 0x222831);
  scene.add(grid);

  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener('resize', resize);

  let mixer = null;
  let prevTime = performance.now();
  let playing = false;

  function animate() {
    requestAnimationFrame(animate);
    const now = performance.now();
    const dt = (now - prevTime) / 1000;
    prevTime = now;
    if (mixer && playing) mixer.update(dt);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  function setMixer(m) { mixer = m; }
  function setPlaying(p) { playing = p; }

  function fitToObject(object) {
    const box = new THREE.Box3().setFromObject(object);
    if (box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = camera.fov * (Math.PI / 180);
    const dist = (maxDim / 2) / Math.tan(fov / 2) * 1.6;

    camera.position.copy(center).add(new THREE.Vector3(dist * 0.7, dist * 0.6, dist * 0.9));
    controls.target.copy(center);
    camera.near = Math.max(0.1, dist / 100);
    camera.far = Math.max(2000, dist * 20);
    camera.updateProjectionMatrix();
    controls.update();

    // adjust grid to character footprint
    const gridSize = Math.max(maxDim * 2, 100);
    grid.scale.setScalar(gridSize / 400);
    grid.position.y = box.min.y;
  }

  return { scene, camera, renderer, controls, setMixer, setPlaying, fitToObject };
}
