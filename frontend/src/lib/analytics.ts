/**
 * Lightweight analytics client for landing pages.
 * Fire-and-forget — failures are silently ignored.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003/api/v1'
const ANALYTICS_URL = `${API_BASE_URL}/analytics/pageview`

const SESSION_KEY = 'mf_session_id'

function getSessionId(): string {
  try {
    let id = localStorage.getItem(SESSION_KEY)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(SESSION_KEY, id)
    }
    return id
  } catch {
    return crypto.randomUUID()
  }
}

export function trackPageview(pageUrl: string): void {
  try {
    fetch(ANALYTICS_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        page_url: pageUrl,
        referrer: document.referrer || null,
        session_id: getSessionId(),
      }),
      keepalive: true,
    }).catch(() => {})
  } catch {
    // Analytics should never break the page
  }
}
