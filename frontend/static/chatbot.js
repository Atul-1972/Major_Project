/* Modular text-only assistant. Server owns conversation history and prediction trust. */
"use strict";
(async () => {
  let config;
  try {
    const response = await fetch("/chat/status", { cache: "no-store" });
    if (!response.ok) return;
    config = await response.json();
    if (!config.enabled) return;
  } catch { return; }

  const element = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content) node.textContent = content;
    return node;
  };
  const launcher = element("button", "chat-launcher");
  launcher.id = "chat-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", "Open skin information assistant");
  launcher.setAttribute("aria-expanded", "false");
  launcher.setAttribute("aria-controls", "chat-panel");
  // Static code-authored icon, with no model or user-generated markup.
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("fill", "none");
  icon.setAttribute("aria-hidden", "true");
  const path = document.createElementNS(icon.namespaceURI, "path");
  path.setAttribute("d", "M20 11.5a8 8 0 0 1-8 8H5l-3 2V12a9 9 0 0 1 18-.5ZM7 10h10M7 14h6");
  path.setAttribute("stroke", "currentColor");
  path.setAttribute("stroke-width", "1.6");
  path.setAttribute("stroke-linecap", "round");
  path.setAttribute("stroke-linejoin", "round");
  icon.append(path);
  launcher.append(icon);

  const panel = element("section", "chat-panel");
  panel.id = "chat-panel";
  panel.hidden = true;
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "Skin information assistant");
  const header = element("header", "chat-head");
  const title = element("div");
  title.append(element("h2", "", "Skin information assistant"), element("p", "", "Education, not a diagnosis · English / हिंदी"));
  const actions = element("div", "chat-head-actions");
  const clear = element("button", "chat-icon-button", "Clear");
  clear.type = "button";
  clear.id = "chat-clear";
  clear.setAttribute("aria-label", "Clear chat and screening context");
  const close = element("button", "chat-icon-button", "−");
  close.type = "button";
  close.id = "chat-close";
  close.setAttribute("aria-label", "Collapse chat");
  actions.append(clear, close);
  header.append(title, actions);
  const toolbar = element("div", "chat-toolbar");
  const status = element("span", "", config.configured ? "AI service configured" : "AI service not configured");
  status.id = "chat-status";
  const language = element("select");
  language.id = "chat-language";
  language.setAttribute("aria-label", "Chat language");
  [["auto", "Auto / स्वतः"], ["en", "English"], ["hi", "हिंदी"]].forEach(([value, label]) => {
    const option = element("option", "", label);
    option.value = value;
    language.append(option);
  });
  toolbar.append(status, language);
  const messages = element("div", "chat-messages");
  messages.id = "chat-messages";
  messages.setAttribute("role", "log");
  messages.setAttribute("aria-live", "polite");
  messages.setAttribute("aria-relevant", "additions");
  const typing = element("div", "chat-typing", "Thinking… / उत्तर तैयार हो रहा है…");
  typing.id = "chat-typing";
  typing.setAttribute("role", "status");
  typing.hidden = true;
  const suggestions = element("div", "chat-suggestions");
  suggestions.setAttribute("aria-label", "Suggested questions");
  const error = element("div", "chat-error");
  error.id = "chat-error";
  error.setAttribute("role", "alert");
  error.hidden = true;
  const notice = element("p", "chat-notice", "Text and opted-in screening labels may be sent to the configured AI provider. No image is shared. Avoid names, contact details or other identifying information.");
  const consentLabel = element("label", "chat-consent");
  const consent = element("input");
  consent.type = "checkbox";
  consent.id = "chat-consent";
  consentLabel.append(consent, element("span", "", "I agree to share this conversation with the configured AI provider. / मैं इस बातचीत को AI सेवा से साझा करने के लिए सहमत हूँ।"));
  const contextLabel = element("label", "chat-consent chat-context-label");
  const context = element("input");
  context.type = "checkbox";
  context.id = "chat-include-prediction";
  context.disabled = true;
  const contextText = element("span", "", "No backend screening result available / अभी कोई जाँचा गया परिणाम उपलब्ध नहीं है");
  contextLabel.append(context, contextText);
  const form = element("form", "chat-composer");
  const input = element("textarea");
  input.id = "chat-input";
  input.rows = 2;
  input.maxLength = 1500;
  input.placeholder = "Ask a skin-health question… / अपना सवाल पूछें…";
  input.setAttribute("aria-label", "Your skin-health question");
  const send = element("button", "chat-send", "Send");
  send.type = "submit";
  send.id = "chat-send";
  send.disabled = true;
  form.append(input, send);
  const footer = element("p", "chat-footnote", "For breathing difficulty or sudden throat/tongue swelling, seek emergency help now. This chat cannot prescribe or confirm a diagnosis. / आपात स्थिति में तुरंत चिकित्सा सहायता लें।");
  panel.append(header, toolbar, messages, typing, suggestions, error, notice, consentLabel, contextLabel, form, footer);
  document.body.append(panel, launcher);

  let busy = false;
  let controller = null;
  let epoch = 0;
  let contextReset = Promise.resolve();
  const headers = { "X-SkinAI-Chat": "1" };
  const update = () => {
    send.disabled = busy || !consent.checked || !input.value.trim();
    input.disabled = busy;
    language.disabled = busy;
    consent.disabled = busy;
    typing.hidden = !busy;
    messages.setAttribute("aria-busy", String(busy));
  };
  function bubble(role, value, response = {}) {
    const item = element("div", `chat-bubble ${role}${response.urgency && response.urgency !== "routine" ? " urgent" : ""}`, value);
    if (Array.isArray(response.sources) && response.sources.length) {
      const citations = element("div", "chat-sources");
      response.sources.forEach((source) => {
        try {
          const url = new URL(source.url);
          if (url.protocol !== "https:" || !["www.nhs.uk", "www.aad.org", "dermnetnz.org"].includes(url.hostname)) return;
          const link = element("a", "", source.title);
          link.href = url.href;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          citations.append(link);
        } catch { /* Unexpected source URLs are never rendered. */ }
      });
      item.append(citations);
    }
    messages.append(item);
    messages.scrollTop = messages.scrollHeight;
  }
  const welcome = () => bubble("assistant", "Hello! I can explain skin-health information and any available screening result. I cannot diagnose or prescribe. What would you like to know?\n\nनमस्ते! मैं त्वचा की सामान्य जानकारी समझा सकता हूँ। मैं निदान या दवा नहीं बता सकता।");
  function showError(value) { error.textContent = value; error.hidden = false; }

  async function loadSession(restore = false) {
    const stamp = epoch;
    try {
      await contextReset;
      const response = await fetch("/chat/session", { headers, cache: "no-store" });
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (stamp !== epoch) return;
      context.disabled = !data.prediction_available;
      if (!data.prediction_available) context.checked = false;
      contextText.textContent = data.prediction_available ? "Include my current backend screening result / मौजूदा स्क्रीनिंग परिणाम भी साझा करें" : "No backend screening result available / अभी कोई जाँचा गया परिणाम उपलब्ध नहीं है";
      if (restore && data.messages.length) {
        messages.replaceChildren();
        data.messages.forEach((message) => bubble(message.role, message.content));
      }
    } catch { if (stamp === epoch) showError("The chat session could not be loaded. Refresh or try again. / चैट सत्र लोड नहीं हुआ।"); }
  }
  function toggle(open) {
    panel.hidden = !open;
    launcher.setAttribute("aria-expanded", String(open));
    launcher.setAttribute("aria-label", open ? "Collapse skin information assistant" : "Open skin information assistant");
    if (open) { loadSession(messages.children.length <= 1); input.focus(); }
    else launcher.focus();
  }
  launcher.addEventListener("click", () => toggle(panel.hidden));
  close.addEventListener("click", () => toggle(false));
  panel.addEventListener("keydown", (event) => { if (event.key === "Escape") toggle(false); });
  input.addEventListener("input", update);
  consent.addEventListener("change", update);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      if (!send.disabled) form.requestSubmit();
    }
  });
  ["How can I care for dry skin?", "Explain my screening result", "खुजली कब डॉक्टर को दिखानी चाहिए?"].forEach((question) => {
    const button = element("button", "", question);
    button.type = "button";
    button.addEventListener("click", () => { if (!busy) { input.value = question; update(); input.focus(); } });
    suggestions.append(button);
  });
  clear.addEventListener("click", async () => {
    epoch += 1;
    if (controller) controller.abort();
    busy = false;
    consent.checked = false;
    context.checked = false;
    context.disabled = true;
    input.value = "";
    messages.replaceChildren();
    welcome();
    error.hidden = true;
    clear.disabled = true;
    update();
    contextReset = fetch("/chat/session", { method: "DELETE", headers }).then((response) => {
      if (!response.ok) throw new Error();
    });
    try { await contextReset; await loadSession(); }
    catch { showError("The server could not clear the chat. Please retry Clear before continuing. / चैट मिट नहीं सकी; फिर प्रयास करें।"); }
    finally { clear.disabled = false; input.focus(); }
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (send.disabled) return;
    const message = input.value.trim();
    const stamp = epoch;
    busy = true;
    update();
    error.hidden = true;
    bubble("user", message);
    const requestController = new AbortController();
    controller = requestController;
    const timeout = setTimeout(() => requestController.abort(), 40000);
    try {
      await contextReset;
      const response = await fetch("/chat", { method: "POST", headers: { ...headers, "Content-Type": "application/json" },
        signal: requestController.signal, body: JSON.stringify({ message, consent: true,
          language: language.value, include_prediction: context.checked }) });
      const data = await response.json();
      if (stamp !== epoch) return;
      if (!response.ok) throw new Error(data.error?.message || "The chat service could not respond.");
      if (typeof data.reply !== "string") throw new Error("Unexpected chat response. Please try again.");
      bubble("assistant", data.reply, data);
      input.value = "";
    } catch (failure) {
      if (stamp === epoch) showError(failure.name === "AbortError" ? "Chat timed out. Please try again. / समय समाप्त; फिर प्रयास करें।" : failure.message || "Chat is unavailable. Try again.");
    } finally {
      clearTimeout(timeout);
      if (stamp === epoch) { busy = false; controller = null; update(); input.focus(); }
    }
  });
  // A same-origin event contains no prediction payload. The server retains authority.
  window.addEventListener("skinai:screening-context", (event) => {
    if (event.detail === "clear") {
      context.checked = false;
      context.disabled = true;
      contextReset = fetch("/chat/context", { method: "DELETE", headers }).then((response) => {
        if (!response.ok) throw new Error();
      });
      contextReset.catch(() => { if (!panel.hidden) showError("Could not clear screening context. Clear the chat before continuing."); });
    } else if (!panel.hidden) loadSession();
  });
  welcome();
})();
