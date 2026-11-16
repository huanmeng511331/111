<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  color: { type: String, default: '#1f6feb' }
})

const maxValue = computed(() => Math.max(...props.data.map((item) => item.value), 1))

const widthOf = (value) => `${Math.round((value / maxValue.value) * 100)}%`
</script>

<template>
  <div v-if="data.length" class="bar-list">
    <div v-for="item in data" :key="item.label" class="bar-row">
      <span class="bar-label">{{ item.label }}</span>
      <div class="bar-track">
        <div
          class="bar-fill"
          :style="{ width: widthOf(item.value), background: item.color || color }"
        />
      </div>
      <span class="bar-value">{{ item.value }}</span>
    </div>
  </div>
  <el-empty v-else class="empty-block" description="暂无统计数据" :image-size="60" />
</template>
