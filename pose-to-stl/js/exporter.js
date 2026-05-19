// exporter.js — bake current pose into a static mesh and export as binary STL

import * as THREE from 'three';
import { STLExporter } from 'three/addons/exporters/STLExporter.js';

export function bakeSkinnedMesh(skinnedMesh, scale = 1) {
  skinnedMesh.updateMatrixWorld(true);
  skinnedMesh.skeleton.update();

  const src = skinnedMesh.geometry;
  const count = src.attributes.position.count;
  const positions = new Float32Array(count * 3);
  const v = new THREE.Vector3();

  for (let i = 0; i < count; i++) {
    skinnedMesh.applyBoneTransform(i, v);
    v.applyMatrix4(skinnedMesh.matrixWorld);
    v.multiplyScalar(scale);
    positions[i * 3]     = v.x;
    positions[i * 3 + 1] = v.y;
    positions[i * 3 + 2] = v.z;
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  if (src.index) geom.setIndex(src.index.clone());
  geom.computeVertexNormals();
  return new THREE.Mesh(geom);
}

export function bakeStaticMesh(mesh, scale = 1) {
  mesh.updateMatrixWorld(true);
  const src = mesh.geometry;
  const cloned = src.clone();
  cloned.applyMatrix4(mesh.matrixWorld);
  if (scale !== 1) cloned.scale(scale, scale, scale);
  cloned.computeVertexNormals();
  return new THREE.Mesh(cloned);
}

export function exportSTL(mesh, filename) {
  const exporter = new STLExporter();
  const buffer = exporter.parse(mesh, { binary: true });
  const blob = new Blob([buffer], { type: 'model/stl' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
