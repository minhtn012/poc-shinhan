import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/login-view.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/components/common/app-layout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/templates' },
        {
          path: 'templates',
          name: 'template-list',
          component: () => import('@/views/template-list-view.vue')
        },
        {
          path: 'templates/create',
          name: 'template-create',
          component: () => import('@/views/template-create-view.vue')
        },
        {
          path: 'templates/:id',
          name: 'template-detail',
          component: () => import('@/views/template-detail-view.vue')
        },
        {
          path: 'templates/:id/versions/:vid',
          name: 'version-view',
          component: () => import('@/views/version-view.vue')
        },
        {
          path: 'ocr',
          name: 'ocr-list',
          component: () => import('@/views/ocr-list-view.vue')
        },
        {
          path: 'ocr/new',
          name: 'ocr-upload',
          component: () => import('@/views/ocr-upload-view.vue')
        },
        {
          path: 'ocr/:id',
          name: 'ocr-review',
          component: () => import('@/views/ocr-review-view.vue')
        }
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/templates' }
  ]
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth !== false)
  if (requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'template-list' }
  }
})

export default router
