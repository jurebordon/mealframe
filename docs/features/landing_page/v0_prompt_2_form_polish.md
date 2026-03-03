# v0 Prompt 2 — Form Polish & State Management

> Use this if the form UX needs refinement after Prompt 1.

Refine the waitlist form component used in both the hero and final CTA sections:

## FORM STATES
Implement all four explicitly:

- **Default:** email input + "Join Waitlist" button
- **Loading:** button shows spinner + "Joining..." text, input disabled
- **Success:** hide the input entirely, show full-width amber success 
  banner: "You're on the list. We'll email you when testing opens."
- **Error:** show red-tinted error message below the form: 
  "Submission failed. Try again or email hello@mealframe.app"

## SHARED STATE ACROSS FORMS
The success state should persist (don't reset) — if user scrolls 
to second form after submitting the first, second form should also 
show success state. Use localStorage key `mf_waitlist_submitted` 
to track this across both form instances.

## EMAIL INPUT STYLING
- Dark background (#1a1a1a), 1px border, white text
- Focus state: amber border glow
- Placeholder: "your@email.com" in muted gray
- On mobile: full-width stacked layout
- On desktop: inline with button, input takes remaining space

## BUTTON STYLING
- Amber background, dark text, slightly bold
- Hover: slightly lighter amber
- Disabled: opacity 50%
