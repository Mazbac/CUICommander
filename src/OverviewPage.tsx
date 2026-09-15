import { useState, type FormEvent } from 'react'
import {
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  PasswordInput,
  SimpleGrid,
  Stack,
  Text,
} from '@mantine/core'
import { CustomGptSetup } from './components/CustomGptSetup'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import { useControlPlane } from './hooks/useControlPlane'

const accessLabels = {
  inspect: 'Inspect only',
  edit: 'Edit ComfyUI',
  full: 'Full control',
} as const

const accessTone = {
  read: 'gray',
  write: 'brand',
  full: 'brand',
} as const

type OverviewPageProps = {
  controlPlane: ReturnType<typeof useControlPlane>
}

export function OverviewPage({ controlPlane }: OverviewPageProps) {
  const [credential, setCredential] = useState('')
  const snapshot = controlPlane.snapshot
  const submitConnection = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void controlPlane.connect(credential)
  }

  const statusLabel = snapshot
    ? snapshot.status === 'ready'
      ? 'Ready'
      : 'Runtime needed'
    : controlPlane.state === 'initializing'
      ? 'Initializing'
      : controlPlane.state === 'connecting'
        ? 'Connecting'
        : 'Authentication required'

  const remoteLabel = controlPlane.remoteAccess?.active
    ? controlPlane.remoteAccess.customGptCompatible
      ? 'HTTPS 443 active'
      : 'Legacy remote API'
    : controlPlane.localSetup?.readiness.customGptOrigin
      ? 'HTTPS 443 configured'
      : 'Local only'

  return (
    <Stack gap="xl">
      <PageHeader
        title="CUICommander"
        description="Connect ChatGPT to this live ComfyUI instance, then operate files, workflows, transfers, and native runtime capabilities from one control plane."
        actions={
          <Group gap="xs">
            {snapshot && (
              <Badge color="brand" variant="light">
                {accessLabels[snapshot.accessLevel]}
              </Badge>
            )}
            <Badge
              color={
                snapshot?.status === 'ready'
                  ? 'green'
                  : controlPlane.state === 'error'
                    ? 'red'
                    : 'yellow'
              }
            >
              {statusLabel}
            </Badge>
            {snapshot &&
              !controlPlane.localSetup &&
              controlPlane.state === 'ready' && (
                <Button variant="subtle" onClick={controlPlane.disconnect}>
                  Disconnect
                </Button>
              )}
          </Group>
        }
      />

      {!snapshot && !import.meta.env.DEV && (
        <Section
          title="Connect this console"
          description="Use the configured bearer key to inspect this CUICommander instance."
        >
          <Paper withBorder p={{ base: 'md', sm: 'lg' }} className="cc-surface">
            {controlPlane.state === 'initializing' ? (
              <Stack gap="xs">
                <Text fw={600}>Checking local setup</Text>
                <Text c="dimmed" size="sm">
                  Detecting local CUICommander settings and restoring the
                  browser session when possible.
                </Text>
              </Stack>
            ) : (
              <form onSubmit={submitConnection}>
                <Stack gap="md">
                  {controlPlane.error && (
                    <Alert color="red" title="Connection failed">
                      {controlPlane.error}
                    </Alert>
                  )}
                  <PasswordInput
                    label="Access key"
                    description="The key stays in this browser session and is not written into the repository or bundled UI."
                    value={credential}
                    onChange={(event) =>
                      setCredential(event.currentTarget.value)
                    }
                    autoComplete="off"
                  />
                  <Group justify="flex-end">
                    <Button
                      type="submit"
                      loading={controlPlane.state === 'connecting'}
                    >
                      Connect
                    </Button>
                  </Group>
                </Stack>
              </form>
            )}
          </Paper>
        </Section>
      )}

      {snapshot && (
        <>
          <SimpleGrid cols={{ base: 2, md: 4 }} spacing="md">
            <Paper withBorder p="md" className="cc-surface">
              <Stack gap={3}>
                <Text size="xs" c="dimmed">
                  ComfyUI
                </Text>
                <Text fw={700}>{snapshot.comfyVersion}</Text>
              </Stack>
            </Paper>
            <Paper withBorder p="md" className="cc-surface">
              <Stack gap={3}>
                <Text size="xs" c="dimmed">
                  Access
                </Text>
                <Text fw={700}>{accessLabels[snapshot.accessLevel]}</Text>
              </Stack>
            </Paper>
            <Paper withBorder p="md" className="cc-surface">
              <Stack gap={3}>
                <Text size="xs" c="dimmed">
                  Managed roots
                </Text>
                <Text fw={700}>{snapshot.rootCount}</Text>
              </Stack>
            </Paper>
            <Paper withBorder p="md" className="cc-surface">
              <Stack gap={3}>
                <Text size="xs" c="dimmed">
                  Remote access
                </Text>
                <Text fw={700}>{remoteLabel}</Text>
              </Stack>
            </Paper>
          </SimpleGrid>

          <CustomGptSetup
            setup={controlPlane.localSetup}
            busy={controlPlane.setupBusy}
            error={controlPlane.setupError}
            remote={controlPlane.remoteAccess}
            remoteBusy={controlPlane.remoteBusy}
            remoteError={controlPlane.remoteError}
            onUpdate={controlPlane.applyLocalSetup}
            onRotateAccessKey={controlPlane.rotateAccessKey}
            onRefreshRemoteAccess={controlPlane.refreshRemoteAccess}
            onPrepareRemoteAccess={controlPlane.prepareRemoteAccess}
            onEnableRemoteAccess={controlPlane.enableRemoteAccess}
            onDisableRemoteAccess={controlPlane.disableRemoteAccess}
          />

          <Section
            title="Live control plane"
            description="CUICommander keeps the same generic operations as ComfyUI models, nodes, routes, and registered folders change."
          >
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              {snapshot.capabilities.map((capability) => (
                <Paper
                  withBorder
                  p="lg"
                  className="cc-surface"
                  key={capability.title}
                >
                  <Stack gap="xs">
                    <Group
                      justify="space-between"
                      align="flex-start"
                      wrap="nowrap"
                    >
                      <Text fw={650}>{capability.title}</Text>
                      <Badge
                        color={accessTone[capability.access]}
                        variant="light"
                      >
                        {capability.access}
                      </Badge>
                    </Group>
                    <Text c="dimmed" size="sm">
                      {capability.description}
                    </Text>
                  </Stack>
                </Paper>
              ))}
            </SimpleGrid>
          </Section>
        </>
      )}
    </Stack>
  )
}
