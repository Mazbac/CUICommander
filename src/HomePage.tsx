import { useEffect, useState } from 'react'
import {
  Button,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { developmentActivity, type ActivityItem } from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'
import type { PageId } from './layouts/AppFrame'

type Props = {
  controlPlane: ReturnType<typeof useControlPlane>
  onNavigate: (page: PageId) => void
}

function formatTime(value: number) {
  return new Date(value).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function eventName(action: string) {
  return action
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function HomePage({ controlPlane, onNavigate }: Props) {
  const [activity, setActivity] = useState<ActivityItem[]>(
    controlPlane.development ? developmentActivity : [],
  )
  const snapshot = controlPlane.snapshot
  const setup = controlPlane.localSetup
  const remote = controlPlane.remoteAccess
  const ready = Boolean(
    setup?.readiness.readyForCustomGPT &&
    remote?.active &&
    remote.customGptCompatible,
  )

  useEffect(() => {
    if (controlPlane.development || controlPlane.state !== 'ready') return
    let active = true
    void controlPlane
      .request<{ items: ActivityItem[] }>('/cuicommander/v1/activity?limit=5')
      .then((response) => {
        if (active) setActivity(response.items)
      })
      .catch(() => undefined)
    return () => {
      active = false
    }
  }, [controlPlane])

  if (!snapshot) {
    return (
      <Stack gap="xl">
        <PageHeader
          title="Home"
          description="CUICommander is not connected in this browser."
        />
        <Paper withBorder p="lg" className="cc-surface">
          <Text size="sm">
            Open this page from the local ComfyUI installation to manage setup.
          </Text>
        </Paper>
      </Stack>
    )
  }

  const accessLabel =
    snapshot.accessLevel === 'full'
      ? 'Full control'
      : snapshot.accessLevel === 'edit'
        ? 'Edit files'
        : 'Inspect only'

  return (
    <Stack gap="xl">
      <PageHeader
        title="Home"
        description="Status and recent activity for this ComfyUI installation."
      />

      <Paper withBorder className="cc-surface">
        <Stack gap={0}>
          <Group justify="space-between" align="center" p="lg" wrap="wrap">
            <Text fw={650} size="lg">
              Connection
            </Text>
            <Group gap="xs">
              <span
                className="cc-status-dot"
                data-tone={ready ? 'success' : 'muted'}
              />
              <Text size="sm">
                {ready ? 'ChatGPT access ready' : 'Setup required'}
              </Text>
            </Group>
          </Group>
          <div className="cc-divider" />
          <div className="cc-definition-grid">
            <Text c="dimmed" size="sm">
              ChatGPT
            </Text>
            <Text size="sm">{ready ? 'Ready' : 'Setup required'}</Text>
            <Text c="dimmed" size="sm">
              ComfyUI
            </Text>
            <Text size="sm">
              {snapshot.status === 'ready'
                ? `Running · ${snapshot.comfyVersion}`
                : 'Runtime not connected'}
            </Text>
          </div>
          <div className="cc-definition-grid cc-definition-grid-secondary">
            <Text c="dimmed" size="sm">
              Permission
            </Text>
            <Text size="sm">{accessLabel}</Text>
          </div>
          <Group justify="flex-end" p="lg" pt="md" gap="sm">
            <Button variant="default" onClick={() => onNavigate('chatgpt')}>
              Connection settings
            </Button>
          </Group>
        </Stack>
      </Paper>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
        <Paper withBorder className="cc-surface" p="lg">
          <Stack gap="md">
            <Text fw={650} size="lg">
              Recent activity
            </Text>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Time</Table.Th>
                  <Table.Th>Event</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {activity.slice(0, 5).map((item) => (
                  <Table.Tr key={item.id}>
                    <Table.Td>
                      <Text size="sm">{formatTime(item.at)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{eventName(item.action)}</Text>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Stack>
        </Paper>

        <Paper withBorder className="cc-surface" p="lg">
          <Stack gap="md">
            <Text fw={650} size="lg">
              Attention
            </Text>
            <Text c="dimmed" size="sm">
              {ready
                ? 'No issues requiring action.'
                : 'ChatGPT setup needs attention.'}
            </Text>
          </Stack>
        </Paper>
      </SimpleGrid>

      <Paper withBorder className="cc-surface" p="lg">
        <Group justify="space-between" align="center" wrap="wrap" gap="md">
          <Stack gap={2}>
            <Text fw={650} size="lg">
              Advanced tools
            </Text>
            <Text c="dimmed" size="sm">
              Files, transfers, workflows, and runtime inspection.
            </Text>
          </Stack>
          <Button variant="default" onClick={() => onNavigate('advanced')}>
            Open
          </Button>
        </Group>
      </Paper>
    </Stack>
  )
}
