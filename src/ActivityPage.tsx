import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Code,
  Group,
  Paper,
  Stack,
  Table,
  Text,
  TextInput,
} from '@mantine/core'
import { EmptyState } from './components/ui/EmptyState'
import { PageHeader } from './components/ui/PageHeader'
import { developmentActivity, type ActivityItem } from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }

function formatTime(value: number) {
  return new Date(value).toLocaleString()
}

function actionLabel(action: string) {
  const labels: Record<string, string> = {
    'resource.create': 'File created',
    'resource.update': 'File updated',
    'resource.patch': 'File updated',
    'resource.move': 'File moved',
    'resource.delete': 'File deleted',
    'runtime.execute': 'ComfyUI action executed',
    'download.create': 'Transfer started',
  }
  return labels[action] ?? action.replaceAll('.', ' ')
}

function target(item: ActivityItem) {
  const value =
    item.detail.path ??
    item.detail.route ??
    item.detail.root ??
    item.detail.jobId
  return typeof value === 'string' ? value : '—'
}

export function ActivityPage({ controlPlane }: Props) {
  const { development, state, request } = controlPlane
  const [items, setItems] = useState<ActivityItem[]>(
    development ? developmentActivity : [],
  )
  const [selected, setSelected] = useState<ActivityItem | null>(null)
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (development || state !== 'ready') return
    try {
      const response = await request<{ items: ActivityItem[] }>(
        '/cuicommander/v1/activity?limit=250',
      )
      setItems(response.items)
      setError(null)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Activity could not be loaded.',
      )
    }
  }, [development, request, state])

  useEffect(() => {
    const timer = window.setTimeout(() => void refresh(), 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  const visibleItems = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return items
    return items.filter((item) =>
      `${item.action} ${target(item)} ${JSON.stringify(item.detail)}`
        .toLowerCase()
        .includes(normalized),
    )
  }, [items, query])

  return (
    <Stack gap="xl">
      <PageHeader
        title="Activity"
        description="A record of recent CUICommander operations."
      />
      {error ? <Alert color="red">{error}</Alert> : null}
      <Paper withBorder className="cc-surface">
        <Stack gap={0}>
          <Group p="md" justify="space-between">
            <TextInput
              placeholder="Search activity"
              value={query}
              onChange={(event) => setQuery(event.currentTarget.value)}
              w={{ base: '100%', sm: 360 }}
            />
            <Button variant="default" onClick={() => void refresh()}>
              Refresh
            </Button>
          </Group>
          {visibleItems.length === 0 ? (
            <EmptyState
              title="No activity"
              description="Recorded operations will appear here."
            />
          ) : (
            <Table.ScrollContainer minWidth={720}>
              <Table highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Time</Table.Th>
                    <Table.Th>Action</Table.Th>
                    <Table.Th>Target</Table.Th>
                    <Table.Th>Details</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {visibleItems.map((item) => (
                    <Table.Tr key={item.id}>
                      <Table.Td>
                        <Text size="sm">{formatTime(item.at)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{actionLabel(item.action)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed" lineClamp={1}>
                          {target(item)}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Button
                          variant="subtle"
                          size="compact-sm"
                          onClick={() => setSelected(item)}
                        >
                          View
                        </Button>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          )}
        </Stack>
      </Paper>
      {selected ? (
        <Paper withBorder className="cc-surface" p="lg">
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Text fw={650} size="lg">
                Event details
              </Text>
              <Button
                variant="subtle"
                size="compact-sm"
                onClick={() => setSelected(null)}
              >
                Close
              </Button>
            </Group>
            <div className="cc-definition-grid">
              <Text c="dimmed" size="sm">
                Time
              </Text>
              <Text size="sm">{formatTime(selected.at)}</Text>
              <Text c="dimmed" size="sm">
                Action
              </Text>
              <Text size="sm">{actionLabel(selected.action)}</Text>
              <Text c="dimmed" size="sm">
                Target
              </Text>
              <Text size="sm">{target(selected)}</Text>
            </div>
            <Code block>{JSON.stringify(selected.detail, null, 2)}</Code>
          </Stack>
        </Paper>
      ) : null}
    </Stack>
  )
}
