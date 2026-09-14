import { spawnSync } from 'node:child_process'

const candidates = [
  { command: 'python', prefix: [] },
  { command: 'python3', prefix: [] },
  { command: 'py', prefix: ['-3'] },
]

const interpreter = candidates.find(({ command, prefix }) => {
  const result = spawnSync(command, [...prefix, '--version'], {
    encoding: 'utf8',
  })
  return result.status === 0
})

if (!interpreter) {
  console.error('Python 3 is required to verify the CUICommander backend.')
  process.exit(1)
}

const pythonFiles = [
  '__init__.py',
  'cuicommander/security.py',
  'cuicommander/roots.py',
  'cuicommander/resources.py',
  'cuicommander/discovery.py',
  'cuicommander/openapi.py',
  'cuicommander/api.py',
]

function run(args, label) {
  const result = spawnSync(
    interpreter.command,
    [...interpreter.prefix, ...args],
    {
      encoding: 'utf8',
      stdio: 'inherit',
    },
  )
  if (result.status !== 0) {
    console.error(`${label} failed.`)
    process.exit(result.status ?? 1)
  }
}

run(['-m', 'py_compile', ...pythonFiles], 'Python syntax check')
run(
  ['-m', 'unittest', 'discover', '-s', 'tests/python', '-p', 'test_*.py'],
  'Python unit tests',
)

console.log('Python backend checks passed.')
