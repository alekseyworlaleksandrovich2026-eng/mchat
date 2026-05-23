import { useEffect, useMemo, useState } from 'react'

function getParams(): { url: string; name: string } {
  const p = new URLSearchParams(window.location.search)
  return {
    url: p.get('url') || '',
    name: p.get('name') || '',
  }
}

export function MpJump() {
  const { url, name } = useMemo(() => getParams(), [])
  const [status, setStatus] = useState<'jumping' | 'no-wechat'>('jumping')
  const isWechat = /MicroMessenger/i.test(navigator.userAgent)

  useEffect(() => {
    if (!url) { setStatus('no-wechat'); return }
    if (isWechat) { window.location.href = url; return }
    setStatus('no-wechat')
  }, [url, isWechat])

  const displayName = name || 'Mini Program'

  if (!url) {
    return (
      <div style={{ display:'flex',alignItems:'center',justifyContent:'center',height:'100dvh',fontFamily:'system-ui,sans-serif',color:'#666',textAlign:'center',padding:24 }}>
        <div>Need <code>?url=</code> parameter</div>
      </div>
    )
  }

  return (
    <div style={{ display:'flex',alignItems:'center',justifyContent:'center',height:'100dvh',fontFamily:'system-ui,sans-serif',textAlign:'center',padding:24,background:'#f5f5f5' }}>
      {status === 'jumping' && isWechat ? (
        <div style={{ color:'#666',fontSize:14 }}>
          <div style={{ marginBottom:12,fontSize:32 }}>🔄</div>
          <div>Opening {displayName}...</div>
        </div>
      ) : (
        <div style={{ maxWidth:320 }}>
          <div style={{ fontSize:40,marginBottom:12 }}>📱</div>
          <div style={{ fontWeight:700,fontSize:16,color:'#333',marginBottom:8 }}>Open in WeChat</div>
          <div style={{ fontSize:14,color:'#666',marginBottom:20 }}>
            Open this link in WeChat to access <strong>{displayName}</strong>.
          </div>
          <a href={url} style={{ display:'inline-block',padding:'12px 28px',background:'#07c160',color:'#fff',borderRadius:8,fontSize:15,fontWeight:600,textDecoration:'none' }}>
            Open {displayName}
          </a>
        </div>
      )}
    </div>
  )
}
