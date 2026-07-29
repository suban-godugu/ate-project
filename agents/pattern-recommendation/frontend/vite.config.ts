import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

const uiPort = Number(process.env.VITE_UI_PORT ?? 5173)
const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000'
const embedBase = process.env.VITE_EMBED_BASE ?? '/embed/pattern-rec/'

export default defineConfig({
  // Namespace Vite assets and client routes behind the VERILUMEN :3000 proxy.
  base: embedBase,
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: uiPort,
    proxy: {
      // Proxy existing FastAPI routes — no backend CORS changes required
      '/health': { target: apiTarget, changeOrigin: true },
      '/version': { target: apiTarget, changeOrigin: true },
      '/datasets': { target: apiTarget, changeOrigin: true },
      '/patterns': { target: apiTarget, changeOrigin: true },
      '/redundancy': { target: apiTarget, changeOrigin: true },
      '/recommendations': { target: apiTarget, changeOrigin: true },
      '/failures': { target: apiTarget, changeOrigin: true },
      '/ml': { target: apiTarget, changeOrigin: true },
    },
  },
})
