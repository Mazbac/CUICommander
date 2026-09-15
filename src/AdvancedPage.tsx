import { Button, Group, Paper, Stack, Text } from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import type { PageId } from './layouts/AppFrame'

type Props = { onNavigate: (page: PageId) => void }

const tools: Array<{ page: PageId; title: string; description: string }> = [
  {
    page: 'resources',
    title: 'Files & resources',
    description:
      'Inspect and manage ComfyUI-owned files and registered folders.',
  },
  {
    page: 'transfers',
    title: 'Jobs & transfers',
    description: 'Review downloads, progress, failures, and background jobs.',
  },
  {
    page: 'workflows',
    title: 'Workflows',
    description: 'Inspect, edit, and queue workflow JSON directly.',
  },
  {
    page: 'runtime',
    title: 'Runtime',
    description:
      'Inspect live nodes and routes or invoke native ComfyUI operations.',
  },
]

export function AdvancedPage({ onNavigate }: Props) {
  return (
    <Stack gap="xl">
      <PageHeader
        title="Advanced"
        description="Manual inspection and intervention tools. Most day-to-day work should happen through your Custom GPT."
      />
      <Paper withBorder className="cc-surface cc-list-surface">
        {tools.map((tool, index) => (
          <Group
            key={tool.page}
            justify="space-between"
            align="center"
            wrap="nowrap"
            p="lg"
            className={index > 0 ? 'cc-list-row' : undefined}
          >
            <Stack gap={2} miw={0}>
              <Text fw={650}>{tool.title}</Text>
              <Text size="sm" c="dimmed">
                {tool.description}
              </Text>
            </Stack>
            <Button variant="default" onClick={() => onNavigate(tool.page)}>
              Open
            </Button>
          </Group>
        ))}
      </Paper>
    </Stack>
  )
}
