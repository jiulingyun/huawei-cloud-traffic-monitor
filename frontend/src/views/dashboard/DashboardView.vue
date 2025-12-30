<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #ecf5ff">
              <el-icon :size="32" color="#409EFF"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.accounts }}</div>
              <div class="stat-label">账户数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f0f9ff">
              <el-icon :size="32" color="#67C23A"><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.servers }}</div>
              <div class="stat-label">服务器数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fef0f0">
              <el-icon :size="32" color="#F56C6C"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.alerts }}</div>
              <div class="stat-label">今日告警</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f4f4f5">
              <el-icon :size="32" color="#909399"><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.monitoring }}</div>
              <div class="stat-label">监控中</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主要内容 -->
    <el-row :gutter="20" class="content-row">
      <!-- 左侧列 -->
      <el-col :xs="24" :lg="16">
        <!-- 流量趋势 -->
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>流量使用趋势</span>
              <el-radio-group v-model="trafficPeriod" size="small">
                <el-radio-button label="7d">7天</el-radio-button>
                <el-radio-button label="30d">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <div class="chart-placeholder">
              <el-icon :size="48" color="#909399"><TrendCharts /></el-icon>
              <p>流量趋势图表</p>
              <el-tag type="info" size="small">图表组件将在后续集成</el-tag>
            </div>
          </div>
        </el-card>

        <!-- 账户状态 -->
        <el-card class="account-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>账户状态</span>
              <el-button type="primary" size="small" @click="$router.push('/accounts')">
                管理账户
              </el-button>
            </div>
          </template>
          <el-table :data="accountList" style="width: 100%" :show-header="true">
            <el-table-column prop="name" label="账户名称" width="180" />
            <el-table-column prop="region" label="区域" width="150" />
            <el-table-column prop="servers" label="服务器" width="100" />
            <el-table-column prop="traffic" label="当月流量" width="120">
              <template #default="scope">
                <span>{{ scope.row.traffic }} GB</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ scope.row.status === 'active' ? '正常' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧列 -->
      <el-col :xs="24" :lg="8">
        <!-- 快速操作 -->
        <el-card class="quick-actions-card" shadow="hover">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" :icon="Plus" @click="$router.push('/accounts')" class="action-btn">
              添加账户
            </el-button>
            <el-button type="success" :icon="Setting" @click="$router.push('/configs')" class="action-btn">
              配置监控
            </el-button>
            <el-button type="info" :icon="View" @click="$router.push('/servers')" class="action-btn">
              查看服务器
            </el-button>
            <el-button type="warning" :icon="Document" @click="$router.push('/logs')" class="action-btn">
              查看日志
            </el-button>
          </div>
        </el-card>

        <!-- 最近通知 -->
        <el-card class="notifications-card" shadow="hover">
          <template #header>
            <span>最近通知</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="item in notifications"
              :key="item.id"
              :timestamp="formatTimelineTimestamp(item.time)"
              :type="item.type"
            >
              {{ item.content }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="notifications.length === 0" description="暂无通知" :image-size="60" />
        </el-card>

        <!-- 系统信息 -->
        <el-card class="system-info-card" shadow="hover">
          <template #header>
            <span>系统信息</span>
          </template>
          <div class="system-info">
            <div class="info-item">
              <span class="info-label">系统版本</span>
              <span class="info-value">v1.0.0</span>
            </div>
            <div class="info-item">
              <span class="info-label">监控状态</span>
              <el-tag type="success" size="small">运行中</el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">上次检查</span>
              <span class="info-value">5 分钟前</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  User, Cpu, Warning, Monitor, TrendCharts,
  Plus, Setting, View, Document
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatTimelineTimestamp } from '@/utils/time'
import {
  getDashboardStats,
  getDashboardAccounts,
  getDashboardNotifications,
  getSystemInfo
} from '@/api/dashboard'

// 统计数据
const stats = reactive({
  accounts: 0,
  servers: 0,
  alerts: 0,
  monitoring: 0
})

// 流量周期
const trafficPeriod = ref('7d')

// 账户列表
const accountList = ref([])

// 通知列表
const notifications = ref([])

// 加载状态
const loading = ref(false)

// 组件加载时
onMounted(() => {
  loadDashboardData()
})

// 加载仪表板数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    // 并发加载所有数据
    const [statsData, accountsData, notificationsData] = await Promise.all([
      getDashboardStats(),
      getDashboardAccounts({ limit: 10 }),
      getDashboardNotifications({ limit: 10 })
    ])

    // 更新统计数据
    stats.accounts = statsData.accounts || 0
    stats.servers = statsData.servers || 0
    stats.alerts = statsData.alerts || 0
    stats.monitoring = statsData.monitoring || 0

    // 更新账户列表
    accountList.value = accountsData || []

    // 更新通知列表
    notifications.value = notificationsData || []
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
    ElMessage.error('加载仪表板数据失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dashboard {
  width: 100%;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

/* 内容区域 */
.content-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 图表卡片 */
.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
  color: #909399;
}

.chart-placeholder p {
  margin: 16px 0 12px 0;
  font-size: 16px;
}

/* 账户卡片 */
.account-card {
  margin-bottom: 20px;
}

/* 快速操作卡片 */
.quick-actions-card {
  margin-bottom: 20px;
}

.quick-actions {
  padding: 8px 0;
}

.action-btn {
  width: 100%;
  margin: 0 0 12px 0 !important;
}

.action-btn:last-child {
  margin-bottom: 0 !important;
}

/* 通知卡片 */
.notifications-card {
  margin-bottom: 20px;
}

.notifications-card :deep(.el-timeline) {
  padding-left: 0;
}

/* 系统信息卡片 */
.system-info-card {
  margin-bottom: 20px;
}

.system-info {
  padding: 8px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #606266;
  font-size: 14px;
}

.info-value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-card {
    margin-bottom: 12px;
  }
  
  .content-row {
    margin-bottom: 12px;
  }
  
  .chart-card,
  .account-card,
  .quick-actions-card,
  .notifications-card,
  .system-info-card {
    margin-bottom: 12px;
  }
}
</style>
