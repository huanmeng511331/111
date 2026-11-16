<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createHazard, fetchDictionaries } from '@/api/hazard'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const dictionaries = reactive({ hazard_types: [], hazard_levels: [] })

const form = reactive({
  hazard_type: '',
  hazard_level: '一般',
  location: '',
  description: '',
  reporter: '',
  due_date: '',
  image_url: '',
})

const rules = {
  hazard_type: [{ required: true, message: '请选择隐患类型', trigger: 'change' }],
  hazard_level: [{ required: true, message: '请选择隐患等级', trigger: 'change' }],
  location: [
    { required: true, message: '请填写隐患位置', trigger: 'blur' },
    { min: 2, max: 100, message: '位置长度需在 2-100 个字符之间', trigger: 'blur' },
  ],
  description: [
    { required: true, message: '请填写隐患描述', trigger: 'blur' },
    { min: 5, max: 500, message: '描述长度需在 5-500 个字符之间', trigger: 'blur' },
  ],
  reporter: [
    { required: true, message: '请填写上报人', trigger: 'blur' },
    { max: 30, message: '上报人不超过 30 个字符', trigger: 'blur' },
  ],
  due_date: [{ required: true, message: '请选择整改期限', trigger: 'change' }],
  image_url: [
    {
      type: 'url',
      message: '请输入合法的图片 URL（含 http/https）',
      trigger: 'blur',
    },
  ],
}

function disabledPastDate(date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date.getTime() < today.getTime()
}

async function loadDictionaries() {
  try {
    const data = await fetchDictionaries()
    dictionaries.hazard_types = data.hazard_types
    dictionaries.hazard_levels = data.hazard_levels
  } catch (error) {
    ElMessage.warning(`字典加载失败：${error.message}`)
  }
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请先完善表单必填项')
    return
  }
  submitting.value = true
  try {
    const payload = { ...form, image_url: form.image_url || null }
    const created = await createHazard(payload)
    ElMessage.success(`隐患 ${created.hazard_no} 上报成功，等待安全管理人员审核分派`)
    router.push(`/hazards/${created.id}`)
  } catch (error) {
    ElMessage.error(`上报失败：${error.message}`)
  } finally {
    submitting.value = false
  }
}

function handleResetForm() {
  formRef.value?.resetFields()
}

onMounted(loadDictionaries)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">上报隐患</h2>
        <p class="page-subtitle">提交后隐患进入「待审核」，由安全管理人员审核并分派整改责任人。</p>
      </div>
      <el-button :icon="'Back'" @click="router.push('/hazards')">返回台账</el-button>
    </div>

    <div class="card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
        label-position="right"
        class="report-form"
        @submit.prevent
      >
        <el-row :gutter="24">
          <el-col :xs="24" :md="12">
            <el-form-item label="隐患类型" prop="hazard_type">
              <el-select v-model="form.hazard_type" placeholder="请选择隐患类型" style="width: 100%">
                <el-option v-for="item in dictionaries.hazard_types" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="隐患等级" prop="hazard_level">
              <el-radio-group v-model="form.hazard_level">
                <el-radio-button v-for="item in dictionaries.hazard_levels" :key="item" :value="item">
                  {{ item }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="隐患位置" prop="location">
              <el-input v-model="form.location" maxlength="100" show-word-limit placeholder="例如：一号厂房东侧消防通道" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="上报人" prop="reporter">
              <el-input v-model="form.reporter" maxlength="30" placeholder="填写上报人姓名" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="整改期限" prop="due_date">
              <el-date-picker
                v-model="form.due_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择整改期限"
                :disabled-date="disabledPastDate"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="图片 URL" prop="image_url">
              <el-input v-model="form.image_url" placeholder="选填，模拟现场照片链接" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="隐患描述" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="4"
                maxlength="500"
                show-word-limit
                placeholder="描述隐患现象、可能风险与发现经过（不少于 5 个字符）"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交上报</el-button>
          <el-button @click="handleResetForm">重置表单</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.report-form {
  max-width: 980px;
}
</style>
