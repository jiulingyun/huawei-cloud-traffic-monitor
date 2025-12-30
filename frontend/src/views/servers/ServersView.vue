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
        <el-table-column label="电源状态" width="120">
          <template #default="scope">
            <el-skeleton v-if="isStatusLoading(scope.row)" :rows="1" animated style="width: 60px" />
            <el-tag v-else :type="getStatusType(getDisplayStatus(scope.row))" size="small">
              {{ getStatusText(getDisplayStatus(scope.row)) }}
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
        <el-table-column label="创建时间" width="170">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :icon="DataLine"
              @click="handleViewTraffic(scope.row)"
            >
              流量
            </el-button>
            
            <!-- 运行中：显示关机和重启按钮 -->
            <template v-if="getDisplayStatus(scope.row) === 'ACTIVE'">
              <el-button
                type="warning"
                size="small"
                :icon="RefreshRight"
                :loading="isActionLoading(scope.row)"
                @click="handleReboot(scope.row)"
              >
                重启
              </el-button>
              <el-button
                type="danger"
                size="small"
                :icon="SwitchButton"
                :loading="isActionLoading(scope.row)"
                @click="handleShutdown(scope.row)"
              >
                关机
              </el-button>
            </template>
            
            <!-- 已关机：显示开机按钮 -->
            <template v-else-if="getDisplayStatus(scope.row) === 'SHUTOFF'">
              <el-button
                type="success"
                size="small"
                :icon="VideoPlay"
                :loading="isActionLoading(scope.row)"
                @click="handleStart(scope.row)"
              >
                开机
              </el-button>
            </template>
            
            <!-- 其他状态 -->
            <template v-else>
              <el-tag type="info" size="small">
                {{ getStatusText(getDisplayStatus(scope.row)) }}
              </el-tag>
            </template>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, SwitchButton, CircleCheckFilled, CircleCloseFilled, DataLine, VideoPlay, RefreshRight
} from '@element-plus/icons-vue'
import { getAccounts } from '@/api/accounts'
import {
  getAllServers, getServers, getInstanceTraffic, getServerStatus,
  startServer, stopServer, rebootServer, getJobStatus
} from '@/api/servers'

// 响应式数据
const loading = ref(false)
const statusLoading = ref({})  // 每个服务器的状态加载标记
const actionLoading = ref({})  // 每个服务器的操作加载标记
const selectedAccountId = ref(null)
const accounts = ref([])
const servers = ref([])

// 任务轮询相关
const pollingJobs = ref({})  // { jobId: { accountId, serverId, region, timer } }

// 流量查询相关
const trafficDialogVisible = ref(false)
const trafficLoading = ref(false)
const trafficData = ref(null)
const currentInstance = ref(null)

// 启用的账户列表
const enabledAccounts = computed(() => {
  return accounts.value.filter(a => a.is_enabled)
})

// 运行中的服务器数量 (优先使用实时状态)
const runningCount = computed(() => {
  return servers.value.filter(s => {
    const status = s.ecs_status || s.status
    return status === 'RUNNING' || status === 'ACTIVE'
  }).length
})

// 已关机的服务器数量 (优先使用实时状态)
const stoppedCount = computed(() => {
  return servers.value.filter(s => {
    const status = s.ecs_status || s.status
    return status === 'SHUTOFF' || status === 'STOPPED'
  }).length
})

// 获取服务器显示状态 (优先显示实时状态)
const getDisplayStatus = (server) => {
  return server.ecs_status || server.status
}

// 判断是否正在加载状态
const isStatusLoading = (server) => {
  const key = `${server.account_id}-${server.server_id}`
  return statusLoading.value[key] === true
}

// 判断是否正在执行操作
const isActionLoading = (server) => {
  const key = `${server.account_id}-${server.server_id}`
  return actionLoading.value[key] === true
}

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
      data = await getServers(selectedAccountId.value)
    } else {
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
  
  // 列表加载完成后，异步加载每个服务器的实时状态
  loadServerStatuses()
}

// 加载所有服务器的实时状态（不阻塞）
const loadServerStatuses = async () => {
  const serversWithId = servers.value.filter(s => s.server_id)
  
  if (serversWithId.length === 0) return
  
  // 并发查询所有云主机状态
  serversWithId.forEach(async (server) => {
    const key = `${server.account_id}-${server.server_id}`
    statusLoading.value[key] = true
    
    try {
      const statusData = await getServerStatus(server.account_id, server.server_id, server.region)
      
      if (statusData) {
        server.ecs_status = statusData.status
        server.vm_state = statusData['OS-EXT-STS:vm_state']
        server.power_state = statusData['OS-EXT-STS:power_state']
        server.ecs_name = statusData.name
      }
    } catch (error) {
      console.warn(`获取服务器 ${server.name} 状态失败:`, error)
    } finally {
      statusLoading.value[key] = false
    }
  })
}

// 刷新单个服务器状态
const refreshServerStatus = async (server) => {
  if (!server.server_id) return
  
  const key = `${server.account_id}-${server.server_id}`
  statusLoading.value[key] = true
  
  try {
    const statusData = await getServerStatus(server.account_id, server.server_id, server.region)
    
    if (statusData) {
      server.ecs_status = statusData.status
      server.vm_state = statusData['OS-EXT-STS:vm_state']
      server.power_state = statusData['OS-EXT-STS:power_state']
    }
  } catch (error) {
    console.warn(`刷新服务器状态失败:`, error)
  } finally {
    statusLoading.value[key] = false
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

// 开机操作
const handleStart = async (server) => {
  if (!server.server_id) {
    ElMessage.warning('该实例没有关联的云主机 ID')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认启动云主机「${server.name}」？`,
      '确认开机',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    const key = `${server.account_id}-${server.server_id}`
    actionLoading.value[key] = true
    
    const result = await startServer(server.account_id, server.server_id, server.region)
    
    if (result && result.job_id) {
      ElMessage.success('开机请求已提交，正在启动...')
      // 开始轮询任务状态
      startJobPolling(result.job_id, server, 'start')
    } else {
      ElMessage.error(result?.message || '开机请求失败')
      actionLoading.value[key] = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('开机失败:', error)
      ElMessage.error('开机失败')
    }
  }
}

// 关机操作
const handleShutdown = async (server) => {
  if (!server.server_id) {
    ElMessage.warning('该实例没有关联的云主机 ID')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认关闭云主机「${server.name}」？`,
      '警告',
      {
        confirmButtonText: '确认关机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const key = `${server.account_id}-${server.server_id}`
    actionLoading.value[key] = true
    
    const result = await stopServer(server.account_id, server.server_id, server.region)
    
    if (result && result.job_id) {
      ElMessage.success('关机请求已提交，正在关闭...')
      startJobPolling(result.job_id, server, 'stop')
    } else {
      ElMessage.error(result?.message || '关机请求失败')
      actionLoading.value[key] = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('关机失败:', error)
      ElMessage.error('关机失败')
    }
  }
}

// 重启操作
const handleReboot = async (server) => {
  if (!server.server_id) {
    ElMessage.warning('该实例没有关联的云主机 ID')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认重启云主机「${server.name}」？`,
      '确认重启',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const key = `${server.account_id}-${server.server_id}`
    actionLoading.value[key] = true
    
    const result = await rebootServer(server.account_id, server.server_id, server.region)
    
    if (result && result.job_id) {
      ElMessage.success('重启请求已提交，正在重启...')
      startJobPolling(result.job_id, server, 'reboot')
    } else {
      ElMessage.error(result?.message || '重启请求失败')
      actionLoading.value[key] = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重启失败:', error)
      ElMessage.error('重启失败')
    }
  }
}

// 开始轮询任务状态
const startJobPolling = (jobId, server, action) => {
  const key = `${server.account_id}-${server.server_id}`
  let pollCount = 0
  const maxPolls = 60  // 最多轮询 60 次 (约 2 分钟)
  
  const poll = async () => {
    pollCount++
    
    try {
      const jobStatus = await getJobStatus(server.account_id, jobId, server.region)
      
      if (!jobStatus) {
        console.warn('获取任务状态失败')
        return
      }
      
      if (jobStatus.status === 'SUCCESS') {
        // 任务成功
        stopJobPolling(jobId)
        actionLoading.value[key] = false
        
        const actionText = { start: '开机', stop: '关机', reboot: '重启' }[action]
        ElMessage.success(`${actionText}成功`)
        
        // 刷新服务器状态
        await refreshServerStatus(server)
        
      } else if (jobStatus.status === 'FAIL') {
        // 任务失败
        stopJobPolling(jobId)
        actionLoading.value[key] = false
        
        const actionText = { start: '开机', stop: '关机', reboot: '重启' }[action]
        ElMessage.error(`${actionText}失败: ${jobStatus.fail_reason || '未知错误'}`)
        
      } else if (pollCount >= maxPolls) {
        // 超时
        stopJobPolling(jobId)
        actionLoading.value[key] = false
        ElMessage.warning('操作超时，请手动刷新查看状态')
        
      } else {
        // 继续轮询
        pollingJobs.value[jobId].timer = setTimeout(poll, 2000)
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
      if (pollCount >= maxPolls) {
        stopJobPolling(jobId)
        actionLoading.value[key] = false
      } else {
        pollingJobs.value[jobId].timer = setTimeout(poll, 2000)
      }
    }
  }
  
  // 保存轮询信息
  pollingJobs.value[jobId] = {
    accountId: server.account_id,
    serverId: server.server_id,
    region: server.region,
    timer: setTimeout(poll, 1000)  // 1 秒后开始第一次轮询
  }
}

// 停止轮询
const stopJobPolling = (jobId) => {
  if (pollingJobs.value[jobId]) {
    clearTimeout(pollingJobs.value[jobId].timer)
    delete pollingJobs.value[jobId]
  }
}

// 停止所有轮询
const stopAllPolling = () => {
  Object.keys(pollingJobs.value).forEach(jobId => {
    stopJobPolling(jobId)
  })
}

// 获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage >= 90) return '#F56C6C'
  if (percentage >= 70) return '#E6A23C'
  return '#67C23A'
}

// 状态映射
const getStatusType = (status) => {
  const statusMap = {
    'RUNNING': 'success',
    'ACTIVE': 'success',
    'SHUTOFF': 'info',
    'STOPPED': 'info',
    'ERROR': 'danger',
    'BUILD': 'warning',
    'REBOOT': 'warning',
    'HARD_REBOOT': 'warning'
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
    'REBOOT': '重启中',
    'HARD_REBOOT': '强制重启中'
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

// 组件卸载时清理轮询
onUnmounted(() => {
  stopAllPolling()
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
