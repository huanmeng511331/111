import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 后端地址默认 8000，可通过环境变量 VITE_API_TARGET 覆盖（如端口被占用时）。
const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true
      }
    }
  }
})
