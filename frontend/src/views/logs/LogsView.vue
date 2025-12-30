<template>
  <div class="logs-view">
    <!-- 统计卡片 -->
    <el-row v-if="stats" :gutter="12" style="margin-bottom: 20px">
      <el-col :span="5">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="监控日志总数" :value="stats.total_monitor_logs">
            <template #suffix>
              <span class="stat-today">今日 +{{ stats.today_monitor_logs }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="操作日志总数" :value="stats.total_operation_logs || 0">
            <template #suffix>
              <span class="stat-today">今日 +{{ stats.today_operation_logs || 0 }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="低于阈值次数" :value="stats.below_threshold_count">
            <template #suffix>
              <el-icon color="#E6A23C"><WarningFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="关机成功/失败">
            <template #default>
              <span style="color: #67C23A">{{ stats.shutdown_success_count }}</span>
              <span style="color: #909399"> / </span>
              <span style="color: #F56C6C">{{ stats.shutdown_failed_count }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="操作成功/失败">
            <template #default>
              <span style="color: #67C23A">{{ stats.operation_success_count || 0 }}</span>
              <span style="color: #909399"> / </span>
              <span style="color: #F56C6C">{{ stats.operation_failed_count || 0 }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <!-- 顶部筛选栏 -->
      <div class="toolbar">
        <el-select
          v-model="logType"
          placeholder="日志类型"
          style="width: 120px"
          @change="handleFilterChange"
        >
          <el-option label="所有日志" value="all" />
          <el-option label="监控日志" value="monitor" />
          <el-option label="操作日志" value="operation" />
          <el-option label="关机日志" value="shutdown" />
        </el-select>

        <el-select
          v-model="logLevel"
          placeholder="日志级别"
          style="width: 120px"
          @change="handleFilterChange"
        >
          <el-option label="所有级别" value="all" />
          <el-option label="INFO" value="INFO" />
          <el-option label="WARNING" value="WARNING" />
          <el-option label="ERROR" value="ERROR" />
          <el-option label="SUCCESS" value="SUCCESS" />
        </el-select>

        <el-select
          v-model="selectedAccountId"
          placeholder="选择账户"
          style="width: 150px"
          clearable
          @change="handleFilterChange"
        >
          <el-option
            v-for="account in accounts"
            :key="account.id"
            :label="account.name"
            :value="account.id"
          />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 280px"
          @change="handleFilterChange"
        />

        <el-input
          v-model="searchKeyword"
          placeholder="搜索日志内容"
          :prefix-icon="Search"
          clearable
          style="width: 200px"
          @input="handleSearch"
        />

        <el-button :icon="Refresh" :loading="loading" @click="loadLogs">
          刷新
        </el-button>
        
        <el-button type="danger" :icon="Delete" @click="handleCleanLogs">
          清理旧日志
        </el-button>
      </div>

      <!-- 日志表格 -->
      <el-table
        v-loading="loading"
        :data="logs"
        style="width: 100%; margin-top: 20px"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="类型" width="120">
          <template #default="scope">
            <el-tag :type="getTypeColor(scope.row.type)" size="small">
              {{ getTypeText(scope.row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="100">
          <template #default="scope">
            <el-tag :type="getLevelColor(scope.row.level)" size="small">
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="日志内容" min-width="400" show-overflow-tooltip />
        <el-table-column prop="account_name" label="账户" width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="180" sortable>
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              text
              @click="handleViewDetail(scope.row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="日志详情"
      width="700px"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getTypeColor(currentLog.type)" size="small">
            {{ getTypeText(currentLog.type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="级别">
          <el-tag :type="getLevelColor(currentLog.level)" size="small">
            {{ currentLog.level }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="账户">{{ currentLog.account_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatDateTime(currentLog.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <div style="white-space: pre-wrap; word-break: break-all">
            {{ currentLog.message }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentLog.details" label="详细信息">
          <pre style="white-space: pre-wrap; word-break: break-all; margin: 0">{{ JSON.stringify(currentLog.details, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Delete, WarningFilled } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'
import { getAllLogs, getLogStats, cleanOldLogs } from '@/api/logs'
import { getAccounts } from '@/api/accounts'

// 响应式数据
const loading = ref(false)
const logType = ref('all')
const logLevel = ref('all')
const selectedAccountId = ref(null)
const dateRange = ref(null)
const searchKeyword = ref('')
const logs = ref([])
const accounts = ref([])
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const dialogVisible = ref(false)
const currentLog = ref({})
const stats = ref(null)

// 加载日志
const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }
    
    // 添加过滤条件
    if (logType.value !== 'all') {
      params.log_type = logType.value
    }
    if (logLevel.value !== 'all') {
      params.level = logLevel.value
    }
    if (selectedAccountId.value) {
      params.account_id = selectedAccountId.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = formatDateParam(dateRange.value[0])
      params.end_date = formatDateParam(dateRange.value[1])
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }

    const response = await getAllLogs(params)
    
    if (response) {
      // request interceptor 已经解包了 res.data，response 直接就是 { total, items }
      logs.value = response.items || []
      total.value = response.total || 0
    } else {
      logs.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败')
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStats = async () => {
  try {
    const response = await getLogStats()
    if (response) {
      // request interceptor 已经解包了 res.data，response 直接就是 stats 对象
      stats.value = response
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

// 加载账户列表
const loadAccounts = async () => {
  try {
    const data = await getAccounts({ limit: 1000 })
    accounts.value = data || []
  } catch (error) {
    console.error('加载账户失败:', error)
  }
}

// 格式化日期参数
const formatDateParam = (date) => {
  if (!date) return null
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// 筛选改变
const handleFilterChange = () => {
  currentPage.value = 1
  loadLogs()
}

// 搜索
let searchTimer = null
const handleSearch = () => {
  // 防抖
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadLogs()
  }, 300)
}

// 分页改变
const handlePageChange = (page) => {
  currentPage.value = page
  loadLogs()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadLogs()
}

// 查看详情
const handleViewDetail = (log) => {
  currentLog.value = log
  dialogVisible.value = true
}

// 清理旧日志
const handleCleanLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确认清理 30 天前的日志？此操作不可撤销。',
      '警告',
      {
        confirmButtonText: '确认清理',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await cleanOldLogs(30)
    if (response) {
      // request interceptor 已经解包了 res.data
      const { monitor_deleted, shutdown_deleted, operation_deleted = 0 } = response
      ElMessage.success(`成功清理 ${monitor_deleted + shutdown_deleted + operation_deleted} 条日志`)
      loadLogs()
      loadStats()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理日志失败:', error)
      ElMessage.error('清理日志失败')
    }
  }
}

// 类型颜色
const getTypeColor = (type) => {
  const colorMap = {
    'monitor': 'primary',
    'shutdown': 'danger',
    'operation': 'warning',
    'notification': 'success'
  }
  return colorMap[type] || 'info'
}

const getTypeText = (type) => {
  const textMap = {
    'monitor': '监控',
    'shutdown': '关机',
    'operation': '操作',
    'notification': '通知'
  }
  return textMap[type] || type
}

// 级别颜色
const getLevelColor = (level) => {
  const colorMap = {
    'INFO': 'info',
    'SUCCESS': 'success',
    'WARNING': 'warning',
    'ERROR': 'danger'
  }
  return colorMap[level] || 'info'
}


// 组件加载时
onMounted(() => {
  loadAccounts()
  loadLogs()
  loadStats()
})
</script>

<style scoped>
.logs-view {
  width: 100%;
}

.stat-card {
  text-align: center;
}

.stat-today {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

:deep(.el-statistic__head) {
  font-size: 13px;
}

:deep(.el-statistic__content) {
  font-size: 24px;
}
</style>
