/* Buildless, same-origin dashboard. No stored uploads, fixtures, or fallback predictions. */
"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const input = $("image-input");
  const consent = $("consent");
  const analyze = $("analyze");
  const state = { file: null, previewUrl: null, selection: 0, busy: false, xhr: null, modelReady: false };
  const MAX_BYTES = 10 * 1024 * 1024;
  const show = (id, visible) => { $(id).hidden = !visible; };
  const text = (id, value) => { $(id).textContent = value; };

  function updateSubmit() {
    analyze.disabled = !state.file || !consent.checked || state.busy;
    text("submit-note", state.busy ? "Your request is in progress. You can cancel below." :
      !state.file ? "Choose an image and agree above to continue." :
      !consent.checked ? "Review and agree to the consent before submitting." :
      state.modelReady ? "Ready to send your image to the screening service." :
      "The model is unavailable. Submitting will not produce a prediction.");
  }

  function clearResults() {
    ["prediction", "request-feedback", "request-progress"].forEach((id) => show(id, false));
    show("empty-results", true);
    text("empty-title", "Your results will appear here");
    text("empty-copy", "Choose an image, review the consent, and submit it for screening.");
    text("result-state", state.file ? "Ready to submit" : "Awaiting image");
    $("class-scores").replaceChildren();
    $("result-warnings").replaceChildren();
    ["predicted-class", "result-model", "result-domain", "explanation-copy", "prediction-id",
      "feedback-title", "feedback-copy", "request-id"].forEach((id) => text(id, ""));
  }

  function releasePreview() {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
    state.previewUrl = null;
    $("preview-image").removeAttribute("src");
  }

  function clearSelection() {
    window.dispatchEvent(new CustomEvent("skinai:screening-context", { detail: "clear" }));
    state.selection += 1;
    state.file = null;
    releasePreview();
    input.value = "";
    consent.checked = false;
    show("preview", false);
    show("preview-actions", false);
    show("drop-prompt", true);
    show("file-error", false);
    clearResults();
    updateSubmit();
  }

  function fileError(message) {
    clearSelection();
    text("file-error", message);
    show("file-error", true);
  }

  async function selectFiles(files) {
    if (state.busy || !files.length) return;
    if (files.length !== 1) return fileError("Choose one image at a time.");
    clearSelection();
    const token = state.selection;
    const file = files[0];
    if (!file.size) return fileError("This file is empty. Choose a JPEG or PNG image.");
    if (file.size > MAX_BYTES) return fileError("This image exceeds 10 MiB. Choose a smaller file.");
    let localUrl = null;
    try {
      const bytes = new Uint8Array(await file.slice(0, 8).arrayBuffer());
      if (token !== state.selection) return;
      const png = [137, 80, 78, 71, 13, 10, 26, 10].every((value, index) => bytes[index] === value);
      const jpeg = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
      if (!png && !jpeg) return fileError("Unsupported file. Choose a JPEG or PNG image.");
      localUrl = URL.createObjectURL(file);
      const image = new Image();
      await new Promise((resolve, reject) => {
        image.onload = resolve;
        image.onerror = reject;
        image.src = localUrl;
      });
      if (token !== state.selection) { URL.revokeObjectURL(localUrl); return; }
      if (image.naturalWidth < 128 || image.naturalHeight < 128) {
        throw new Error("The image must be at least 128 × 128 pixels.");
      }
      if (image.naturalWidth * image.naturalHeight > 20000000) {
        throw new Error("This image exceeds 20 million pixels. Choose a smaller image.");
      }
      state.file = file;
      state.previewUrl = localUrl;
      $("preview-image").src = localUrl;
      text("file-name", file.name);
      text("file-detail", `${image.naturalWidth} × ${image.naturalHeight} px · ${(file.size / 1024).toFixed(1)} KiB · ${png ? "PNG" : "JPEG"}`);
      show("preview", true);
      show("preview-actions", true);
      show("drop-prompt", false);
      text("result-state", "Ready to submit");
      updateSubmit();
    } catch (error) {
      if (localUrl) URL.revokeObjectURL(localUrl);
      if (token !== state.selection) return;
      fileError(error instanceof Error && error.message ? error.message : "This image could not be opened. Choose a different JPEG or PNG.");
    }
  }

  function setBusy(busy) {
    state.busy = busy;
    input.disabled = busy;
    consent.disabled = busy;
    $("remove-image").disabled = busy;
    $("results").setAttribute("aria-busy", String(busy));
    show("cancel-request", busy);
    updateSubmit();
  }

  function feedback(title, message, id = "", label = "No result") {
    show("empty-results", false);
    show("prediction", false);
    show("request-feedback", true);
    text("feedback-title", title);
    text("feedback-copy", message);
    text("request-id", id ? `Request ID: ${id}` : "");
    text("result-state", label);
    $("request-feedback").focus();
  }

  function validPrediction(body) {
    if (!body || body.score_type !== "uncalibrated_softmax" || body.calibrated !== false ||
        typeof body.request_id !== "string" || typeof body.model_version !== "string" ||
        typeof body.input_domain !== "string" || !Array.isArray(body.scores) || !body.scores.length ||
        !Array.isArray(body.limitations) || !body.limitations.every((item) => typeof item === "string") ||
        !body.explanation || body.explanation.available !== false || typeof body.explanation.reason !== "string" ||
        !body.quality || !Array.isArray(body.quality.warnings) ||
        !body.quality.warnings.every((item) => typeof item === "string")) return false;
    if (!body.scores.every((item) => item && typeof item.code === "string" && typeof item.name === "string" &&
        Number.isInteger(item.index) && Number.isFinite(item.score) && item.score >= 0 && item.score <= 1)) return false;
    const codes = new Set(body.scores.map((item) => item.code));
    const indices = new Set(body.scores.map((item) => item.index));
    const predicted = body.predicted_class;
    const selected = body.scores.find((item) => predicted && item.code === predicted.code &&
      item.index === predicted.index && item.name === predicted.name);
    return codes.size === body.scores.length && indices.size === body.scores.length && selected &&
      selected.score === Math.max(...body.scores.map((item) => item.score));
  }

  function renderPrediction(body) {
    if (!validPrediction(body)) {
      feedback("The response could not be verified", "The service returned an unexpected result format. No prediction is displayed. Please try again or contact the project maintainer.");
      return;
    }
    show("empty-results", false);
    show("request-feedback", false);
    show("prediction", true);
    text("result-state", "Result received");
    text("predicted-class", body.predicted_class.name);
    text("result-model", body.model_version);
    text("result-domain", body.input_domain);
    text("explanation-copy", body.explanation.reason);
    text("prediction-id", `Request ID: ${body.request_id}`);
    $("class-scores").replaceChildren(...[...body.scores].sort((a, b) => b.score - a.score).map((item) => {
      const row = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = item.name;
      const score = document.createElement("strong");
      score.textContent = `${(item.score * 100).toFixed(1)}%`;
      const bar = document.createElement("progress");
      bar.max = 1;
      bar.value = item.score;
      bar.setAttribute("aria-label", `${item.name}: ${(item.score * 100).toFixed(1)} percent model score`);
      row.append(label, score, bar);
      return row;
    }));
    $("result-warnings").replaceChildren(...[...body.quality.warnings, ...body.limitations].map((warning) => {
      const item = document.createElement("li");
      item.textContent = warning;
      return item;
    }));
    $("predicted-class").focus();
    window.dispatchEvent(new CustomEvent("skinai:screening-context", { detail: "refresh" }));
  }

  $("screening-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.file || !consent.checked || state.busy) return;
    clearResults();
    setBusy(true);
    show("empty-results", false);
    show("request-progress", true);
    text("result-state", "In progress");
    text("progress-label", "Uploading image");
    text("progress-value", "0%");
    $("upload-progress").value = 0;
    const xhr = new XMLHttpRequest();
    state.xhr = xhr;
    xhr.upload.addEventListener("progress", (progress) => {
      if (progress.lengthComputable) {
        const percent = Math.round(progress.loaded / progress.total * 100);
        $("upload-progress").value = percent;
        text("progress-value", `${percent}%`);
      } else {
        $("upload-progress").removeAttribute("value");
        text("progress-value", "");
      }
    });
    xhr.upload.addEventListener("load", () => {
      text("progress-label", "Waiting for the service");
      text("progress-value", "");
      $("upload-progress").removeAttribute("value");
    });
    xhr.addEventListener("load", () => {
      let body;
      try { body = JSON.parse(xhr.responseText); } catch { body = null; }
      if (xhr.status === 200) return renderPrediction(body);
      const id = body && typeof body.request_id === "string" ? body.request_id : "";
      if (xhr.status === 503) {
        state.modelReady = false;
        feedback("Model not available yet", "Your image was submitted, but no prediction was generated. A verified, evaluated model must be configured before analysis is available.", id, "Model unavailable");
        text("availability-title", "Model not available yet");
        text("availability-copy", "You can preview an image. Predictions need a verified, evaluated model.");
        $("availability").className = "availability";
        text("model-status", "Unavailable");
        text("model-architecture", "Not available");
        text("model-explanation", "Grad-CAM pending validation");
      } else {
        const message = body && body.error && typeof body.error.message === "string" ? body.error.message :
          "The service could not process the request. Please try again.";
        feedback([413, 415, 422].includes(xhr.status) ? "Please check your image" : "Screening could not finish", message, id);
      }
    });
    xhr.addEventListener("error", () => feedback("Could not reach the service", "Check that the local server is running, then try again. No result is available."));
    xhr.addEventListener("timeout", () => feedback("The request timed out", "The service did not respond within two minutes. No result is available. Try again when the service is ready."));
    xhr.addEventListener("abort", () => feedback("Request cancelled", "No result is displayed. The service may already have received the image; cancellation does not guarantee processing stopped.", "", "Cancelled"));
    xhr.addEventListener("loadend", () => {
      show("request-progress", false);
      state.xhr = null;
      setBusy(false);
    });
    xhr.open("POST", "/predict");
    xhr.timeout = 120000;
    const data = new FormData();
    data.append("image", state.file);
    xhr.send(data);
  });

  async function refreshStatus() {
    const button = $("refresh-status");
    if (button.disabled) return;
    button.disabled = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const responses = await Promise.all(["/health", "/model-info"].map((url) =>
        fetch(url, { signal: controller.signal, cache: "no-store" })));
      if (!responses.every((response) => response.ok)) throw new Error("Unavailable");
      const [health, info] = await Promise.all(responses.map((response) => response.json()));
      if (health.status !== "ok" || typeof info.model_ready !== "boolean") throw new Error("Invalid metadata");
      state.modelReady = health.model_ready === true && info.model_ready === true;
      $("availability").className = state.modelReady ? "availability ready" : "availability";
      text("availability-title", state.modelReady ? "Model available for research screening" : "Model not available yet");
      text("availability-copy", state.modelReady ? "An evaluated export is loaded. Results remain research outputs, not a medical diagnosis." :
        "You can preview an image. Predictions need a verified, evaluated model.");
      text("service-status", "Online");
      text("model-status", state.modelReady ? info.model_version || "Loaded" : "Unavailable");
      text("model-architecture", state.modelReady ? info.architecture || "Not available" : "Not available");
      text("model-explanation", "Grad-CAM pending validation");
    } catch {
      state.modelReady = false;
      $("availability").className = "availability offline";
      text("availability-title", "Screening service is unreachable");
      text("availability-copy", "You can still preview an image. Check the server and refresh its status before screening.");
      text("service-status", "Unreachable");
      text("model-status", "Unknown");
      text("model-architecture", "Not available");
      text("model-explanation", "Not available");
    } finally {
      clearTimeout(timer);
      button.disabled = false;
      updateSubmit();
    }
  }

  input.addEventListener("change", () => selectFiles(Array.from(input.files)));
  consent.addEventListener("change", updateSubmit);
  $("remove-image").addEventListener("click", () => { clearSelection(); input.focus(); });
  $("cancel-request").addEventListener("click", () => { if (state.xhr) state.xhr.abort(); });
  $("refresh-status").addEventListener("click", refreshStatus);
  const dropZone = $("drop-zone");
  ["dragenter", "dragover"].forEach((type) => dropZone.addEventListener(type, (event) => {
    event.preventDefault();
    if (!state.busy) dropZone.classList.add("dragging");
  }));
  ["dragleave", "drop"].forEach((type) => dropZone.addEventListener(type, () => dropZone.classList.remove("dragging")));
  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    selectFiles(Array.from(event.dataTransfer.files));
  });
  // Prevent dropping an image outside the target from navigating away with private content.
  document.addEventListener("dragover", (event) => event.preventDefault());
  document.addEventListener("drop", (event) => event.preventDefault());
  window.addEventListener("pagehide", releasePreview);
  window.addEventListener("pageshow", (event) => { if (event.persisted) clearSelection(); });
  updateSubmit();
  refreshStatus();
})();
