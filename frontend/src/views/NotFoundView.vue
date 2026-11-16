<template>
  <div class="page">
    <el-result icon="warning" title="页面不存在" sub-title="请从左侧菜单进入统计看板或隐患台账">
      <template #extra>
        <el-button type="primary" @click="$router.push('/dashboard')">返回统计看板</el-button>
      </template>
    </el-result>
  </div>
</template>
