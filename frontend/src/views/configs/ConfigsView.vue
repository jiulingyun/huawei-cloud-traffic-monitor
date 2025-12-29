<template>
  <div class="configs-view">
    <!-- 全局配置卡片 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>全局配置</span>
          <el-button
            v-if="!editingGlobal"
            type="primary"
            size="small"
            :icon="Edit"
            @click="handleEditGlobal"
          >
            编辑
          </el-button>
          <div v-else>
            <el-button size="small" @click="cancelEditGlobal">取消</el-button>
            <el-button type="primary" size="small" :loading="saving" @click="handleSaveGlobal">
              保存
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        v-loading="loading"
        ref="globalFormRef"
        :model="globalConfig"
        :rules="formRules"
        :disabled="!editingGlobal"
        label-width="160px"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="监控检查间隔" prop="check_interval">
              <el-input-number
                v-model="globalConfig.check_interval"
                :min="1"
                :max="1440"
                :step="1"
                style="width: 100%"
              />
              <span class="unit-text">分钟</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="流量阈值" prop="traffic_threshold">
              <el-input-number
                v-model="globalConfig.traffic_threshold"
                :min="0.1"
                :step="0.5"
                :precision="2"
                style="width: 100%"
              />
              <span class="unit-text">GB</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="自动关机延迟" prop="shutdown_delay">
              <el-input-number
                v-model="globalConfig.shutdown_delay"
                :min="0"
                :max="60"
                :step="1"
                style="width: 100%"
              />
              <span class="unit-text">分钟</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="失败重试次数" prop="retry_times">
              <el-input-number
                v-model="globalConfig.retry_times"
                :min="1"
                :max="10"
                :step="1"
                style="width: 100%"
              />
              <span class="unit-text">次</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="飞书 Webhook URL" prop="feishu_webhook_url">
          <el-input
            v-model="globalConfig.feishu_webhook_url"
            placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
            clearable
          />
        </el-form-item>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="启用自动关机">
              <el-switch v-model="globalConfig.auto_shutdown_enabled" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用通知">
              <el-switch v-model="globalConfig.notification_enabled" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider />

        <el-descriptions :column="2" border>
          <el-descriptions-item label="创建时间">
            {{ formatDate(globalConfig.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDate(globalConfig.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-form>
    </el-card>

    <!-- 账户配置列表 -->
    <el-card class="config-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>账户专属配置</span>
          <el-button
            type="primary"
            size="small"
            :icon="Plus"
            @click="handleAddAccount"
          >
            新增账户配置
          </el-button>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          账户专属配置优先级高于全局配置。如果账户未配置专属配置，将使用全局配置。
        </template>
      </el-alert>

      <el-table
        v-loading="loadingList"
        :data="accountConfigs"
        stripe
      >
        <el-table-column label="账户 ID" prop="account_id" width="100" />
        <el-table-column label="检查间隔" width="120">
          <template #default="scope">
            {{ scope.row.check_interval }} 分钟
          </template>
        </el-table-column>
        <el-table-column label="流量阈值" width="120">
          <template #default="scope">
            {{ scope.row.traffic_threshold }} GB
          </template>
        </el-table-column>
        <el-table-column label="自动关机" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.auto_shutdown_enabled ? 'success' : 'info'" size="small">
              {{ scope.row.auto_shutdown_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通知" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.notification_enabled ? 'success' : 'info'" size="small">
              {{ scope.row.notification_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEditAccount(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDeleteAccount(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 账户配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="accountFormRef"
        :model="accountForm"
        :rules="accountFormRules"
        label-width="160px"
      >
        <el-form-item label="关联账户" prop="account_id">
          <el-select
            v-model="accountForm.account_id"
            placeholder="请选择账户"
            style="width: 100%"
            :disabled="isEditMode"
          >
            <el-option
              v-for="account in availableAccounts"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            />
          </el-select>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="监控检查间隔" prop="check_interval">
              <el-input-number
                v-model="accountForm.check_interval"
                :min="1"
                :max="1440"
                :step="1"
                style="width: 100%"
              />
              <span class="unit-text">分钟</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="流量阈值" prop="traffic_threshold">
              <el-input-number
                v-model="accountForm.traffic_threshold"
                :min="0.1"
                :step="0.5"
                :precision="2"
                style="width: 100%"
              />
              <span class="unit-text">GB</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="自动关机延迟" prop="shutdown_delay">
              <el-input-number
                v-model="accountForm.shutdown_delay"
                :min="0"
                :max="60"
                :step="1"
                style="width: 100%"
              />
              <span class="unit-text">分钟</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="失败重试次数" prop="retry_times">
              <el-input-number
                v-model="accountForm.retry_times"
                :min="1"
                :max="10"
                :step="1"
                style="width: 100%"
              />
              <span class="unit-text">次</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="飞书 Webhook URL" prop="feishu_webhook_url">
          <el-input
            v-model="accountForm.feishu_webhook_url"
            placeholder="留空则使用全局配置"
            clearable
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="启用自动关机">
              <el-switch v-model="accountForm.auto_shutdown_enabled" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用通知">
              <el-switch v-model="accountForm.notification_enabled" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAccountSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import {
  getGlobalConfig,
  updateConfig,
  getConfigs,
  createConfig,
  deleteConfig
} from '@/api/configs'
import { getAccounts } from '@/api/accounts'

// 响应式数据
const loading = ref(false)
const loadingList = ref(false)
const saving = ref(false)
const submitting = ref(false)
const editingGlobal = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新增账户配置')
const isEditMode = ref(false)

const globalFormRef = ref(null)
const accountFormRef = ref(null)

// 全局配置
const globalConfig = reactive({
  id: null,
  check_interval: 5,
  traffic_threshold: 10.0,
  auto_shutdown_enabled: true,
  feishu_webhook_url: '',
  notification_enabled: true,
  shutdown_delay: 0,
  retry_times: 3,
  created_at: null,
  updated_at: null
})

const globalConfigBackup = ref(null)

// 账户配置列表
const accountConfigs = ref([])
const accounts = ref([])

// 账户配置表单
const accountForm = reactive({
  id: null,
  account_id: null,
  check_interval: 5,
  traffic_threshold: 10.0,
  auto_shutdown_enabled: true,
  feishu_webhook_url: '',
  notification_enabled: true,
  shutdown_delay: 0,
  retry_times: 3
})

// 可选择的账户（排除已配置的，且只显示启用的账户）
const availableAccounts = computed(() => {
  const configuredIds = accountConfigs.value.map(c => c.account_id)
  return accounts.value.filter(a => {
    // 编辑模式下，当前账户也要显示
    const isCurrentAccount = a.id === accountForm.account_id
    // 新增模式下，排除已配置的账户，且只显示启用的账户
    const isAvailable = !configuredIds.includes(a.id) && a.is_enabled
    return isCurrentAccount || isAvailable
  })
})

// 表单验证规则
const formRules = {
  check_interval: [
    { required: true, message: '请输入检查间隔', trigger: 'blur' },
    { type: 'number', min: 1, max: 1440, message: '范围 1-1440 分钟', trigger: 'blur' }
  ],
  traffic_threshold: [
    { required: true, message: '请输入流量阈值', trigger: 'blur' },
    { type: 'number', min: 0.1, message: '最小 0.1 GB', trigger: 'blur' }
  ],
  shutdown_delay: [
    { type: 'number', min: 0, max: 60, message: '范围 0-60 分钟', trigger: 'blur' }
  ],
  retry_times: [
    { type: 'number', min: 1, max: 10, message: '范围 1-10 次', trigger: 'blur' }
  ],
  feishu_webhook_url: [
    { type: 'url', message: '请输入有效的 URL', trigger: 'blur' }
  ]
}

const accountFormRules = {
  account_id: [
    { required: true, message: '请选择账户', trigger: 'change' }
  ],
  ...formRules
}

// 加载全局配置
const loadGlobalConfig = async () => {
  loading.value = true
  try {
    const data = await getGlobalConfig()
    Object.assign(globalConfig, data)
  } catch (error) {
    console.error('加载全局配置失败:', error)
    ElMessage.error('加载全局配置失败')
  } finally {
    loading.value = false
  }
}

// 编辑全局配置
const handleEditGlobal = () => {
  globalConfigBackup.value = { ...globalConfig }
  editingGlobal.value = true
}

// 取消编辑全局配置
const cancelEditGlobal = () => {
  Object.assign(globalConfig, globalConfigBackup.value)
  editingGlobal.value = false
}

// 保存全局配置
const handleSaveGlobal = async () => {
  if (!globalFormRef.value) return

  const valid = await globalFormRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const data = {
      check_interval: globalConfig.check_interval,
      traffic_threshold: globalConfig.traffic_threshold,
      auto_shutdown_enabled: globalConfig.auto_shutdown_enabled,
      feishu_webhook_url: globalConfig.feishu_webhook_url || null,
      notification_enabled: globalConfig.notification_enabled,
      shutdown_delay: globalConfig.shutdown_delay,
      retry_times: globalConfig.retry_times
    }

    await updateConfig(globalConfig.id, data)
    ElMessage.success('保存成功')
    editingGlobal.value = false
    await loadGlobalConfig()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 加载账户配置列表
const loadAccountConfigs = async () => {
  loadingList.value = true
  try {
    const data = await getConfigs({ limit: 1000 })
    // 过滤出账户配置（account_id 不为 null）
    accountConfigs.value = data.filter(c => c.account_id !== null)
  } catch (error) {
    console.error('加载账户配置失败:', error)
    ElMessage.error('加载账户配置失败')
  } finally {
    loadingList.value = false
  }
}

// 加载账户列表
const loadAccounts = async () => {
  try {
    accounts.value = await getAccounts({ limit: 1000 })
  } catch (error) {
    console.error('加载账户列表失败:', error)
  }
}

// 新增账户配置
const handleAddAccount = () => {
  isEditMode.value = false
  dialogTitle.value = '新增账户配置'
  resetAccountForm()
  dialogVisible.value = true
}

// 编辑账户配置
const handleEditAccount = (row) => {
  isEditMode.value = true
  dialogTitle.value = '编辑账户配置'
  Object.assign(accountForm, row)
  dialogVisible.value = true
}

// 删除账户配置
const handleDeleteAccount = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除账户 ${row.account_id} 的专属配置？删除后将使用全局配置。`,
      '警告',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteConfig(row.id)
    ElMessage.success('删除成功')
    await loadAccountConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 提交账户配置
const handleAccountSubmit = async () => {
  if (!accountFormRef.value) return

  const valid = await accountFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = {
      account_id: accountForm.account_id,
      check_interval: accountForm.check_interval,
      traffic_threshold: accountForm.traffic_threshold,
      auto_shutdown_enabled: accountForm.auto_shutdown_enabled,
      feishu_webhook_url: accountForm.feishu_webhook_url || null,
      notification_enabled: accountForm.notification_enabled,
      shutdown_delay: accountForm.shutdown_delay,
      retry_times: accountForm.retry_times
    }

    if (isEditMode.value) {
      await updateConfig(accountForm.id, data)
      ElMessage.success('更新成功')
    } else {
      await createConfig(data)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    await loadAccountConfigs()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

// 重置账户表单
const resetAccountForm = () => {
  accountForm.id = null
  accountForm.account_id = null
  accountForm.check_interval = 5
  accountForm.traffic_threshold = 10.0
  accountForm.auto_shutdown_enabled = true
  accountForm.feishu_webhook_url = ''
  accountForm.notification_enabled = true
  accountForm.shutdown_delay = 0
  accountForm.retry_times = 3
  if (accountFormRef.value) {
    accountFormRef.value.clearValidate()
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 组件加载时
onMounted(() => {
  loadGlobalConfig()
  loadAccountConfigs()
  loadAccounts()
})
</script>

<style scoped>
.configs-view {
  width: 100%;
}

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.unit-text {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}
</style>
