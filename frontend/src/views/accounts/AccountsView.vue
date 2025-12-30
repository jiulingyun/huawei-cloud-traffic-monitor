<template>
  <div class="accounts-view">
    <el-card>
      <!-- 顶部操作栏 -->
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          添加账户
        </el-button>
        <div class="toolbar-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索账户名称"
            :prefix-icon="Search"
            clearable
            style="width: 250px; margin-right: 12px"
            @input="handleSearch"
          />
          <el-button :icon="Refresh" @click="loadAccounts">刷新</el-button>
        </div>
      </div>

      <!-- 账户表格 -->
      <el-table
        v-loading="loading"
        :data="filteredAccounts"
        style="width: 100%; margin-top: 20px"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="账户名称" width="180" />
        <el-table-column prop="region" label="区域" width="150">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.region }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_international" label="站点" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.is_international ? 'primary' : 'info'" size="small">
              {{ scope.row.is_international ? '国际站' : '中国站' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_enabled ? 'success' : 'info'" size="small">
              {{ scope.row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="360" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              type="info"
              size="small"
              :loading="testingId === scope.row.id"
              @click="handleTestConnection(scope.row)"
            >
              测试连接
            </el-button>
            <el-button
              v-if="scope.row.is_enabled"
              type="warning"
              size="small"
              @click="handleToggleStatus(scope.row)"
            >
              禁用
            </el-button>
            <el-button
              v-else
              type="success"
              size="small"
              @click="handleToggleStatus(scope.row)"
            >
              启用
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="账户名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入账户名称" clearable />
        </el-form-item>
        <el-form-item label="Access Key" prop="ak">
          <el-input
            v-model="formData.ak"
            :placeholder="isEdit ? '留空则不修改' : '请输入 Access Key'"
            clearable
            show-password
          />
        </el-form-item>
        <el-form-item label="Secret Key" prop="sk">
          <el-input
            v-model="formData.sk"
            :placeholder="isEdit ? '留空则不修改' : '请输入 Secret Key'"
            clearable
            show-password
          />
        </el-form-item>
        <el-form-item label="首选区域" prop="region">
          <el-select v-model="formData.region" placeholder="请选择首选区域" style="width: 100%">
            <el-option label="华北-北京四 (cn-north-4)" value="cn-north-4" />
            <el-option label="华东-上海一 (cn-east-3)" value="cn-east-3" />
            <el-option label="华南-广州 (cn-south-1)" value="cn-south-1" />
            <el-option label="西南-贵阳一 (cn-southwest-2)" value="cn-southwest-2" />
          </el-select>
          <div class="form-tip">系统会自动发现该账户下所有区域的服务器</div>
        </el-form-item>
        <el-form-item label="站点" prop="is_international">
          <el-radio-group v-model="formData.is_international">
            <el-radio :label="true">国际站</el-radio>
            <el-radio :label="false">中国站</el-radio>
          </el-radio-group>
          <div class="form-tip">选择账户所属站点，决定使用哪个 BSS/区域端点进行流量查询</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入账户描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Edit, Delete, Search, Refresh
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/time'
import {
  getAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  enableAccount,
  disableAccount,
  testAccountConnection
} from '@/api/accounts'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const testingId = ref(null)
const searchKeyword = ref('')
const accounts = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加账户')
const isEdit = ref(false)
const formRef = ref(null)

// 表单数据
const formData = reactive({
  id: null,
  name: '',
  ak: '',
  sk: '',
  region: 'cn-north-4',
  is_international: true,
  description: ''
})

// 表单验证规则（动态生成）
const formRules = computed(() => ({
  name: [
    { required: true, message: '请输入账户名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  ak: isEdit.value
    ? [
        { min: 10, message: 'Access Key 长度不能少于 10 个字符', trigger: 'blur' }
      ]
    : [
        { required: true, message: '请输入 Access Key', trigger: 'blur' },
        { min: 10, message: 'Access Key 长度不能少于 10 个字符', trigger: 'blur' }
      ],
  sk: isEdit.value
    ? [
        { min: 10, message: 'Secret Key 长度不能少于 10 个字符', trigger: 'blur' }
      ]
    : [
        { required: true, message: '请输入 Secret Key', trigger: 'blur' },
        { min: 10, message: 'Secret Key 长度不能少于 10 个字符', trigger: 'blur' }
      ],
  region: [
    { required: true, message: '请选择区域', trigger: 'change' }
  ]
}))

// 过滤后的账户列表
const filteredAccounts = computed(() => {
  if (!searchKeyword.value) {
    return accounts.value
  }
  return accounts.value.filter(account =>
    account.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 加载账户列表
const loadAccounts = async () => {
  loading.value = true
  try {
    const data = await getAccounts({ limit: 1000 })
    accounts.value = data
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  // 搜索由 computed 属性自动处理
}

// 添加账户
const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '添加账户'
  resetForm()
  dialogVisible.value = true
}

// 编辑账户
const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑账户'
  formData.id = row.id
  formData.name = row.name
  formData.ak = '' // 不显示原密钥
  formData.sk = '' // 不显示原密钥
  formData.region = row.region
  formData.is_international = typeof row.is_international !== 'undefined' ? row.is_international : true
  formData.description = row.description || ''
  dialogVisible.value = true
}

// 切换状态
const handleToggleStatus = async (row) => {
  const action = row.is_enabled ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确认${action}账户「${row.name}」？`,
      '提示',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (row.is_enabled) {
      await disableAccount(row.id)
    } else {
      await enableAccount(row.id)
    }

    ElMessage.success(`${action}成功`)
    await loadAccounts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(`${action}账户失败:`, error)
      ElMessage.error(`${action}失败`)
    }
  }
}

// 测试连接
const handleTestConnection = async (row) => {
  testingId.value = row.id
  try {
    const result = await testAccountConnection(row.id)
    
    if (result.success) {
      ElMessage({
        message: result.message,
        type: 'success',
        duration: 5000
      })
    } else {
      ElMessage({
        message: result.message,
        type: 'error',
        duration: 5000
      })
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    ElMessage.error('测试连接失败')
  } finally {
    testingId.value = null
  }
}

// 删除账户
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除账户「${row.name}」？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await deleteAccount(row.id)
    ElMessage.success('删除成功')
    await loadAccounts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除账户失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true

  try {
    const data = {
      name: formData.name,
      region: formData.region,
      is_international: formData.is_international,
      description: formData.description || undefined
    }

    // 编辑模式下，只在填写了密钥时才更新
    if (isEdit.value) {
      if (formData.ak) data.ak = formData.ak
      if (formData.sk) data.sk = formData.sk
      await updateAccount(formData.id, data)
      ElMessage.success('更新成功')
    } else {
      data.ak = formData.ak
      data.sk = formData.sk
      await createAccount(data)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    await loadAccounts()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.id = null
  formData.name = ''
  formData.ak = ''
  formData.sk = ''
  formData.region = 'cn-north-4'
  formData.description = ''
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}


// 组件加载时
onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.accounts-view {
  width: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}
</style>
