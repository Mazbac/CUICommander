import { useCallback, useEffect, useState } from 'react'
import { Badge, Button, Code, Paper, Stack, Table, Text } from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import { developmentActivity, type ActivityItem } from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }

function formatTime(value: number) {
  return new Date(value).toLocaleString()
}

export function ActivityPage({ controlPlane }: Props) {
  const { development, state, request } = controlPlane
  const [items, setItems] = useState<ActivityItem[]>(
    development ? developmentActivity : [],
  )
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

  return (
    <Stack gap="xl">
      <PageHeader
        title="Activity"
        description="Recent CUICommander mutations and control-plane actions. Sensitive content and credentials are deliberately not recorded."
        actions={
          <Button variant="default" onClick={() => void refresh()}>
            Refresh
          </Button>
        }
      />
      {error && (
        <Paper withBorder p="md">
          <Text c="red" size="sm">
            {error}
          </Text>
        </Paper>
      )}
      <Section
        title="Recent activity"
        description="This is an operational audit trail, not a full packet/body log."
      >
        <Paper withBorder p="lg">
          {items.length === 0 ? (
            <Text c="dimmed" size="sm">
              No recorded CUICommander mutation activity yet.
            </Text>
          ) : (
            <Table.ScrollContainer minWidth={760}>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Time</Table.Th>
                    <Table.Th>Action</Table.Th>
                    <Table.Th>Detail</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {items.map((item) => (
                    <Table.Tr key={item.id}>
                      <Table.Td>
                        <Text size="sm">{formatTime(item.at)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="outline">{item.action}</Badge>
                      </Table.Td>
                      <Table.Td>
                        <Code>{JSON.stringify(item.detail)}</Code>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          )}
        </Paper>
      </Section>
    </Stack>
  )
}
