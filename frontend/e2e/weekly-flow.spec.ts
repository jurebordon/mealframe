import { test, expect } from '@playwright/test'
import {
  ensureWeeklyPlan,
  getDayTemplates,
  type WeeklyPlanData,
  type DayTemplateListItem,
} from './helpers'

let weekPlan: WeeklyPlanData
let seedTemplates: DayTemplateListItem[]

test.beforeAll(async () => {
  weekPlan = await ensureWeeklyPlan()
  const allTemplates = await getDayTemplates()
  // Filter out E2E test fixtures — only use seed templates
  seedTemplates = allTemplates.filter(t => !t.name.startsWith('E2E'))
})

test.describe('Weekly plan view', () => {
  test('Week View shows day cards with progress', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    // Each non-override day shows "X/Y completed"
    // Some days may be overridden (No Plan), so count is <= 7
    const progressTexts = page.getByText(/\d\/\d completed/)
    const count = await progressTexts.count()
    expect(count).toBeGreaterThanOrEqual(1)
    expect(count).toBeLessThanOrEqual(7)
  })

  test('Week View header shows week plan name', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header')).toBeVisible({ timeout: 10000 })

    if (weekPlan.week_plan?.name) {
      await expect(page.getByText(weekPlan.week_plan.name)).toBeVisible()
    }
  })

  test('Today is highlighted in the week view', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    await expect(page.getByText('Today').first()).toBeVisible()
  })

  test('Clicking a day card expands to show meals', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    // Click a day's progress text to expand it
    const expandButton = page.getByText(/\d\/\d completed/).first()
    await expandButton.click()

    // The first day's first meal name should appear in expanded view
    const firstDay = weekPlan.days[0]
    if (firstDay && !firstDay.is_override && firstDay.slots.length > 0) {
      const mealName = firstDay.slots[0].meal?.name
      if (mealName) {
        await expect(page.getByText(mealName).first()).toBeVisible({ timeout: 5000 })
      }
    }
  })

  test('Generate Next Week button is visible', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    const generateButton = page.getByRole('button', { name: /generate next week/i })
    await expect(generateButton).toBeVisible()
  })
})

test.describe('Template switching', () => {
  test('Edit button opens template picker modal', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    // Edit buttons contain the lucide-pen SVG icon
    const editButtons = page.locator('button:has(svg.lucide-pen)')
    await expect(editButtons.first()).toBeVisible({ timeout: 5000 })
    await editButtons.first().click()

    // Template picker should open
    await expect(page.getByRole('heading', { name: 'Change Template' })).toBeVisible({ timeout: 5000 })

    // At least one seed template should be listed
    if (seedTemplates.length > 0) {
      await expect(page.getByText(seedTemplates[0].name).first()).toBeVisible()
    }

    // "No Plan" option should be available
    await expect(
      page.locator('button').filter({ hasText: 'No Plan' }).filter({ hasText: 'Skip meal planning' })
    ).toBeVisible()
  })

  test('Selecting a different template updates the day', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    // Find the template used on the first day
    const firstDay = weekPlan.days[0]
    const currentTemplateName = firstDay?.template?.name

    // Find a seed template different from the current one
    const alternateTemplate = seedTemplates.find(t => t.name !== currentTemplateName)
    if (!alternateTemplate) {
      test.skip(true, 'Only one seed template available')
      return
    }

    // Open template picker for first day
    const editButtons = page.locator('button:has(svg.lucide-pen)')
    await editButtons.first().click()
    await expect(page.getByRole('heading', { name: 'Change Template' })).toBeVisible({ timeout: 5000 })

    // Click the alternate template button inside the modal.
    // The template list may be long (scrollable), so scroll into view first.
    const templateButton = page.locator('.fixed.inset-0.z-50 .relative.z-10')
      .getByText(alternateTemplate.name)
    await templateButton.scrollIntoViewIfNeeded()
    await templateButton.click({ force: true })

    // If the day has completed meals, a "Regenerate Day?" confirmation appears
    const regenerateHeading = page.getByRole('heading', { name: /regenerate day/i })
    if (await regenerateHeading.isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.getByRole('button', { name: /^regenerate$/i }).click()
    }

    // Modal should close
    await expect(page.getByRole('heading', { name: 'Change Template' })).not.toBeVisible({ timeout: 10000 })

    // The first day card should now show the new template name
    await expect(page.getByText(alternateTemplate.name).first()).toBeVisible({ timeout: 5000 })
  })

  test('Setting No Plan override marks day appropriately', async ({ page }) => {
    await page.goto('/week')
    await expect(page.locator('header h1')).toBeVisible({ timeout: 10000 })

    // Open template picker for the last day
    const editButtons = page.locator('button:has(svg.lucide-pen)')
    const editCount = await editButtons.count()
    if (editCount === 0) {
      test.skip(true, 'No edit buttons found')
      return
    }
    await editButtons.last().click()
    await expect(page.getByRole('heading', { name: 'Change Template' })).toBeVisible({ timeout: 5000 })

    // Click "No Plan"
    await page.locator('button').filter({ hasText: 'No Plan' }).filter({ hasText: 'Skip meal planning' }).click()

    // Should show reason input
    await expect(page.getByPlaceholder(/traveling/i)).toBeVisible({ timeout: 5000 })

    // Type reason and confirm
    await page.getByPlaceholder(/traveling/i).fill('Team dinner out')
    await page.getByRole('button', { name: /confirm/i }).click()

    // Modal should close
    await expect(page.getByPlaceholder(/traveling/i)).not.toBeVisible({ timeout: 5000 })

    // The day should now show "No Plan"
    await expect(page.getByText('No Plan').first()).toBeVisible({ timeout: 5000 })
  })
})
