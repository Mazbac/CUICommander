import type { ReactNode } from 'react'
import { Stack, Text, Title } from '@mantine/core'

type SectionProps = {
  title: string
  description?: string
  children: ReactNode
}

export function Section({ title, description, children }: SectionProps) {
  return (
    <Stack gap="md">
      <Stack gap={4} maw="52rem">
        <Title order={2} size="h4">
          {title}
        </Title>
        {description ? (
          <Text c="dimmed" size="sm" lh={1.55}>
            {description}
          </Text>
        ) : null}
      </Stack>
      {children}
    </Stack>
  )
}
