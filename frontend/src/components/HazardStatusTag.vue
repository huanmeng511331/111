<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: '' },
  isOverdue: { type: Boolean, default: false },
})

const statusType = computed(
  () =>
    ({
      待审核: 'warning',
      整改中: 'primary',
      待验收: 'info',
      已关闭: 'success',
    })[props.status] || 'info',
)
</script>

<template>
  <span class="status-tags">
    <el-tag :type="statusType" effect="light">{{ status || '未知' }}</el-tag>
    <el-tag v-if="isOverdue" type="danger" effect="dark">已超期</el-tag>
  </span>
</template>

<style scoped>
.status-tags {
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
</style>
