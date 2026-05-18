/**
 * MChat Widget Loader
 *
 * Usage:
 *   <script
 *     src="https://your-domain.com/widget-loader.js"
 *     data-mchat-url="https://api.your-domain.com"
 *     data-agent-id="xxx"
 *     data-position="right"
 *     data-primary-color="#3b82f6"
 *     data-welcome-message="你好！有什么可以帮助你的？"
 *     data-bot-name="智能助手"
 *   ></script>
 */
(function () {
  'use strict'

  // Get config from script tag
  var scripts = document.getElementsByTagName('script')
  var script = scripts[scripts.length - 1]
  var config = {
    apiUrl: script.getAttribute('data-mchat-url') || '/api',
    agentId: script.getAttribute('data-agent-id') || '',
    position: script.getAttribute('data-position') || 'right',
    primaryColor: script.getAttribute('data-primary-color') || '#3b82f6',
    welcomeMessage:
      script.getAttribute('data-welcome-message') ||
      '你好！我是智能客服助手，有什么可以帮助你的？',
    botName: script.getAttribute('data-bot-name') || '智能助手',
  }

  var STATE = {
    isOpen: false,
    isMinimized: false,
    messages: [
      {
        id: 'welcome',
        role: 'assistant',
        content: config.welcomeMessage,
        timestamp: new Date().toISOString(),
      },
    ],
    isLoading: false,
  }

  var elements = {}

  // Create styles
  var style = document.createElement('style')
  style.textContent =
    '\n    #mchat-widget-container {\n      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;\n    }\n    #mchat-widget-container textarea {\n      min-height: 42px;\n      height: auto;\n    }\n    @keyframes mchat-widget-slide-in {\n      from { opacity: 0; transform: translateY(20px) scale(0.95); }\n      to { opacity: 1; transform: translateY(0) scale(1); }\n    }\n    @keyframes mchat-message-fade-in {\n      from { opacity: 0; transform: translateY(8px); }\n      to { opacity: 1; transform: translateY(0); }\n    }\n    @keyframes mchat-spin {\n      to { transform: rotate(360deg); }\n    }\n  '
  document.head.appendChild(style)

  function createContainer() {
    var container = document.createElement('div')
    container.id = 'mchat-widget-container'

    // Button
    var button = document.createElement('button')
    button.id = 'mchat-widget-button'
    var posAttr = config.position === 'left' ? 'left' : 'right'
    button.style.cssText =
      '\n      position: fixed;\n      bottom: 24px;\n      ' +
      posAttr +
      ': 24px;\n      z-index: 999999;\n      width: 56px;\n      height: 56px;\n      border-radius: 50%;\n      border: none;\n      background-color: ' +
      config.primaryColor +
      ';\n      color: white;\n      cursor: pointer;\n      box-shadow: 0 4px 20px rgba(0,0,0,0.15);\n      display: flex;\n      align-items: center;\n      justify-content: center;\n      transition: all 0.3s ease;\n    '
    button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>'
    button.onmouseover = function () {
      button.style.transform = 'scale(1.1)'
      button.style.boxShadow = '0 6px 24px rgba(0,0,0,0.2)'
    }
    button.onmouseout = function () {
      button.style.transform = ''
      button.style.boxShadow = ''
    }
    button.onclick = toggleWidget
    container.appendChild(button)
    elements.button = button

    // Chat window
    var chatWindow = document.createElement('div')
    chatWindow.id = 'mchat-widget-chat'
    chatWindow.style.cssText =
      '\n      position: fixed;\n      bottom: 92px;\n      ' +
      posAttr +
      ': 24px;\n      z-index: 999999;\n      width: 360px;\n      height: 560px;\n      background: white;\n      border-radius: 16px;\n      box-shadow: 0 8px 40px rgba(0,0,0,0.12);\n      border: 1px solid #e5e7eb;\n      display: flex;\n      flex-direction: column;\n      overflow: hidden;\n      animation: mchat-widget-slide-in 0.3s ease-out;\n      transform-origin: bottom ' +
      (config.position === 'left' ? 'left' : 'right') +
      ';\n    '
    chatWindow.style.display = 'none'

    // Header
    var header = document.createElement('div')
    header.style.cssText =
      '\n      display: flex;\n      align-items: center;\n      justify-content: space-between;\n      padding: 12px 16px;\n      background-color: ' +
      config.primaryColor +
      ';\n      color: white;\n      cursor: pointer;\n    '
    header.innerHTML =
      '\n      <div style="display: flex; align-items: center; gap: 8px;">\n        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>\n        <span style="font-size: 14px; font-weight: 500;">' +
      config.botName +
      '</span>\n      </div>\n      <button id="mchat-widget-close" style="background: none; border: none; color: white; cursor: pointer; padding: 4px; border-radius: 4px;">\n        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>\n      </button>\n    '
    header.onclick = function () {
      STATE.isMinimized = !STATE.isMinimized
      messagesContainer.style.display = STATE.isMinimized ? 'none' : 'block'
      inputArea.style.display = STATE.isMinimized ? 'none' : 'block'
    }
    header
      .querySelector('#mchat-widget-close')
      .addEventListener('click', function (e) {
        e.stopPropagation()
        closeWidget()
      })

    // Messages container
    var messagesContainer = document.createElement('div')
    messagesContainer.style.cssText =
      '\n      flex: 1;\n      overflow-y: auto;\n      padding: 16px;\n      background: #f9fafb;\n      display: flex;\n      flex-direction: column;\n      gap: 12px;\n    '

    // Input area
    var inputArea = document.createElement('div')
    inputArea.style.cssText =
      '\n      border-top: 1px solid #e5e7eb;\n      padding: 12px;\n      background: white;\n      display: flex;\n      gap: 8px;\n      align-items: flex-end;\n    '

    var textarea = document.createElement('textarea')
    textarea.placeholder = '输入消息...'
    textarea.rows = 1
    textarea.style.cssText =
      '\n      flex: 1;\n      resize: none;\n      border: 1px solid #d1d5db;\n      border-radius: 12px;\n      padding: 8px 12px;\n      font-size: 14px;\n      font-family: inherit;\n      outline: none;\n      line-height: 1.5;\n      min-height: 42px;\n      height: auto;\n      max-height: 120px;\n    '
    textarea.onfocus = function () {
      textarea.style.borderColor = config.primaryColor
    }
    textarea.onblur = function () {
      textarea.style.borderColor = '#d1d5db'
    }
    textarea.oninput = function () {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    }
    textarea.onkeydown = function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
      }
    }

    var sendButton = document.createElement('button')
    sendButton.style.cssText =
      '\n      width: 40px;\n      height: 40px;\n      border-radius: 12px;\n      border: none;\n      background-color: ' +
      config.primaryColor +
      ';\n      color: white;\n      cursor: pointer;\n      display: flex;\n      align-items: center;\n      justify-content: center;\n      flex-shrink: 0;\n      transition: opacity 0.2s;\n    '
    sendButton.innerHTML =
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>'
    sendButton.onclick = sendMessage

    inputArea.appendChild(textarea)
    inputArea.appendChild(sendButton)

    chatWindow.appendChild(header)
    chatWindow.appendChild(messagesContainer)
    chatWindow.appendChild(inputArea)

    container.appendChild(chatWindow)
    document.body.appendChild(container)

    elements.chatWindow = chatWindow
    elements.messagesContainer = messagesContainer
    elements.textarea = textarea
    elements.sendButton = sendButton
  }

  function renderMessages() {
    elements.messagesContainer.innerHTML = ''
    STATE.messages.forEach(function (msg) {
      var bubble = document.createElement('div')
      var isUser = msg.role === 'user'
      bubble.style.cssText =
        '\n        display: flex;\n        justify-content: ' +
        (isUser ? 'flex-end' : 'flex-start') +
        ';\n        animation: mchat-message-fade-in 0.3s ease-out;\n      '

      var content = document.createElement('div')
      var borderRadius = isUser
        ? '16px 16px 4px 16px'
        : '16px 16px 16px 4px'
      content.style.cssText =
        '\n        max-width: 85%;\n        padding: 10px 14px;\n        border-radius: ' +
        borderRadius +
        ';\n        font-size: 14px;\n        line-height: 1.5;\n        word-wrap: break-word;\n        ' +
        (isUser
          ? 'background-color: ' +
            config.primaryColor +
            '; color: white;'
          : 'background: white; border: 1px solid #e5e7eb; color: #374151;') +
        '\n      '
      content.textContent = msg.content

      var time = document.createElement('div')
      time.style.cssText =
        '\n        font-size: 11px;\n        margin-top: 4px;\n        ' +
        (isUser ? 'opacity: 0.7; text-align: right;' : 'color: #9ca3af;') +
        '\n      '
      time.textContent = new Date(msg.timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      })

      content.appendChild(time)
      bubble.appendChild(content)
      elements.messagesContainer.appendChild(bubble)
    })

    // Scroll to bottom
    elements.messagesContainer.scrollTop =
      elements.messagesContainer.scrollHeight
  }

  function sendMessage() {
    var text = elements.textarea.value.trim()
    if (!text || STATE.isLoading) return

    elements.textarea.value = ''
    elements.textarea.style.height = 'auto'

    STATE.messages.push({
      id: 'user-' + Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    })

    STATE.isLoading = true
    renderMessages()
    showTyping()

    var xhr = new XMLHttpRequest()
    xhr.open(
      'POST',
      config.apiUrl + '/widget/' + config.agentId + '/chat',
      true,
    )
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.onload = function () {
      STATE.isLoading = false
      hideTyping()

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText)

          if (data.conversationId && window.localStorage) {
            try {
              window.localStorage.setItem(
                'mchat_widget_conv_' + config.agentId,
                data.conversationId,
              )
            } catch (e) {}
          }

          STATE.messages.push({
            id: 'assistant-' + Date.now(),
            role: 'assistant',
            content: data.response || data.message || '抱歉，我没有理解你的意思。',
            timestamp: new Date().toISOString(),
          })
        } catch (e) {
          STATE.messages.push({
            id: 'error-' + Date.now(),
            role: 'assistant',
            content: '抱歉，回复解析失败。',
            timestamp: new Date().toISOString(),
          })
        }
      } else {
        STATE.messages.push({
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: '网络请求失败，请稍后重试。',
          timestamp: new Date().toISOString(),
        })
      }

      renderMessages()
    }
    xhr.onerror = function () {
      STATE.isLoading = false
      hideTyping()
      STATE.messages.push({
        id: 'error-' + Date.now(),
        role: 'assistant',
        content: '网络连接失败，请检查网络后重试。',
        timestamp: new Date().toISOString(),
      })
      renderMessages()
    }
    xhr.send(JSON.stringify({ message: text, conversationId: (function(){ try { return window.localStorage.getItem('mchat_widget_conv_' + config.agentId) || window.localStorage.getItem('mchat_widget_conv') || null } catch(e){ return null } })() }))
  }

  function showTyping() {
    // Loading indicator
    var loader = document.createElement('div')
    loader.id = 'mchat-typing-indicator'
    loader.style.cssText =
      '\n      display: flex;\n      justify-content: flex-start;\n      animation: mchat-message-fade-in 0.3s ease-out;\n    '

    var bubble = document.createElement('div')
    bubble.style.cssText =
      '\n      background: white;\n      border: 1px solid #e5e7eb;\n      border-radius: 16px 16px 16px 4px;\n      padding: 12px 16px;\n      display: flex;\n      align-items: center;\n      gap: 4px;\n    '
    bubble.innerHTML =
      '\n      <div style="width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; animation: mchat-bounce 1s ease-in-out infinite;"></div>\n      <div style="width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; animation: mchat-bounce 1s ease-in-out 0.15s infinite;"></div>\n      <div style="width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; animation: mchat-bounce 1s ease-in-out 0.3s infinite;"></div>\n    '

    loader.appendChild(bubble)
    elements.messagesContainer.appendChild(loader)
    elements.messagesContainer.scrollTop =
      elements.messagesContainer.scrollHeight

    // Add bounce animation
    var bounceStyle = document.createElement('style')
    bounceStyle.id = 'mchat-bounce-style'
    bounceStyle.textContent =
      '\n      @keyframes mchat-bounce {\n        0%, 60%, 100% { transform: translateY(0); }\n        30% { transform: translateY(-4px); }\n      }\n    '
    if (!document.getElementById('mchat-bounce-style')) {
      document.head.appendChild(bounceStyle)
    }
  }

  function hideTyping() {
    var indicator = document.getElementById('mchat-typing-indicator')
    if (indicator) indicator.remove()
  }

  function toggleWidget() {
    if (STATE.isOpen) {
      closeWidget()
    } else {
      openWidget()
    }
  }

  function openWidget() {
    STATE.isOpen = true
    elements.chatWindow.style.display = 'flex'
    elements.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
    elements.textarea.focus()
  }

  function closeWidget() {
    STATE.isOpen = false
    elements.chatWindow.style.display = 'none'
    elements.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>'
  }

  // Initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createContainer)
  } else {
    createContainer()
  }
})()
