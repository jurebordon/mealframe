# v0 Prompt 1 — Full Landing Page (Primary)

Build a single-page waitlist landing page for MealFrame, a meal planning app. 
This is a standalone Next.js page (not the app itself) for collecting early 
access emails.

## DESIGN SYSTEM
- Dark theme: background #0f0f0f or similar near-black
- Accent color: warm amber/orange (not green - this should feel different from 
  typical health apps)
- Font: Inter or similar clean sans-serif
- Spacing: generous, breathable - this is minimal and premium
- No rounded pill buttons - use slightly rounded rectangles (radius ~6px)
- Subtle borders: 1px solid with low opacity white for card edges

## PAGE STRUCTURE (single scroll, no navigation)

### 1. HERO SECTION
- Headline: "Plan when calm. Follow when stressed."
- Subheadline: "Eliminate food decisions. Beat evening overeating. Exact 
  portions, zero willpower required."
- Email input + "Join Waitlist" CTA button (full width on mobile, 
  inline on desktop)
- Below form: small trust line "No spam. Notified when testing opens."
- Right side or below (mobile): a stat card showing "91% adherence rate" 
  with "Week 1 results" label - styled like an app metric card, dark with 
  amber accent

### 2. THE PROBLEM (narrow centered column, max-w-2xl)
- Section eyebrow: "SOUND FAMILIAR?"
- Headline: "You know what to eat. You just eat too much of it."
- 3 short problem statements in a grid or list - no icons, just bold lead 
  text + 1 sentence:
  * "Decision fatigue is real" - By 8pm, your willpower is gone. 
    That's when the damage happens.
  * "Tracking is reactive" - Logging what you ate doesn't stop you 
    from eating it.
  * "Flexibility backfires" - "I'll figure out dinner later" always 
    ends the same way.

### 3. THE SOLUTION (slightly different background - maybe #161616)
- Eyebrow: "HOW MEALFRAME WORKS"
- Headline: "Instructions, not suggestions."
- 2-column feature layout:
  * "Plan once on Sunday" - Generate your full week in 2 minutes. 
    No daily decisions.
  * "Exact portions" - "2 eggs + 1 slice toast + 10g butter" — 
    not "eat healthy breakfast"
  * "Follow, don't decide" - When stress hits, open the app. 
    It tells you what to eat.
  * "Track completion" - One tap. Done. Watch your adherence rate build.

### 4. EARLY RESULTS
- Full-width dark card with amber accent border
- Large stat: "91%"
- Label: "adherence rate, week 1"
- Subtext: "Built to solve my own evening overeating. After years of 
  failed tracking apps, exact portions + zero flexibility actually worked."
- Secondary stat: "7-day streak" in smaller treatment

### 5. ABOUT
- Minimal: small photo (circular, 64px), name "Jure", 
  title "Product & Data Leader"
- 2 sentences: "I build tools to solve my own problems. MealFrame 
  started as a personal experiment — now I'm opening it to early testers."
- LinkedIn link (subtle, text link)

### 6. FINAL CTA
- Repeat headline: "Get early access"
- Subtext: "Launching to testers in March 2025. Join the waitlist."
- Same email form as hero
- Fine print: "We'll notify you when testing opens. No spam, 
  unsubscribe anytime."

## TECHNICAL REQUIREMENTS
- Form submission: POST to a Google Apps Script URL stored in an env 
  variable (NEXT_PUBLIC_GOOGLE_SCRIPT_URL). On success show inline 
  success state (replace button with "You're on the list ✓" in amber). 
  Disable form after submission to prevent duplicates.
- Basic email validation before submit
- Loading state on button during submission
- Error state if submission fails: "Something went wrong. Try again."
- Both forms share the same submission logic (extract to a hook or 
  shared function)

## RESPONSIVE
- Mobile-first
- Hero stacks vertically on mobile, stat card goes below form
- Problem grid: 1 col mobile, 3 col desktop
- Solution grid: 1 col mobile, 2 col desktop
- About section centered on mobile

NO placeholders for images - use a styled div for the profile photo 
(initials "J" in a circle) and skip the screenshot for now.

## SEO REQUIREMENTS

### Head tags
- `<title>`: "MealFrame — Plan when calm, follow when stressed"
- `<meta name="description">`: "MealFrame eliminates food decisions with exact meal portions and structured weekly plans. Beat evening overeating without willpower. Join the early access waitlist."
- `<link rel="canonical">` pointing to the production URL (use env variable NEXT_PUBLIC_SITE_URL, fallback to https://mealframe-waitlist.vercel.app)

### Open Graph + Twitter
- `og:title`: "MealFrame — Plan when calm, follow when stressed"
- `og:description`: same as meta description above
- `og:type`: "website"
- `og:url`: canonical URL
- `og:image`: /og-image.png (placeholder path)
- `twitter:card`: "summary_large_image"
- `twitter:title` and `twitter:description`: same as og equivalents

### Semantic HTML structure
- Use a single `<h1>` for the hero headline only
- All other section headlines use `<h2>`
- Problem and solution items use `<h3>`
- Wrap the about section in `<section aria-label="About the creator">`
- Both email forms use proper `<label>` elements (visually hidden is fine) linked to inputs via `htmlFor`
- Stat figures use `<figure>` + `<figcaption>` markup

### Performance basics
- Add `<link rel="preconnect">` for Google Fonts if used
- Defer non-critical scripts
- All images (when added) should include descriptive `alt` attributes
