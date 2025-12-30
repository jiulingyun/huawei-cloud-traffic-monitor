<template>
  <div class="servers-view">
    <el-card>
      <!-- 顶部操作栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="label">选择账户：</span>
          <el-select
            v-model="selectedAccountId"
            placeholder="全部账户"
            style="width: 200px"
            clearable
            @change="handleAccountChange"
          >
            <el-option
              v-for="account in enabledAccounts"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button
            :icon="Refresh"
            :loading="loading"
            @click="loadServers"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 服务器表格 -->
      <el-table
        v-loading="loading"
        :data="servers"
        style="width: 100%; margin-top: 20px"
        stripe
        empty-text="暂无 Flexus L 实例"
      >
        <el-table-column prop="name" label="实例名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="公网 IP" width="150">
          <template #default="scope">
            <span v-if="scope.row.public_ip">{{ scope.row.public_ip }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="region_name" label="区域" width="140" />
        <el-table-column prop="account_name" label="所属账户" width="140" />
        <el-table-column label="规格" width="200">
          <template #default="scope">
            <span v-if="scope.row.flavor">{{ scope.row.flavor.vcpus }} vCPU / {{ scope.row.flavor.ram_gb }} GB</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :icon="DataLine"
              @click="handleViewTraffic(scope.row)"
            >
              流量
            </el-button>
            <el-button
              v-if="scope.row.status === 'RUNNING' || scope.row.status === 'ACTIVE'"
              type="danger"
              size="small"
              :icon="SwitchButton"
              @click="handleShutdown(scope.row)"
            >
              关机
            </el-button>
            <el-tag v-else-if="scope.row.status === 'SHUTOFF' || scope.row.status === 'STOPPED'" type="info" size="small">
              已关机
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 统计信息 -->
      <div v-if="servers.length > 0" class="stats-bar">
        <el-statistic title="总数" :value="servers.length" />
        <el-statistic title="运行中" :value="runningCount">
          <template #suffix>
            <el-icon color="#67C23A"><CircleCheckFilled /></el-icon>
          </template>
        </el-statistic>
        <el-statistic title="已关机" :value="stoppedCount">
          <template #suffix>
            <el-icon color="#909399"><CircleCloseFilled /></el-icon>
          </template>
        </el-statistic>
      </div>
    </el-card>

    <!-- 流量详情弹窗 -->
    <el-dialog
      v-model="trafficDialogVisible"
      :title="`流量详情 - ${currentInstance?.name || ''}`"
      width="500px"
    >
      <div v-loading="trafficLoading">
        <template v-if="trafficData">
          <template v-if="trafficData.has_traffic_package && trafficData.traffic">
            <div class="traffic-info">
              <div class="traffic-header">
                <span class="instance-name">{{ trafficData.instance_name }}</span>
                <el-tag size="small">{{ trafficData.region_name }}</el-tag>
              </div>
              
              <el-progress
                :percentage="trafficData.traffic.usage_percentage"
                :color="getProgressColor(trafficData.traffic.usage_percentage)"
                :stroke-width="20"
                style="margin: 20px 0;"
              />
              
              <el-descriptions :column="1" border>
                <el-descriptions-item label="总流量">
                  {{ trafficData.traffic.total_amount }} {{ trafficData.traffic.measure_unit }}
                </el-descriptions-item>
                <el-descriptions-item label="已使用">
                  <span :class="{ 'text-warning': trafficData.traffic.usage_percentage > 80 }">
                    {{ trafficData.traffic.used_amount.toFixed(2) }} {{ trafficData.traffic.measure_unit }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="剩余流量">
                  <span :class="{ 'text-danger': trafficData.traffic.usage_percentage > 90 }">
                    {{ trafficData.traffic.remaining_amount.toFixed(2) }} {{ trafficData.traffic.measure_unit }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="使用率">
                  {{ trafficData.traffic.usage_percentage }}%
                </el-descriptions-item>
                <el-descriptions-item v-if="trafficData.traffic.end_time" label="有效期至">
                  {{ formatDate(trafficData.traffic.end_time) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
          <template v-else>
            <el-empty description="该实例没有关联的流量包" />
          </template>
        </template>
        <template v-else-if="!trafficLoading">
          <el-empty description="查询失败" />
        </template>
      </div>
      <template #footer>
        <el-button @click="trafficDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, SwitchButton, CircleCheckFilled, CircleCloseFilled, DataLine
} from '@element-plus/icons-vue'
import { getAccounts } from '@/api/accounts'
import { getAllServers, getServers, getInstanceTraffic } from '@/api/servers'

// 响应式数据
const loading = ref(false)
const selectedAccountId = ref(null)
const accounts = ref([])
const servers = ref([])

// 流量查询相关
const trafficDialogVisible = ref(false)
const trafficLoading = ref(false)
const trafficData = ref(null)
const currentInstance = ref(null)

// 启用的账户列表
const enabledAccounts = computed(() => {
  return accounts.value.filter(a => a.is_enabled)
})

// 运行中的服务器数量
const runningCount = computed(() => {
  return servers.value.filter(s => s.status === 'RUNNING' || s.status === 'ACTIVE').length
})

// 已关机的服务器数量
const stoppedCount = computed(() => {
  return servers.value.filter(s => s.status === 'SHUTOFF' || s.status === 'STOPPED').length
})

// 加载账户列表
const loadAccounts = async () => {
  try {
    const data = await getAccounts({ limit: 1000 })
    accounts.value = data
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
  }
}

// 账户切换
const handleAccountChange = async () => {
  await loadServers()
}

// 加载 Flexus L 实例列表
const loadServers = async () => {
  loading.value = true
  try {
    let data
    if (selectedAccountId.value) {
      // 查询指定账户
      data = await getServers(selectedAccountId.value)
    } else {
      // 查询所有账户
      data = await getAllServers()
    }
    servers.value = data || []
  } catch (error) {
    console.error('加载实例列表失败:', error)
    ElMessage.error('加载实例列表失败')
    servers.value = []
  } finally {
    loading.value = false
  }
}

// 查看流量
const handleViewTraffic = async (server) => {
  currentInstance.value = server
  trafficDialogVisible.value = true
  trafficLoading.value = true
  trafficData.value = null
  
  try {
    const data = await getInstanceTraffic(server.account_id, server.id)
    trafficData.value = data
  } catch (error) {
    console.error('查询流量失败:', error)
    ElMessage.error('查询流量失败')
  } finally {
    trafficLoading.value = false
  }
}

// 获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage >= 90) return '#F56C6C'
  if (percentage >= 70) return '#E6A23C'
  return '#67C23A'
}

// 关机操作
const handleShutdown = async (server) => {
  try {
    await ElMessageBox.confirm(
      `确认关闭实例「${server.name}」？`,
      '警告',
      {
        confirmButtonText: '确认关机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    ElMessage.info('关机功能将在后端 API 实现后启用')
    // TODO: 调用关机 API
  } catch (error) {
    if (error !== 'cancel') {
      console.error('关机失败:', error)
      ElMessage.error('关机失败')
    }
  }
}

// 状态映射 (Flexus L 状态)
const getStatusType = (status) => {
  const statusMap = {
    'RUNNING': 'success',
    'ACTIVE': 'success',
    'SHUTOFF': 'info',
    'STOPPED': 'info',
    'ERROR': 'danger',
    'BUILD': 'warning',
    'REBOOT': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'RUNNING': '运行中',
    'ACTIVE': '运行中',
    'SHUTOFF': '已关机',
    'STOPPED': '已关机',
    'ERROR': '错误',
    'BUILD': '构建中',
    'REBOOT': '重启中'
  }
  return statusMap[status] || status
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
onMounted(async () => {
  await loadAccounts()
  await loadServers()
})
</script>

<style scoped>
.servers-view {
  width: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-left .label {
  margin-right: 12px;
  font-weight: 500;
  color: #606266;
}

.text-muted {
  color: #909399;
}

.text-warning {
  color: #E6A23C;
  font-weight: 500;
}

.text-danger {
  color: #F56C6C;
  font-weight: 500;
}

.traffic-info {
  padding: 10px 0;
}

.traffic-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.instance-name {
  font-size: 16px;
  font-weight: 500;
}

.stats-bar {
  display: flex;
  gap: 60px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #EBEEF5;
}
</style>
