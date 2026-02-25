'use client'

import { useEffect, useRef, useState } from 'react'
import { WaitlistForm } from '@/components/landing/waitlist-form'
import { trackPageview } from '@/lib/analytics'

/* ─── Design tokens ─────────────────────────────────────────────────────── */
const c = {
  bg: '#0d0c0b',
  bgAlt: '#111010',
  bgCard: '#181614',
  border: 'rgba(255,255,255,0.08)',
  borderStrong: 'rgba(255,255,255,0.14)',
  amber: '#c47a30',
  amberDim: 'rgba(196,122,48,0.10)',
  amberBorder: 'rgba(196,122,48,0.28)',
  text: '#f0ede8',
  textMuted: '#7a7370',
  textDim: '#b0aaa4',
}

/* ─── Scroll-fade hook ───────────────────────────────────────────────────── */
function useFadeIn() {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); observer.disconnect() } },
      { threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return { ref, style: { opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(24px)', transition: 'opacity 0.55s ease, transform 0.55s ease' } }
}

/* ─── Sticky header ──────────────────────────────────────────────────────── */
function StickyHeader() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 480)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const scrollToForm = () => {
    document.getElementById('waitlist-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <div
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        background: 'rgba(13,12,11,0.90)',
        backdropFilter: 'blur(12px)',
        borderBottom: `1px solid ${c.border}`,
        opacity: show ? 1 : 0,
        pointerEvents: show ? 'auto' : 'none',
        transform: show ? 'translateY(0)' : 'translateY(-8px)',
        transition: 'opacity 0.3s ease, transform 0.3s ease',
      }}
    >
      <div style={{ maxWidth: 1024, margin: '0 auto', padding: '0 24px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: c.text }}>
          MealFrame
        </span>
        <button
          onClick={scrollToForm}
          style={{
            padding: '7px 16px', fontSize: 13, fontWeight: 600,
            background: c.amber, color: '#0d0c0b', border: 'none',
            borderRadius: 6, cursor: 'pointer', letterSpacing: '0.02em',
          }}
        >
          Join Waitlist
        </button>
      </div>
    </div>
  )
}

/* ─── Section wrapper with fade-in ──────────────────────────────────────── */
function FadeSection({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  const fade = useFadeIn()
  return (
    <div ref={fade.ref} style={{ ...fade.style, ...style }}>
      {children}
    </div>
  )
}

/* ─── Main page ─────────────────────────────────────────────────────────── */
export default function WaitlistPage() {
  useEffect(() => {
    trackPageview('/waitlist')
  }, [])

  const scrollToForm = () => {
    document.getElementById('waitlist-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <div style={{ background: c.bg, color: c.text, minHeight: '100vh', fontFamily: 'inherit' }}>
      <StickyHeader />

      {/* ── Wordmark header ──────────────────────────────────────────── */}
      <header
        style={{ borderBottom: `1px solid ${c.border}`, padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        className="md:px-12"
      >
        <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: c.text }}>
          MealFrame
        </span>
        <button
          onClick={scrollToForm}
          style={{ fontSize: 12, color: c.amber, background: 'none', border: `1px solid ${c.amberBorder}`, borderRadius: 5, padding: '5px 12px', cursor: 'pointer', fontWeight: 600, letterSpacing: '0.04em' }}
        >
          Early access
        </button>
      </header>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-5xl px-6 py-20 md:px-12 md:py-32" style={{ position: 'relative', overflow: 'hidden' }}>
        {/* Subtle noise/gradient bg */}
        <div aria-hidden="true" style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          background: `radial-gradient(ellipse 70% 60% at 60% 0%, rgba(196,122,48,0.07) 0%, transparent 70%)`,
        }} />

        <div className="flex flex-col gap-16 md:flex-row md:items-start md:gap-12" style={{ position: 'relative' }}>

          {/* Left — copy + form */}
          <div className="flex flex-1 flex-col gap-8">
            <div className="flex flex-col gap-5">
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: c.amber }}>
                Now accepting early testers
              </p>
              <h1
                className="text-balance text-4xl font-bold md:text-5xl lg:text-6xl"
                style={{ color: c.text, lineHeight: 1.08, letterSpacing: '-0.02em' }}
              >
                Plan when calm.{' '}
                <span style={{ color: c.amber }}>Follow</span>{' '}
                when stressed.
              </h1>
              <p
                className="text-balance text-lg leading-relaxed md:text-xl"
                style={{ color: c.textDim, maxWidth: '38ch' }}
              >
                Eliminate food decisions. Beat evening overeating. Exact portions, zero willpower required.
              </p>
            </div>

            <div className="flex flex-col gap-3" id="waitlist-form">
              <WaitlistForm id="hero" size="large" />
              <p style={{ fontSize: 12, color: c.textMuted }}>No spam. Notified when testing opens.</p>
            </div>
          </div>

          {/* Right — stat card */}
          <div className="md:w-64 lg:w-72">
            <figure
              className="rounded-xl p-6"
              style={{ background: c.bgCard, border: `1px solid ${c.amberBorder}`, position: 'relative' }}
            >
              {/* MEALFRAME label */}
              <span style={{
                position: 'absolute', top: 12, left: 14,
                fontSize: 9, fontWeight: 700, letterSpacing: '0.18em',
                textTransform: 'uppercase', color: c.amber, opacity: 0.6,
              }}>
                MealFrame
              </span>

              <div className="mb-4 mt-4 flex items-start justify-between">
                <div
                  className="rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wider"
                  style={{ background: c.amberDim, color: c.amber, fontSize: 10 }}
                >
                  Week 1
                </div>
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ background: c.amber, boxShadow: `0 0 6px ${c.amber}` }}
                />
              </div>

              <p
                className="leading-none"
                style={{ fontSize: 64, fontWeight: 800, color: c.text, letterSpacing: '-0.03em' }}
                aria-label="91 percent adherence rate"
              >
                91<span style={{ fontSize: 28, color: c.amber, fontWeight: 700 }}>%</span>
              </p>
              <figcaption style={{ marginTop: 6, fontSize: 13, color: c.textDim }}>
                adherence rate
              </figcaption>

              <div
                style={{ marginTop: 20, paddingTop: 16, borderTop: `1px solid ${c.border}`, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: c.textDim }}
              >
                <svg className="h-4 w-4 shrink-0" style={{ color: c.amber }} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.047 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
                </svg>
                <span>7-day streak</span>
              </div>
            </figure>
          </div>
        </div>
      </section>

      {/* ── Problem ──────────────────────────────────────────────────── */}
      <section style={{ background: c.bgAlt }} className="px-6 py-20 md:px-12 md:py-28">
        <FadeSection>
          <div className="mx-auto max-w-3xl">
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: c.amber, marginBottom: 16 }}>
              Sound familiar?
            </p>
            <h2
              className="text-balance text-3xl font-bold md:text-4xl"
              style={{ color: c.text, lineHeight: 1.15 }}
            >
              You know what to eat.{' '}
              <br className="hidden md:block" />
              You just eat too much of it.
            </h2>

            <div className="mt-12 grid gap-8 md:grid-cols-3">
              {[
                { lead: 'Decision fatigue is real', body: 'By 8pm, your willpower is gone. That\'s when the damage happens.' },
                { lead: 'Tracking is reactive', body: 'Logging what you ate doesn\'t stop you from eating it.' },
                { lead: 'Flexibility backfires', body: '"I\'ll figure out dinner later" always ends the same way.' },
              ].map(({ lead, body }) => (
                <div key={lead} className="flex flex-col gap-2">
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: c.text }}>{lead}</h3>
                  <p style={{ fontSize: 14, lineHeight: 1.65, color: c.textDim }}>{body}</p>
                </div>
              ))}
            </div>
          </div>
        </FadeSection>
      </section>

      {/* ── Solution ─────────────────────────────────────────────────── */}
      <section className="px-6 py-20 md:px-12 md:py-28">
        <FadeSection>
          <div className="mx-auto max-w-3xl">
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: c.amber, marginBottom: 16 }}>
              How MealFrame works
            </p>
            <h2
              className="text-balance text-3xl font-bold md:text-4xl"
              style={{ color: c.text, lineHeight: 1.15 }}
            >
              Instructions, not suggestions.
            </h2>

            <div className="mt-12 grid gap-6 md:grid-cols-2">
              {[
                { title: 'Plan once on Sunday', body: 'Generate your full week in 2 minutes. No daily decisions.' },
                { title: 'Exact portions', body: '"3 spoons of oat flakes + 200ml milk + 1 banana" — not "eat healthy breakfast".' },
                { title: 'Follow, don\'t decide', body: 'When stress hits, open the app. It tells you what to eat.' },
                { title: 'Track completion', body: 'One tap. Done. Watch your adherence rate build.' },
              ].map(({ title, body }) => (
                <div
                  key={title}
                  className="rounded-lg p-5"
                  style={{ background: c.bgCard, border: `1px solid ${c.border}` }}
                >
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: c.text, marginBottom: 8 }}>{title}</h3>
                  <p style={{ fontSize: 14, lineHeight: 1.65, color: c.textDim }}>{body}</p>
                </div>
              ))}
            </div>
          </div>
        </FadeSection>
      </section>

      {/* ── Results ──────────────────────────────────────────────────── */}
      <section style={{ background: c.bgAlt }} className="px-6 py-20 md:px-12 md:py-28">
        <FadeSection>
          <div className="mx-auto max-w-3xl">
            <div
              className="rounded-xl p-8 md:p-12"
              style={{ background: c.bgCard, border: `1px solid ${c.amberBorder}` }}
            >
              <figure>
                <div className="flex flex-wrap items-end gap-6 md:gap-10">
                  <div>
                    <p
                      className="leading-none"
                      style={{ fontSize: 96, fontWeight: 800, color: c.text, letterSpacing: '-0.04em' }}
                      aria-label="91 percent"
                    >
                      91<span style={{ color: c.amber }}>%</span>
                    </p>
                    <figcaption style={{ marginTop: 8, fontSize: 15, color: c.textDim }}>
                      adherence rate, week 1
                    </figcaption>
                  </div>
                  <div
                    className="rounded px-3 py-1.5"
                    style={{ background: c.amberDim, color: c.amber, fontSize: 13, fontWeight: 600 }}
                  >
                    7-day streak
                  </div>
                </div>
                <p
                  style={{ marginTop: 32, fontSize: 15, lineHeight: 1.7, color: c.textDim, maxWidth: '52ch' }}
                >
                  Built to solve my own evening overeating. After years of failed tracking apps, exact portions&nbsp;+ zero flexibility actually worked.
                </p>
              </figure>
            </div>
          </div>
        </FadeSection>
      </section>

      {/* ── About ────────────────────────────────────────────────────── */}
      <section className="px-6 py-20 md:px-12 md:py-28" aria-label="About the creator">
        <FadeSection>
          <div className="mx-auto flex max-w-3xl flex-col items-center gap-5 text-center">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold"
              style={{ background: c.amberDim, border: `1px solid ${c.amberBorder}`, color: c.amber }}
              aria-label="Jure's profile"
            >
              J
            </div>
            <div>
              <p style={{ fontWeight: 600, color: c.text }}>Jure</p>
              <p style={{ fontSize: 13, color: c.textMuted, marginTop: 2 }}>Product &amp; Data Leader</p>
            </div>
            <p
              className="text-balance"
              style={{ fontSize: 15, lineHeight: 1.7, color: c.textDim, maxWidth: '44ch' }}
            >
              I build tools to solve my own problems. MealFrame started as a personal experiment&nbsp;— now I&apos;m opening it to early testers.
            </p>
            <a
              href="https://linkedin.com/in/jurebordon"
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 13, color: c.textMuted, textDecoration: 'underline', textUnderlineOffset: 4 }}
            >
              LinkedIn
            </a>
          </div>
        </FadeSection>
      </section>

      {/* ── Final CTA ────────────────────────────────────────────────── */}
      <section
        className="px-6 py-20 md:px-12 md:py-32"
        style={{ background: c.bgAlt, borderTop: `1px solid ${c.border}` }}
      >
        <FadeSection>
          <div className="mx-auto flex max-w-xl flex-col items-center gap-6 text-center">
            <h2
              className="text-balance text-3xl font-bold md:text-4xl"
              style={{ color: c.text, lineHeight: 1.15 }}
            >
              Get early access
            </h2>
            <p style={{ fontSize: 15, color: c.textDim }}>
              Launching to testers in March 2026. Join the waitlist.
            </p>
            <div className="w-full max-w-md">
              <WaitlistForm id="footer" size="large" />
            </div>
            <p style={{ fontSize: 12, color: c.textMuted }}>
              {"We'll notify you when testing opens. No spam, unsubscribe anytime."}
            </p>
          </div>
        </FadeSection>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer
        className="flex items-center justify-between px-6 py-6 md:px-12"
        style={{ borderTop: `1px solid ${c.border}` }}
      >
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: c.textMuted }}>
          MealFrame
        </span>
        <div className="flex items-center gap-4" style={{ fontSize: 12, color: c.textMuted }}>
          <a
            href="/privacy"
            style={{ textDecoration: 'underline', textUnderlineOffset: '3px' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = c.amber }}
            onMouseLeave={(e) => { e.currentTarget.style.color = c.textMuted }}
          >
            Privacy
          </a>
          <span>&copy; {new Date().getFullYear()}</span>
        </div>
      </footer>
    </div>
  )
}
