import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'
import { theme } from './theme/theme'

describe('CUICommander overview', () => {
  it('renders the universal control-plane setup surface', () => {
    render(
      <MantineProvider theme={theme}>
        <App />
      </MantineProvider>,
    )

    expect(screen.getByRole('heading', { name: 'CUICommander' })).toBeVisible()
    expect(screen.getByText('Universal control model')).toBeVisible()
    expect(screen.getByRole('table')).toHaveTextContent(
      'ComfyUI base directory',
    )
    expect(
      screen.getByRole('button', { name: 'Copy schema URL' }),
    ).toBeEnabled()
  })
})
