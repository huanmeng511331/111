import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'

const COMPONENTS_SPECIFIER = 'element-plus/es/components'
const COMPONENTS_DIR = fileURLToPath(
  new URL('./node_modules/element-plus/es/components', import.meta.url),
)

// 子组件从父组件模块导出，按需解析时需指向父目录，避免退化为整库导入
const SUB_COMPONENT_FOLDER = {
  aside: 'container',
  header: 'container',
  footer: 'container',
  main: 'container',
  'menu-item': 'menu',
  'menu-item-group': 'menu',
  'sub-menu': 'menu',
  'form-item': 'form',
  option: 'select',
  'option-group': 'select',
  'table-column': 'table',
  'radio-group': 'radio',
  'radio-button': 'radio',
  'descriptions-item': 'descriptions',
  'timeline-item': 'timeline',
  'skeleton-item': 'skeleton',
}

function kebabCase(name) {
  return name
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
    .toLowerCase()
}

// 预构建实际使用的组件模块，避免开发时按页面逐步发现依赖导致多次页面刷新
const PREDEPENDED_COMPONENTS = [
  'alert',
  'button',
  'col',
  'config-provider',
  'container',
  'date-picker',
  'descriptions',
  'dialog',
  'empty',
  'form',
  'icon',
  'image',
  'input',
  'link',
  'loading',
  'menu',
  'message',
  'pagination',
  'radio',
  'result',
  'row',
  'select',
  'skeleton',
  'switch',
  'table',
  'tag',
  'timeline',
]

/**
 * Element Plus 深度按需引入解析器。
 * 官方 ElementPlusResolver 从 element-plus/es 汇总入口导入，会把整个组件库拉入构建图；
 * 这里直接定位到 element-plus/es/components/<component>/index，显著降低构建内存与产物体积。
 */
function ElementPlusDeepResolver() {
  return {
    type: 'component',
    resolve(name) {
      if (!/^El[A-Z]/.test(name)) {
        return undefined
      }
      const rawFolder = kebabCase(name.slice(2))
      const folder = SUB_COMPONENT_FOLDER[rawFolder] || rawFolder
      if (!fs.existsSync(path.join(COMPONENTS_DIR, folder, 'index.mjs'))) {
        return undefined
      }
      return { name, from: `${COMPONENTS_SPECIFIER}/${folder}/index` }
    },
  }
}

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({ resolvers: [ElementPlusDeepResolver()], dts: 'auto-imports.d.ts' }),
    Components({ resolvers: [ElementPlusDeepResolver()], dts: 'components.d.ts' }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    include: PREDEPENDED_COMPONENTS.map((name) => `${COMPONENTS_SPECIFIER}/${name}/index`),
  },
  build: {
    chunkSizeWarningLimit: 1500,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 开发环境将 /api 转发到 FastAPI，避免跨域配置；端口冲突时可用 VITE_API_TARGET 覆盖
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      // 生产构建预览同样转发 /api，便于构建后本地验证
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
