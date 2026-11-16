<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchStatistics } from '@/api/hazard'

const loading = ref(false)
const errorMessage = ref('')
const stats = ref(null)

const STATUS_COLORS = {
  待审核: '#e6a23c',
  整改中: '#1f6feb',
  待验收: '#7b61ff',
  已关闭: '#2e9b5b',
}

const LEVEL_COLORS = {
  一般: '#909399',
  较大: '#e6a23c',
  重大: '#d93025',
}

const TYPE_COLORS = ['#1f6feb', '#2e9b5b', '#e6a23c', '#7b61ff', '#00a6a6', '#d93025']

const totalHazards = computed(() => stats.value?.total ?? 0)

function ratio(count) {
  if (!stats.value || !stats.value.total) return 0
  return Math.round((count / stats.value.total) * 100)
}

function levelColor(name) {
  return LEVEL_COLORS[name] || '#909399'
}

function typeColor(index) {
  return TYPE_COLORS[index % TYPE_COLORS.length]
}

const maxTrend = computed(() =>
  Math.max(1, ...(stats.value?.trend?.map((item) => item.count) || [1])),
)

const maxTypeCount = computed(() =>
  Math.max(1, ...(stats.value?.by_type?.map((item) => item.count) || [1])),
)

const typeBars = computed(() =>
  (stats.value?.by_type || []).map((item) => ({
    ...item,
    width: Math.round((item.count / maxTypeCount.value) * 100),
  })),
)

async function loadStatistics() {
  loading.value = true
  errorMessage.value = ''
  try {
    stats.value = await fetchStatistics()
  } catch (error) {
    errorMessage.value = error.message
    stats.value = null
    ElMessage.error(`统计数据加载失败：${error.message}`)
  } finally {
    loading.value = false
  }
}

function shortDate(value) {
  return value?.slice(5) || ''
}

onMounted(loadStatistics)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">统计看板</h2>
        <p class="page-subtitle">按状态、等级与类型统计隐患分布，展示近 7 日上报趋势。</p>
      </div>
      <el-button :icon="'Refresh'" :loading="loading" @click="loadStatistics">刷新数据</el-button>
    </div>

    <el-alert
      v-if="errorMessage"
      type="error"
      show-icon
      :closable="false"
      :title="`统计数据加载失败：${errorMessage}`"
    />

    <div v-loading="loading">
      <el-empty v-if="!loading && stats && totalHazards === 0" description="暂无隐患数据，请先上报隐患">
        <el-button type="primary" @click="$router.push('/hazards/new')">去上报隐患</el-button>
      </el-empty>

      <template v-else-if="stats">
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-card__label">
              <el-icon><Tickets /></el-icon>隐患总数
            </div>
            <div class="stat-card__value">{{ stats.total }}</div>
            <div class="stat-card__hint">演示数据 + 现场上报累计</div>
          </div>
          <div class="stat-card stat-card--warning">
            <div class="stat-card__label">
              <el-icon><Bell /></el-icon>待审核
            </div>
            <div class="stat-card__value">{{ stats.pending_review }}</div>
            <div class="stat-card__hint">等待安全管理人员分派</div>
          </div>
          <div class="stat-card">
            <div class="stat-card__label">
              <el-icon><Tools /></el-icon>整改中
            </div>
            <div class="stat-card__value">{{ stats.rectifying }}</div>
            <div class="stat-card__hint">责任人正在整改</div>
          </div>
          <div class="stat-card">
            <div class="stat-card__label">
              <el-icon><View /></el-icon>待验收
            </div>
            <div class="stat-card__value">{{ stats.pending_acceptance }}</div>
            <div class="stat-card__hint">等待安全管理人员验收</div>
          </div>
          <div class="stat-card stat-card--success">
            <div class="stat-card__label">
              <el-icon><CircleCheck /></el-icon>已关闭
            </div>
            <div class="stat-card__value">{{ stats.closed }}</div>
            <div class="stat-card__hint">闭环率 {{ stats.closing_rate }}%</div>
          </div>
          <div class="stat-card stat-card--danger">
            <div class="stat-card__label">
              <el-icon><WarningFilled /></el-icon>已超期
            </div>
            <div class="stat-card__value">{{ stats.overdue }}</div>
            <div class="stat-card__hint">超过整改期限且未关闭</div>
          </div>
        </div>

        <div class="chart-grid">
          <div class="card">
            <div class="card-title">状态分布</div>
            <div v-for="item in stats.by_status" :key="item.name" class="bar-row">
              <span class="bar-row__label">{{ item.name }}</span>
              <div class="bar-row__track">
                <div
                  class="bar-row__fill"
                  :style="{ width: `${ratio(item.count)}%`, background: STATUS_COLORS[item.name] || '#909399' }"
                />
              </div>
              <span class="bar-row__value">{{ item.count }}</span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">隐患等级分布</div>
            <div v-for="item in stats.by_level" :key="item.name" class="bar-row">
              <span class="bar-row__label">{{ item.name }}</span>
              <div class="bar-row__track">
                <div
                  class="bar-row__fill"
                  :style="{ width: `${ratio(item.count)}%`, background: levelColor(item.name) }"
                />
              </div>
              <span class="bar-row__value">{{ item.count }}</span>
            </div>
            <p class="muted note">重大隐患应优先分派并在最短期限内闭环。</p>
          </div>

          <div class="card">
            <div class="card-title">隐患类型分布</div>
            <div v-for="(item, index) in typeBars" :key="item.name" class="bar-row">
              <span class="bar-row__label">{{ item.name }}</span>
              <div class="bar-row__track">
                <div
                  class="bar-row__fill"
                  :style="{ width: `${item.width}%`, background: typeColor(index) }"
                />
              </div>
              <span class="bar-row__value">{{ item.count }}</span>
            </div>
            <el-empty v-if="!stats.by_type.length" description="暂无类型数据" :image-size="70" />
          </div>
        </div>

        <div class="card trend-card">
          <div class="card-title">
            <span>近 7 日上报趋势</span>
            <span class="muted">按上报时间统计</span>
          </div>
          <div class="trend">
            <div v-for="item in stats.trend" :key="item.date" class="trend__item">
              <span class="trend__value">{{ item.count }}</span>
              <div
                class="trend__bar"
                :style="{ height: `${Math.max(4, Math.round((item.count / maxTrend) * 140))}px` }"
              />
              <span class="trend__label">{{ shortDate(item.date) }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.card-title {
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trend-card {
  margin-top: 16px;
}

.note {
  margin: 12px 0 0;
  font-size: 12px;
}
</style>
