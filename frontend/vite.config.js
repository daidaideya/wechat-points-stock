import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router'],
      resolvers: [ElementPlusResolver()],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [
        ElementPlusResolver({
          importStyle: 'css',
        }),
      ],
      dts: 'src/components.d.ts',
    }),
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap',
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // Modern browsers only — smaller syntax, less polyfill-ish output.
    target: 'es2020',
    cssCodeSplit: true,
    // Faster CI builds; we report sizes via gzip-assets script instead.
    reportCompressedSize: false,
    sourcemap: mode === 'analyze',
    // Avoid preloading every vendor chunk on first paint. The browser still
    // fetches what the entry graph needs; skipping speculative preloads reduces
    // contention on slow Docker / reverse-proxy links.
    modulePreload: {
      polyfill: false,
      resolveDependencies(filename, deps) {
        return deps.filter((dep) => {
          // Icons are only needed after first interactive paint of the shell.
          if (dep.includes('element-plus-icons')) return false
          return true
        })
      },
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }

          if (id.includes('@element-plus/icons-vue')) {
            return 'element-plus-icons'
          }

          if (id.includes('element-plus')) {
            return 'element-plus'
          }

          if (id.includes('vue-router')) {
            return 'vue-router'
          }

          if (id.includes('axios')) {
            return 'axios'
          }

          if (id.includes('vue')) {
            return 'vue-vendor'
          }
        },
      },
    },
  },
}))
