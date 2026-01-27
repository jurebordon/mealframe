import { test, expect } from '@playwright/test'
import { ensureWeeklyPlan, resetTodayCompletions } from './helpers'

test.beforeAll(async () => {
  await ensureWeeklyPlan()
  await resetTodayCompletions()
})

test.describe('Offline behavior', () => {
  test('Offline banner appears when network is lost', async ({ page, context }) => {
    // Load the page online first
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Go offline (emulates navigator.onLine = false)
    await context.setOffline(true)

    // Trigger the browser's "offline" event
    await page.evaluate(() => window.dispatchEvent(new Event('offline')))

    // The offline banner should appear
    await expect(page.getByText(/you.re offline/i)).toBeVisible({ timeout: 5000 })

    // Restore online
    await context.setOffline(false)
    await page.evaluate(() => window.dispatchEvent(new Event('online')))
  })

  test('Page recovers when network is restored', async ({ page, context }) => {
    // Load page online first
    await page.goto('/')
    await expect(page.getByText('Next', { exact: true })).toBeVisible({ timeout: 10000 })

    // Go offline
    await context.setOffline(true)
    await page.evaluate(() => window.dispatchEvent(new Event('offline')))
    await expect(page.getByText(/you.re offline/i)).toBeVisible({ timeout: 5000 })

    // Go back online
    await context.setOffline(false)
    await page.evaluate(() => window.dispatchEvent(new Event('online')))

    // Offline banner should disappear
    await expect(page.getByText(/you.re offline/i)).not.toBeVisible({ timeout: 5000 })
  })

  test('All main routes are accessible and render', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('header h1, h1, h2').first()).toBeVisible({ timeout: 10000 })

    await page.goto('/week')
    await expect(page.locator('header h1, h1').first()).toBeVisible({ timeout: 10000 })

    await page.goto('/meals')
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 })

    await page.goto('/setup')
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 })

    await page.goto('/stats')
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 })
  })
})
