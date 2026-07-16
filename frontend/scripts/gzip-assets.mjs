/**
 * Post-build: write .gz siblings for hashed assets so the backend can serve
 * precompressed bytes without Python GZipMiddleware CPU cost on every request.
 */
import { createReadStream, createWriteStream, readdirSync, statSync } from 'node:fs'
import { pipeline } from 'node:stream/promises'
import { createGzip } from 'node:zlib'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const assetsDir = path.resolve(__dirname, '../dist/assets')

const COMPRESS_EXT = new Set(['.js', '.css', '.svg', '.json', '.html', '.mjs', '.map'])
const MIN_BYTES = 1024

async function gzipFile(srcPath) {
  const destPath = `${srcPath}.gz`
  await pipeline(
    createReadStream(srcPath),
    createGzip({ level: 9 }),
    createWriteStream(destPath),
  )
  return destPath
}

async function main() {
  let files
  try {
    files = readdirSync(assetsDir)
  } catch (err) {
    console.error('[gzip-assets] dist/assets not found — run vite build first')
    process.exit(1)
  }

  let count = 0
  let saved = 0
  for (const name of files) {
    if (name.endsWith('.gz')) continue
    const ext = path.extname(name).toLowerCase()
    if (!COMPRESS_EXT.has(ext)) continue
    const full = path.join(assetsDir, name)
    const st = statSync(full)
    if (!st.isFile() || st.size < MIN_BYTES) continue
    await gzipFile(full)
    const gzSize = statSync(`${full}.gz`).size
    saved += Math.max(0, st.size - gzSize)
    count += 1
    console.log(
      `[gzip-assets] ${name}: ${(st.size / 1024).toFixed(1)}KB -> ${(gzSize / 1024).toFixed(1)}KB`,
    )
  }
  console.log(
    `[gzip-assets] done: ${count} files, saved ~${(saved / 1024).toFixed(0)}KB uncompressed equivalent`,
  )
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
