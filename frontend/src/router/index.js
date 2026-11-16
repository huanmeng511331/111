import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '统计看板' },
  },
  {
    path: '/hazards',
    name: 'hazard-list',
    component: () => import('@/views/HazardListView.vue'),
    meta: { title: '隐患台账' },
  },
  {
    path: '/hazards/new',
    name: 'hazard-create',
    component: () => import('@/views/HazardReportView.vue'),
    meta: { title: '隐患上报' },
  },
  {
    path: '/hazards/:id',
    name: 'hazard-detail',
    component: () => import('@/views/HazardDetailView.vue'),
    meta: { title: '隐患详情' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - HSE 隐患闭环演示` : 'HSE 隐患闭环演示'
})

export default router
