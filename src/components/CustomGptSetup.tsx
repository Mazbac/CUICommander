import { useRef } from 'react'
import {
  Alert,
  Badge,
  Button,
  Code,
  CopyButton,
  Group,
  List,
  Paper,
  PasswordInput,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
} from '@mantine/core'
import { Section } from './ui/Section'
import type { AccessLevel } from '../data/controlPlane'
import type { LocalSetupState, LocalSetupUpdate } from '../data/gptSetup'
import type { RemoteAccessState } from '../data/remoteAccess'

type CustomGptSetupProps = {
  setup: LocalSetupState | null
  busy: boolean
  error: string | null
  remote: RemoteAccessState | null
  remoteBusy: boolean
  remoteError: string | null
  onUpdate: (update: LocalSetupUpdate) => Promise<void>
  onRotateAccessKey: () => Promise<void>
  onRefreshRemoteAccess: () => Promise<void>
  onEnableRemoteAccess: () => Promise<void>
  onDisableRemoteAccess: () => Promise<void>
}

const accessOptions = [
  { value: 'inspect', label: 'Inspect only' },
  { value: 'edit', label: 'Edit ComfyUI files' },
  { value: 'full', label: 'Full ComfyUI control' },
]

export function CustomGptSetup({
  setup,
  busy,
  error,
  remote,
  remoteBusy,
  remoteError,
  onUpdate,
  onRotateAccessKey,
  onRefreshRemoteAccess,
  onEnableRemoteAccess,
  onDisableRemoteAccess,
}: CustomGptSetupProps) {
  const endpointRef = useRef<HTMLInputElement>(null)

  if (!setup) {
    return (
      <Section
        title="Custom GPT setup"
        description="Prepare the private Action connection without exposing local administration to ChatGPT."
      >
        <Alert title="Local setup controls unavailable">
          Open CUICommander from the ComfyUI machine using localhost to manage
          access, the public HTTPS endpoint, and the Action access key.
        </Alert>
      </Section>
    )
  }

  const saveEndpoint = async () => {
    const normalized = (endpointRef.current?.value ?? '')
      .trim()
      .replace(/\/$/, '')
    await onUpdate({ publicBaseUrl: normalized })
  }

  const updateAccess = (value: string | null) => {
    if (!value) return
    void onUpdate({ accessLevel: value as AccessLevel })
  }

  return (
    <Section
      title="Custom GPT setup"
      description="Prepare the instructions, Action schema, authentication, and control level for this ComfyUI instance."
    >
      <Stack gap="md">
        <Group justify="space-between" align="center" wrap="wrap">
          <Stack gap={2}>
            <Text fw={600}>Setup readiness</Text>
            <Text size="sm" c="dimmed">
              Local admin settings stay outside the Action schema.
            </Text>
          </Stack>
          <Badge color={setup.readiness.readyForCustomGPT ? 'green' : 'yellow'}>
            {setup.readiness.readyForCustomGPT
              ? 'Ready for Custom GPT'
              : 'Setup incomplete'}
          </Badge>
        </Group>

        {error && (
          <Alert color="red" title="Setup change failed">
            {error}
          </Alert>
        )}

        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
          <Paper withBorder p="lg">
            <Stack gap="sm">
              <Text fw={600}>1. Control access</Text>
              <Select
                label="Custom GPT access level"
                data={accessOptions}
                value={setup.accessLevel}
                onChange={updateAccess}
                disabled={busy || setup.environmentOverrides.accessLevel}
              />
              {setup.environmentOverrides.accessLevel ? (
                <Text size="xs" c="dimmed">
                  Controlled by the CUICOMMANDER_ACCESS environment variable.
                </Text>
              ) : setup.accessLevel !== 'full' ? (
                <Alert color="dark" title="Full control is not enabled">
                  Inspect or edit access is useful for limited GPTs, but native
                  ComfyUI execution requires Full control.
                </Alert>
              ) : (
                <Alert color="green" title="Full control enabled">
                  Native discovered-route execution is available, with existing
                  confirmation and stale-state safeguards still enforced.
                </Alert>
              )}
            </Stack>
          </Paper>

          <Paper withBorder p="lg">
            <Stack gap="sm">
              <Group justify="space-between" align="center" wrap="wrap">
                <Text fw={600}>2. Remote access</Text>
                <Button
                  variant="subtle"
                  size="compact-sm"
                  onClick={() => void onRefreshRemoteAccess()}
                  loading={remoteBusy}
                >
                  Refresh detection
                </Button>
              </Group>
              <Text size="sm" c="dimmed">
                CUICommander can create a free Tailscale Funnel to its isolated
                Action gateway. Raw ComfyUI and local setup routes stay private.
              </Text>
              {remoteError && (
                <Alert color="red" title="Remote access check failed">
                  {remoteError}
                </Alert>
              )}
              {!remote ? (
                <Alert title="Remote access unavailable">
                  Remote access can only be managed from the local ComfyUI
                  machine.
                </Alert>
              ) : !remote.installed ? (
                <Alert color="yellow" title="Tailscale is not installed">
                  Install the free Tailscale client, sign in once, then choose
                  Refresh detection. CUICommander will handle the Funnel setup.
                </Alert>
              ) : !remote.connected ? (
                <Alert color="yellow" title="Connect Tailscale first">
                  Tailscale {remote.version || 'is installed'}, but this PC is
                  not currently connected to a tailnet.
                </Alert>
              ) : remote.active ? (
                <>
                  <Alert color="green" title="Remote access active">
                    The public endpoint reaches only the authenticated
                    CUICommander Action API.
                  </Alert>
                  <Code block>{remote.publicBaseUrl}</Code>
                  <Group justify="space-between" align="center" wrap="wrap">
                    <Badge color="green">
                      Funnel HTTPS {remote.funnelPort}
                    </Badge>
                    <Button
                      variant="outline"
                      color="red"
                      loading={remoteBusy}
                      onClick={() => {
                        if (
                          window.confirm(
                            'Disable CUICommander remote access? Your Custom GPT will stop connecting until it is enabled again.',
                          )
                        ) {
                          void onDisableRemoteAccess()
                        }
                      }}
                    >
                      Disable remote access
                    </Button>
                  </Group>
                </>
              ) : (
                <>
                  <Alert color="blue" title="Tailscale ready">
                    Connected as {remote.dnsName}. CUICommander detected{' '}
                    {remote.existingServices} existing Tailscale service
                    {remote.existingServices === 1 ? '' : 's'} and will preserve
                    them.
                  </Alert>
                  <Group justify="space-between" align="center" wrap="wrap">
                    <Badge variant="outline">
                      {remote.recommendedFunnelPort
                        ? `Free Funnel port: ${remote.recommendedFunnelPort}`
                        : 'No free Funnel port'}
                    </Badge>
                    <Button
                      onClick={() => void onEnableRemoteAccess()}
                      loading={remoteBusy}
                      disabled={!remote.recommendedFunnelPort}
                    >
                      Enable free remote access
                    </Button>
                  </Group>
                </>
              )}
              <Text size="xs" c="dimmed">
                Existing Tailscale Serve/Funnel entries are inspected first and
                are never reset by CUICommander.
              </Text>
              <Text fw={500} size="sm">
                Advanced: manual HTTPS origin
              </Text>
              <TextInput
                key={setup.publicBaseUrl}
                label="Public origin"
                placeholder="https://comfy.example.com"
                defaultValue={setup.publicBaseUrl}
                ref={endpointRef}
                disabled={busy || remoteBusy || remote?.active}
              />
              <Text size="xs" c="dimmed">
                Advanced origins must terminate at the CUICommander Action API;
                never publish raw ComfyUI port 8188 directly.
              </Text>
              {remote?.active && (
                <Text size="xs" c="dimmed">
                  Disable managed remote access before switching to a manual
                  HTTPS origin.
                </Text>
              )}
              <Group justify="space-between" align="center" wrap="wrap">
                <Badge
                  color={setup.readiness.httpsEndpoint ? 'green' : 'yellow'}
                >
                  {setup.readiness.httpsEndpoint
                    ? 'HTTPS configured'
                    : 'HTTPS required'}
                </Badge>
                <Button
                  variant="default"
                  onClick={saveEndpoint}
                  loading={busy}
                  disabled={remote?.active}
                >
                  Save manual endpoint
                </Button>
              </Group>
            </Stack>
          </Paper>
          <Paper withBorder p="lg">
            <Stack gap="sm">
              <Group justify="space-between" align="center" wrap="wrap">
                <Text fw={600}>3. GPT instructions</Text>
                <CopyButton value={setup.gpt.instructions}>
                  {({ copied, copy }) => (
                    <Button variant="default" onClick={copy}>
                      {copied ? 'Copied' : 'Copy instructions'}
                    </Button>
                  )}
                </CopyButton>
              </Group>
              <Text size="sm" c="dimmed">
                Paste these into the Instructions field of your Custom GPT. They
                keep discovery, verification, and no-adapter behavior consistent
                across changing ComfyUI installs.
              </Text>
              <Code block tabIndex={0}>
                {setup.gpt.instructions}
              </Code>
            </Stack>
          </Paper>
          <Paper withBorder p="lg">
            <Stack gap="sm">
              <Group justify="space-between" align="center" wrap="wrap">
                <Text fw={600}>4. Action connection</Text>
                <CopyButton value={setup.gpt.schemaUrl}>
                  {({ copied, copy }) => (
                    <Button variant="default" onClick={copy}>
                      {copied ? 'Copied' : 'Copy Action schema URL'}
                    </Button>
                  )}
                </CopyButton>
              </Group>
              <Stack gap={4}>
                <Text size="xs" c="dimmed">
                  OpenAPI schema URL
                </Text>
                <Code block>{setup.gpt.schemaUrl}</Code>
              </Stack>
              <Text size="sm" c="dimmed">
                Configure Action authentication as an API key in the
                Authorization header using Bearer authentication.
              </Text>
              <PasswordInput
                label="Action access key"
                value={setup.accessKey}
                readOnly
                autoComplete="off"
              />
              <Group justify="space-between" align="center" wrap="wrap">
                <CopyButton value={setup.accessKey}>
                  {({ copied, copy }) => (
                    <Button variant="default" onClick={copy}>
                      {copied ? 'Copied' : 'Copy access key'}
                    </Button>
                  )}
                </CopyButton>
                <Button
                  variant="outline"
                  color="red"
                  disabled={busy || setup.environmentOverrides.accessKey}
                  onClick={() => {
                    if (
                      window.confirm(
                        'Rotate the CUICommander access key? Existing Custom GPT connections will stop working until updated.',
                      )
                    ) {
                      void onRotateAccessKey()
                    }
                  }}
                >
                  Rotate key
                </Button>
              </Group>
              {setup.environmentOverrides.accessKey && (
                <Text size="xs" c="dimmed">
                  The access key is controlled by the CUICOMMANDER_API_TOKEN
                  environment variable and cannot be rotated here.
                </Text>
              )}
            </Stack>
          </Paper>
        </SimpleGrid>

        <Paper withBorder p="lg">
          <Stack gap="sm">
            <Text fw={600}>Finish in ChatGPT</Text>
            <List spacing="xs" size="sm">
              {setup.gpt.steps.map((step) => (
                <List.Item key={step}>{step}</List.Item>
              ))}
            </List>
            <Text size="xs" c="dimmed">
              The local setup routes that reveal or change these settings are
              intentionally absent from the Action schema and cannot be invoked
              through executeComfyUI.
            </Text>
          </Stack>
        </Paper>
      </Stack>
    </Section>
  )
}
