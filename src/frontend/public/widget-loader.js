/**
 * MChat Widget Loader v16 — iframe embed; drag inner edge to resize width (ew).
 * Bump ?v= on the script tag when embedding; version is passed through to widget.html.
 */
(function () {
  'use strict'

  var LOADER_VERSION = '16'

  var scripts = document.getElementsByTagName('script')
  var script = scripts[scripts.length - 1]

  function resolveLoaderVersion() {
    try {
      var fromUrl = new URL(script.src).searchParams.get('v')
      if (fromUrl) return fromUrl
    } catch (e) {
      /* ignore */
    }
    return LOADER_VERSION
  }

  var cacheVersion = resolveLoaderVersion()

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
    launcherIcon: script.getAttribute('data-launcher-icon') || 'chat',
    launcherText: script.getAttribute('data-launcher-text') || '',
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
      launcherIcon: config.launcherIcon,
      launcherText: config.launcherText,
      _v: cacheVersion,
    })
    return widgetOrigin + '/widget.html?' + q.toString()
  }

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
  }

  function launcherSvg(name, size) {
    var n = String(name || 'chat').toLowerCase()
    var s = size || 24
    if (n === 'bot' || n === 'robot') {
      return (
        '<svg width="' +
        s +
        '" height="' +
        s +
        '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<rect x="3" y="11" width="18" height="10" rx="2"/>' +
        '<circle cx="8" cy="16" r="1"/><circle cx="16" cy="16" r="1"/>' +
        '<path d="M12 11V7"/><path d="M8 7h8"/>' +
        '</svg>'
      )
    }
    if (n === 'spark' || n === 'sparkles') {
      return (
        '<svg width="' +
        s +
        '" height="' +
        s +
        '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<path d="M12 3l1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3z"/>' +
        '<path d="M19 14l.9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14z"/>' +
        '</svg>'
      )
    }
    if (n === 'support' || n === 'headset') {
      return (
        '<svg width="' +
        s +
        '" height="' +
        s +
        '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<path d="M4 13a8 8 0 0 1 16 0"/>' +
        '<rect x="2" y="12" width="4" height="7" rx="1"/>' +
        '<rect x="18" y="12" width="4" height="7" rx="1"/>' +
        '<path d="M18 19a4 4 0 0 1-4 4h-2"/>' +
        '</svg>'
      )
    }
    return (
      '<svg width="' +
      s +
      '" height="' +
      s +
      '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' +
      '</svg>'
    )
  }

  function closeSvg() {
    return (
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>' +
      '</svg>'
    )
  }

  function applyLauncherButton(open) {
    if (!elements.button) return

    var label = String(config.launcherText || '').trim()
    var hasText = !open && label.length > 0
    var baseStyle =
      'position:fixed;bottom:24px;' +
      posSide +
      ':24px;z-index:2147483646;border:none;background-color:' +
      config.primaryColor +
      ';color:#fff;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.18);display:flex;align-items:center;justify-content:center;transition:transform 0.2s ease, box-shadow 0.2s ease;'

    elements.button.style.cssText = hasText
      ? baseStyle +
        'height:48px;padding:0 16px;border-radius:999px;gap:8px;'
      : baseStyle + 'width:56px;height:56px;border-radius:50%;'

    if (open) {
      elements.button.innerHTML = closeSvg()
      return
    }

    if (hasText) {
      elements.button.innerHTML =
        launcherSvg(config.launcherIcon, 20) +
        '<span style="font-size:14px;font-weight:600;line-height:1;white-space:nowrap;">' +
        escapeHtml(label) +
        '</span>'
      return
    }

    elements.button.innerHTML = launcherSvg(config.launcherIcon, 26)
  }

  function startResize(event) {
    if (state.isExpanded || !elements.panel) return
    event.preventDefault()
    event.stopPropagation()

    var rect = elements.panel.getBoundingClientRect()
    var startX = event.clientX
    var startW = rect.width

    function onMove(e) {
      var dx = e.clientX - startX
      var maxW = Math.max(320, window.innerWidth - 24)
      var nextW =
        posSide === 'right'
          ? clamp(startW - dx, 320, maxW)
          : clamp(startW + dx, 320, maxW)
      state.width = Math.round(nextW)
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
    resizeHandle.title = '左右拖拽调整宽度'
    resizeHandle.setAttribute('role', 'separator')
    resizeHandle.setAttribute('aria-label', 'Resize widget width')
    var edgeSide = posSide === 'right' ? 'left:0;' : 'right:0;'
    resizeHandle.style.cssText =
      'position:absolute;top:0;bottom:0;' +
      edgeSide +
      'z-index:2147483647;width:10px;cursor:ew-resize;pointer-events:auto;' +
      'background:transparent;'
    resizeHandle.onpointerdown = startResize
    resizeHandle.onmouseenter = function () {
      resizeHandle.style.background =
        'linear-gradient(to ' +
        (posSide === 'right' ? 'left' : 'right') +
        ', rgba(0,0,0,0.06), transparent)'
    }
    resizeHandle.onmouseleave = function () {
      resizeHandle.style.background = 'transparent'
    }
    panel.appendChild(resizeHandle)

    document.body.appendChild(button)
    document.body.appendChild(panel)

    elements.button = button
    elements.panel = panel
    elements.iframe = iframe
    elements.resizeHandle = resizeHandle
    applyLauncherButton(false)
    applyPanelLayout()
  }

  function setOpen(open) {
    state.isOpen = open
    if (!open) state.isExpanded = false
    applyPanelLayout()
    applyLauncherButton(open)
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
