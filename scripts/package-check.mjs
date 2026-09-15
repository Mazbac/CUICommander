import { existsSync, readFileSync } from 'node:fs'

const packageJson = JSON.parse(readFileSync('package.json', 'utf8'))
const pyproject = readFileSync('pyproject.toml', 'utf8')
const comfyignore = readFileSync('.comfyignore', 'utf8')

function requireMatch(pattern, label) {
  const match = pyproject.match(pattern)
  if (!match) throw new Error(`pyproject.toml is missing ${label}.`)
  return match[1]
}

const projectVersion = requireMatch(
  /^version\s*=\s*"([^"]+)"/m,
  'project version',
)
const publisher = requireMatch(
  /^PublisherId\s*=\s*"([^"]+)"/m,
  'Comfy Registry PublisherId',
)

if (projectVersion !== packageJson.version) {
  throw new Error(
    `Version mismatch: pyproject ${projectVersion}, package ${packageJson.version}.`,
  )
}
if (!publisher || /replace|todo|example/i.test(publisher)) {
  throw new Error('Comfy Registry PublisherId is still a placeholder.')
}

for (const file of [
  '__init__.py',
  'cuicommander/api.py',
  'web/console/index.html',
]) {
  if (!existsSync(file))
    throw new Error(`Required release file is missing: ${file}`)
}

if (/^web\/console\/?$/m.test(comfyignore)) {
  throw new Error('.comfyignore must not exclude the production web console.')
}
if (!/includes\s*=\s*\[[^\]]*"web\/console"/m.test(pyproject)) {
  throw new Error(
    '[tool.comfy].includes must preserve the production web console.',
  )
}

console.log(
  `Comfy Registry package metadata is consistent (${projectVersion}, publisher ${publisher}).`,
)
