import { readFileSync } from 'node:fs'
import process from 'node:process'
import { chromium } from '@playwright/test'

const baseUrl = process.env.CUICOMMANDER_BASE_URL ?? 'http://127.0.0.1:8188'
const tokenFile = process.env.CUICOMMANDER_TOKEN_FILE
const configuredToken = process.env.CUICOMMANDER_API_TOKEN?.trim()

function readAccessKey() {
  if (configuredToken) return configuredToken
  if (!tokenFile) {
    throw new Error(
      'Set CUICOMMANDER_API_TOKEN or CUICOMMANDER_TOKEN_FILE before running live UI acceptance.',
    )
  }
  const value = JSON.parse(
    readFileSync(tokenFile, 'utf8').replace(/^\uFEFF/, ''),
  )
  const token = String(value.token ?? '').trim()
  if (!token) throw new Error('Configured CUICommander access key is empty.')
  return token
}

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
try {
  await page.goto(`${baseUrl.replace(/\/$/, '')}/cuicommander/`, {
    waitUntil: 'networkidle',
  })
  await page.getByRole('heading', { name: 'CUICommander' }).waitFor()
  await page.getByLabel('Access key').fill(readAccessKey())
  await page.getByRole('button', { name: 'Connect' }).click()
  await page.getByText('Ready', { exact: true }).waitFor()
  await page.getByText(/CUICommander .* \| ComfyUI /).waitFor()
  await page
    .getByRole('table')
    .getByText('ComfyUI base directory', { exact: true })
    .waitFor()

  await page.reload({ waitUntil: 'networkidle' })
  await page.getByText('Ready', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Disconnect' }).click()
  await page.getByText('Authentication required', { exact: true }).waitFor()
  await page.getByLabel('Access key').waitFor()

  console.log('Live embedded UI acceptance passed.')
} finally {
  await browser.close()
}
