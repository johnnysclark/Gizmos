import {
  FilesetResolver,
  FaceDetector,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

const MEDIAPIPE_WASM_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const FACE_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite";
const JSZIP_URL = "https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js";

const MIN_BOX_DRAG_PX = 12;
const BLUR_PADDING = 0.15;
const MIN_BLUR_RADIUS = 12;
const JPEG_QUALITY = 0.92;

const cardTemplate = document.getElementById("fb-card-template");
const fileInput = document.getElementById("fb-file-input");
const cardsEl = document.getElementById("fb-cards");
const statusEl = document.getElementById("fb-status");
const footerEl = document.getElementById("fb-footer");
const footerInfoEl = document.getElementById("fb-footer-info");
const downloadAllBtn = document.getElementById("fb-download-all");

const images = [];
let detectorPromise = null;
let jszipPromise = null;

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("fb-status-error", !!isError);
}

async function getDetector() {
  if (!detectorPromise) {
    setStatus("Loading face detector…");
    detectorPromise = (async () => {
      const vision = await FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_URL);
      const detector = await FaceDetector.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: FACE_MODEL_URL,
          delegate: "GPU",
        },
        runningMode: "IMAGE",
        minDetectionConfidence: 0.3,
        minSuppressionThreshold: 0.3,
      });
      setStatus("");
      return detector;
    })().catch((err) => {
      detectorPromise = null;
      setStatus(
        "Could not load face detector. Check your internet connection and reload.",
        true,
      );
      throw err;
    });
  }
  return detectorPromise;
}

function loadJSZip() {
  if (window.JSZip) return Promise.resolve(window.JSZip);
  if (!jszipPromise) {
    jszipPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = JSZIP_URL;
      script.onload = () => resolve(window.JSZip);
      script.onerror = () => {
        jszipPromise = null;
        reject(new Error("Failed to load JSZip"));
      };
      document.head.appendChild(script);
    });
  }
  return jszipPromise;
}

function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.decoding = "async";
    img.onload = () => resolve({ img, url });
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(`Could not load ${file.name}`));
    };
    img.src = url;
  });
}

function normalizeBox(det, imgW, imgH) {
  const b = det.boundingBox;
  if (!b) return null;
  const x = Math.max(0, b.originX / imgW);
  const y = Math.max(0, b.originY / imgH);
  const w = Math.min(1 - x, b.width / imgW);
  const h = Math.min(1 - y, b.height / imgH);
  if (w <= 0 || h <= 0) return null;
  return { x, y, w, h, source: "detected", active: true };
}

async function detectFaces(state) {
  const detector = await getDetector();
  const result = detector.detect(state.img);
  const imgW = state.img.naturalWidth;
  const imgH = state.img.naturalHeight;
  return (result.detections || [])
    .map((d) => normalizeBox(d, imgW, imgH))
    .filter(Boolean);
}

function renderBoxes(state) {
  const overlay = state.overlayEl;
  overlay.innerHTML = "";
  for (const box of state.boxes) {
    const el = document.createElement("div");
    el.className = "fb-box";
    if (!box.active) el.classList.add("fb-box-off");
    if (box.source === "manual") el.classList.add("fb-box-manual");
    el.style.left = box.x * 100 + "%";
    el.style.top = box.y * 100 + "%";
    el.style.width = box.w * 100 + "%";
    el.style.height = box.h * 100 + "%";

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "fb-box-remove";
    remove.setAttribute("aria-label", "Remove this blur");
    remove.textContent = "×";
    remove.addEventListener("pointerdown", (e) => e.stopPropagation());
    remove.addEventListener("click", (e) => {
      e.stopPropagation();
      state.boxes = state.boxes.filter((b) => b !== box);
      renderBoxes(state);
      updateCardMeta(state);
      updateFooter();
    });
    el.appendChild(remove);

    el.addEventListener("pointerdown", (e) => e.stopPropagation());
    el.addEventListener("click", () => {
      box.active = !box.active;
      el.classList.toggle("fb-box-off", !box.active);
      updateCardMeta(state);
    });

    overlay.appendChild(el);
  }
}

function attachDrawHandler(state) {
  const overlay = state.overlayEl;
  overlay.addEventListener("pointerdown", (e) => {
    if (e.target !== overlay) return;
    e.preventDefault();
    overlay.setPointerCapture(e.pointerId);
    const rect = overlay.getBoundingClientRect();
    const startX = (e.clientX - rect.left) / rect.width;
    const startY = (e.clientY - rect.top) / rect.height;
    let curX = startX;
    let curY = startY;

    const temp = document.createElement("div");
    temp.className = "fb-box fb-box-manual fb-box-drawing";
    overlay.appendChild(temp);

    const updateTemp = () => {
      const x = Math.max(0, Math.min(startX, curX));
      const y = Math.max(0, Math.min(startY, curY));
      const w = Math.min(1, Math.max(startX, curX)) - x;
      const h = Math.min(1, Math.max(startY, curY)) - y;
      temp.style.left = x * 100 + "%";
      temp.style.top = y * 100 + "%";
      temp.style.width = w * 100 + "%";
      temp.style.height = h * 100 + "%";
    };

    const onMove = (ev) => {
      curX = (ev.clientX - rect.left) / rect.width;
      curY = (ev.clientY - rect.top) / rect.height;
      updateTemp();
    };
    const onUp = () => {
      overlay.removeEventListener("pointermove", onMove);
      overlay.removeEventListener("pointerup", onUp);
      overlay.removeEventListener("pointercancel", onUp);
      temp.remove();
      const dxPx = Math.abs(curX - startX) * rect.width;
      const dyPx = Math.abs(curY - startY) * rect.height;
      if (dxPx < MIN_BOX_DRAG_PX || dyPx < MIN_BOX_DRAG_PX) return;
      const x = Math.max(0, Math.min(startX, curX));
      const y = Math.max(0, Math.min(startY, curY));
      const w = Math.min(1, Math.max(startX, curX)) - x;
      const h = Math.min(1, Math.max(startY, curY)) - y;
      state.boxes.push({ x, y, w, h, source: "manual", active: true });
      renderBoxes(state);
      updateCardMeta(state);
      updateFooter();
    };

    overlay.addEventListener("pointermove", onMove);
    overlay.addEventListener("pointerup", onUp);
    overlay.addEventListener("pointercancel", onUp);
  });
}

function activeBoxCount(state) {
  return state.boxes.filter((b) => b.active).length;
}

function updateCardMeta(state) {
  if (state.detecting) {
    state.countEl.textContent = "Detecting faces…";
    state.warningEl.hidden = true;
    return;
  }
  const active = activeBoxCount(state);
  const total = state.boxes.length;
  state.countEl.textContent =
    total === 0
      ? "No faces detected"
      : `${active}/${total} will be blurred`;
  state.warningEl.hidden = total !== 0;
}

function updateFooter() {
  const total = images.length;
  if (total === 0) {
    footerEl.hidden = true;
    return;
  }
  const faces = images.reduce((n, s) => n + activeBoxCount(s), 0);
  footerInfoEl.textContent = `${total} photo${total === 1 ? "" : "s"} · ${faces} face${faces === 1 ? "" : "s"} to blur`;
  footerEl.hidden = false;
  downloadAllBtn.disabled = false;
}

function blurredFileName(originalName) {
  const dot = originalName.lastIndexOf(".");
  const base = dot > 0 ? originalName.slice(0, dot) : originalName;
  return `${base}-blurred.jpg`;
}

function renderBlurred(state) {
  const img = state.img;
  const canvas = document.createElement("canvas");
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0);

  for (const box of state.boxes) {
    if (!box.active) continue;
    const bx = box.x * canvas.width;
    const by = box.y * canvas.height;
    const bw = box.w * canvas.width;
    const bh = box.h * canvas.height;
    const pad = Math.max(bw, bh) * BLUR_PADDING;
    const rx = Math.max(0, Math.floor(bx - pad));
    const ry = Math.max(0, Math.floor(by - pad));
    const rw = Math.min(canvas.width - rx, Math.ceil(bw + pad * 2));
    const rh = Math.min(canvas.height - ry, Math.ceil(bh + pad * 2));
    if (rw <= 0 || rh <= 0) continue;

    const blurR = Math.max(MIN_BLUR_RADIUS, Math.min(rw, rh) / 4);
    const tmp = document.createElement("canvas");
    tmp.width = rw;
    tmp.height = rh;
    const tctx = tmp.getContext("2d");
    tctx.filter = `blur(${blurR}px)`;
    tctx.drawImage(img, rx, ry, rw, rh, 0, 0, rw, rh);
    tctx.filter = "none";
    ctx.drawImage(tmp, rx, ry);
  }

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) resolve(blob);
        else reject(new Error("Could not encode image"));
      },
      "image/jpeg",
      JPEG_QUALITY,
    );
  });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function downloadOne(state) {
  setStatus(`Blurring ${state.file.name}…`);
  try {
    const blob = await renderBlurred(state);
    downloadBlob(blob, blurredFileName(state.file.name));
    setStatus("");
  } catch (err) {
    console.error(err);
    setStatus(`Failed to export ${state.file.name}.`, true);
  }
}

async function downloadAll() {
  if (images.length === 0) return;
  downloadAllBtn.disabled = true;
  setStatus("Preparing ZIP…");
  try {
    const JSZip = await loadJSZip();
    const zip = new JSZip();
    for (let i = 0; i < images.length; i++) {
      const state = images[i];
      setStatus(`Blurring ${i + 1} of ${images.length}…`);
      const blob = await renderBlurred(state);
      zip.file(blurredFileName(state.file.name), blob);
    }
    setStatus("Building ZIP…");
    const zipBlob = await zip.generateAsync({ type: "blob" });
    downloadBlob(zipBlob, "blurred-photos.zip");
    setStatus("");
  } catch (err) {
    console.error(err);
    setStatus("Could not create ZIP. Try downloading photos individually.", true);
  } finally {
    downloadAllBtn.disabled = false;
  }
}

function removeImage(state) {
  const idx = images.indexOf(state);
  if (idx >= 0) images.splice(idx, 1);
  state.cardEl.remove();
  if (state.url) URL.revokeObjectURL(state.url);
  updateFooter();
}

async function redetect(state) {
  state.detecting = true;
  state.spinnerEl.hidden = false;
  try {
    const boxes = await detectFaces(state);
    state.boxes = boxes;
    renderBoxes(state);
  } catch (err) {
    console.error(err);
    setStatus(`Detection failed on ${state.file.name}.`, true);
  } finally {
    state.detecting = false;
    state.spinnerEl.hidden = true;
    updateCardMeta(state);
    updateFooter();
  }
}

function buildCard(state) {
  const frag = cardTemplate.content.cloneNode(true);
  const cardEl = frag.querySelector(".fb-card");
  const imgEl = frag.querySelector(".fb-card-img");
  const overlayEl = frag.querySelector(".fb-card-overlay");
  const spinnerEl = frag.querySelector(".fb-card-spinner");
  const nameEl = frag.querySelector(".fb-card-name");
  const countEl = frag.querySelector(".fb-card-count");
  const redetectBtn = frag.querySelector(".fb-card-redetect");
  const downloadBtn = frag.querySelector(".fb-card-download");
  const removeBtn = frag.querySelector(".fb-card-remove");
  const warningEl = frag.querySelector(".fb-card-warning");

  imgEl.src = state.url;
  imgEl.alt = state.file.name;
  nameEl.textContent = state.file.name;

  state.cardEl = cardEl;
  state.overlayEl = overlayEl;
  state.spinnerEl = spinnerEl;
  state.countEl = countEl;
  state.warningEl = warningEl;

  redetectBtn.addEventListener("click", () => redetect(state));
  downloadBtn.addEventListener("click", () => downloadOne(state));
  removeBtn.addEventListener("click", () => removeImage(state));

  attachDrawHandler(state);
  cardsEl.appendChild(cardEl);
}

async function addFile(file) {
  let loaded;
  try {
    loaded = await loadImageFromFile(file);
  } catch (err) {
    console.error(err);
    setStatus(`Could not open ${file.name}.`, true);
    return;
  }
  const state = {
    file,
    img: loaded.img,
    url: loaded.url,
    boxes: [],
    detecting: true,
  };
  images.push(state);
  buildCard(state);
  state.spinnerEl.hidden = false;
  updateCardMeta(state);
  updateFooter();

  try {
    state.boxes = await detectFaces(state);
  } catch (err) {
    console.error(err);
    setStatus(`Detection failed on ${file.name}.`, true);
  } finally {
    state.detecting = false;
    state.spinnerEl.hidden = true;
    renderBoxes(state);
    updateCardMeta(state);
    updateFooter();
  }
}

fileInput.addEventListener("change", async () => {
  const files = Array.from(fileInput.files || []);
  fileInput.value = "";
  if (files.length === 0) return;
  try {
    await getDetector();
  } catch {
    return;
  }
  for (const file of files) {
    await addFile(file);
  }
});

downloadAllBtn.addEventListener("click", downloadAll);
