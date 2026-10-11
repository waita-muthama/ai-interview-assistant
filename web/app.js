'use strict';

/* Interview Assist. No API keys, secrets, or third-party scripts in the browser. */
const $ = (id) => document.getElementById(id);
const state = {
  busy: false, recording: false, stopping: false,
  stream: null, recorder: null, audioContext: null, analyser: null, source: null,
  animation: null, timer: null, started: 0, firstVoice: 0, lastVoice: 0,
  profile: null, history: [], lastAnswer: null, toastTimer: null
};

async function api(path, opts = {}) {
  let response;
  try { response = await fetch(path, opts); }
  catch (_) { throw new Error('Cannot reach the local server. Check that the launch window is running.'); }
  const json = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = json.detail;
    throw new Error(typeof detail === 'string' ? detail : 'Request failed. Please check your input and try again.');
  }
  return json;
}
const jsonOpts = (method, obj) => ({ method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(obj) });

function notify(message, error = false) {
  const box = $('toast');
  box.textContent = message;
  box.classList.toggle('error', error);
  box.hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { box.hidden = true; }, 5500);
}
function setBusy(busy) {
  state.busy = busy;
  $('generateBtn').disabled = busy || state.recording;
  $('listenBtn').disabled = busy || state.recording;
  $('stopBtn').disabled = !state.recording || state.stopping;
  $('regenerateBtn').disabled = busy;
  $('generateBtn').textContent = busy ? '✦  Working on your answer...' : '✦  Generate suggested answer  →';
}
function setPage(name) {
  for (const key of ['live', 'profile', 'history']) {
    $('page-' + key).hidden = key !== name;
  }
  const labels = {live: 'Live assistant', profile: 'Candidate profile', history: 'Interview history'};
  $('crumb').textContent = labels[name];
  document.querySelectorAll('.nav-link').forEach(el => el.classList.toggle('is-active', el.dataset.page === name));
  if (name === 'history') renderHistory();
  window.scrollTo({top: 0, behavior: 'smooth'});
}
function applyProfile(p) {
  state.profile = p;
  $('profileName').value = p.name || '';
  $('profileRole').value = p.target_role || '';
  $('profileExperience').value = p.experience || '';
  $('profileJob').value = p.job_description || '';
  const exists = Boolean(p.resume_filename);
  $('resumeDetails').hidden = !exists;
  if (exists) {
    $('resumeName').textContent = '▤  ' + p.resume_filename;
    $('resumeCount').textContent = `${(p.resume_text || '').length.toLocaleString()} characters extracted for interview context`;
  }
}
function refreshCount() {
  $('navHistoryCount').textContent = String(state.history.length);
}
async function loadHistory() {
  const data = await api('/api/history');
  state.history = data.items || [];
  refreshCount();
  if (!$('page-history').hidden) renderHistory();
}
function makeNode(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}
function renderHistory() {
  const holder = $('historyList');
  holder.replaceChildren();
  $('historyEmpty').hidden = state.history.length > 0;
  const query = $('historyFilter').value.toLowerCase().trim();
  const displayed = query ? state.history.filter(x => (x.question + ' ' + x.answer).toLowerCase().includes(query)) : state.history;
  $('historyNoMatches').hidden = !state.history.length || displayed.length > 0;
  displayed.forEach((item, idx) => {
    const entry = makeNode('article', 'panel history-item');
    const head = makeNode('div', 'history-item-head');
    let when = 'Previous session';
    try { when = new Date(item.created_at).toLocaleString(); } catch (_) { /* safe fallback */ }
    head.appendChild(makeNode('span', '', `QUESTION ${state.history.length - idx}   ·   ${when}`));
    const button = makeNode('button', '', 'Reuse question →');
    button.type = 'button';
    button.addEventListener('click', () => {
      $('questionInput').value = item.question;
      updateQuestionCount();
      showAnswer(item);
      setPage('live');
    });
    head.appendChild(button);
    entry.appendChild(head);
    entry.appendChild(makeNode('h3', '', item.question));
    entry.appendChild(makeNode('p', '', item.answer));
    holder.appendChild(entry);
  });
}
function updateQuestionCount() {
  $('questionCount').textContent = `${$('questionInput').value.length} / 3500`;
}
function showAnswer(item) {
  state.lastAnswer = item;
  $('emptyAnswer').hidden = true;
  $('answerContent').hidden = false;
  $('answerQuestion').textContent = item.question;
  $('answerText').textContent = item.answer;
  const words = item.answer.trim().split(/\s+/).filter(Boolean).length;
  $('answerWords').textContent = `${words} words`;
  $('answerUpdated').textContent = 'Review for accuracy before speaking';
}
async function requestAnswer() {
  const question = $('questionInput').value.trim();
  if (question.length < 3) return notify('Please record or type a complete interview question.', true);
  if (state.busy || state.recording) return;
  setBusy(true);
  try {
    const item = await api('/api/answer', jsonOpts('POST', {
      question, style: $('answerStyle').value, tone: $('answerTone').value
    }));
    showAnswer(item);
    await loadHistory();
    notify('Suggested response ready. Read and adapt it in your own words.');
  } catch (err) { notify(err.message, true); }
  finally { setBusy(false); }
}

// Record a question in the selected microphone without uploading raw audio to local storage.
function recordingFormat() {
  const options = [
    {type: 'audio/webm;codecs=opus', ext: 'webm'},
    {type: 'audio/webm', ext: 'webm'},
    {type: 'audio/mp4', ext: 'mp4'},
    {type: 'audio/ogg;codecs=opus', ext: 'ogg'},
    {type: 'audio/ogg', ext: 'ogg'}
  ];
  return options.find(o => MediaRecorder.isTypeSupported(o.type)) || null;
}
function recorderUi(mode, title, subtitle) {
  $('recorderStage').classList.toggle('recording', mode === 'recording');
  $('recorderTitle').textContent = title;
  $('recorderSubtitle').textContent = subtitle;
  $('captureBadge').textContent = mode === 'recording' ? '● Recording' : (mode === 'working' ? 'Processing' : 'Ready');
}
function fmtTime(ms) {
  const seconds = Math.floor(ms / 1000);
  return `${String(Math.floor(seconds / 60)).padStart(2,'0')}:${String(seconds % 60).padStart(2,'0')}`;
}
async function microphones() {
  if (!navigator.mediaDevices?.enumerateDevices) return;
  const inputs = (await navigator.mediaDevices.enumerateDevices()).filter(x => x.kind === 'audioinput');
  const selected = $('micSelect').value;
  $('micSelect').replaceChildren(new Option('Default microphone', ''));
  inputs.forEach((entry, i) => $('micSelect').add(new Option(entry.label || `Microphone ${i + 1}`, entry.deviceId)));
  if (inputs.some(x => x.deviceId === selected)) $('micSelect').value = selected;
}
function monitorVolume() {
  if (!state.recording || !state.analyser) return;
  const samples = new Uint8Array(state.analyser.fftSize);
  state.analyser.getByteTimeDomainData(samples);
  let sum = 0;
  for (let i = 0; i < samples.length; i++) {
    const n = (samples[i] - 128) / 128;
    sum += n * n;
  }
  const rms = Math.sqrt(sum / samples.length);
  const now = performance.now();
  const duration = now - state.started;
  if (rms > 0.025) {
    if (!state.firstVoice) state.firstVoice = now;
    state.lastVoice = now;
  }
  if ($('autoStop').checked && state.firstVoice && duration > 1250 &&
      now - state.firstVoice > 550 && now - state.lastVoice > 1650) {
    finishListening();
    return;
  }
  if (duration > 55000) { finishListening(); return; }
  state.animation = requestAnimationFrame(monitorVolume);
}
async function startListening() {
  if (state.busy || state.recording) return;
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    return notify('Microphone recording is unsupported. Use current Chrome or Edge, or type your question.', true);
  }
  const format = recordingFormat();
  if (!format) return notify('This browser cannot record in an accepted audio format. Try Chrome or Edge.', true);
  try {
    const selectedDevice = $('micSelect').value;
    state.stream = await navigator.mediaDevices.getUserMedia({audio: {
      ...(selectedDevice ? {deviceId: {ideal: selectedDevice}} : {}),
      echoCancellation: true, noiseSuppression: true, autoGainControl: true
    }});
    await microphones().catch(() => {});
    state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    state.source = state.audioContext.createMediaStreamSource(state.stream);
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 1024;
    state.source.connect(state.analyser);
    const recorder = new MediaRecorder(state.stream, {mimeType: format.type, audioBitsPerSecond: 64000});
    state.recorder = recorder;
    const parts = [];
    recorder.addEventListener('dataavailable', e => { if (e.data.size) parts.push(e.data); });
    recorder.addEventListener('stop', () => processRecording(new Blob(parts, {type: format.type}), format.ext));
    recorder.addEventListener('error', () => { notify('Audio recorder reported an error.', true); finishListening(); });
    state.recording = true;
    state.stopping = false;
    state.firstVoice = 0;
    state.lastVoice = 0;
    state.started = performance.now();
    recorder.start(300);
    recorderUi('recording', 'Listening to the question...', 'Speak clearly. Recording will stop after silence if enabled.');
    setBusy(false);
    $('listenBtn').disabled = true;
    $('stopBtn').disabled = false;
    $('recordTimer').textContent = '00:00';
    state.timer = setInterval(() => { $('recordTimer').textContent = fmtTime(performance.now() - state.started); }, 300);
    monitorVolume();
  } catch (err) {
    cleanupMic();
    recorderUi('ready', 'Microphone is ready', 'Select an input and start listening to the next question.');
    notify(err.name === 'NotAllowedError' ? 'Microphone access denied. Allow access in your browser settings.' : `Microphone failed: ${err.message}`, true);
  }
}
function cleanupMic() {
  cancelAnimationFrame(state.animation);
  clearInterval(state.timer);
  if (state.stream) state.stream.getTracks().forEach(t => t.stop());
  if (state.source) { try {state.source.disconnect();} catch (_) {} }
  if (state.audioContext) state.audioContext.close().catch(() => {});
  state.stream = null; state.source = null; state.analyser = null; state.audioContext = null;
  state.recording = false;
  state.stopping = false;
  $('listenBtn').disabled = state.busy;
  $('stopBtn').disabled = true;
}
function finishListening() {
  if (!state.recording || state.stopping) return;
  state.stopping = true;
  $('stopBtn').disabled = true;
  cancelAnimationFrame(state.animation);
  clearInterval(state.timer);
  const recorder = state.recorder;
  if (recorder?.state === 'recording') recorder.stop();
  cleanupMic();
  recorderUi('working', 'Transcribing question...', 'Sending this audio segment securely to the transcription service.');
}
async function processRecording(blob, extension) {
  if (blob.size < 1400) {
    recorderUi('ready', 'Microphone is ready', 'The audio was too short. Please record the question again.');
    return notify('Recording was too short to transcribe.', true);
  }
  setBusy(true);
  try {
    const data = new FormData();
    data.append('file', blob, 'question.' + extension);
    const transcript = await api('/api/transcribe', {method: 'POST', body: data});
    if (!transcript.text || transcript.text.trim().length < 3) {
      notify('No clear question detected. Check microphone input and record again.', true);
      return;
    }
    $('questionInput').value = transcript.text.slice(0,3500);
    updateQuestionCount();
    recorderUi('ready', 'Question captured', 'Review the transcription and suggested response below.');
    setBusy(false);
    await requestAnswer();
  } catch (err) { notify(err.message, true); }
  finally {
    setBusy(false);
    if ($('recorderTitle').textContent === 'Transcribing question...') recorderUi('ready','Microphone is ready','Select an input and start listening to the next question.');
  }
}

async function saveProfile(e) {
  e.preventDefault();
  const form = $('profileForm');
  const button = form.querySelector('button[type=submit]');
  button.disabled = true;
  try {
    const p = await api('/api/profile', jsonOpts('PUT', {
      name: $('profileName').value.trim(),
      target_role: $('profileRole').value.trim(),
      experience: $('profileExperience').value.trim(),
      job_description: $('profileJob').value.trim()
    }));
    applyProfile(p);
    notify('Candidate profile saved locally.');
  } catch (err) { notify(err.message, true); }
  finally { button.disabled = false; }
}
async function uploadResume(file) {
  if (!file) return;
  if (file.size > 8 * 1024 * 1024) return notify('Document must be 8 MB or smaller.', true);
  if (!/\.(pdf|docx|txt|md)$/i.test(file.name)) return notify('Please select a PDF, DOCX, TXT or MD document.', true);
  const data = new FormData();
  data.append('file', file);
  try {
    notify('Reading your resume...');
    await api('/api/resume', {method: 'POST', body: data});
    applyProfile(await api('/api/profile'));
    notify('Resume successfully extracted and stored locally.');
  } catch (err) { notify(err.message, true); }
  finally { $('resumeFile').value = ''; }
}
function downloadHistory() {
  if (!state.history.length) return notify('No history to export yet.', true);
  const content = '# Interview Assist — Interview Notes\n\n' + [...state.history].reverse().map((i, n) =>
    `## Question ${n + 1}\n\n**Asked:** ${i.created_at}\n\n**Question:** ${i.question}\n\n**Suggested answer:**\n\n${i.answer}\n`
  ).join('\n---\n\n');
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([content], {type: 'text/markdown;charset=utf-8'}));
  link.download = 'interview-notes.md';
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}
async function init() {
  document.querySelectorAll('[data-page]').forEach(b => b.addEventListener('click', () => setPage(b.dataset.page)));
  $('questionInput').addEventListener('input', updateQuestionCount);
  $('questionInput').addEventListener('keydown', e => { if (e.ctrlKey && e.key === 'Enter') {e.preventDefault(); requestAnswer();} });
  $('generateBtn').addEventListener('click', requestAnswer);
  $('regenerateBtn').addEventListener('click', requestAnswer);
  $('copyBtn').addEventListener('click', async () => {
    if (!state.lastAnswer) return;
    try { await navigator.clipboard.writeText(state.lastAnswer.answer); notify('Answer copied.'); }
    catch (_) { notify('Copy failed. Select and copy the text manually.', true); }
  });
  $('listenBtn').addEventListener('click', startListening);
  $('stopBtn').addEventListener('click', finishListening);
  $('profileForm').addEventListener('submit', saveProfile);
  $('resumeFile').addEventListener('change', e => uploadResume(e.target.files[0]));
  const drop = $('dropZone');
  ['dragenter','dragover'].forEach(ev => drop.addEventListener(ev, e => {e.preventDefault(); drop.classList.add('dragover');}));
  ['dragleave','drop'].forEach(ev => drop.addEventListener(ev, e => {e.preventDefault();drop.classList.remove('dragover');}));
  drop.addEventListener('drop', e => uploadResume(e.dataTransfer.files[0]));
  $('removeResume').addEventListener('click', async () => {
    if (!confirm('Remove the resume text stored in the local profile?')) return;
    try { await api('/api/resume', {method:'DELETE'}); applyProfile(await api('/api/profile')); notify('Resume removed.'); }
    catch (err) { notify(err.message, true); }
  });
  $('historyFilter').addEventListener('input', renderHistory);
  $('exportHistory').addEventListener('click', downloadHistory);
  $('clearHistory').addEventListener('click', async () => {
    if (!confirm('Permanently delete all locally saved interview history?')) return;
    try { await api('/api/history', {method:'DELETE'}); await loadHistory(); notify('History deleted.'); }
    catch (err) { notify(err.message, true); }
  });
  try {
    const [health, profile, history] = await Promise.all([api('/api/health'), api('/api/profile'), api('/api/history')]);
    applyProfile(profile);
    state.history = history.items || [];
    refreshCount();
    $('apiStatus').classList.add(health.configured ? 'ready' : 'missing');
    $('apiStatus').lastChild.textContent = health.configured ? 'API configured' : 'API key needed';
    if (!health.configured) notify('To generate answers, add OPENAI_API_KEY to your .env file and restart the server.');
  } catch (err) { notify(err.message, true); }
  microphones().catch(() => {});
}
document.addEventListener('DOMContentLoaded', init);
