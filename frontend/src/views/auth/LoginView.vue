<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48" color="#409EFF"><Monitor /></el-icon>
        </div>
        <h2>华为云流量监控系统</h2>
        <p class="subtitle">Huawei Cloud Traffic Monitor</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <el-alert
          title="默认账户：admin / admin123"
          type="info"
          :closable="false"
          show-icon
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import { login } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref(null)

// 加载状态
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  // 验证表单
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true

  try {
    // 调用登录 API
    const response = await login({
      username: loginForm.username,
      password: loginForm.password
    })

    // 保存 token 和用户信息
    userStore.setToken(response.access_token)
    userStore.setUserInfo({
      username: response.username,
      tokenType: response.token_type
    })

    ElMessage.success('登录成功')

    // 跳转到原页面或首页
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
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
  width: 420px;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header .logo {
  margin-bottom: 20px;
}

.login-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.login-header .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.login-form {
  margin-top: 30px;
}

.login-form .el-form-item {
  margin-bottom: 24px;
}

.login-footer {
  margin-top: 20px;
}

.login-footer :deep(.el-alert) {
  border-radius: 6px;
}
</style>
