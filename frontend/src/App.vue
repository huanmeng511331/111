<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const route = useRoute()
const locale = zhCn

const menus = [
  { path: '/dashboard', label: '统计看板', icon: 'DataAnalysis' },
  { path: '/hazards', label: '隐患台账', icon: 'Tickets' },
  { path: '/hazards/new', label: '隐患上报', icon: 'EditPen' },
]

const activeMenu = computed(() => {
  if (route.path === '/hazards/new') {
    return '/hazards/new'
  }
  if (route.path.startsWith('/hazards')) {
    return '/hazards'
  }
  return '/dashboard'
})
</script>

<template>
  <el-config-provider :locale="locale">
    <el-container class="layout">
    <el-aside width="216px" class="layout__aside">
      <div class="brand">
        <el-icon :size="22"><FirstAidKit /></el-icon>
        <div>
          <div class="brand__name">HSE 隐患闭环</div>
          <div class="brand__desc">上报 · 分派 · 整改 · 验收</div>
        </div>
      </div>
      <el-menu :default-active="activeMenu" router class="layout__menu">
        <el-menu-item v-for="menu in menus" :key="menu.path" :index="menu.path">
          <el-icon><component :is="menu.icon" /></el-icon>
          <span>{{ menu.label }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-tip">
        <el-tag type="info" effect="plain" size="small">演示环境</el-tag>
        <p>数据为模拟数据，仅用于现场培训与 Demo 演示。</p>
      </div>
    </el-aside>

    <el-container>
      <el-header class="layout__header">
        <div class="header-title">{{ route.meta.title || 'HSE 隐患闭环演示' }}</div>
        <div class="header-user">
          <el-tag type="success" effect="plain" size="small">安全管理员</el-tag>
        </div>
      </el-header>
      <el-main class="layout__main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
    </el-container>
  </el-config-provider>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.layout__aside {
  background: #101a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 18px 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px 18px;
  color: #fff;
}

.brand__name {
  font-size: 16px;
  font-weight: 600;
}

.brand__desc {
  font-size: 12px;
  color: #8b9ab5;
  margin-top: 2px;
}

.layout__menu {
  background: transparent;
  border-right: none;
  flex: 1;
}

.layout__menu :deep(.el-menu-item) {
  color: #c6d1e4;
  border-radius: 8px;
  margin-bottom: 6px;
}

.layout__menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.layout__menu :deep(.el-menu-item.is-active) {
  background: #1f6feb;
  color: #fff;
}

.aside-tip {
  color: #8b9ab5;
  font-size: 12px;
  line-height: 1.6;
  padding: 12px 8px 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.aside-tip p {
  margin: 8px 0 0;
}

.layout__header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid var(--hse-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.layout__main {
  padding: 0;
  background: var(--hse-bg);
}

@media (max-width: 900px) {
  .layout__aside {
    width: 76px !important;
    padding: 12px 6px;
  }

  .brand__name,
  .brand__desc,
  .aside-tip,
  .layout__menu :deep(.el-menu-item span) {
    display: none;
  }
}
</style>
