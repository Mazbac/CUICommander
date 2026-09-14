import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { developmentLocalSetup } from '../data/gptSetup'
import { theme } from '../theme/theme'
import { CustomGptSetup } from './CustomGptSetup'

function renderSetup(
  onUpdate = vi.fn().mockResolvedValue(undefined),
  onRotateAccessKey = vi.fn().mockResolvedValue(undefined),
) {
  render(
    <MantineProvider theme={theme}>
      <CustomGptSetup
        setup={developmentLocalSetup}
        busy={false}
        error={null}
        onUpdate={onUpdate}
        onRotateAccessKey={onRotateAccessKey}
      />
    </MantineProvider>,
  )
  return { onUpdate, onRotateAccessKey }
}
describe('CustomGptSetup', () => {
  it('renders the copy-ready Custom GPT setup contract', () => {
    renderSetup()

    expect(screen.getByText('Custom GPT setup')).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Copy instructions' }),
    ).toBeEnabled()
    expect(
      screen.getByRole('button', { name: 'Copy Action schema URL' }),
    ).toBeEnabled()
    expect(screen.getByLabelText('Action access key')).toHaveValue(
      developmentLocalSetup.accessKey,
    )
  })

  it('normalizes and saves the public HTTPS origin', async () => {
    const user = userEvent.setup()
    const { onUpdate } = renderSetup()

    await user.type(
      screen.getByLabelText('Public origin'),
      'https://comfy.example.com/',
    )
    await user.click(screen.getByRole('button', { name: 'Save endpoint' }))

    expect(onUpdate).toHaveBeenCalledWith({
      publicBaseUrl: 'https://comfy.example.com',
    })
  })

  it('rotates the access key only after explicit confirmation', async () => {
    const user = userEvent.setup()
    const { onRotateAccessKey } = renderSetup()
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)

    await user.click(screen.getByRole('button', { name: 'Rotate key' }))

    expect(confirm).toHaveBeenCalledOnce()
    expect(onRotateAccessKey).toHaveBeenCalledOnce()
    confirm.mockRestore()
  })
})
