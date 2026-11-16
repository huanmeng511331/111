<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  acceptHazard,
  assignHazard,
  fetchDictionaries,
  fetchHazardDetail,
  submitRectification,
} from '@/api/hazard'
import HazardLevelTag from '@/components/HazardLevelTag.vue'
import HazardStatusTag from '@/components/HazardStatusTag.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const hazard = ref(null)
const notFound = ref(false)
const errorMessage = ref('')
const ownerOptions = ref([])

const assignVisible = ref(false)
const assignSubmitting = ref(false)
const assignFormRef = ref(null)
const assignForm = reactive({
  owner: '',
  due_date: '',
  auditor: '安全管理员',
  comment: '',
})

const rectifyVisible = ref(false)
const rectifySubmitting = ref(false)
const rectifyFormRef = ref(null)
const rectifyForm = reactive({
  rectification_measure: '',
  rectification_result: '',
  operator: '',
})

const acceptVisible = ref(false)
const acceptSubmitting = ref(false)
const acceptFormRef = ref(null)
const acceptForm = reactive({
  decision: 'pass',
  acceptance_comment: '现场核查通过，同意关闭隐患。',
  operator: '安全管理员',
})

const assignRules = {
  owner: [{ required: true, message: '请选择或填写整改责任人', trigger: 'change' }],
  due_date: [{ required: true, message: '请选择整改期限', trigger: 'change' }],
  auditor: [{ required: true, message: '请填写审核人', trigger: 'blur' }],
}

const rectifyRules = {
  rectification_measure: [
    { required: true, message: '请填写整改措施', trigger: 'blur' },
    { min: 2, max: 500, message: '整改措施需在 2-500 个字符之间', trigger: 'blur' },
  ],
  rectification_result: [
    { required: true, message: '请填写整改完成情况', trigger: 'blur' },
    { min: 2, max: 500, message: '整改结果需在 2-500 个字符之间', trigger: 'blur' },
  ],
  operator: [{ required: true, message: '请填写提交人', trigger: 'blur' }],
}

const acceptRules = {
  acceptance_comment: [
    { required: true, message: '请填写验收意见', trigger: 'blur' },
    { min: 2, max: 300, message: '验收意见需在 2-300 个字符之间', trigger: 'blur' },
  ],
  operator: [{ required: true, message: '请填写验收人', trigger: 'blur' }],
}

const canAssign = computed(() => hazard.value?.status === '待审核')
const canRectify = computed(() => hazard.value?.status === '整改中')
const canAccept = computed(() => hazard.value?.status === '待验收')

const statusHint = computed(() => {
  const status = hazard.value?.status
  if (status === '待审核') return '等待安全管理人员审核并分派整改责任人。'
  if (status === '整改中') return '责任人需在整改期限前提交整改措施与完成情况。'
  if (status === '待验收') return '等待安全管理人员验收，验收通过后隐患关闭。'
  if (status === '已关闭') return '隐患已闭环关闭，如需复查可在台账中新增记录。'
  return ''
})

// 整改要求取自最近一次「审核并分派」的审核意见
const rectificationRequirement = computed(() => {
  const logs = hazard.value?.flow_logs || []
  const assignLogs = logs.filter((log) => log.action === '审核并分派')
  return assignLogs.length ? assignLogs[assignLogs.length - 1].comment : ''
})

function disabledPastDate(date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date.getTime() < today.getTime()
}

async function loadDetail() {
  loading.value = true
  errorMessage.value = ''
  notFound.value = false
  try {
    hazard.value = await fetchHazardDetail(route.params.id)
  } catch (error) {
    hazard.value = null
    if (error.status === 404) {
      notFound.value = true
    } else {
      errorMessage.value = error.message
      ElMessage.error(`详情加载失败：${error.message}`)
    }
  } finally {
    loading.value = false
  }
}

async function loadOwners() {
  try {
    const data = await fetchDictionaries()
    ownerOptions.value = data.owners
  } catch (error) {
    ElMessage.warning(`责任人候选加载失败：${error.message}`)
  }
}

function openAssign() {
  Object.assign(assignForm, {
    owner: hazard.value?.owner || '',
    due_date: hazard.value?.due_date || '',
    auditor: '安全管理员',
    comment: '',
  })
  assignVisible.value = true
}

function openRectify() {
  Object.assign(rectifyForm, {
    rectification_measure: '',
    rectification_result: '',
    operator: hazard.value?.owner || '',
  })
  rectifyVisible.value = true
}

function openAccept() {
  Object.assign(acceptForm, {
    decision: 'pass',
    acceptance_comment: '现场核查通过，同意关闭隐患。',
    operator: '安全管理员',
  })
  acceptVisible.value = true
}

async function submitAssign() {
  if (!assignFormRef.value) return
  try {
    await assignFormRef.value.validate()
  } catch {
    return
  }
  assignSubmitting.value = true
  try {
    await assignHazard(hazard.value.id, { ...assignForm, comment: assignForm.comment || null })
    ElMessage.success('审核分派成功，隐患进入整改中')
    assignVisible.value = false
    await loadDetail()
  } catch (error) {
    ElMessage.error(`分派失败：${error.message}`)
  } finally {
    assignSubmitting.value = false
  }
}

async function submitRectify() {
  if (!rectifyFormRef.value) return
  try {
    await rectifyFormRef.value.validate()
  } catch {
    return
  }
  rectifySubmitting.value = true
  try {
    await submitRectification(hazard.value.id, { ...rectifyForm })
    ElMessage.success('整改已提交，等待验收')
    rectifyVisible.value = false
    await loadDetail()
  } catch (error) {
    ElMessage.error(`提交整改失败：${error.message}`)
  } finally {
    rectifySubmitting.value = false
  }
}

async function submitAccept() {
  if (!acceptFormRef.value) return
  try {
    await acceptFormRef.value.validate()
  } catch {
    return
  }
  acceptSubmitting.value = true
  try {
    const updated = await acceptHazard(hazard.value.id, { ...acceptForm })
    ElMessage.success(acceptForm.decision === 'pass' ? '验收通过，隐患已关闭' : '已退回责任人继续整改')
    acceptVisible.value = false
    hazard.value = updated
    await loadDetail()
  } catch (error) {
    ElMessage.error(`验收失败：${error.message}`)
  } finally {
    acceptSubmitting.value = false
  }
}

onMounted(() => {
  loadOwners()
  loadDetail()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div class="detail-heading">
        <el-button :icon="'Back'" @click="router.push('/hazards')">返回台账</el-button>
        <h2 class="page-title">隐患详情</h2>
        <template v-if="hazard">
          <HazardStatusTag :status="hazard.status" :is-overdue="hazard.is_overdue" />
        </template>
      </div>
      <div v-if="hazard" class="detail-actions">
        <el-button v-if="canAssign" type="primary" :icon="'UserFilled'" @click="openAssign">
          审核并分派
        </el-button>
        <el-button v-if="canRectify" type="primary" :icon="'Tools'" @click="openRectify">
          提交整改
        </el-button>
        <el-button v-if="canAccept" type="success" :icon="'CircleCheck'" @click="openAccept">
          验收处理
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="card">
      <el-skeleton :rows="6" animated />
    </div>

    <el-alert
      v-else-if="errorMessage"
      type="error"
      show-icon
      :closable="false"
      :title="`详情加载失败：${errorMessage}`"
    />

    <div v-else-if="notFound" class="card">
      <el-empty description="该隐患不存在或已被删除">
        <el-button type="primary" @click="router.push('/hazards')">返回隐患台账</el-button>
      </el-empty>
    </div>

    <template v-else-if="hazard">
      <el-alert
        v-if="hazard.is_overdue"
        class="overdue-alert"
        type="error"
        show-icon
        :closable="false"
        title="该隐患已超过整改期限，请尽快跟进整改与验收。"
      />
      <el-alert class="hint-alert" type="info" show-icon :closable="false" :title="statusHint" />

      <div class="detail-grid">
        <div class="card">
          <div class="card-title">
            <span>上报信息</span>
            <span class="muted">{{ hazard.hazard_no }}</span>
          </div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="隐患编号">{{ hazard.hazard_no }}</el-descriptions-item>
            <el-descriptions-item label="隐患类型">{{ hazard.hazard_type }}</el-descriptions-item>
            <el-descriptions-item label="隐患等级">
              <HazardLevelTag :level="hazard.hazard_level" />
            </el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <HazardStatusTag :status="hazard.status" :is-overdue="hazard.is_overdue" />
            </el-descriptions-item>
            <el-descriptions-item label="隐患位置" :span="2">{{ hazard.location }}</el-descriptions-item>
            <el-descriptions-item label="上报人">{{ hazard.reporter }}</el-descriptions-item>
            <el-descriptions-item label="上报时间">{{ hazard.created_at }}</el-descriptions-item>
            <el-descriptions-item label="责任人">
              <span :class="{ muted: !hazard.owner }">{{ hazard.owner || '待分派' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="整改期限">
              <span :style="hazard.is_overdue ? 'color:#d93025;font-weight:600' : ''">
                {{ hazard.due_date }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="隐患描述" :span="2">{{ hazard.description }}</el-descriptions-item>
            <el-descriptions-item v-if="hazard.image_url" label="现场图片" :span="2">
              <el-image
                :src="hazard.image_url"
                :preview-src-list="[hazard.image_url]"
                fit="cover"
                style="width: 160px; height: 100px; border-radius: 6px"
              >
                <template #error>
                  <span class="muted">图片不可访问（演示链接）</span>
                </template>
              </el-image>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="card">
          <div class="card-title">
            <span>整改与验收</span>
            <span class="muted">最近更新 {{ hazard.updated_at }}</span>
          </div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="整改要求">
              <span :class="{ muted: !rectificationRequirement }">
                {{ rectificationRequirement || '待审核分派后确定' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="整改措施">
              <span :class="{ muted: !hazard.rectification_measure }">
                {{ hazard.rectification_measure || '暂未提交' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="整改完成情况">
              <span :class="{ muted: !hazard.rectification_result }">
                {{ hazard.rectification_result || '暂未提交' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="验收意见">
              <span :class="{ muted: !hazard.acceptance_comment }">
                {{ hazard.acceptance_comment || '暂未验收' }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <div class="card timeline-card">
        <div class="card-title">
          <span>状态流转记录</span>
          <span class="muted">共 {{ hazard.flow_logs.length }} 条</span>
        </div>
        <el-timeline v-if="hazard.flow_logs.length">
          <el-timeline-item
            v-for="log in hazard.flow_logs"
            :key="log.id"
            :timestamp="log.created_at"
            placement="top"
            :type="log.to_status === '已关闭' ? 'success' : 'primary'"
          >
            <div class="flow-head">
              <strong>{{ log.action }}</strong>
              <span class="muted">
                {{ log.from_status ? `${log.from_status} → ${log.to_status}` : log.to_status }}
                · {{ log.operator }}
              </span>
            </div>
            <div v-if="log.comment" class="flow-comment">{{ log.comment }}</div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无流转记录" :image-size="80" />
      </div>
    </template>

    <el-dialog v-model="assignVisible" title="审核并分派" width="520px" destroy-on-close>
      <el-form ref="assignFormRef" :model="assignForm" :rules="assignRules" label-width="96px">
        <el-form-item label="责任人" prop="owner">
          <el-select
            v-model="assignForm.owner"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入责任人"
            style="width: 100%"
          >
            <el-option v-for="item in ownerOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="整改期限" prop="due_date">
          <el-date-picker
            v-model="assignForm.due_date"
            type="date"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledPastDate"
            placeholder="选择整改期限"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="审核人" prop="auditor">
          <el-input v-model="assignForm.auditor" maxlength="30" />
        </el-form-item>
        <el-form-item label="审核意见">
          <el-input
            v-model="assignForm.comment"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="选填，例如：立即整改并留存整改照片"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="assignSubmitting" @click="submitAssign">确认分派</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rectifyVisible" title="提交整改" width="560px" destroy-on-close>
      <el-form ref="rectifyFormRef" :model="rectifyForm" :rules="rectifyRules" label-width="110px">
        <el-form-item label="整改措施" prop="rectification_measure">
          <el-input
            v-model="rectifyForm.rectification_measure"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="例如：清理杂物并设置禁放标识"
          />
        </el-form-item>
        <el-form-item label="整改完成情况" prop="rectification_result">
          <el-input
            v-model="rectifyForm.rectification_result"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="说明整改完成情况与验证结果"
          />
        </el-form-item>
        <el-form-item label="提交人" prop="operator">
          <el-input v-model="rectifyForm.operator" maxlength="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rectifyVisible = false">取消</el-button>
        <el-button type="primary" :loading="rectifySubmitting" @click="submitRectify">提交整改</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="acceptVisible" title="验收处理" width="540px" destroy-on-close>
      <el-form ref="acceptFormRef" :model="acceptForm" :rules="acceptRules" label-width="96px">
        <el-form-item label="验收结论">
          <el-radio-group v-model="acceptForm.decision">
            <el-radio-button value="pass">验收通过并关闭</el-radio-button>
            <el-radio-button value="reject">退回继续整改</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="验收意见" prop="acceptance_comment">
          <el-input
            v-model="acceptForm.acceptance_comment"
            type="textarea"
            :rows="3"
            maxlength="300"
            show-word-limit
            placeholder="填写现场核查情况与结论"
          />
        </el-form-item>
        <el-form-item label="验收人" prop="operator">
          <el-input v-model="acceptForm.operator" maxlength="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="acceptVisible = false">取消</el-button>
        <el-button type="primary" :loading="acceptSubmitting" @click="submitAccept">提交验收</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.overdue-alert,
.hint-alert {
  margin-bottom: 12px;
}

.hint-alert {
  margin-bottom: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  margin-bottom: 14px;
}

.timeline-card {
  margin-top: 16px;
}

.flow-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 1100px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
