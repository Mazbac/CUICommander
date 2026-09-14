import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

test('overview and Custom GPT setup are usable and accessible', async ({
  page,
}) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  await expect(page.getByText('Custom GPT setup')).toBeVisible()
  await expect(
    page.getByRole('button', { name: 'Copy instructions' }),
  ).toBeEnabled()
  await expect(
    page.getByRole('button', { name: 'Copy Action schema URL' }),
  ).toBeEnabled()
  await expect(
    page.getByRole('table').getByText('ComfyUI base directory'),
  ).toBeVisible()

  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
