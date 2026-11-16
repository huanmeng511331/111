<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from '../utils/message'
import { createHazard } from '../api/hazards'
import { LEVEL_OPTIONS, TYPE_OPTIONS } from '../constants/hazard'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)

const form = reactive({
  hazard_type: '消防安全',
  hazard_level: '一般',
  location: '',
  description: '',
  reporter: '',
  due_date: '',
  attachment_url: ''
})

const validateAttachment = (rule, value, callback) => {
  if (!value) {
    callback()
    return
  }
  if (!/^https?:\/\/[^\s]+$/.test(value)) {
    callback(new Error('附件地址需以 http:// 或 https:// 开头'))
    return
  }
  callback()
}

const rules = {
  hazard_type: [{ required: true, message: '请选择隐患类型', trigger: 'change' }],
  hazard_level: [{ required: true, message: '请选择隐患等级', trigger: 'change' }],
  location: [
    { required: true, message: '请填写隐患位置', trigger: 'blur' },
    { min: 2, max: 100, message: '隐患位置长度需在 2-100 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请填写隐患描述', trigger: 'blur' },
    { min: 5, max: 500, message: '隐患描述长度需在 5-500 个字符', trigger: 'blur' }
  ],
  reporter: [
    { required: true, message: '请填写上报人', trigger: 'blur' },
    { min: 2, max: 30, message: '上报人姓名长度需在 2-30 个字符', trigger: 'blur' }
  ],
  due_date: [{ required: true, message: '请选择整改期限', trigger: 'change' }],
  attachment_url: [{ validator: validateAttachment, trigger: 'blur' }]
}

const disabledPastDate = (day) => day.getTime() < Date.now() - 24 * 60 * 60 * 1000

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...form }
    if (!payload.attachment_url) delete payload.attachment_url
    const created = await createHazard(payload)
    ElMessage.success(`隐患 ${created.hazard_no} 上报成功，等待审核分派`)
    router.push(`/hazards/${created.id}`)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  formRef.value?.resetFields()
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2 class="page-title">上报隐患</h2>
        <p class="page-desc">填写现场隐患信息，提交后进入「待审核」，由安全管理人员审核并分派责任人。</p>
      </div>
      <div class="page-actions">
        <el-button @click="router.push('/hazards')">返回台账</el-button>
      </div>
    </div>

    <div class="page-card form-card">
      <el-alert
        type="info"
        show-icon
        :closable="false"
        title="演示提示"
        description="所有信息仅用于本地演示，请勿填写真实敏感数据；带 * 的为必填项。"
        style="margin-bottom: 20px"
      />

      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="隐患类型" prop="hazard_type">
          <el-select v-model="form.hazard_type" placeholder="请选择隐患类型">
            <el-option v-for="item in TYPE_OPTIONS" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>

        <el-form-item label="隐患等级" prop="hazard_level">
          <el-radio-group v-model="form.hazard_level">
            <el-radio-button v-for="item in LEVEL_OPTIONS" :key="item" :value="item">
              {{ item }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="隐患位置" prop="location">
          <el-input v-model="form.location" maxlength="100" show-word-limit placeholder="例如：1号厂房东侧消防通道" />
        </el-form-item>

        <el-form-item label="隐患描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="描述隐患现象、可能后果和发现时间"
          />
        </el-form-item>

        <el-form-item label="上报人" prop="reporter">
          <el-input v-model="form.reporter" maxlength="30" placeholder="例如：张伟" />
        </el-form-item>

        <el-form-item label="整改期限" prop="due_date">
          <el-date-picker
            v-model="form.due_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择整改期限"
            :disabled-date="disabledPastDate"
            style="width: 220px"
          />
        </el-form-item>

        <el-form-item label="附件图片" prop="attachment_url">
          <el-input v-model="form.attachment_url" maxlength="500" placeholder="选填：图片 URL，例如 https://example.com/hazard.jpg" />
        </el-form-item>

        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="submitting" @click="handleSubmit">提交上报</el-button>
            <el-button :disabled="submitting" @click="handleReset">重置</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </section>
</template>
