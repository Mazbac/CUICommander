import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'
import { theme } from './theme/theme'

describe('CUICommander overview', () => {
  it('renders the guided setup and live control-plane summary', () => {
    render(
      <MantineProvider theme={theme}>
        <App />
      </MantineProvider>,
    )

    expect(screen.getByRole('heading', { name: 'CUICommander' })).toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Connect ChatGPT' }),
    ).toBeVisible()
    expect(screen.getByText('Connection readiness')).toBeVisible()
    expect(screen.getByText('Managed roots')).toBeVisible()
    expect(screen.getByText('Live control plane')).toBeVisible()
    expect(
      screen.getByRole('button', { name: /1 Choose control access/ }),
    ).toHaveAttribute('aria-expanded', 'true')
  })
})
