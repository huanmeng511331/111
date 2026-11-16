<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDictionaries, fetchHazards } from '@/api/hazard'
import HazardLevelTag from '@/components/HazardLevelTag.vue'
import HazardStatusTag from '@/components/HazardStatusTag.vue'

const router = useRouter()

const loading = ref(false)
const items = ref([])
const total = ref(0)
const errorMessage = ref('')
const dictionaries = reactive({ hazard_types: [], hazard_levels: [], statuses: [] })

const query = reactive({
  status: '',
  level: '',
  type: '',
  keyword: '',
  overdue_only: false,
  page: 1,
  page_size: 10,
  sort_by: 'created_at',
  sort_order: 'desc',
})

const SORT_FIELDS = {
  hazard_no: 'hazard_no',
  hazard_level: 'hazard_level',
  due_date: 'due_date',
  status: 'status',
  created_at: 'created_at',
}

function buildParams() {
  return {
    status: query.status || undefined,
    level: query.level || undefined,
    type: query.type || undefined,
    keyword: query.keyword.trim() || undefined,
    overdue_only: query.overdue_only || false,
    page: query.page,
    page_size: query.page_size,
    sort_by: query.sort_by,
    sort_order: query.sort_order,
  }
}

async function loadHazards() {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchHazards(buildParams())
    items.value = data.items
    total.value = data.total
  } catch (error) {
    errorMessage.value = error.message
    items.value = []
    total.value = 0
    ElMessage.error(`隐患列表加载失败：${error.message}`)
  } finally {
    loading.value = false
  }
}

async function loadDictionaries() {
  try {
    const data = await fetchDictionaries()
    Object.assign(dictionaries, data)
  } catch (error) {
    ElMessage.warning(`筛选项加载失败：${error.message}`)
  }
}

function handleSearch() {
  query.page = 1
  loadHazards()
}

function handleReset() {
  Object.assign(query, {
    status: '',
    level: '',
    type: '',
    keyword: '',
    overdue_only: false,
    page: 1,
    page_size: 10,
    sort_by: 'created_at',
    sort_order: 'desc',
  })
  loadHazards()
}

function handleSortChange({ prop, order }) {
  query.sort_by = SORT_FIELDS[prop] || 'created_at'
  query.sort_order = order === 'ascending' ? 'asc' : 'desc'
  query.page = 1
  loadHazards()
}

function handlePageChange(page) {
  query.page = page
  loadHazards()
}

function handleSizeChange(size) {
  query.page_size = size
  query.page = 1
  loadHazards()
}

function viewDetail(row) {
  router.push(`/hazards/${row.id}`)
}

onMounted(() => {
  loadDictionaries()
  loadHazards()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">隐患台账</h2>
        <p class="page-subtitle">
          共 {{ total }} 条隐患，可按状态、等级、类型筛选并排序；点击编号进入详情执行审核、整改与验收。
        </p>
      </div>
      <el-button type="primary" :icon="'Plus'" @click="router.push('/hazards/new')">
        上报隐患
      </el-button>
    </div>

    <div class="card">
      <el-form class="filter-form" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 130px">
            <el-option v-for="item in dictionaries.statuses" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="query.level" placeholder="全部等级" clearable style="width: 120px">
            <el-option v-for="item in dictionaries.hazard_levels" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="query.type" placeholder="全部类型" clearable style="width: 140px">
            <el-option v-for="item in dictionaries.hazard_types" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input
            v-model="query.keyword"
            placeholder="编号 / 位置 / 描述 / 责任人"
            clearable
            style="width: 230px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="超期">
          <el-switch v-model="query.overdue_only" @change="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="'Search'" @click="handleSearch">查询</el-button>
          <el-button :icon="'Refresh'" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-alert
      v-if="errorMessage"
      class="list-error"
      type="error"
      :closable="false"
      show-icon
      :title="`列表加载失败：${errorMessage}`"
    />

    <div class="card list-card">
      <el-table
        v-loading="loading"
        :data="items"
        row-key="id"
        stripe
        :default-sort="{ prop: 'created_at', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="hazard_no" label="编号" width="160" sortable="custom">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="viewDetail(row)">
              {{ row.hazard_no }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="hazard_type" label="类型" width="90" />
        <el-table-column prop="hazard_level" label="等级" width="90" sortable="custom">
          <template #default="{ row }">
            <HazardLevelTag :level="row.hazard_level" />
          </template>
        </el-table-column>
        <el-table-column prop="location" label="隐患位置" min-width="165" show-overflow-tooltip />
        <el-table-column prop="owner" label="责任人" width="120">
          <template #default="{ row }">
            <span :class="{ muted: !row.owner }">{{ row.owner || '待分派' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="整改期限" width="120" sortable="custom">
          <template #default="{ row }">
            <span :style="row.is_overdue ? 'color:#d93025;font-weight:600' : ''">{{ row.due_date }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="150" sortable="custom">
          <template #default="{ row }">
            <HazardStatusTag :status="row.status" :is-overdue="row.is_overdue" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上报时间" width="158" sortable="custom" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无符合条件的隐患记录">
            <el-button type="primary" @click="router.push('/hazards/new')">立即上报隐患</el-button>
          </el-empty>
        </template>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-card {
  margin-top: 16px;
}

.list-error {
  margin-top: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}
</style>
