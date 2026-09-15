import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'
import { theme } from './theme/theme'

describe('CUICommander shell', () => {
  it('renders the simplified product navigation and home status', () => {
    render(
      <MantineProvider theme={theme}>
        <App />
      </MantineProvider>,
    )

    expect(screen.getByRole('heading', { name: 'Home' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Home' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'ChatGPT' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Activity' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Advanced' })).toBeVisible()
    expect(screen.getByText('Connection', { exact: true })).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Connection settings' }),
    ).toBeVisible()
    expect(screen.getByText('Advanced tools')).toBeVisible()
  })
})
