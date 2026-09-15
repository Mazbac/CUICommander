import type { ReactNode } from 'react'
import { AppShell, Burger, Group, NavLink, Stack, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { layoutTokens } from '../theme/theme'

export type PageId =
  'overview' | 'resources' | 'transfers' | 'workflows' | 'runtime' | 'activity'

type AppFrameProps = {
  children: ReactNode
  activePage: PageId
  onNavigate: (page: PageId) => void
}

const pages: Array<{ id: PageId; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'resources', label: 'Resources' },
  { id: 'transfers', label: 'Transfers & jobs' },
  { id: 'workflows', label: 'Workflows' },
  { id: 'runtime', label: 'Runtime' },
  { id: 'activity', label: 'Activity' },
]

export function AppFrame({ children, activePage, onNavigate }: AppFrameProps) {
  const [opened, { toggle, close }] = useDisclosure(false)

  return (
    <AppShell
      header={{ height: layoutTokens.headerHeight }}
      navbar={{
        width: layoutTokens.navbarWidth,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="lg"
    >
      {' '}
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger
            opened={opened}
            onClick={toggle}
            hiddenFrom="sm"
            size="sm"
            aria-label="Toggle navigation"
          />
          <Stack gap={0}>
            <Text fw={700}>CUICommander</Text>
            <Text c="dimmed" size="xs">
              Universal ComfyUI control plane
            </Text>
          </Stack>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="sm">
        <Stack gap="xs">
          {pages.map((page) => (
            <NavLink
              key={page.id}
              label={page.label}
              active={activePage === page.id}
              color="dark"
              variant="filled"
              href={page.id === 'overview' ? '#/' : `#/${page.id}`}
              onClick={(event) => {
                event.preventDefault()
                onNavigate(page.id)
                close()
              }}
            />
          ))}
        </Stack>
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
