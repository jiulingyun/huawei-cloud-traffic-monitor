/**
 * 应用全局状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 侧边栏状态
  const sidebarCollapsed = ref(false)
  
  // 加载状态
  const loading = ref(false)
  
  // 主题
  const theme = ref(localStorage.getItem('theme') || 'light')

  // 方法
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setLoading(value) {
    loading.value = value
  }

  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
  }

  return {
    sidebarCollapsed,
    loading,
    theme,
    toggleSidebar,
    setLoading,
    setTheme
  }
})
