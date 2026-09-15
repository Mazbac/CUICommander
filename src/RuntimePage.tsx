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
  type DiscoveryPage,
  type NativeResponseChunk,
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
  const [discoveryNextOffset, setDiscoveryNextOffset] = useState<number | null>(
    null,
  )
  const [discoveryTotal, setDiscoveryTotal] = useState<number | null>(null)
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
        const response = await request<DiscoveryPage<NodeItem>>(
          '/cuicommander/v1/discover',
          {
            method: 'POST',
            body: JSON.stringify({ kind, query, limit: 250 }),
          },
        )
        setNodes(response.items)
        setDiscoveryNextOffset(response.nextOffset)
        setDiscoveryTotal(response.totalItems)
      } else {
        const response = await request<DiscoveryPage<RouteItem>>(
          '/cuicommander/v1/discover',
          {
            method: 'POST',
            body: JSON.stringify({ kind, query, limit: 500 }),
          },
        )
        setRoutes(response.items)
        setDiscoveryNextOffset(response.nextOffset)
        setDiscoveryTotal(response.totalItems)
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

  const loadMoreDiscovery = async () => {
    if (development || state !== 'ready' || discoveryNextOffset == null) return
    setBusy(true)
    setError(null)
    try {
      if (kind === 'nodes') {
        const response = await request<DiscoveryPage<NodeItem>>(
          '/cuicommander/v1/discover',
          {
            method: 'POST',
            body: JSON.stringify({
              kind,
              query,
              limit: 250,
              offset: discoveryNextOffset,
            }),
          },
        )
        setNodes((current) => [...current, ...response.items])
        setDiscoveryNextOffset(response.nextOffset)
        setDiscoveryTotal(response.totalItems)
      } else {
        const response = await request<DiscoveryPage<RouteItem>>(
          '/cuicommander/v1/discover',
          {
            method: 'POST',
            body: JSON.stringify({
              kind,
              query,
              limit: 500,
              offset: discoveryNextOffset,
            }),
          },
        )
        setRoutes((current) => [...current, ...response.items])
        setDiscoveryNextOffset(response.nextOffset)
        setDiscoveryTotal(response.totalItems)
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not load the next discovery page.',
      )
    } finally {
      setBusy(false)
    }
  }

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

  const loadFullResponse = async () => {
    if (!result?.responseId) return
    setBusy(true)
    setError(null)
    try {
      let offset = 0
      const chunks: string[] = []
      while (true) {
        const chunk = await request<NativeResponseChunk>(
          '/cuicommander/v1/runtime/responses/read',
          {
            method: 'POST',
            body: JSON.stringify({
              responseId: result.responseId,
              offset,
              maxBytes: 131072,
              encoding: 'utf-8',
            }),
          },
        )
        chunks.push(chunk.content ?? '')
        if (chunk.eof) break
        if (chunk.nextOffset === null || chunk.nextOffset <= offset) {
          throw new Error('Response read did not make forward progress.')
        }
        offset = chunk.nextOffset
      }
      const text = chunks.join('')
      let body: unknown = text
      if (
        result.contentType === 'application/json' ||
        result.contentType.endsWith('+json')
      ) {
        body = JSON.parse(text)
      }
      setResult({ ...result, body, bodyTruncated: false, nextOffset: null })
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not read the complete native response.',
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
        <Paper withBorder p="lg" className="cc-surface">
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
                    ? 'KSampler, audio, controlÃ¢â‚¬Â¦'
                    : '/prompt, history, managerÃ¢â‚¬Â¦'
                }
                value={query}
                onChange={(event) => setQuery(event.currentTarget.value)}
                flex={1}
              />
              <Button
                variant="light"
                loading={busy}
                onClick={() => void discover()}
              >
                Search
              </Button>
            </Group>
          </Stack>
        </Paper>
        <Paper withBorder className="cc-surface">
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
                    <Table.Td>
                      {(item as NodeItem).category || 'Ã¢â‚¬â€'}
                    </Table.Td>
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
        {discoveryNextOffset != null && (
          <Group justify="center">
            <Button
              variant="default"
              loading={busy}
              onClick={() => void loadMoreDiscovery()}
            >
              Load more ({kind === 'nodes' ? nodes.length : routes.length} of{' '}
              {discoveryTotal ?? '…'})
            </Button>
          </Group>
        )}
      </Section>{' '}
      <Section
        title="Native execution"
        description="Invoke only routes that exist in the live ComfyUI router. Mutating calls require Full control and explicit confirmation."
      >
        <Paper withBorder p="lg" className="cc-surface">
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
              <Alert className="cc-warning-alert" color="yellow">
                Native route execution requires Full control. Discovery remains
                available.
              </Alert>
            )}
            <Textarea
              label="Query JSON"
              minRows={3}
              value={queryJson}
              onChange={(event) => setQueryJson(event.currentTarget.value)}
              classNames={{ input: 'cc-mono' }}
            />{' '}
            {method !== 'GET' && (
              <Textarea
                label="Body JSON"
                minRows={6}
                value={bodyJson}
                onChange={(event) => setBodyJson(event.currentTarget.value)}
                classNames={{ input: 'cc-mono' }}
              />
            )}
            {result && (
              <Paper withBorder p="md" className="cc-surface">
                <Stack gap="xs">
                  <Group justify="space-between" wrap="wrap">
                    <Text fw={600}>HTTP {result.status}</Text>
                    <Badge variant="outline">
                      {result.contentType || 'unknown'}
                    </Badge>
                  </Group>
                  <Code block>{JSON.stringify(result.body, null, 2)}</Code>
                  {result.bodyTruncated && result.responseId && (
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">
                        The full response is retained (
                        {result.responseSize ?? 'unknown'} bytes). Read it in
                        chunks instead of losing data at the inline limit.
                      </Text>
                      {(result.contentType.startsWith('text/') ||
                        result.contentType === 'application/json' ||
                        result.contentType.endsWith('+json')) && (
                        <Group>
                          <Button
                            size="xs"
                            variant="default"
                            loading={busy}
                            onClick={() => void loadFullResponse()}
                          >
                            Load complete response
                          </Button>
                        </Group>
                      )}
                    </Stack>
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
