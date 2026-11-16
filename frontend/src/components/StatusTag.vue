<script setup>
import { computed } from 'vue'
import { STATUS_META } from '../constants/hazard'

const props = defineProps({
  status: { type: String, required: true }
})

const tagType = computed(() => STATUS_META[props.status]?.tag || 'info')
</script>

<template>
  <el-tag :type="tagType" effect="light" round>{{ status }}</el-tag>
</template>
