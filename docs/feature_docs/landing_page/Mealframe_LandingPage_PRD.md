# Product Requirements Document (PRD)
# MealFrame Waitlist Landing Page

**Version:** 1.0  
**Last Updated:** February 18, 2026  
**Status:** Ready for Implementation  
**Build Time:** One evening (2-3 hours)

---

## 1. Overview

### 1.1 Purpose

Single-page landing site to capture email signups for MealFrame early access. Serves as professional conversion point for LinkedIn traffic and demonstrates serious product intent.

### 1.2 Target User

- Saw MealFrame LinkedIn posts
- Interested in trying the app
- Won't comment publicly but will provide email
- Wants to be notified when testing opens

### 1.3 Core Value Proposition

Convert passive interest → active intent through low-friction email signup.

### 1.4 Non-Goals

- No pricing information (TBD)
- No feature list (keep simple)
- No blog/content (just signup)
- No user accounts (just email collection)

---

## 2. Content Structure

### 2.1 Hero Section

**Headline:** "MealFrame: Plan when calm, follow when stressed"

**Subheadline:** "Eliminate food decisions. Beat evening overeating. Exact portions, zero willpower required."

**Primary CTA:** Email input + "Join Waitlist" button

**Visual:** Screenshot of MealFrame stats page (91% adherence, 7-day streak)

### 2.2 The Problem (Brief)

3-4 sentences explaining:
- Decision fatigue leads to overeating
- You know WHAT to eat, but eat too MUCH
- Evening willpower is depleted
- Traditional tracking is reactive, not preventive

### 2.3 The Solution (Brief)

3-4 sentences explaining:
- Authoritative meal planning with exact portions
- No suggestions, no flexibility - just instructions
- Plan once on Sunday, execute all week
- "2 eggs + 2 slices bread" not "eat healthy"

### 2.4 Early Results

**Stat callout:** "91% adherence rate after week 1"

**Context:** Built for personal use, tested for 7 days, now expanding to early testers.

### 2.5 About

Short bio:
- Photo
- Name + title
- 1-2 sentences: "I'm Jure, a product and data leader who builds tools to solve my own problems. MealFrame eliminates my evening decision fatigue."
- LinkedIn link

### 2.6 Final CTA

**Text:** "Join the waitlist - launching March 2025"

**Email input + button**

**Fine print:** "We'll notify you when testing opens. No spam, unsubscribe anytime."

---

## 3. Design Principles

### 3.1 Visual Style

- Clean, minimal, mobile-first
- Dark theme (matches MealFrame app aesthetic)
- Single-page scroll (no navigation needed)
- Professional but not corporate

### 3.2 Copy Tone

- Direct, honest, conversational
- No marketing fluff
- Problem-focused, not feature-focused
- "You" language, not "we" language

### 3.3 Conversion Focus

- Email signup visible immediately (above fold)
- Repeat CTA at bottom (after social proof)
- No distractions, no external links (except LinkedIn bio)

---

## 4. Technical Implementation

### 4.1 Stack (Minimal Version)

**Frontend:**
- Single HTML file
- Tailwind CSS (CDN) for styling
- Vanilla JavaScript for form handling
- No build process required

**Backend:**
- Form submission → Google Sheets via Google Apps Script
- Alternative: Airtable form endpoint
- Alternative: Tally.so embedded form

**Hosting:**
- Vercel (free tier, instant deploy)
- Custom domain optional: waitlist.mealframe.app

**Email Validation:**
- Client-side regex check
- Server-side validation via Google Sheets script

### 4.2 Form Flow

1. User enters email
2. Client validates format
3. Submit to Google Sheets
4. Show success message: "You're on the list! We'll email you when ready."
5. Disable form (prevent duplicate submissions)

### 4.3 Data Collection

**Google Sheet columns:**
- Timestamp (auto)
- Email
- Source (UTM or "direct")
- IP (optional, for spam detection)

### 4.4 Analytics (Optional)

- Vercel Analytics (free, built-in)
- Simple: Track page views and form submissions
- No Google Analytics needed yet

---

## 5. Technical Specification

### 5.1 File Structure

```
/
├── index.html          # Single page with inline CSS/JS
├── /images
│   └── stats-screenshot.png
│   └── profile-photo.jpg
└── README.md           # Deployment instructions
```

### 5.2 Implementation Steps

1. **Create base HTML structure** (15 min)
   - Sections: Hero, Problem, Solution, Results, About, CTA
   - Tailwind CDN for styling

2. **Build form with Google Sheets integration** (30 min)
   - Create Google Sheet
   - Write Apps Script for form submission
   - Test submission flow

3. **Add content and images** (30 min)
   - Copy from this PRD
   - Screenshot from MealFrame app
   - Profile photo

4. **Style and responsive design** (45 min)
   - Mobile-first approach
   - Dark theme
   - Clean typography

5. **Deploy to Vercel** (10 min)
   - Connect GitHub repo
   - Deploy
   - Test live version

### 5.3 Google Sheets Integration (Code Snippet)

**Apps Script (Google Sheets):**
```javascript
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSheet();
  var email = e.parameter.email;
  var timestamp = new Date();
  
  sheet.appendRow([timestamp, email]);
  
  return ContentService.createTextOutput(
    JSON.stringify({success: true})
  ).setMimeType(ContentService.MimeType.JSON);
}
```

**HTML Form:**
```html
<form id="waitlist-form">
  <input type="email" required placeholder="your@email.com" />
  <button type="submit">Join Waitlist</button>
</form>

<script>
document.getElementById('waitlist-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = e.target.email.value;
  
  await fetch('YOUR_GOOGLE_APPS_SCRIPT_URL', {
    method: 'POST',
    body: new URLSearchParams({email})
  });
  
  alert('You\'re on the list!');
  e.target.email.value = '';
});
</script>
```

---

## 6. Success Metrics

### 6.1 Launch Metrics (First Week)

- Page views: 100-200 (from LinkedIn traffic)
- Email signups: 10-20 (5-10% conversion)
- Mobile vs. desktop split (expect 60% mobile)

### 6.2 Validation Threshold

- **15+ signups in 2 weeks** = Validates demand, prioritize auth implementation
- **<10 signups in 2 weeks** = Keep posting content, build V2 features first

---

## 7. MVP Scope

### 7.1 In Scope

- Single-page responsive site
- Email collection form
- Google Sheets backend
- Basic success message
- Mobile-optimized
- Vercel hosting

### 7.2 Out of Scope (Deferred)

- Email confirmation/double opt-in
- Custom domain (use vercel.app subdomain)
- Email automation (manual notification when ready)
- Analytics dashboard (just check sheet)
- A/B testing
- Exit intent popups

---

## 8. Deployment

**URL:** `mealframe-waitlist.vercel.app` (or custom domain later)

**Timeline:** Ship this weekend, link in next LinkedIn post

**Maintenance:** Check signups weekly, no active management needed

---

## Appendix: Copy Bank

**Hero variations:**
- "Plan when calm, follow when stressed"
- "Exact portions. Zero decisions. No willpower required."
- "The meal planning app that tells you what to eat"

**CTA variations:**
- "Join the waitlist"
- "Get early access"
- "Notify me when ready"

**Social proof:**
- "91% adherence after week 1"
- "46 of 78 meals followed exactly"
- "7-day streak maintained"
