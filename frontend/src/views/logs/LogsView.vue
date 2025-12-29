<template>
  <div class="logs-view">
    <el-card>
      <!-- 顶部筛选栏 -->
      <div class="toolbar">
        <el-select
          v-model="logType"
          placeholder="日志类型"
          style="width: 150px; margin-right: 12px"
          @change="handleFilterChange"
        >
          <el-option label="所有日志" value="all" />
          <el-option label="监控日志" value="monitor" />
          <el-option label="关机日志" value="shutdown" />
          <el-option label="通知日志" value="notification" />
        </el-select>

        <el-select
          v-model="logLevel"
          placeholder="日志级别"
          style="width: 150px; margin-right: 12px"
          @change="handleFilterChange"
        >
          <el-option label="所有级别" value="all" />
          <el-option label="INFO" value="INFO" />
          <el-option label="WARNING" value="WARNING" />
          <el-option label="ERROR" value="ERROR" />
          <el-option label="SUCCESS" value="SUCCESS" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 320px; margin-right: 12px"
          @change="handleFilterChange"
        />

        <el-input
          v-model="searchKeyword"
          placeholder="搜索日志内容"
          :prefix-icon="Search"
          clearable
          style="width: 250px; margin-right: 12px"
          @input="handleSearch"
        />

        <el-button :icon="Refresh" :loading="loading" @click="loadLogs">
          刷新
        </el-button>
      </div>

      <!-- 日志表格 -->
      <el-table
        v-loading="loading"
        :data="filteredLogs"
        style="width: 100%; margin-top: 20px"
        stripe
        :default-sort="{ prop: 'created_at', order: 'descending' }"
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
            {{ formatDate(scope.row.created_at) }}
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
        <el-descriptions-item label="时间">{{ formatDate(currentLog.created_at) }}</el-descriptions-item>
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
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getMonitorLogs } from '@/api/servers'

// 响应式数据
const loading = ref(false)
const logType = ref('all')
const logLevel = ref('all')
const dateRange = ref(null)
const searchKeyword = ref('')
const logs = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const currentLog = ref({})

// 过滤后的日志列表
const filteredLogs = computed(() => {
  let result = logs.value

  // 类型过滤
  if (logType.value !== 'all') {
    result = result.filter(log => log.type === logType.value)
  }

  // 级别过滤
  if (logLevel.value !== 'all') {
    result = result.filter(log => log.level === logLevel.value)
  }

  // 日期范围过滤
  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    result = result.filter(log => {
      const logDate = new Date(log.created_at)
      return logDate >= start && logDate <= end
    })
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(log =>
      log.message?.toLowerCase().includes(keyword) ||
      log.account_name?.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 加载日志
const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    const data = await getMonitorLogs(params)
    logs.value = data || []
    total.value = logs.value.length

    // 如果后端返回的是分页数据，使用后端的 total
    // total.value = data.total || logs.value.length
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败')
    logs.value = []
  } finally {
    loading.value = false
  }
}

// 筛选改变
const handleFilterChange = () => {
  currentPage.value = 1
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
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

// 类型颜色
const getTypeColor = (type) => {
  const colorMap = {
    'monitor': 'primary',
    'shutdown': 'danger',
    'notification': 'success'
  }
  return colorMap[type] || 'info'
}

const getTypeText = (type) => {
  const textMap = {
    'monitor': '监控',
    'shutdown': '关机',
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

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 组件加载时
onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.logs-view {
  width: 100%;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
</style>
