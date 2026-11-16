<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataAnalysis, DocumentAdd, List } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const route = useRoute()

const activeMenu = computed(() => {
  if (route.path === '/hazards/new') return '/hazards/new'
  if (route.path.startsWith('/hazards')) return '/hazards'
  return route.path
})
</script>

<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-shell">
      <el-aside width="224px" class="app-aside">
        <div class="brand">
          <span class="brand-badge">HSE</span>
          <div class="brand-text">
            <strong>隐患闭环管理</strong>
            <small>Hazard Demo</small>
          </div>
        </div>
        <el-menu :default-active="activeMenu" router class="app-menu">
          <el-menu-item index="/hazards">
            <el-icon><List /></el-icon>
            <span>隐患台账</span>
          </el-menu-item>
          <el-menu-item index="/hazards/new">
            <el-icon><DocumentAdd /></el-icon>
            <span>上报隐患</span>
          </el-menu-item>
          <el-menu-item index="/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计看板</span>
          </el-menu-item>
        </el-menu>
        <div class="aside-footer">演示数据 · 非生产环境</div>
      </el-aside>

      <el-container>
        <el-header class="app-header">
          <div>
            <div class="header-title">HSE 隐患上报与闭环管理演示系统</div>
            <div class="header-subtitle">上报 → 审核分派 → 整改 → 验收关闭</div>
          </div>
          <el-tag type="info" effect="plain">Demo 数据</el-tag>
        </el-header>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>
