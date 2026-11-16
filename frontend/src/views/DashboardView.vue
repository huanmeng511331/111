<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from '../utils/message'
import { fetchStatistics } from '../api/hazards'
import BarChart from '../components/BarChart.vue'

const router = useRouter()
const loading = ref(true)
const stats = ref(null)
const errorText = ref('')
const refreshedAt = ref('')

const STATUS_COLORS = {
  待审核: '#e6a23c',
  整改中: '#1f6feb',
  待验收: '#22b8cf',
  已关闭: '#2f9e44'
}

const LEVEL_COLORS = {
  一般: '#4dabf7',
  较大: '#e6a23c',
  重大: '#d64545'
}

const statusBars = computed(() =>
  Object.entries(stats.value?.status_counts || {}).map(([label, value]) => ({
    label,
    value,
    color: STATUS_COLORS[label]
  }))
)

const levelBars = computed(() =>
  Object.entries(stats.value?.level_counts || {}).map(([label, value]) => ({
    label,
    value,
    color: LEVEL_COLORS[label]
  }))
)

const typeBars = computed(() =>
  Object.entries(stats.value?.type_counts || {})
    .map(([label, value]) => ({ label, value, color: '#1f6feb' }))
    .sort((a, b) => b.value - a.value)
)

const trendMax = computed(() =>
  Math.max(...(stats.value?.recent_7_days || []).map((item) => item.count), 1)
)

const trendBars = computed(() =>
  (stats.value?.recent_7_days || []).map((item) => ({
    label: item.date.slice(5),
    value: item.count,
    height: `${Math.max(4, Math.round((item.count / trendMax.value) * 120))}px`
  }))
)

const cards = computed(() => {
  if (!stats.value) return []
  return [
    { label: '隐患总数', value: stats.value.total, tone: '', extra: '全部已上报隐患' },
    {
      label: '待审核',
      value: stats.value.status_counts['待审核'] || 0,
      tone: 'warning',
      extra: '等待审核分派'
    },
    {
      label: '整改中',
      value: stats.value.status_counts['整改中'] || 0,
      tone: 'primary',
      extra: '责任人整改中'
    },
    {
      label: '待验收',
      value: stats.value.status_counts['待验收'] || 0,
      tone: 'info',
      extra: '等待验收确认'
    },
    {
      label: '已关闭',
      value: stats.value.status_counts['已关闭'] || 0,
      tone: 'success',
      extra: `关闭率 ${stats.value.closed_rate}%`
    },
    {
      label: '超期隐患',
      value: stats.value.overdue_count,
      tone: 'danger',
      extra: '未关闭且已过整改期限'
    }
  ]
})

async function loadStatistics() {
  loading.value = true
  errorText.value = ''
  try {
    stats.value = await fetchStatistics()
    refreshedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (error) {
    errorText.value = error.message
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function goOverdueList() {
  router.push('/hazards')
}

onMounted(loadStatistics)
</script>

<template>
  <section v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">统计看板</h2>
        <p class="page-desc">查看待审核、整改中、待验收、已关闭数量，以及按等级、类型的分布与超期情况。</p>
      </div>
      <div class="page-actions">
        <span v-if="refreshedAt" class="muted" style="align-self: center">更新于 {{ refreshedAt }}</span>
        <el-button :loading="loading" @click="loadStatistics">刷新数据</el-button>
        <el-button type="primary" @click="router.push('/hazards/new')">上报隐患</el-button>
      </div>
    </div>

    <el-alert
      v-if="errorText"
      type="error"
      show-icon
      :closable="false"
      :title="errorText"
      description="请确认后端服务已启动后点击「刷新数据」。"
      style="margin-bottom: 16px"
    />

    <template v-if="stats">
      <div class="stat-grid">
        <div v-for="card in cards" :key="card.label" class="stat-card" :class="card.tone">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-extra">{{ card.extra }}</div>
        </div>
      </div>

      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <div class="page-card">
            <div class="chart-card-title">状态分布 <small>共 {{ stats.total }} 条</small></div>
            <BarChart :data="statusBars" />
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <div class="page-card">
            <div class="chart-card-title">
              等级分布
              <small>
                超期 {{ stats.overdue_count }} 条 ·
                <el-link type="primary" :underline="false" @click="goOverdueList">去台账处理</el-link>
              </small>
            </div>
            <BarChart :data="levelBars" />
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <div class="page-card">
            <div class="chart-card-title">隐患类型分布</div>
            <BarChart :data="typeBars" />
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <div class="page-card">
            <div class="chart-card-title">近 7 日上报趋势 <small>单位：条</small></div>
            <div class="trend-chart">
              <div v-for="item in trendBars" :key="item.label" class="trend-item">
                <span class="trend-value">{{ item.value }}</span>
                <div class="trend-bar" :style="{ height: item.height }" />
                <span class="trend-label">{{ item.label }}</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else-if="!loading && !errorText" description="暂无统计数据" />
  </section>
</template>
