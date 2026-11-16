<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from '../utils/message'
import { assignHazard, fetchHazard, submitAcceptance, submitRectification } from '../api/hazards'
import LevelTag from '../components/LevelTag.vue'
import StatusTag from '../components/StatusTag.vue'
import { formatDate, formatDateTime } from '../utils/format'

const route = useRoute()
const router = useRouter()
const hazardId = Number(route.params.id)

const loading = ref(true)
const errorText = ref('')
const hazard = ref(null)
const actionLoading = ref(false)

const assignFormRef = ref()
const rectifyFormRef = ref()
const acceptanceFormRef = ref()

const assignForm = reactive({ owner: '', due_date: '', operator: '安全管理员', comment: '' })
const rectifyForm = reactive({
  rectification_measure: '',
  rectification_result: '',
  operator: '责任人'
})
const acceptanceForm = reactive({ acceptance_comment: '', operator: '安全管理员' })

const assignRules = {
  owner: [
    { required: true, message: '请填写责任人', trigger: 'blur' },
    { min: 2, max: 30, message: '责任人姓名长度需在 2-30 个字符', trigger: 'blur' }
  ],
  due_date: [{ required: true, message: '请选择整改期限', trigger: 'change' }]
}

const rectifyRules = {
  rectification_measure: [
    { required: true, message: '请填写整改措施', trigger: 'blur' },
    { min: 5, max: 500, message: '整改措施长度需在 5-500 个字符', trigger: 'blur' }
  ],
  rectification_result: [
    { required: true, message: '请填写整改完成情况', trigger: 'blur' },
    { min: 5, max: 500, message: '整改完成情况需在 5-500 个字符', trigger: 'blur' }
  ]
}

const acceptanceRules = {
  acceptance_comment: [
    { required: true, message: '请填写验收意见', trigger: 'blur' },
    { min: 2, max: 300, message: '验收意见长度需在 2-300 个字符', trigger: 'blur' }
  ]
}

const statusStep = computed(() => {
  const map = { 待审核: 1, 整改中: 2, 待验收: 3, 已关闭: 4 }
  return map[hazard.value?.status] || 1
})

const disabledPastDate = (day) => day.getTime() < Date.now() - 24 * 60 * 60 * 1000

async function loadHazard() {
  loading.value = true
  errorText.value = ''
  try {
    hazard.value = await fetchHazard(hazardId)
    assignForm.owner = hazard.value.owner || ''
    assignForm.due_date = hazard.value.due_date
    assignForm.comment = ''
    rectifyForm.operator = hazard.value.owner || '责任人'
    rectifyForm.rectification_measure = hazard.value.rectification_measure || ''
    rectifyForm.rectification_result = ''
    acceptanceForm.acceptance_comment = ''
  } catch (error) {
    errorText.value = error.message
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function handleAssign() {
  const valid = await assignFormRef.value?.validate().catch(() => false)
  if (!valid) return
  actionLoading.value = true
  try {
    await assignHazard(hazardId, { ...assignForm })
    ElMessage.success('审核分派成功，隐患进入整改中')
    await loadHazard()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    actionLoading.value = false
  }
}

async function handleRectification() {
  const valid = await rectifyFormRef.value?.validate().catch(() => false)
  if (!valid) return
  actionLoading.value = true
  try {
    await submitRectification(hazardId, { ...rectifyForm })
    ElMessage.success('整改已提交，等待验收')
    await loadHazard()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    actionLoading.value = false
  }
}

async function handleAcceptance(approved) {
  const valid = await acceptanceFormRef.value?.validate().catch(() => false)
  if (!valid) return
  actionLoading.value = true
  try {
    await submitAcceptance(hazardId, {
      approved,
      acceptance_comment: acceptanceForm.acceptance_comment,
      operator: acceptanceForm.operator
    })
    ElMessage.success(approved ? '验收通过，隐患已关闭' : '已退回整改，隐患回到整改中')
    await loadHazard()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    actionLoading.value = false
  }
}

onMounted(loadHazard)
</script>

<template>
  <section v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">隐患详情</h2>
        <p class="page-desc">查看上报信息与状态流转记录，并按当前状态执行审核、整改、验收操作。</p>
      </div>
      <div class="page-actions">
        <el-button @click="loadHazard">刷新</el-button>
        <el-button @click="router.push('/hazards')">返回台账</el-button>
      </div>
    </div>

    <el-alert
      v-if="errorText"
      type="error"
      show-icon
      :closable="false"
      :title="errorText"
      description="请确认后端服务已启动，或返回台账重新选择隐患。"
      style="margin-bottom: 16px"
    />

    <template v-if="hazard">
      <div class="page-card">
        <div class="detail-meta">
          <el-tag type="info" effect="plain">{{ hazard.hazard_no }}</el-tag>
          <LevelTag :level="hazard.hazard_level" />
          <StatusTag :status="hazard.status" />
          <el-tag v-if="hazard.is_overdue" type="danger" effect="dark">已超期</el-tag>
        </div>
        <el-steps :active="statusStep" finish-status="success" process-status="process" align-center>
          <el-step title="上报" description="现场上报隐患" />
          <el-step title="审核分派" description="安全管理人员分派" />
          <el-step title="整改" description="责任人落实整改" />
          <el-step title="验收关闭" description="验收通过后关闭" />
        </el-steps>
      </div>

      <div class="detail-grid">
        <div>
          <div class="page-card">
            <div class="chart-card-title">上报信息</div>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="隐患编号">{{ hazard.hazard_no }}</el-descriptions-item>
              <el-descriptions-item label="隐患类型">{{ hazard.hazard_type }}</el-descriptions-item>
              <el-descriptions-item label="隐患等级">{{ hazard.hazard_level }}</el-descriptions-item>
              <el-descriptions-item label="当前状态">{{ hazard.status }}</el-descriptions-item>
              <el-descriptions-item label="隐患位置" :span="2">{{ hazard.location }}</el-descriptions-item>
              <el-descriptions-item label="隐患描述" :span="2">
                <span style="white-space: pre-wrap">{{ hazard.description }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="上报人">{{ hazard.reporter }}</el-descriptions-item>
              <el-descriptions-item label="责任人">{{ hazard.owner || '待分派' }}</el-descriptions-item>
              <el-descriptions-item label="整改期限">
                {{ formatDate(hazard.due_date) }}
                <el-tag v-if="hazard.is_overdue" type="danger" size="small" effect="dark" style="margin-left: 6px">
                  超期
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="上报时间">{{ formatDateTime(hazard.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="最近更新">{{ formatDateTime(hazard.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="附件图片">
                <el-link v-if="hazard.attachment_url" type="primary" :href="hazard.attachment_url" target="_blank">
                  查看附件
                </el-link>
                <span v-else class="muted">无</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="page-card">
            <div class="chart-card-title">整改与验收</div>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="整改措施">
                {{ hazard.rectification_measure || '尚未提交' }}
              </el-descriptions-item>
              <el-descriptions-item label="整改完成情况">
                {{ hazard.rectification_result || '尚未提交' }}
              </el-descriptions-item>
              <el-descriptions-item label="验收意见">
                {{ hazard.acceptance_comment || '尚未验收' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="page-card">
            <div class="chart-card-title">状态流转记录</div>
            <el-timeline v-if="hazard.logs.length">
              <el-timeline-item
                v-for="log in hazard.logs"
                :key="log.id"
                :timestamp="formatDateTime(log.created_at)"
                placement="top"
                :type="log.to_status === '已关闭' ? 'success' : 'primary'"
              >
                <strong>{{ log.action_label }}</strong>
                <span class="muted">
                  · {{ log.operator || '系统' }} · {{ log.from_status ? `${log.from_status} → ` : '' }}{{ log.to_status }}
                </span>
                <div v-if="log.comment" class="log-comment">{{ log.comment }}</div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无流转记录" :image-size="60" />
          </div>
        </div>

        <div>
          <div class="page-card">
            <div class="chart-card-title">待办操作</div>

            <div v-if="hazard.status === '待审核'" class="action-panel">
              <h4>审核并分派责任人</h4>
              <el-form ref="assignFormRef" :model="assignForm" :rules="assignRules" label-position="top">
                <el-form-item label="责任人" prop="owner">
                  <el-input v-model="assignForm.owner" placeholder="例如：李强" />
                </el-form-item>
                <el-form-item label="整改期限" prop="due_date">
                  <el-date-picker
                    v-model="assignForm.due_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    :disabled-date="disabledPastDate"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="分派备注">
                  <el-input v-model="assignForm.comment" type="textarea" :rows="2" maxlength="200" placeholder="选填" />
                </el-form-item>
                <el-button type="primary" :loading="actionLoading" @click="handleAssign">
                  审核并分派
                </el-button>
              </el-form>
            </div>

            <div v-else-if="hazard.status === '整改中'" class="action-panel">
              <h4>提交整改措施与结果</h4>
              <el-form ref="rectifyFormRef" :model="rectifyForm" :rules="rectifyRules" label-position="top">
                <el-form-item label="整改措施" prop="rectification_measure">
                  <el-input
                    v-model="rectifyForm.rectification_measure"
                    type="textarea"
                    :rows="3"
                    maxlength="500"
                    show-word-limit
                  />
                </el-form-item>
                <el-form-item label="整改完成情况" prop="rectification_result">
                  <el-input
                    v-model="rectifyForm.rectification_result"
                    type="textarea"
                    :rows="3"
                    maxlength="500"
                    show-word-limit
                    placeholder="例如：已清理并设置禁放标识"
                  />
                </el-form-item>
                <el-form-item label="提交人">
                  <el-input v-model="rectifyForm.operator" maxlength="30" />
                </el-form-item>
                <el-button type="primary" :loading="actionLoading" @click="handleRectification">
                  提交整改
                </el-button>
              </el-form>
            </div>

            <div v-else-if="hazard.status === '待验收'" class="action-panel">
              <h4>验收确认</h4>
              <el-form
                ref="acceptanceFormRef"
                :model="acceptanceForm"
                :rules="acceptanceRules"
                label-position="top"
              >
                <el-form-item label="验收意见" prop="acceptance_comment">
                  <el-input
                    v-model="acceptanceForm.acceptance_comment"
                    type="textarea"
                    :rows="3"
                    maxlength="300"
                    show-word-limit
                    placeholder="例如：现场复核已整改到位，同意关闭"
                  />
                </el-form-item>
                <div class="form-actions">
                  <el-button type="success" :loading="actionLoading" @click="handleAcceptance(true)">
                    验收通过并关闭
                  </el-button>
                  <el-button type="warning" plain :loading="actionLoading" @click="handleAcceptance(false)">
                    退回整改
                  </el-button>
                </div>
              </el-form>
            </div>

            <div v-else class="action-panel">
              <h4>隐患已关闭</h4>
              <p class="muted">该隐患已完成验收关闭，如需补充信息请上报新的隐患记录。</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>
