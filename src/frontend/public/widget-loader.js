/**
 * MChat Widget Loader v8 — iframe embed with in-page expand/shrink.
 */
(function () {
  'use strict'

  var LOADER_VERSION = '8'

  var scripts = document.getElementsByTagName('script')
  var script = scripts[scripts.length - 1]

  function originFromScript() {
    try {
      return new URL(script.src).origin
    } catch (e) {
      return window.location.origin
    }
  }

  var widgetOrigin = script.getAttribute('data-mchat-origin') || originFromScript()
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

  if (!config.agentId) {
    console.warn('[MChat] data-agent-id is required on the widget script tag')
    return
  }

  var state = { isOpen: false, isExpanded: false, width: null, height: null }
  var elements = {}

  var posSide = config.position === 'left' ? 'left' : 'right'

  function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val))
  }

  function normalSize() {
    var maxW = Math.max(320, window.innerWidth - 24)
    var maxH = Math.max(420, window.innerHeight - 24)
    var defaultW = Math.min(window.innerWidth - 32, 440)
    var defaultH = Math.min(window.innerHeight - 116, 720)
    return {
      width: clamp(state.width || defaultW, 320, maxW),
      height: clamp(state.height || defaultH, 420, maxH),
    }
  }

  function panelNormalStyle() {
    var size = normalSize()
    return (
      'position:fixed;bottom:92px;' +
      posSide +
      ':24px;z-index:2147483646;' +
      'width:' +
      size.width +
      'px;height:' +
      size.height +
      'px;' +
      'min-width:320px;min-height:420px;max-width:calc(100vw - 24px);max-width:calc(100dvw - 24px);max-height:calc(100vh - 24px);max-height:calc(100dvh - 24px);' +
      'resize:none;border:none;border-radius:16px;box-shadow:0 12px 48px rgba(0,0,0,0.18);overflow:hidden;background:transparent;'
    )
  }

  function panelExpandedStyle() {
    return (
      'position:fixed;top:12px;left:12px;z-index:2147483646;' +
      'width:calc(100vw - 24px);width:calc(100dvw - 24px);' +
      'height:calc(100vh - 24px);height:calc(100dvh - 24px);' +
      'max-width:none;max-height:none;border:none;border-radius:16px;' +
      'resize:none;box-shadow:0 12px 48px rgba(0,0,0,0.22);overflow:hidden;background:transparent;'
    )
  }

  function buildWidgetUrl(mode) {
    var q = new URLSearchParams({
      mode: mode,
      agentId: config.agentId,
      apiUrl: config.apiUrl,
      position: config.position,
      primaryColor: config.primaryColor,
      welcomeMessage: config.welcomeMessage,
      botName: config.botName,
    })
    return widgetOrigin + '/widget.html?' + q.toString()
  }

  function startResize(event) {
    if (state.isExpanded || !elements.panel) return
    event.preventDefault()
    event.stopPropagation()

    var rect = elements.panel.getBoundingClientRect()
    var startX = event.clientX
    var startY = event.clientY
    var startW = rect.width
    var startH = rect.height

    function onMove(e) {
      var dx = e.clientX - startX
      var dy = e.clientY - startY
      var maxW = Math.max(320, window.innerWidth - 24)
      var maxH = Math.max(420, window.innerHeight - 24)
      var nextW =
        posSide === 'right'
          ? clamp(startW - dx, 320, maxW)
          : clamp(startW + dx, 320, maxW)
      var nextH = clamp(startH + dy, 420, maxH)
      state.width = Math.round(nextW)
      state.height = Math.round(nextH)
      applyPanelLayout()
    }

    function onUp() {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }

    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  function applyPanelLayout() {
    if (!elements.panel) return
    var layout = state.isExpanded ? panelExpandedStyle() : panelNormalStyle()
    elements.panel.style.cssText =
      layout + 'display:' + (state.isOpen ? 'block' : 'none') + ';'
    if (elements.iframe) {
      elements.iframe.style.cssText =
        'width:100%;height:100%;border:0;border-radius:16px;display:block;'
    }
    if (elements.resizeHandle) {
      elements.resizeHandle.style.display =
        state.isOpen && !state.isExpanded ? 'block' : 'none'
    }
  }

  function createUI() {
    var button = document.createElement('button')
    button.type = 'button'
    button.id = 'mchat-widget-button'
    button.setAttribute('aria-label', 'Open chat')
    button.style.cssText =
      'position:fixed;bottom:24px;' +
      posSide +
      ':24px;z-index:2147483646;width:56px;height:56px;border-radius:50%;border:none;background-color:' +
      config.primaryColor +
      ';color:#fff;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.18);display:flex;align-items:center;justify-content:center;transition:transform 0.2s ease, box-shadow 0.2s ease;'
    button.innerHTML =
      '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
    button.onmouseover = function () {
      button.style.transform = 'scale(1.08)'
    }
    button.onmouseout = function () {
      button.style.transform = ''
    }
    button.onclick = toggleWidget

    var panel = document.createElement('div')
    panel.id = 'mchat-widget-panel'
    panel.style.touchAction = 'none'

    var iframe = document.createElement('iframe')
    iframe.id = 'mchat-widget-iframe'
    iframe.src = buildWidgetUrl('embed')
    iframe.title = config.botName
    iframe.setAttribute('allow', 'microphone')
    iframe.style.cssText = 'width:100%;height:100%;border:0;border-radius:16px;display:block;'
    panel.appendChild(iframe)

    var resizeHandle = document.createElement('div')
    resizeHandle.id = 'mchat-widget-resize-handle'
    resizeHandle.title = '拖拽调大小'
    resizeHandle.setAttribute('role', 'button')
    resizeHandle.setAttribute('aria-label', 'Resize widget')
    resizeHandle.style.cssText =
      'position:absolute;left:0;bottom:0;z-index:2147483647;width:16px;height:16px;' +
      'cursor:nesw-resize;pointer-events:auto;' +
      'background:linear-gradient(135deg,transparent 0%,transparent 45%,' +
      config.primaryColor +
      ' 46%,' +
      config.primaryColor +
      ' 100%);opacity:0.55;border-radius:0 0 0 16px;'
    resizeHandle.onpointerdown = startResize
    resizeHandle.onmouseenter = function () {
      resizeHandle.style.opacity = '0.85'
    }
    resizeHandle.onmouseleave = function () {
      resizeHandle.style.opacity = '0.55'
    }
    panel.appendChild(resizeHandle)

    document.body.appendChild(button)
    document.body.appendChild(panel)

    elements.button = button
    elements.panel = panel
    elements.iframe = iframe
    elements.resizeHandle = resizeHandle
    applyPanelLayout()
  }

  function setOpen(open) {
    state.isOpen = open
    if (!open) state.isExpanded = false
    applyPanelLayout()
    elements.button.innerHTML = open
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
      : '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
  }

  function setExpanded(expanded) {
    state.isExpanded = expanded
    if (expanded) state.isOpen = true
    applyPanelLayout()
  }

  function toggleWidget() {
    setOpen(!state.isOpen)
  }

  window.MChatWidget = {
    version: LOADER_VERSION,
    open: function () {
      setOpen(true)
    },
    close: function () {
      setOpen(false)
    },
    toggle: toggleWidget,
    expand: function () {
      setOpen(true)
      setExpanded(true)
    },
    shrink: function () {
      setExpanded(false)
    },
    openFullscreen: function () {
      setOpen(true)
      setExpanded(true)
    },
  }

  window.addEventListener('message', function (event) {
    if (!event.data || !event.data.type) return
    if (event.origin !== widgetOrigin) return
    if (event.data.type === 'mchat:close') {
      setOpen(false)
      return
    }
    if (event.data.type === 'mchat:resize') {
      setExpanded(!!event.data.expanded)
    }
  })

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createUI)
  } else {
    createUI()
  }
})()
