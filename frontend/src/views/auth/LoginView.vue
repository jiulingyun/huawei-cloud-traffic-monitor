<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>华为云流量监控系统</h2>
      <p>登录功能将在 M4-T2 任务中实现</p>
      <el-button type="primary" @click="handleMockLogin" style="margin-top: 20px">
        Mock 登录（开发模式）
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const handleMockLogin = () => {
  // Mock 登录
  userStore.setToken('mock_token_for_development')
  userStore.setUserInfo({ username: 'admin' })
  ElMessage.success('Mock 登录成功')
  router.push('/')
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  text-align: center;
  padding: 40px;
}

.login-card h2 {
  margin-bottom: 16px;
  color: #303133;
}

.login-card p {
  color: #909399;
}
</style>
