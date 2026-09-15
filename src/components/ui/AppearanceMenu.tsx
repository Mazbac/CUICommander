import { Button, Menu, Text, useMantineColorScheme } from '@mantine/core'

const options = [
  { value: 'auto', label: 'System' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
] as const

export function AppearanceMenu() {
  const { colorScheme, setColorScheme } = useMantineColorScheme()
  const current =
    options.find((option) => option.value === colorScheme) ?? options[0]

  return (
    <Menu position="bottom-end" width="target">
      <Menu.Target>
        <Button
          variant="default"
          size="compact-sm"
          aria-label={`Appearance: ${current.label}`}
        >
          {current.label}
        </Button>
      </Menu.Target>
      <Menu.Dropdown>
        {options.map((option) => (
          <Menu.Item
            key={option.value}
            onClick={() => setColorScheme(option.value)}
          >
            <Text size="sm" fw={option.value === colorScheme ? 650 : 400}>
              {option.value === colorScheme ? '✓ ' : ''}
              {option.label}
            </Text>
          </Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  )
}
