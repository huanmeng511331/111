<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: { type: String, default: '' },
})

const levelType = computed(
  () =>
    ({
      一般: 'info',
      较大: 'warning',
      重大: 'danger',
    })[props.level] || 'info',
)
</script>

<template>
  <el-tag :type="levelType" effect="plain">{{ level || '未分级' }}</el-tag>
</template>
