import fs from 'node:fs'
import path from 'node:path'

const frontendRoot = path.resolve(import.meta.dirname, '..')
const resourceRoots = [path.join(frontendRoot, 'public'), path.join(frontendRoot, 'src', 'assets')]
const sourceRoots = [path.join(frontendRoot, 'index.html'), path.join(frontendRoot, 'src')]
const forbiddenStarterResources = [
  path.join(frontendRoot, 'public', 'vite.svg'),
  path.join(frontendRoot, 'src', 'assets', 'vue.svg'),
  path.join(frontendRoot, 'src', 'components', 'HelloWorld.vue'),
]

function collectFiles(target) {
  if (!fs.existsSync(target)) return []
  const stat = fs.statSync(target)
  if (stat.isFile()) return [target]

  const files = []
  for (const entry of fs.readdirSync(target, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'dist') continue
    files.push(...collectFiles(path.join(target, entry.name)))
  }
  return files
}

function normalized(value) {
  return value.split(path.sep).join('/')
}

const sourceText = sourceRoots
  .flatMap((root) => collectFiles(root))
  .filter((file) => !file.endsWith('.d.ts'))
  .map((file) => fs.readFileSync(file, 'utf8'))
  .join('\n')

const errors = []
for (const file of forbiddenStarterResources) {
  if (fs.existsSync(file)) {
    errors.push(`starter resource should be removed: ${normalized(path.relative(frontendRoot, file))}`)
  }
}

let scanned = 0
for (const root of resourceRoots) {
  for (const file of collectFiles(root)) {
    scanned += 1
    const relative = normalized(path.relative(frontendRoot, file))
    const publicRelative = relative.startsWith('public/') ? relative.slice('public/'.length) : relative
    const basename = path.basename(file)
    const candidates = [relative, publicRelative, `/${publicRelative}`, basename]
    if (!candidates.some((candidate) => sourceText.includes(candidate))) {
      errors.push(`resource is not referenced by frontend source: ${relative}`)
    }
  }
}

if (errors.length > 0) {
  console.error('[resource-check] failed')
  for (const error of errors) console.error(`- ${error}`)
  process.exitCode = 1
} else {
  console.log(`[resource-check] passed; scanned ${scanned} static resource(s)`)
}
