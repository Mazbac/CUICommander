import { useCallback, useEffect, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Code,
  Group,
  Paper,
  SegmentedControl,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import {
  developmentNodes,
  developmentRoutes,
  type NativeResult,
  type NodeItem,
  type RouteItem,
} from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }
type DiscoverKind = 'nodes' | 'routes'

export function RuntimePage({ controlPlane }: Props) {
  const { development, state, request, snapshot } = controlPlane
  const [kind, setKind] = useState<DiscoverKind>('nodes')
  const [query, setQuery] = useState('')
  const [nodes, setNodes] = useState<NodeItem[]>(
    development ? developmentNodes : [],
  )
  const [routes, setRoutes] = useState<RouteItem[]>(
    development ? developmentRoutes : [],
  )
  const [method, setMethod] = useState('GET')
  const [route, setRoute] = useState('/system_stats')
  const [queryJson, setQueryJson] = useState('{}')
  const [bodyJson, setBodyJson] = useState('{}')
  const [result, setResult] = useState<NativeResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const full = snapshot?.accessLevel === 'full'

  const discover = useCallback(async () => {
    if (development || state !== 'ready') return
    setBusy(true)
    setError(null)
    try {
      if (kind === 'nodes') {
        const response = await request<{ items: NodeItem[] }>(
          '/cuicommander/v1/discover',
          {
            method: 'POST',
            body: JSON.stringify({ kind, query, limit: 250 }),
          },
        )
        setNodes(response.items)
      } else {
        const response = await request<{ items: RouteItem[] }>(
          '/cuicommander/v1/discover',
          {
            method: 'POST',
            body: JSON.stringify({ kind, query, limit: 500 }),
          },
        )
        setRoutes(response.items)
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Discovery failed.',
      )
    } finally {
      setBusy(false)
    }
  }, [development, kind, query, request, state])

  useEffect(() => {
    const timer = window.setTimeout(() => void discover(), 0)
    return () => window.clearTimeout(timer)
  }, [discover])

  const execute = async () => {
    setBusy(true)
    setError(null)
    try {
      const parsedQuery = queryJson.trim() ? JSON.parse(queryJson) : {}
      const parsedBody = bodyJson.trim() ? JSON.parse(bodyJson) : undefined
      if (method !== 'GET' && !window.confirm(`Execute ${method} ${route}?`))
        return
      const response = await request<NativeResult>('/cuicommander/v1/execute', {
        method: 'POST',
        body: JSON.stringify({
          method,
          route,
          query: parsedQuery,
          ...(method === 'GET' ? {} : { body: parsedBody, confirmed: true }),
        }),
      })
      setResult(response)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Execution failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Stack gap="xl">
      <PageHeader
        title="Runtime"
        description="Discover the live node registry and route table, then invoke existing native ComfyUI routes generically."
        actions={
          <Badge variant="outline">
            {full ? 'Full control' : 'Read discovery'}
          </Badge>
        }
      />
      {error && <Alert color="red">{error}</Alert>}
      <Section
        title="Discover"
        description="No provider adapters: inspect whatever the current ComfyUI runtime exposes."
      >
        <Paper withBorder p="lg">
          <Stack gap="md">
            <SegmentedControl
              value={kind}
              onChange={(value) => setKind(value as DiscoverKind)}
              data={[
                { value: 'nodes', label: 'Nodes' },
                { value: 'routes', label: 'Routes' },
              ]}
            />
            <Group align="end" wrap="wrap">
              <TextInput
                label="Search"
                placeholder={
                  kind === 'nodes'
                    ? 'KSampler, audio, control…'
                    : '/prompt, history, manager…'
                }
                value={query}
                onChange={(event) => setQuery(event.currentTarget.value)}
                flex={1}
              />
              <Button
                variant="default"
                loading={busy}
                onClick={() => void discover()}
              >
                Search
              </Button>
            </Group>
          </Stack>
        </Paper>
        <Paper withBorder>
          <Table verticalSpacing="sm" horizontalSpacing="md">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>{kind === 'nodes' ? 'Node' : 'Method'}</Table.Th>
                <Table.Th>{kind === 'nodes' ? 'Category' : 'Route'}</Table.Th>
                <Table.Th>
                  {kind === 'nodes' ? 'Module / returns' : 'Source'}
                </Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(kind === 'nodes' ? nodes : routes).map((item) =>
                kind === 'nodes' ? (
                  <Table.Tr key={(item as NodeItem).name}>
                    <Table.Td>
                      <Code>{(item as NodeItem).name}</Code>
                    </Table.Td>
                    <Table.Td>{(item as NodeItem).category || '—'}</Table.Td>
                    <Table.Td>
                      <Text size="sm">{(item as NodeItem).module}</Text>
                      <Text size="xs" c="dimmed">
                        {(item as NodeItem).returnTypes.join(', ') ||
                          'No return types'}
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                ) : (
                  <Table.Tr
                    key={`${(item as RouteItem).method}:${(item as RouteItem).path}`}
                  >
                    <Table.Td>
                      <Badge variant="outline">
                        {(item as RouteItem).method}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Code>{(item as RouteItem).path}</Code>
                    </Table.Td>
                    <Table.Td>{(item as RouteItem).source}</Table.Td>
                  </Table.Tr>
                ),
              )}
            </Table.Tbody>
          </Table>
        </Paper>
      </Section>{' '}
      <Section
        title="Native execution"
        description="Invoke only routes that exist in the live ComfyUI router. Mutating calls require Full control and explicit confirmation."
      >
        <Paper withBorder p="lg">
          <Stack gap="md">
            <Group align="end" wrap="wrap">
              <SegmentedControl
                value={method}
                onChange={setMethod}
                data={['GET', 'POST', 'PUT', 'PATCH', 'DELETE']}
              />
              <TextInput
                label="Route"
                value={route}
                onChange={(event) => setRoute(event.currentTarget.value)}
                placeholder="/system_stats"
                flex={1}
              />
              <Button
                loading={busy}
                disabled={!full}
                onClick={() => void execute()}
              >
                Execute
              </Button>
            </Group>
            {!full && (
              <Alert color="yellow">
                Native route execution requires Full control. Discovery remains
                available.
              </Alert>
            )}
            <Textarea
              label="Query JSON"
              minRows={3}
              value={queryJson}
              onChange={(event) => setQueryJson(event.currentTarget.value)}
              styles={{ input: { fontFamily: 'monospace' } }}
            />{' '}
            {method !== 'GET' && (
              <Textarea
                label="Body JSON"
                minRows={6}
                value={bodyJson}
                onChange={(event) => setBodyJson(event.currentTarget.value)}
                styles={{ input: { fontFamily: 'monospace' } }}
              />
            )}
            {result && (
              <Paper withBorder p="md">
                <Stack gap="xs">
                  <Group justify="space-between" wrap="wrap">
                    <Text fw={600}>HTTP {result.status}</Text>
                    <Badge variant="outline">
                      {result.contentType || 'unknown'}
                    </Badge>
                  </Group>
                  <Code block>{JSON.stringify(result.body, null, 2)}</Code>
                  {result.bodyTruncated && (
                    <Text size="xs" c="orange">
                      Response preview was truncated by the runtime safety
                      limit.
                    </Text>
                  )}
                </Stack>
              </Paper>
            )}
          </Stack>
        </Paper>
      </Section>
    </Stack>
  )
}
