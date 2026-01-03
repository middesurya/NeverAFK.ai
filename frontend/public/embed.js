(function() {
  'use strict';

  // Get creator ID from script tag
  var scriptTag = document.currentScript;
  var creatorId = scriptTag.getAttribute('data-creator-id');
  var position = scriptTag.getAttribute('data-position') || 'bottom-right';
  var primaryColor = scriptTag.getAttribute('data-color') || '#4F46E5';
  var welcomeMessage = scriptTag.getAttribute('data-welcome') || 'Hi! How can I help you today?';

  if (!creatorId) {
    console.error('Creator Support AI: data-creator-id attribute is required');
    return;
  }

  // CSS for the widget
  var styles = `
    #creator-ai-widget {
      position: fixed;
      z-index: 9999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    #creator-ai-widget.bottom-right {
      bottom: 20px;
      right: 20px;
    }

    #creator-ai-widget.bottom-left {
      bottom: 20px;
      left: 20px;
    }

    #creator-ai-widget.top-right {
      top: 20px;
      right: 20px;
    }

    #creator-ai-widget.top-left {
      top: 20px;
      left: 20px;
    }

    #creator-ai-button {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: ${primaryColor};
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
    }

    #creator-ai-button:hover {
      transform: scale(1.1);
    }

    #creator-ai-button svg {
      width: 28px;
      height: 28px;
      fill: white;
    }

    #creator-ai-chat {
      display: none;
      flex-direction: column;
      width: 380px;
      height: 600px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      overflow: hidden;
    }

    #creator-ai-chat.visible {
      display: flex;
    }

    #creator-ai-header {
      background: ${primaryColor};
      color: white;
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    #creator-ai-header h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }

    #creator-ai-header p {
      margin: 4px 0 0 0;
      font-size: 12px;
      opacity: 0.9;
    }

    #creator-ai-close {
      background: none;
      border: none;
      color: white;
      font-size: 24px;
      cursor: pointer;
      padding: 0;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    #creator-ai-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #f9fafb;
    }

    .creator-ai-message {
      margin-bottom: 12px;
      display: flex;
    }

    .creator-ai-message.user {
      justify-content: flex-end;
    }

    .creator-ai-message.assistant {
      justify-content: flex-start;
    }

    .creator-ai-message-bubble {
      max-width: 80%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
    }

    .creator-ai-message.user .creator-ai-message-bubble {
      background: ${primaryColor};
      color: white;
    }

    .creator-ai-message.assistant .creator-ai-message-bubble {
      background: white;
      color: #1f2937;
      border: 1px solid #e5e7eb;
    }

    .creator-ai-sources {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid rgba(0, 0, 0, 0.1);
      font-size: 11px;
      opacity: 0.8;
    }

    #creator-ai-input-area {
      padding: 16px;
      border-top: 1px solid #e5e7eb;
      background: white;
    }

    #creator-ai-input-wrapper {
      display: flex;
      gap: 8px;
    }

    #creator-ai-input {
      flex: 1;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 14px;
      outline: none;
    }

    #creator-ai-input:focus {
      border-color: ${primaryColor};
    }

    #creator-ai-send {
      background: ${primaryColor};
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 16px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
    }

    #creator-ai-send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .creator-ai-loading {
      display: flex;
      gap: 4px;
      padding: 10px 14px;
    }

    .creator-ai-loading-dot {
      width: 8px;
      height: 8px;
      background: #9ca3af;
      border-radius: 50%;
      animation: creator-ai-bounce 1.4s infinite ease-in-out both;
    }

    .creator-ai-loading-dot:nth-child(1) {
      animation-delay: -0.32s;
    }

    .creator-ai-loading-dot:nth-child(2) {
      animation-delay: -0.16s;
    }

    @keyframes creator-ai-bounce {
      0%, 80%, 100% {
        transform: scale(0);
      }
      40% {
        transform: scale(1);
      }
    }

    @media (max-width: 480px) {
      #creator-ai-chat {
        width: calc(100vw - 40px);
        height: calc(100vh - 40px);
      }
    }
  `;

  // Inject styles
  var styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);

  // Create widget HTML
  var widgetHTML = `
    <div id="creator-ai-widget" class="${position}">
      <button id="creator-ai-button" aria-label="Open chat">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
      </button>
      <div id="creator-ai-chat">
        <div id="creator-ai-header">
          <div>
            <h3>AI Assistant</h3>
            <p>Ask me anything!</p>
          </div>
          <button id="creator-ai-close" aria-label="Close chat">&times;</button>
        </div>
        <div id="creator-ai-messages">
          <div class="creator-ai-message assistant">
            <div class="creator-ai-message-bubble">${welcomeMessage}</div>
          </div>
        </div>
        <div id="creator-ai-input-area">
          <div id="creator-ai-input-wrapper">
            <input type="text" id="creator-ai-input" placeholder="Type your question..." />
            <button id="creator-ai-send">Send</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Insert widget
  var widgetContainer = document.createElement('div');
  widgetContainer.innerHTML = widgetHTML;
  document.body.appendChild(widgetContainer.firstElementChild);

  // Get elements
  var button = document.getElementById('creator-ai-button');
  var chat = document.getElementById('creator-ai-chat');
  var closeBtn = document.getElementById('creator-ai-close');
  var input = document.getElementById('creator-ai-input');
  var sendBtn = document.getElementById('creator-ai-send');
  var messagesContainer = document.getElementById('creator-ai-messages');

  var isLoading = false;
  var apiUrl = scriptTag.getAttribute('data-api-url') || 'http://localhost:8000';

  // Toggle chat
  button.addEventListener('click', function() {
    chat.classList.toggle('visible');
    if (chat.classList.contains('visible')) {
      input.focus();
    }
  });

  closeBtn.addEventListener('click', function() {
    chat.classList.remove('visible');
  });

  // Send message
  function sendMessage() {
    var message = input.value.trim();
    if (!message || isLoading) return;

    // Add user message
    addMessage(message, 'user');
    input.value = '';

    // Show loading
    isLoading = true;
    sendBtn.disabled = true;
    var loadingId = addLoadingIndicator();

    // Call API
    fetch(apiUrl + '/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        creator_id: creatorId
      })
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      removeLoadingIndicator(loadingId);
      addMessage(data.response, 'assistant', data.sources);
      isLoading = false;
      sendBtn.disabled = false;
    })
    .catch(function(error) {
      removeLoadingIndicator(loadingId);
      addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
      isLoading = false;
      sendBtn.disabled = false;
      console.error('Creator Support AI Error:', error);
    });
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });

  // Helper functions
  function addMessage(text, role, sources) {
    var messageDiv = document.createElement('div');
    messageDiv.className = 'creator-ai-message ' + role;

    var bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'creator-ai-message-bubble';
    bubbleDiv.textContent = text;

    if (sources && sources.length > 0) {
      var sourcesDiv = document.createElement('div');
      sourcesDiv.className = 'creator-ai-sources';
      sourcesDiv.textContent = 'Sources: ' + sources.join(', ');
      bubbleDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function addLoadingIndicator() {
    var loadingDiv = document.createElement('div');
    loadingDiv.className = 'creator-ai-message assistant';
    loadingDiv.id = 'creator-ai-loading-' + Date.now();

    var bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'creator-ai-message-bubble';

    var loadingDotsDiv = document.createElement('div');
    loadingDotsDiv.className = 'creator-ai-loading';
    loadingDotsDiv.innerHTML = '<div class="creator-ai-loading-dot"></div><div class="creator-ai-loading-dot"></div><div class="creator-ai-loading-dot"></div>';

    bubbleDiv.appendChild(loadingDotsDiv);
    loadingDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return loadingDiv.id;
  }

  function removeLoadingIndicator(id) {
    var element = document.getElementById(id);
    if (element) {
      element.remove();
    }
  }

})();
