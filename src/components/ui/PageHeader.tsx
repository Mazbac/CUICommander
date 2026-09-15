import type { ReactNode } from 'react'
import { Box, Group, Stack, Text, Title } from '@mantine/core'

type PageHeaderProps = {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <Group justify="space-between" align="flex-start" wrap="wrap" gap="lg">
      <Stack gap={4} maw="48rem">
        <Title order={1} size="h2">
          {title}
        </Title>
        {description ? (
          <Text c="dimmed" size="sm" lh={1.55}>
            {description}
          </Text>
        ) : null}
      </Stack>
      {actions ? (
        <Box w={{ base: '100%', sm: 'auto' }} maw="100%">
          {actions}
        </Box>
      ) : null}
    </Group>
  )
}
