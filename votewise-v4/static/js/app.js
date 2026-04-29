/**
 * VoteWise — client-side application script.
 *
 * Handles user interactions, API communication, and DOM updates
 * for the election education chat interface.
 *
 * @module votewise
 */

'use strict';

/* ─── Constants ─────────────────────────────────────────────── */

/** @type {Object.<string, string>} */
const TOPIC_LABELS = {
  voter_registration:   '📋 Voter Registration',
  how_to_vote:          '🗳️ How to Vote',
  election_commission:  '⚖️ Election Commission',
  evm_vvpat:            '🖥️ EVM & VVPAT',
  election_types:       '🏛️ Election Types',
  constituencies:       '📍 Constituencies',
  election_timeline:    '📅 Timeline',
  parties_and_symbols:  '🏳️ Parties & Symbols',
  nota:                 '✖️ NOTA',
  results_and_counting: '📊 Results',
  general:              '🇮🇳 General',
};

const API_ENDPOINT = '/api/ask';
const MAX_TEXTAREA_HEIGHT = 120;

/* ─── State ─────────────────────────────────────────────────── */

let isLoading = false;

/* ─── DOM helpers ───────────────────────────────────────────── */

/**
 * Return an element by ID.
 * @param {string} id
 * @returns {HTMLElement}
 */
const getEl = (id) => document.getElementById(id);

/** @returns {string} Selected language code */
const getLanguage = () => getEl('lang-select').value;

/** @returns {string} Trimmed textarea value */
const getInputValue = () => getEl('question-input').value.trim();

/**
 * Display an error toast for 4 seconds.
 * @param {string} message
 */
function showToast(message) {
  const toast = getEl('toast');
  getEl('toast-msg').textContent = message;
  toast.classList.add('toast--visible');
  setTimeout(() => toast.classList.remove('toast--visible'), 4000);
}

/** Remove the empty-state placeholder from the message list. */
function hideEmptyState() {
  const el = getEl('empty-state');
  if (el) el.remove();
}

/**
 * Enable or disable interactive input elements.
 * @param {boolean} loading
 */
function setLoading(loading) {
  isLoading = loading;
  getEl('send-btn').disabled = loading;
  getEl('question-input').disabled = loading;
  // Inform screen readers the conversation is updating
  getEl('messages').setAttribute('aria-busy', loading ? 'true' : 'false');
}

/* ─── Textarea ──────────────────────────────────────────────── */

/**
 * Auto-resize a textarea to fit its content up to MAX_TEXTAREA_HEIGHT.
 * @param {HTMLTextAreaElement} el
 */
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
}

/* ─── Message rendering ─────────────────────────────────────── */

/**
 * Append a user message bubble to the conversation.
 * @param {string} text - Sanitised question text.
 */
function appendUserMessage(text) {
  hideEmptyState();
  const msg = document.createElement('div');
  msg.className = 'msg msg--user';
  msg.setAttribute('role', 'article');
  msg.setAttribute('aria-label', 'Your question');
  msg.innerHTML = `
    <div class="msg__avatar" aria-hidden="true">👤</div>
    <div class="msg__body">
      <div class="msg__bubble">${escapeHtml(text)}</div>
    </div>`;
  getEl('messages').appendChild(msg);
  msg.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/**
 * Append an animated typing indicator to the conversation.
 */
function showTypingIndicator() {
  const wrap = document.createElement('div');
  wrap.className = 'msg msg--bot';
  wrap.id = 'typing-indicator';
  wrap.setAttribute('role', 'status');
  wrap.setAttribute('aria-label', 'VoteWise is thinking');
  wrap.innerHTML = `
    <div class="msg__avatar" aria-hidden="true">🗳️</div>
    <div class="msg__body">
      <div class="typing" aria-hidden="true">
        <span class="typing__dot"></span>
        <span class="typing__dot"></span>
        <span class="typing__dot"></span>
      </div>
    </div>`;
  getEl('messages').appendChild(wrap);
  wrap.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/** Remove the typing indicator from the DOM. */
function removeTypingIndicator() {
  const el = getEl('typing-indicator');
  if (el) el.remove();
}

/**
 * Build the HTML for follow-up suggestion buttons.
 * @param {string[]} suggestions
 * @returns {string} HTML string
 */
function buildSuggestionsHtml(suggestions) {
  if (!suggestions || suggestions.length === 0) return '';
  const buttons = suggestions
    .map((s) => `
      <button class="suggestion-btn"
        onclick="sendChip(this.textContent)"
        aria-label="Ask: ${escapeAttr(s)}">${escapeHtml(s)}</button>`)
    .join('');
  return `<div class="suggestions" role="list" aria-label="Follow-up questions">${buttons}</div>`;
}

/**
 * Append a bot answer bubble to the conversation.
 * @param {string} answer - The answer text.
 * @param {string} topic  - The detected ElectionTopic value.
 * @param {string[]} suggestions - Suggested follow-up questions.
 */
function appendBotMessage(answer, topic, suggestions) {
  const topicLabel = TOPIC_LABELS[topic] || '🇮🇳 General';
  const msg = document.createElement('div');
  msg.className = 'msg msg--bot';
  msg.setAttribute('role', 'article');
  msg.setAttribute('aria-label', 'VoteWise answer');
  msg.innerHTML = `
    <div class="msg__avatar" aria-hidden="true">🗳️</div>
    <div class="msg__body">
      <div class="msg__bubble">${formatAnswerText(answer)}</div>
      <div class="msg__topic" aria-label="Topic: ${escapeAttr(topicLabel)}">
        <span aria-hidden="true">●</span> ${escapeHtml(topicLabel)}
      </div>
      ${buildSuggestionsHtml(suggestions)}
    </div>`;
  getEl('messages').appendChild(msg);
  msg.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/* ─── API ───────────────────────────────────────────────────── */

/**
 * Submit the current textarea value as a question.
 * Validates input, calls the API, and renders the response.
 * @returns {Promise<void>}
 */
async function submitQuestion() {
  const question = getInputValue();
  if (!question || isLoading) return;

  resetInput();
  appendUserMessage(question);
  setLoading(true);
  showTypingIndicator();

  try {
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, language: getLanguage() }),
    });

    const data = await response.json();
    removeTypingIndicator();

    if (!response.ok) {
      showToast(data.error || 'Something went wrong. Please try again.');
      return;
    }

    appendBotMessage(data.answer, data.topic, data.suggested_questions);
  } catch (_err) {
    removeTypingIndicator();
    showToast('Network error. Please check your connection.');
  } finally {
    setLoading(false);
    getEl('question-input').focus();
  }
}

/** Reset the input textarea to its empty state. */
function resetInput() {
  const input = getEl('question-input');
  input.value = '';
  input.style.height = 'auto';
}

/**
 * Pre-fill the input with a chip label and submit.
 * @param {string} text - The chip's question text.
 */
function sendChip(text) {
  const input = getEl('question-input');
  input.value = text;
  autoResize(input);
  submitQuestion();
}

/* ─── Event handlers ────────────────────────────────────────── */

/**
 * Handle keydown on the textarea — submit on Enter (no Shift).
 * @param {KeyboardEvent} event
 */
function onKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    submitQuestion();
  }
}

/* ─── Utilities ─────────────────────────────────────────────── */

/**
 * Escape a string for safe insertion as HTML content.
 * @param {string} s
 * @returns {string}
 */
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Escape a string for safe use in an HTML attribute value.
 * @param {string} s
 * @returns {string}
 */
function escapeAttr(s) {
  return escapeHtml(s);
}

/**
 * Convert answer plain text to paragraph HTML.
 * @param {string} text
 * @returns {string}
 */
function formatAnswerText(text) {
  return escapeHtml(text)
    .split(/\n{2,}/)
    .map((p) => `<p style="margin-bottom:10px">${p.replace(/\n/g, '<br/>')}</p>`)
    .join('');
}
