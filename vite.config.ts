import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  root: 'app',
  plugins: [react(), tailwindcss()],
  resolve: {
    // Mirrors the "@/*" path alias in tsconfig.json
    alias: {
      '@': fileURLToPath(new URL('./app/src', import.meta.url)),
    },
  },
  build: {
    outDir: '../app-dist',
    emptyOutDir: true,
  },
})
