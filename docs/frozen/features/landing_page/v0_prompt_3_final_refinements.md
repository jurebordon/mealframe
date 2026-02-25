# v0 Prompt 3 — Final Refinements

> Use this for any remaining visual/copy tweaks after Prompts 1 and 2.

## 1. Hero Background
Add a subtle animated gradient or noise texture to the hero 
background to give it depth without being distracting. 
Keep it very subtle.

## 2. Stat Card
The stat card in the hero (91% adherence): style it to look like 
a real app widget — dark card, thin amber border, small "MEALFRAME" 
label in top corner in tiny caps, the number large and prominent.

## 3. Scroll Animations
Add scroll-triggered fade-in animations (simple opacity + translateY) 
to each section as it enters viewport. Use Intersection Observer, 
not a heavy animation library.

## 4. Sticky Header
Add a minimal sticky header that appears only after user scrolls 
past the hero:
- "MealFrame" wordmark on left
- "Join Waitlist" button on right (scrolls to #waitlist-form)
- Backdrop blur, dark background at 90% opacity

## 5. Social Meta Tags
Add meta tags for social sharing:

```html
<meta property="og:title" content="MealFrame — Plan when calm, follow when stressed" />
<meta property="og:description" content="Eliminate food decisions. Beat evening overeating. Join the waitlist for early access." />
<meta property="og:image" content="/og-image.png" />
<meta name="twitter:card" content="summary_large_image" />
```

## 6. Early access active button

Make the early access button in the top left corner active and pressing it should scroll to the email input.
