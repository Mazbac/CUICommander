import {
  createTheme,
  type CSSVariablesResolver,
  type MantineColorsTuple,
} from '@mantine/core'

const fontFamily =
  'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'

const brand: MantineColorsTuple = [
  '#eef3ff',
  '#dce7ff',
  '#bdd0ff',
  '#93b1ff',
  '#688fff',
  '#426fff',
  '#2858ff',
  '#1b45e6',
  '#1638bd',
  '#132f99',
]

const neutral: MantineColorsTuple = [
  '#f7f8fa',
  '#f1f2f4',
  '#e4e7eb',
  '#cdd2d8',
  '#a0a7b0',
  '#747c87',
  '#535b66',
  '#343a42',
  '#1b1e23',
  '#0d0f12',
]

const dark: MantineColorsTuple = [
  '#f2f3f5',
  '#d8dbe0',
  '#aeb4bd',
  '#7c848f',
  '#454c56',
  '#343a42',
  '#252a31',
  '#1b1e23',
  '#14171b',
  '#0d0f12',
]
export const layoutTokens = {
  headerHeight: 64,
  navbarWidth: 224,
  contentMaxWidth: '86rem',
} as const

export const theme = createTheme({
  colors: { brand, neutral, gray: neutral, dark },
  primaryColor: 'brand',
  primaryShade: { light: 7, dark: 5 },
  autoContrast: true,
  defaultRadius: 'md',
  fontFamily,
  headings: { fontFamily, fontWeight: '600' },
})

export const cssVariablesResolver: CSSVariablesResolver = (resolvedTheme) => ({
  variables: {},
  light: { '--mantine-color-dimmed': resolvedTheme.colors.neutral[6] },
  dark: { '--mantine-color-dimmed': resolvedTheme.colors.dark[2] },
})
