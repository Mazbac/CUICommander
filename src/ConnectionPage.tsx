import { Button, Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core'
import { CustomGptSetup } from './components/CustomGptSetup'
import { PageHeader } from './components/ui/PageHeader'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }

export function ConnectionPage({ controlPlane }: Props) {
  const setup = controlPlane.localSetup
  const remote = controlPlane.remoteAccess
  const snapshot = controlPlane.snapshot

  if (!setup) {
    return (
      <PageHeader title="ChatGPT" description="Local setup is unavailable." />
    )
  }

  const ready = Boolean(
    setup.readiness.readyForCustomGPT &&
    remote?.active &&
    remote.customGptCompatible,
  )
  if (!ready) {
    return (
      <Stack gap="xl">
        <PageHeader
          title="ChatGPT"
          description="Set up the connection to your Custom GPT."
        />
        <CustomGptSetup
          setup={setup}
          busy={controlPlane.setupBusy}
          error={controlPlane.setupError}
          remote={remote}
          remoteBusy={controlPlane.remoteBusy}
          remoteError={controlPlane.remoteError}
          onUpdate={controlPlane.applyLocalSetup}
          onRotateAccessKey={controlPlane.rotateAccessKey}
          onRefreshRemoteAccess={controlPlane.refreshRemoteAccess}
          onPrepareRemoteAccess={controlPlane.prepareRemoteAccess}
          onEnableRemoteAccess={controlPlane.enableRemoteAccess}
          onDisableRemoteAccess={controlPlane.disableRemoteAccess}
        />
      </Stack>
    )
  }
  return (
    <Stack gap="xl">
      <PageHeader
        title="ChatGPT"
        description="Manage ChatGPT access to this ComfyUI installation."
      />

      <Paper withBorder className="cc-surface">
        <Stack gap={0}>
          <Group justify="space-between" p="lg" wrap="wrap">
            <Stack gap={2}>
              <Text fw={650} size="lg">
                ChatGPT access
              </Text>
              <Text size="sm" c="dimmed">
                Configured and ready to use.
              </Text>
            </Stack>
            <Group gap="xs">
              <span className="cc-status-dot" data-tone="success" />
              <Text size="sm">Ready</Text>
            </Group>
          </Group>
          <div className="cc-divider" />
          <div className="cc-definition-grid">
            <Text c="dimmed" size="sm">
              Address
            </Text>
            <Text size="sm" className="cc-mono">
              {remote?.publicBaseUrl}
            </Text>
            <Text c="dimmed" size="sm">
              Permission
            </Text>
            <Text size="sm">
              {setup.accessLevel === 'full'
                ? 'Full control'
                : setup.accessLevel}
            </Text>
            <Text c="dimmed" size="sm">
              ComfyUI
            </Text>
            <Text size="sm">{snapshot?.comfyVersion ?? 'Unknown'}</Text>
          </div>
          <Group justify="flex-end" p="lg" pt="md" gap="sm">
            <Button
              variant="default"
              onClick={() => void controlPlane.refreshRemoteAccess()}
            >
              Refresh status
            </Button>
            <Button
              variant="default"
              onClick={() => void controlPlane.rotateAccessKey()}
            >
              Rotate key
            </Button>
          </Group>
        </Stack>
      </Paper>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
        <Paper withBorder p="lg" className="cc-surface">
          <Stack gap="sm">
            <Text fw={650}>What ChatGPT can do</Text>
            <Text size="sm">Read ComfyUI files and registered resources</Text>
            <Text size="sm">Update workflows and configuration</Text>
            <Text size="sm">Run discovered ComfyUI operations</Text>
            <Text size="sm">Review results and activity</Text>
          </Stack>
        </Paper>
        <Paper withBorder p="lg" className="cc-surface">
          <Stack gap="md">
            <Stack gap={2}>
              <Text fw={650}>Connection controls</Text>
              <Text size="sm" c="dimmed">
                Changes here affect the Custom GPT connection only.
              </Text>
            </Stack>
            <Button
              variant="default"
              onClick={() => void controlPlane.disableRemoteAccess()}
            >
              Turn off public access
            </Button>
          </Stack>
        </Paper>
      </SimpleGrid>
    </Stack>
  )
}
