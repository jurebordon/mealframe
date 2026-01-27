import { test, expect } from '@playwright/test'
import { resetTodayCompletions, ensureWeeklyPlan, type TodayData } from './helpers'

let today: TodayData

test.beforeAll(async () => {
  await ensureWeeklyPlan()
})

test.beforeEach(async () => {
  // Reset all completions so each test starts with all slots pending
  today = await resetTodayCompletions()
})

/** Click the "next" hero meal card (avoids gesture handler conflicts). */
async function clickHeroCard(page: import('@playwright/test').Page) {
  // The "Next" label and hero card are in the first <section> before "Remaining Today"
  // Click the meal name heading inside the card that has ring-primary (next status)
  // Using the "Next meal" text's parent section to scope the click
  const nextSection = page.locator('section').filter({ hasText: 'Next' }).first()
  const mealHeading = nextSection.locator('h3').first()
  await mealHeading.click()
}

test.describe('Daily meal completion flow', () => {
  test('Today View shows date header and template name', async ({ page }) => {
    await page.goto('/')
    const header = page.locator('header h1')
    await expect(header).toBeVisible({ timeout: 10000 })

    // Date header contains a weekday name
    await expect(header).toHaveText(
      /Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday/
    )

    // Template name should be visible below the date
    if (today.template) {
      await expect(page.getByText(today.template.name)).toBeVisible()
    }
  })

  test('Today View renders meal slots with "Next" indicator', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // The first meal's name should be visible on the page
    const firstMealName = today.slots[0]?.meal?.name
    if (firstMealName) {
      await expect(page.getByText(firstMealName).first()).toBeVisible()
    }
  })

  test('Today View shows progress ring', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Progress ring shows "X of Y" — with 0 completed: "0 of N"
    const totalSlots = today.slots.length
    await expect(page.getByText(`of ${totalSlots}`).first()).toBeVisible()
  })

  test('Tapping a meal card opens the completion sheet', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Click the hero card's meal name (bubbles up to onClick handler)
    await clickHeroCard(page)

    // Completion sheet opens with all 5 status options
    await expect(page.getByText('Mark completion status')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Followed', { exact: true })).toBeVisible()
    await expect(page.getByText('Adjusted', { exact: true })).toBeVisible()
    await expect(page.getByText('Skipped', { exact: true })).toBeVisible()
    await expect(page.getByText('Replaced', { exact: true })).toBeVisible()
    await expect(page.getByText('Social', { exact: true })).toBeVisible()
  })

  test('Selecting "Followed" completes the meal and shows toast', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Open completion sheet
    await clickHeroCard(page)
    await expect(page.getByText('Mark completion status')).toBeVisible({ timeout: 5000 })

    // Select "Followed"
    await page.getByLabel(/mark as followed/i).click()

    // Toast confirms the action
    await expect(page.getByText('Marked as followed')).toBeVisible({ timeout: 5000 })
  })

  test('After completing first meal, next meal becomes "Next"', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Complete the first meal
    await clickHeroCard(page)
    await expect(page.getByText('Mark completion status')).toBeVisible({ timeout: 5000 })
    await page.getByLabel(/mark as followed/i).click()

    // Wait for UI to settle
    await page.waitForTimeout(2000)

    // If there are more slots, "Next" should still appear for the second meal
    if (today.slots.length > 1) {
      await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 5000 })
    }
  })

  test('Completing all meals shows "Day Complete" celebration', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Complete every slot one by one
    for (let i = 0; i < today.slots.length; i++) {
      await clickHeroCard(page)
      await expect(page.getByText('Mark completion status')).toBeVisible({ timeout: 5000 })
      await page.getByLabel(/mark as followed/i).click()
      await page.waitForTimeout(2000)
    }

    // "Day Complete" should appear
    await expect(page.getByText('Day Complete')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/all meals completed/i)).toBeVisible()
  })

  test('Undo via toast resets completion', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Get the first meal's name before completing
    const firstMealName = today.slots[0]?.meal?.name ?? ''

    // Complete a meal
    await clickHeroCard(page)
    await expect(page.getByText('Mark completion status')).toBeVisible({ timeout: 5000 })
    await page.getByLabel(/mark as followed/i).click()

    // Toast appears
    await expect(page.getByText('Marked as followed')).toBeVisible({ timeout: 5000 })

    // Click Undo
    const undoButton = page.getByRole('button', { name: /undo/i })
    await undoButton.click()

    // After undo, the same meal should reappear as "next"
    await page.waitForTimeout(1000)
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 5000 })
    if (firstMealName) {
      await expect(page.getByText(firstMealName).first()).toBeVisible()
    }
  })
})
