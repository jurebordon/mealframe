'use client'

const c = {
  bg: '#0d0c0b',
  text: '#f0ede8',
  textMuted: 'rgba(240,237,232,0.50)',
  accent: '#c47a30',
  border: 'rgba(255,255,255,0.08)',
}

export default function PrivacyPage() {
  return (
    <div
      className="min-h-screen"
      style={{ background: c.bg, color: c.text }}
    >
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="px-6 py-6 md:px-12">
        <a
          href="/waitlist"
          style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: c.textMuted }}
        >
          &larr; MealFrame
        </a>
      </header>

      {/* ── Content ─────────────────────────────────────────────── */}
      <main className="mx-auto max-w-2xl px-6 pb-24 pt-8 md:px-12">
        <h1
          className="mb-2 text-3xl font-bold tracking-tight md:text-4xl"
          style={{ color: c.text }}
        >
          Privacy Policy
        </h1>
        <p className="mb-12" style={{ fontSize: 14, color: c.textMuted }}>
          Last updated: February 25, 2026
        </p>

        <div className="space-y-10" style={{ fontSize: 15, lineHeight: 1.7, color: 'rgba(240,237,232,0.80)' }}>
          {/* ── Intro ─────────────────────────────────────── */}
          <section>
            <p>
              MealFrame (&ldquo;we&rdquo;, &ldquo;us&rdquo;) is a meal planning application
              built by an independent developer. This policy explains what data
              we collect through our waitlist page and how we handle it.
            </p>
          </section>

          {/* ── What we collect ────────────────────────────── */}
          <section>
            <H2>What we collect</H2>

            <H3>Email address</H3>
            <p>
              When you join the waitlist, we collect your email address. This is
              stored in a Google Sheets spreadsheet and used solely to notify you
              when early access opens.
            </p>

            <H3>Pageview analytics</H3>
            <p>
              We run lightweight, self-hosted analytics on our landing page. Each
              pageview records:
            </p>
            <ul className="ml-5 mt-2 list-disc space-y-1">
              <li>Page URL and referrer</li>
              <li>Browser user-agent string</li>
              <li>A privacy-friendly hash of your IP address (rotated daily &mdash; we never store raw IPs)</li>
              <li>A random session identifier stored in your browser&apos;s localStorage</li>
            </ul>
            <p className="mt-3">
              This data helps us understand how people find MealFrame. We do not
              use third-party analytics services, advertising pixels, or
              cross-site tracking of any kind.
            </p>

            <H3>Local storage</H3>
            <p>
              We store two small values in your browser&apos;s localStorage (not
              cookies):
            </p>
            <ul className="ml-5 mt-2 list-disc space-y-1">
              <li>
                <strong>Waitlist status</strong> &mdash; remembers that you
                already signed up, so the form shows a confirmation instead of
                asking again.
              </li>
              <li>
                <strong>Session ID</strong> &mdash; a random identifier for
                grouping pageviews in a single visit. Contains no personal
                information.
              </li>
            </ul>
          </section>

          {/* ── Cookies ────────────────────────────────────── */}
          <section>
            <H2>Cookies</H2>
            <p>
              MealFrame does not set any cookies on the waitlist page.
            </p>
          </section>

          {/* ── Third parties ──────────────────────────────── */}
          <section>
            <H2>Third parties</H2>
            <p>Your data is shared with the following services:</p>
            <ul className="ml-5 mt-2 list-disc space-y-1">
              <li>
                <strong>Google Sheets</strong> (via Google Apps Script) &mdash;
                stores waitlist email addresses.{' '}
                <a
                  href="https://policies.google.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: c.accent, textDecoration: 'underline', textUnderlineOffset: '3px' }}
                >
                  Google&apos;s Privacy Policy
                </a>
              </li>
              <li>
                <strong>Hosting provider</strong> &mdash; serves the website and
                may process standard server logs (IP addresses, request
                timestamps).
              </li>
            </ul>
            <p className="mt-3">
              We do not sell, rent, or share your data with advertisers or data
              brokers.
            </p>
          </section>

          {/* ── Data retention ─────────────────────────────── */}
          <section>
            <H2>Data retention</H2>
            <ul className="ml-5 list-disc space-y-1">
              <li>
                <strong>Email addresses</strong> are retained until you
                unsubscribe or ask us to delete them.
              </li>
              <li>
                <strong>Pageview data</strong> is retained for up to 12 months,
                then deleted.
              </li>
              <li>
                <strong>IP hashes</strong> rotate daily and cannot be reversed
                to recover your IP address.
              </li>
            </ul>
          </section>

          {/* ── Your rights ────────────────────────────────── */}
          <section>
            <H2>Your rights</H2>
            <p>You can at any time:</p>
            <ul className="ml-5 mt-2 list-disc space-y-1">
              <li>Request a copy of the data we hold about you</li>
              <li>Ask us to delete your email from the waitlist</li>
              <li>Clear localStorage in your browser to remove local data</li>
            </ul>
            <p className="mt-3">
              To make a request, email us at{' '}
              <a
                href="mailto:hello@mealframe.io"
                style={{ color: c.accent, textDecoration: 'underline', textUnderlineOffset: '3px' }}
              >
                hello@mealframe.io
              </a>
              .
            </p>
          </section>

          {/* ── Changes ────────────────────────────────────── */}
          <section>
            <H2>Changes to this policy</H2>
            <p>
              If we make material changes, we will update the date at the top of
              this page. For significant changes, we may also notify waitlist
              subscribers by email.
            </p>
          </section>

          {/* ── Contact ────────────────────────────────────── */}
          <section>
            <H2>Contact</H2>
            <p>
              Questions or concerns? Reach us at{' '}
              <a
                href="mailto:hello@mealframe.io"
                style={{ color: c.accent, textDecoration: 'underline', textUnderlineOffset: '3px' }}
              >
                hello@mealframe.io
              </a>
              .
            </p>
          </section>
        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer
        className="flex items-center justify-between px-6 py-6 md:px-12"
        style={{ borderTop: `1px solid ${c.border}` }}
      >
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: c.textMuted }}>
          MealFrame
        </span>
        <p style={{ fontSize: 12, color: c.textMuted }}>
          &copy; {new Date().getFullYear()}
        </p>
      </footer>
    </div>
  )
}

/* ── Heading helpers ──────────────────────────────────────────── */

function H2({ children }: { children: React.ReactNode }) {
  return (
    <h2
      className="mb-3 text-lg font-semibold"
      style={{ color: '#f0ede8' }}
    >
      {children}
    </h2>
  )
}

function H3({ children }: { children: React.ReactNode }) {
  return (
    <h3
      className="mb-1 mt-5 text-sm font-semibold uppercase tracking-wider"
      style={{ color: 'rgba(240,237,232,0.60)' }}
    >
      {children}
    </h3>
  )
}
