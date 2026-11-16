<script setup>
import { computed } from 'vue'
import { LEVEL_META } from '../constants/hazard'

const props = defineProps({
  level: { type: String, required: true }
})

const tagType = computed(() => LEVEL_META[props.level]?.tag || 'info')
</script>

<template>
  <el-tag :type="tagType" effect="plain" size="small">{{ level }}</el-tag>
</template>
