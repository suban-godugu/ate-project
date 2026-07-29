import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

const uiPort = Number(process.env.VITE_UI_PORT ?? 3043)
const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8043'
const embedBase = process.env.VITE_EMBED_BASE ?? '/embed/test-opt/'

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
    host: '127.0.0.1',
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
  },
})
