<template>
  <div class="servers-view">
    <el-card>
      <!-- 顶部操作栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="label">选择账户：</span>
          <el-select
            v-model="selectedAccountId"
            placeholder="请选择账户"
            style="width: 200px"
            @change="handleAccountChange"
          >
            <el-option
              v-for="account in enabledAccounts"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            />
          </el-select>
          
          <span class="label" style="margin-left: 20px;">选择区域：</span>
          <el-select
            v-model="selectedRegion"
            placeholder="请选择区域"
            style="width: 200px"
            :disabled="!selectedAccountId || regionsLoading"
            :loading="regionsLoading"
            @change="handleRegionChange"
          >
            <el-option
              v-for="region in regions"
              :key="region.id"
              :label="region.display_name"
              :value="region.name"
            >
              <span>{{ region.display_name }}</span>
              <span style="color: #909399; font-size: 12px; margin-left: 8px;">{{ region.name }}</span>
            </el-option>
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button
            :icon="Refresh"
            :loading="loading"
            :disabled="!selectedAccountId || !selectedRegion"
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
        empty-text="请选择账户和区域查看服务器列表"
      >
        <el-table-column prop="id" label="服务器 ID" width="280" show-overflow-tooltip />
        <el-table-column prop="name" label="名称" width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="IP 地址" width="200">
          <template #default="scope">
            <div v-if="scope.row.public_ips && scope.row.public_ips.length > 0">
              <div v-for="ip in scope.row.public_ips" :key="ip" class="ip-item">
                <el-tag size="small" type="success">公网</el-tag>
                {{ ip }}
              </div>
            </div>
            <div v-if="scope.row.private_ips && scope.row.private_ips.length > 0">
              <div v-for="ip in scope.row.private_ips" :key="ip" class="ip-item">
                <el-tag size="small" type="info">私网</el-tag>
                {{ ip }}
              </div>
            </div>
            <span v-if="!scope.row.public_ips?.length && !scope.row.private_ips?.length">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="availability_zone" label="可用区" width="150" />
        <el-table-column prop="flavor_id" label="规格" width="150" show-overflow-tooltip />
        <el-table-column label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'ACTIVE'"
              type="danger"
              size="small"
              :icon="SwitchButton"
              @click="handleShutdown(scope.row)"
            >
              关机
            </el-button>
            <el-tag v-else-if="scope.row.status === 'SHUTOFF'" type="info" size="small">
              已关机
            </el-tag>
            <el-tag v-else type="warning" size="small">
              {{ getStatusText(scope.row.status) }}
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, SwitchButton, CircleCheckFilled, CircleCloseFilled
} from '@element-plus/icons-vue'
import { getAccounts } from '@/api/accounts'
import { getServers, getRegions } from '@/api/servers'

// localStorage key
const REGION_CACHE_KEY = 'huawei_cloud_selected_region'

// 响应式数据
const loading = ref(false)
const regionsLoading = ref(false)
const selectedAccountId = ref(null)
const selectedRegion = ref(null)
const accounts = ref([])
const regions = ref([])
const servers = ref([])

// 启用的账户列表
const enabledAccounts = computed(() => {
  return accounts.value.filter(a => a.is_enabled)
})

// 运行中的服务器数量
const runningCount = computed(() => {
  return servers.value.filter(s => s.status === 'ACTIVE').length
})

// 已关机的服务器数量
const stoppedCount = computed(() => {
  return servers.value.filter(s => s.status === 'SHUTOFF').length
})

// 从缓存获取上次选择的区域
const getCachedRegion = (accountId) => {
  try {
    const cached = localStorage.getItem(`${REGION_CACHE_KEY}_${accountId}`)
    return cached ? JSON.parse(cached) : null
  } catch {
    return null
  }
}

// 缓存选择的区域
const cacheRegion = (accountId, region) => {
  try {
    localStorage.setItem(`${REGION_CACHE_KEY}_${accountId}`, JSON.stringify(region))
  } catch {
    // ignore
  }
}

// 加载账户列表
const loadAccounts = async () => {
  try {
    const data = await getAccounts({ limit: 1000 })
    accounts.value = data
    
    // 自动选择第一个启用的账户
    if (enabledAccounts.value.length > 0 && !selectedAccountId.value) {
      selectedAccountId.value = enabledAccounts.value[0].id
      await loadRegions()
    }
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
  }
}

// 加载区域列表
const loadRegions = async () => {
  if (!selectedAccountId.value) return
  
  regionsLoading.value = true
  regions.value = []
  selectedRegion.value = null
  servers.value = []
  
  try {
    const data = await getRegions(selectedAccountId.value)
    regions.value = data
    
    if (data.length > 0) {
      // 尝试从缓存恢复上次选择的区域
      const cached = getCachedRegion(selectedAccountId.value)
      if (cached && data.find(r => r.name === cached.name)) {
        selectedRegion.value = cached.name
      } else {
        // 默认选择第一个区域
        selectedRegion.value = data[0].name
      }
      // 加载服务器
      await loadServers()
    }
  } catch (error) {
    console.error('加载区域列表失败:', error)
    ElMessage.error('加载区域列表失败')
  } finally {
    regionsLoading.value = false
  }
}

// 账户切换
const handleAccountChange = async () => {
  servers.value = []
  regions.value = []
  selectedRegion.value = null
  if (selectedAccountId.value) {
    await loadRegions()
  }
}

// 区域切换
const handleRegionChange = async () => {
  servers.value = []
  if (selectedRegion.value) {
    // 缓存选择
    const region = regions.value.find(r => r.name === selectedRegion.value)
    if (region) {
      cacheRegion(selectedAccountId.value, region)
    }
    await loadServers()
  }
}

// 加载服务器列表
const loadServers = async () => {
  if (!selectedAccountId.value || !selectedRegion.value) {
    return
  }
  
  // 获取当前选中区域的 project_id
  const region = regions.value.find(r => r.name === selectedRegion.value)
  if (!region) {
    ElMessage.warning('请选择区域')
    return
  }

  loading.value = true
  try {
    const data = await getServers(selectedAccountId.value, {
      region: selectedRegion.value,
      project_id: region.id,
      limit: 1000
    })
    servers.value = data
  } catch (error) {
    console.error('加载服务器列表失败:', error)
    ElMessage.error('加载服务器列表失败')
    servers.value = []
  } finally {
    loading.value = false
  }
}

// 关机操作
const handleShutdown = async (server) => {
  try {
    await ElMessageBox.confirm(
      `确认关闭服务器「${server.name}」？`,
      '警告',
      {
        confirmButtonText: '确认关机',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    ElMessage.info('关机功能将在后端 API 实现后启用')
    // TODO: 调用关机 API
    // await shutdownServer(selectedAccountId.value, server.id)
    // ElMessage.success('关机指令已发送')
    // await loadServers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('关机失败:', error)
      ElMessage.error('关机失败')
    }
  }
}

// 状态映射
const getStatusType = (status) => {
  const statusMap = {
    'ACTIVE': 'success',
    'SHUTOFF': 'info',
    'ERROR': 'danger',
    'BUILD': 'warning',
    'REBOOT': 'warning',
    'HARD_REBOOT': 'warning',
    'REBUILD': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'ACTIVE': '运行中',
    'SHUTOFF': '已关机',
    'ERROR': '错误',
    'BUILD': '构建中',
    'REBOOT': '重启中',
    'HARD_REBOOT': '强制重启',
    'REBUILD': '重建中'
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
onMounted(() => {
  loadAccounts()
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

.ip-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0;
  font-size: 13px;
}

.stats-bar {
  display: flex;
  gap: 60px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #EBEEF5;
}
</style>
