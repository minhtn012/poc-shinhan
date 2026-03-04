import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [tailwindcss(), vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy /static/* to the OCR backend so images are same-origin (avoids cross-origin SVG rendering issues)
      '/static': {
        target: 'http://10.3.11.150:8000',
        changeOrigin: true
      }
    }
  }
})
