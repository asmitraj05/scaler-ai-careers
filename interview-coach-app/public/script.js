let selectedDifficulty = 'medium';
let selectedTopic = '';

document.addEventListener('DOMContentLoaded', () => {
  setupDifficultyButtons();
});

function setupDifficultyButtons() {
  const buttons = document.querySelectorAll('.difficulty-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', function() {
      buttons.forEach(b => b.style.borderColor = 'var(--border)');
      this.style.borderColor = 'var(--primary)';
      selectedDifficulty = this.getAttribute('data-level');
    });
  });
}

function handleKeyPress(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    askQuestion(document.getElementById('messageInput').value);
  }
}

async function askQuestion(question) {
  if (!question.trim()) return;

  const chatBox = document.getElementById('chatBox');
  const messageInput = document.getElementById('messageInput');
  const loadingIndicator = document.getElementById('loadingIndicator');

  if (chatBox.children.length === 1 && chatBox.children[0].classList.contains('welcome-message')) {
    chatBox.innerHTML = '';
  }

  const userMessage = document.createElement('div');
  userMessage.className = 'message user';
  userMessage.innerHTML = `<div class="message-content">${escapeHtml(question)}</div>`;
  chatBox.appendChild(userMessage);

  messageInput.value = '';
  loadingIndicator.classList.remove('hidden');
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question })
    });

    const data = await response.json();

    if (response.ok) {
      const assistantMessage = document.createElement('div');
      assistantMessage.className = 'message assistant';
      assistantMessage.innerHTML = `<div class="message-content">${formatResponse(data.reply)}</div>`;
      chatBox.appendChild(assistantMessage);
    } else {
      showError(`Error: ${data.error}`);
    }
  } catch (error) {
    showError(`Failed to get response: ${error.message}`);
  } finally {
    loadingIndicator.classList.add('hidden');
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

function showGenerateQuestion() {
  document.getElementById('generateModal').classList.remove('hidden');
}

function showGetHint() {
  document.getElementById('hintModal').classList.remove('hidden');
}

function showEvaluateAnswer() {
  document.getElementById('evaluateModal').classList.remove('hidden');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.add('hidden');
}

async function submitGenerateQuestion() {
  const topic = document.getElementById('topic').value.trim();
  const difficulty = document.getElementById('difficulty').value;

  if (!topic) {
    alert('Please enter a topic');
    return;
  }

  const message = `Generate a ${difficulty} DSA problem on ${topic}`;
  closeModal('generateModal');
  document.getElementById('topic').value = '';

  await askQuestion(message);
}

async function submitGetHint() {
  const problem = document.getElementById('problemText').value.trim();
  const stuckPoint = document.getElementById('stuckPoint').value.trim();

  if (!problem || !stuckPoint) {
    alert('Please fill in both fields');
    return;
  }

  const chatBox = document.getElementById('chatBox');
  const loadingIndicator = document.getElementById('loadingIndicator');

  if (chatBox.children.length === 1 && chatBox.children[0].classList.contains('welcome-message')) {
    chatBox.innerHTML = '';
  }

  const userMessage = document.createElement('div');
  userMessage.className = 'message user';
  userMessage.innerHTML = `<div class="message-content">Getting hint for: ${escapeHtml(problem.substring(0, 50))}...</div>`;
  chatBox.appendChild(userMessage);

  closeModal('hintModal');
  document.getElementById('problemText').value = '';
  document.getElementById('stuckPoint').value = '';
  loadingIndicator.classList.remove('hidden');
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch('/api/get-hint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: problem, stuckPoint: stuckPoint })
    });

    const data = await response.json();

    if (response.ok) {
      const assistantMessage = document.createElement('div');
      assistantMessage.className = 'message assistant';
      assistantMessage.innerHTML = `<div class="message-content">${formatResponse(data.hint)}</div>`;
      chatBox.appendChild(assistantMessage);
    } else {
      showError(`Error: ${data.error}`);
    }
  } catch (error) {
    showError(`Failed to get hint: ${error.message}`);
  } finally {
    loadingIndicator.classList.add('hidden');
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

async function submitEvaluateAnswer() {
  const question = document.getElementById('evalProblem').value.trim();
  const answer = document.getElementById('evalAnswer').value.trim();

  if (!question || !answer) {
    alert('Please fill in both fields');
    return;
  }

  const chatBox = document.getElementById('chatBox');
  const loadingIndicator = document.getElementById('loadingIndicator');

  if (chatBox.children.length === 1 && chatBox.children[0].classList.contains('welcome-message')) {
    chatBox.innerHTML = '';
  }

  const userMessage = document.createElement('div');
  userMessage.className = 'message user';
  userMessage.innerHTML = `<div class="message-content">Evaluating your solution...</div>`;
  chatBox.appendChild(userMessage);

  closeModal('evaluateModal');
  document.getElementById('evalProblem').value = '';
  document.getElementById('evalAnswer').value = '';
  loadingIndicator.classList.remove('hidden');
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch('/api/evaluate-answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question, answer: answer })
    });

    const data = await response.json();

    if (response.ok) {
      const assistantMessage = document.createElement('div');
      assistantMessage.className = 'message assistant';
      assistantMessage.innerHTML = `<div class="message-content">${formatResponse(data.evaluation)}</div>`;
      chatBox.appendChild(assistantMessage);
    } else {
      showError(`Error: ${data.error}`);
    }
  } catch (error) {
    showError(`Failed to evaluate: ${error.message}`);
  } finally {
    loadingIndicator.classList.add('hidden');
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

function generateForTopic(topic) {
  document.getElementById('topic').value = topic;
  document.getElementById('difficulty').value = selectedDifficulty;
  submitGenerateQuestion();
}

function formatResponse(text) {
  return text
    .replace(/\n/g, '<br>')
    .replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*?)$/gm, '<li>$1</li>')
    .replace(/(<li>.*?<\/li>)/s, '<ul>$1</ul>')
    .trim();
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function showError(message) {
  const chatBox = document.getElementById('chatBox');
  const errorMessage = document.createElement('div');
  errorMessage.className = 'message assistant';
  errorMessage.innerHTML = `<div class="message-content" style="color: #ef4444;">⚠️ ${escapeHtml(message)}</div>`;
  chatBox.appendChild(errorMessage);
  chatBox.scrollTop = chatBox.scrollHeight;
}

window.onclick = function(event) {
  const generateModal = document.getElementById('generateModal');
  const hintModal = document.getElementById('hintModal');
  const evaluateModal = document.getElementById('evaluateModal');

  if (event.target === generateModal) {
    generateModal.classList.add('hidden');
  }
  if (event.target === hintModal) {
    hintModal.classList.add('hidden');
  }
  if (event.target === evaluateModal) {
    evaluateModal.classList.add('hidden');
  }
};
