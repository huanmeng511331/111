import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/hazards' },
  {
    path: '/hazards',
    name: 'hazard-list',
    component: () => import('../views/HazardListView.vue'),
    meta: { title: '隐患台账' }
  },
  {
    path: '/hazards/new',
    name: 'hazard-create',
    component: () => import('../views/HazardCreateView.vue'),
    meta: { title: '上报隐患' }
  },
  {
    path: '/hazards/:id',
    name: 'hazard-detail',
    component: () => import('../views/HazardDetailView.vue'),
    meta: { title: '隐患详情' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: '统计看板' }
  },
  { path: '/:pathMatch(.*)*', redirect: '/hazards' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · HSE 隐患闭环管理` : 'HSE 隐患闭环管理'
})

export default router
