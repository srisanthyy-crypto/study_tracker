// ============================================================
// chatbot.js — StudyTrack AI — Chat Interface Logic
// Talks to Flask /api/chat endpoint
// ============================================================

const chatMessages = document.getElementById("chatMessages");

/**
 * Send a message typed in the input box.
 */
function sendMessage() {
  const input = document.getElementById("chatInput");
  const text  = input.value.trim();
  if (!text) return;

  // Show user's message
  appendBubble(text, "user");
  input.value = "";

  // Show typing indicator
  const typingId = showTyping();

  // POST to Flask chatbot API
  fetch("/api/chat", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ message: text })
  })
  .then(function (res) { return res.json(); })
  .then(function (data) {
    removeTyping(typingId);
    appendBubble(data.reply, "bot");
  })
  .catch(function (err) {
    removeTyping(typingId);
    appendBubble("⚠️ Sorry, something went wrong. Please try again.", "bot");
    console.error("Chat error:", err);
  });
}

/**
 * Send a suggestion pill message.
 */
function sendSuggestion(text) {
  document.getElementById("chatInput").value = text;
  sendMessage();
}

/**
 * Append a chat bubble to the message list.
 * Supports **bold** markdown-style formatting.
 */
function appendBubble(text, sender) {
  const wrapper = document.createElement("div");
  wrapper.className = "chat-bubble " + (sender === "bot" ? "bot-bubble" : "user-bubble");

  const avatar  = document.createElement("div");
  avatar.className = "bubble-avatar";
  avatar.textContent = sender === "bot" ? "🤖" : "👤";

  const content = document.createElement("div");
  content.className = "bubble-content";

  // Render **bold** and newlines
  content.innerHTML = formatMessage(text);

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);
  chatMessages.appendChild(wrapper);

  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Format plain text: newlines → <br>, **text** → <strong>text</strong>
 */
function formatMessage(text) {
  // Escape HTML to prevent XSS
  var safe = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold markdown (**text**)
  safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Newlines to <br>
  safe = safe.replace(/\n/g, "<br>");

  // Bullet points (• item)
  safe = safe.replace(/^• (.+)$/gm, '<li>$1</li>');
  safe = safe.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  return safe;
}

/**
 * Show animated typing indicator. Returns a unique ID to remove it later.
 */
function showTyping() {
  var id      = "typing-" + Date.now();
  var wrapper = document.createElement("div");
  wrapper.className = "chat-bubble bot-bubble";
  wrapper.id        = id;

  wrapper.innerHTML =
    '<div class="bubble-avatar">🤖</div>' +
    '<div class="bubble-content">' +
    '  <div class="typing-dots">' +
    '    <span></span><span></span><span></span>' +
    '  </div>' +
    '</div>';

  chatMessages.appendChild(wrapper);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

/**
 * Remove the typing indicator bubble by its ID.
 */
function removeTyping(id) {
  var el = document.getElementById(id);
  if (el) el.remove();
}
