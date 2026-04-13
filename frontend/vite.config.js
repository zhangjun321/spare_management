import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // base 必须与 Flask 静态资源路径一致，构建后无需手动修改 index.html
  base: '/static/react/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // 开发模式端口（通过代理访问 Flask 5000）
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // 开发时代理静态资源请求到 Flask
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // 输出到 Flask 静态目录，构建后直接可用，无需手动复制
    outDir: '../app/static/react',
    assetsDir: 'assets',
    // 清空旧产物，避免残留文件
    emptyOutDir: true,
  },
})
