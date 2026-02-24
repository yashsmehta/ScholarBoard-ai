import fs from 'node:fs'
import path from 'node:path'

const projectRoot = path.resolve(import.meta.dirname, '..')
const sourcePath = path.resolve(projectRoot, '..', 'website', 'data', 'scholars.json')
const targetPath = path.resolve(projectRoot, 'public', 'embedded-scholars.json')
const countArg = process.argv[2]
const count = Number.parseInt(countArg ?? process.env.EMBEDDED_COUNT ?? '100', 10)

if (!Number.isFinite(count) || count <= 0) {
  console.error('Embedded sample count must be a positive integer.')
  process.exit(1)
}

const raw = JSON.parse(fs.readFileSync(sourcePath, 'utf8'))
const subset = Object.fromEntries(Object.entries(raw).slice(0, count))

fs.mkdirSync(path.dirname(targetPath), { recursive: true })
fs.writeFileSync(targetPath, JSON.stringify(subset))

console.log(`Wrote ${Object.keys(subset).length} scholars to ${targetPath}`)
