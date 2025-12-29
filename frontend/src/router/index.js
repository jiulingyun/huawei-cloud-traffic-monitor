import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue')
        },
        {
          path: 'accounts',
          name: 'Accounts',
          component: () => import('@/views/accounts/AccountsView.vue')
        },
        {
          path: 'configs',
          name: 'Configs',
          component: () => import('@/views/configs/ConfigsView.vue')
        },
        {
          path: 'servers',
          name: 'Servers',
          component: () => import('@/views/servers/ServersView.vue')
        },
        {
          path: 'logs',
          name: 'Logs',
          component: () => import('@/views/logs/LogsView.vue')
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/SettingsView.vue')
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    // 需要认证但未登录，跳转到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && userStore.isLoggedIn) {
    // 已登录访问登录页，跳转到首页
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
