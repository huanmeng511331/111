<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from '../utils/message'
import { fetchHazards } from '../api/hazards'
import LevelTag from '../components/LevelTag.vue'
import StatusTag from '../components/StatusTag.vue'
import { LEVEL_OPTIONS, STATUS_OPTIONS, TYPE_OPTIONS } from '../constants/hazard'
import { formatDate, formatDateTime } from '../utils/format'

const router = useRouter()
const loading = ref(false)
const rows = ref([])
const total = ref(0)

const query = reactive({
  status: '',
  type: '',
  level: '',
  keyword: '',
  overdue: false,
  page: 1,
  page_size: 10,
  sort_by: 'created_at',
  sort_order: 'desc'
})

async function loadHazards() {
  loading.value = true
  try {
    const params = {
      page: query.page,
      page_size: query.page_size,
      sort_by: query.sort_by,
      sort_order: query.sort_order
    }
    if (query.status) params.status = query.status
    if (query.type) params.type = query.type
    if (query.level) params.level = query.level
    if (query.keyword.trim()) params.keyword = query.keyword.trim()
    if (query.overdue) params.overdue = true

    const data = await fetchHazards(params)
    rows.value = data.items
    total.value = data.total
  } catch (error) {
    rows.value = []
    total.value = 0
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  loadHazards()
}

function handleReset() {
  Object.assign(query, {
    status: '',
    type: '',
    level: '',
    keyword: '',
    overdue: false,
    page: 1,
    page_size: 10,
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  loadHazards()
}

function handleSort({ prop, order }) {
  if (!order) {
    query.sort_by = 'created_at'
    query.sort_order = 'desc'
  } else {
    query.sort_by = prop
    query.sort_order = order === 'ascending' ? 'asc' : 'desc'
  }
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

function goDetail(row) {
  router.push(`/hazards/${row.id}`)
}

onMounted(loadHazards)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2 class="page-title">隐患台账</h2>
        <p class="page-desc">按状态、等级、类型筛选隐患，点击编号查看详情并执行审核、整改、验收。</p>
      </div>
      <div class="page-actions">
        <el-button :loading="loading" @click="loadHazards">刷新</el-button>
        <el-button type="primary" @click="router.push('/hazards/new')">上报隐患</el-button>
      </div>
    </div>

    <div class="page-card">
      <div class="filter-bar">
        <el-select v-model="query.status" placeholder="全部状态" clearable>
          <el-option v-for="item in STATUS_OPTIONS" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="query.level" placeholder="全部等级" clearable>
          <el-option v-for="item in LEVEL_OPTIONS" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="query.type" placeholder="全部类型" clearable>
          <el-option v-for="item in TYPE_OPTIONS" :key="item" :label="item" :value="item" />
        </el-select>
        <el-input
          v-model="query.keyword"
          class="keyword-input"
          placeholder="编号 / 位置 / 描述 / 人员"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-checkbox v-model="query.overdue">只看超期</el-checkbox>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
    </div>

    <div class="page-card">
      <div class="table-toolbar">
        <span class="total-text">共 {{ total }} 条隐患记录</span>
        <span class="muted">支持点击表头按编号、整改期限、上报时间排序</span>
      </div>

      <el-table
        v-loading="loading"
        :data="rows"
        border
        stripe
        style="width: 100%"
        @sort-change="handleSort"
      >
        <el-table-column prop="hazard_no" label="隐患编号" min-width="170" sortable="custom">
          <template #default="{ row }">
            <a class="link-text" @click="goDetail(row)">{{ row.hazard_no }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="hazard_type" label="隐患类型" width="110" />
        <el-table-column prop="hazard_level" label="等级" width="90" align="center">
          <template #default="{ row }">
            <LevelTag :level="row.hazard_level" />
          </template>
        </el-table-column>
        <el-table-column prop="location" label="隐患位置" min-width="170" show-overflow-tooltip />
        <el-table-column prop="owner" label="责任人" width="100">
          <template #default="{ row }">{{ row.owner || '待分派' }}</template>
        </el-table-column>
        <el-table-column prop="due_date" label="整改期限" width="140" sortable="custom">
          <template #default="{ row }">
            <span>{{ formatDate(row.due_date) }}</span>
            <el-tag v-if="row.is_overdue" type="danger" size="small" effect="dark" class="ml-4">
              超期
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上报时间" width="160" sortable="custom">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">详情</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :image-size="80" description="暂无符合条件的隐患，试试调整筛选条件或上报新隐患" />
        </template>
      </el-table>

      <div class="pagination-bar">
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
  </section>
</template>

<style scoped>
.ml-4 {
  margin-left: 6px;
}
</style>
