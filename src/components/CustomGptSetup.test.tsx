import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { developmentLocalSetup } from '../data/gptSetup'
import { developmentRemoteAccess } from '../data/remoteAccess'
import { theme } from '../theme/theme'
import { CustomGptSetup } from './CustomGptSetup'

function renderSetup(
  onUpdate = vi.fn().mockResolvedValue(undefined),
  onRotateAccessKey = vi.fn().mockResolvedValue(undefined),
  remote = developmentRemoteAccess,
  onPrepareRemoteAccess = vi.fn().mockResolvedValue(undefined),
) {
  render(
    <MantineProvider theme={theme}>
      <CustomGptSetup
        setup={developmentLocalSetup}
        busy={false}
        error={null}
        remote={remote}
        remoteBusy={false}
        remoteError={null}
        onUpdate={onUpdate}
        onRotateAccessKey={onRotateAccessKey}
        onRefreshRemoteAccess={vi.fn().mockResolvedValue(undefined)}
        onPrepareRemoteAccess={onPrepareRemoteAccess}
        onEnableRemoteAccess={vi.fn().mockResolvedValue(undefined)}
        onDisableRemoteAccess={vi.fn().mockResolvedValue(undefined)}
      />
    </MantineProvider>,
  )
  return { onUpdate, onRotateAccessKey, onPrepareRemoteAccess }
}

async function openStep(
  user: ReturnType<typeof userEvent.setup>,
  name: RegExp,
) {
  const control = screen.getByRole('button', { name })
  if (control.getAttribute('aria-expanded') !== 'true') {
    await user.click(control)
  }
  expect(control).toHaveAttribute('aria-expanded', 'true')
}

async function openRemote(user: ReturnType<typeof userEvent.setup>) {
  await openStep(user, /2 Create a secure remote endpoint/)
}

async function openChatGpt(user: ReturnType<typeof userEvent.setup>) {
  await openStep(user, /3 Copy the connection into ChatGPT/)
}

describe('CustomGptSetup', () => {
  it('renders the guided copy-ready Custom GPT setup contract', async () => {
    const user = userEvent.setup()
    renderSetup()

    expect(
      screen.getByRole('heading', { name: 'Connect ChatGPT' }),
    ).toBeVisible()
    expect(screen.getByText('Connection readiness')).toBeVisible()
    expect(
      screen.getByRole('button', { name: /1 Choose control access/ }),
    ).toHaveAttribute('aria-expanded', 'true')

    await openChatGpt(user)
    expect(
      screen.getByRole('button', { name: 'Copy instructions' }),
    ).toBeEnabled()
    expect(
      screen.getByRole('button', { name: 'Copy Action schema' }),
    ).toBeEnabled()
    expect(screen.getByLabelText('Action access key')).toHaveValue(
      developmentLocalSetup.accessKey,
    )
    expect(
      screen.queryByLabelText('OpenAPI Action schema'),
    ).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Preview' }))
    expect(screen.getByLabelText('OpenAPI Action schema')).toHaveValue(
      developmentLocalSetup.gpt.schema,
    )

    await openRemote(user)
    expect(screen.getByText('Create an isolated endpoint')).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Set up isolated endpoint' }),
    ).toBeEnabled()
  })

  it('normalizes and saves the advanced public HTTPS origin', async () => {
    const user = userEvent.setup()
    const { onUpdate } = renderSetup()

    await openRemote(user)
    await user.click(screen.getByRole('button', { name: 'Show advanced' }))
    await user.type(
      screen.getByLabelText('Manual public origin'),
      'https://comfy.example.com/',
    )
    await user.click(
      screen.getByRole('button', { name: 'Save manual endpoint' }),
    )

    expect(onUpdate).toHaveBeenCalledWith({
      publicBaseUrl: 'https://comfy.example.com',
    })
  })

  it('locks the advanced manual origin while managed remote access is active', async () => {
    const user = userEvent.setup()
    renderSetup(undefined, undefined, {
      ...developmentRemoteAccess,
      mode: 'action-node',
      configured: true,
      active: true,
      customGptCompatible: true,
      gatewayRunning: true,
      funnelPort: 443,
      publicBaseUrl: 'https://cuicommander-example.example.ts.net',
      actionNodeRunning: true,
      actionNodeConnected: true,
      actionNodeDnsName: 'cuicommander-example.example.ts.net',
    })

    await openRemote(user)
    expect(
      screen.getByRole('button', { name: 'Disable remote access' }),
    ).toBeEnabled()
    await user.click(screen.getByRole('button', { name: 'Show advanced' }))
    expect(screen.getByLabelText('Manual public origin')).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Save manual endpoint' }),
    ).toBeDisabled()
  })

  it('shows the Tailscale sign-in step for a prepared isolated node', async () => {
    const user = userEvent.setup()
    const onPrepareRemoteAccess = vi.fn().mockResolvedValue(undefined)
    renderSetup(
      undefined,
      undefined,
      {
        ...developmentRemoteAccess,
        actionNodeRunning: true,
        actionNodeLoginUrl: 'https://login.tailscale.com/a/example',
      },
      onPrepareRemoteAccess,
    )

    await openRemote(user)
    await user.click(
      screen.getByRole('button', { name: 'Set up isolated endpoint' }),
    )
    expect(onPrepareRemoteAccess).toHaveBeenCalledOnce()
    expect(
      screen.getByRole('link', { name: 'Sign in to Tailscale' }),
    ).toHaveAttribute('href', 'https://login.tailscale.com/a/example')
  })

  it('rotates the access key only after explicit confirmation', async () => {
    const user = userEvent.setup()
    const { onRotateAccessKey } = renderSetup()
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)

    await openChatGpt(user)
    await user.click(screen.getByRole('button', { name: 'Rotate key' }))

    expect(confirm).toHaveBeenCalledOnce()
    expect(onRotateAccessKey).toHaveBeenCalledOnce()
    confirm.mockRestore()
  })
})
