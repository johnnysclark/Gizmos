// loader.js — load FBX or GLB from a File, return { root, skinnedMesh, mixer, clip }

import * as THREE from 'three';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export async function loadModelFromFile(file) {
  const buffer = await file.arrayBuffer();
  const name = file.name.toLowerCase();

  let root;
  let animations;

  if (name.endsWith('.fbx')) {
    const loader = new FBXLoader();
    root = loader.parse(buffer, '');
    animations = root.animations || [];
  } else if (name.endsWith('.glb') || name.endsWith('.gltf')) {
    const loader = new GLTFLoader();
    const gltf = await loader.parseAsync(buffer, '');
    root = gltf.scene;
    animations = gltf.animations || [];
  } else {
    throw new Error(`Unsupported file extension: ${name}`);
  }

  let skinnedMesh = null;
  root.traverse((obj) => {
    if (!skinnedMesh && obj.isSkinnedMesh) skinnedMesh = obj;
  });

  // Strip Mixamo-style embedded materials so meshes render predictably under our lights.
  // Keep them lit but neutral — this is a posing tool, not a render preview.
  root.traverse((obj) => {
    if (obj.isMesh || obj.isSkinnedMesh) {
      obj.material = new THREE.MeshStandardMaterial({
        color: 0xc8ccd1,
        roughness: 0.7,
        metalness: 0.0,
      });
      obj.frustumCulled = false;
    }
  });

  let mixer = null;
  let clip = null;
  if (animations.length > 0) {
    mixer = new THREE.AnimationMixer(root);
    clip = animations[0];
    const action = mixer.clipAction(clip);
    action.play();
    action.paused = true;
    mixer.setTime(0);
  }

  return { root, skinnedMesh, mixer, clip, animationCount: animations.length };
}
