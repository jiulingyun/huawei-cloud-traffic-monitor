<template>
  <div class="settings-view">
    <!-- 系统信息 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>系统信息</span>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="系统名称">
          华为云流量监控系统
        </el-descriptions-item>
        <el-descriptions-item label="系统版本">
          v1.0.0
        </el-descriptions-item>
        <el-descriptions-item label="后端框架">
          FastAPI 0.109.0 + Python 3.11
        </el-descriptions-item>
        <el-descriptions-item label="前端框架">
          Vue 3.4 + Vite 5.0 + Element Plus 2.5
        </el-descriptions-item>
        <el-descriptions-item label="数据库">
          SQLite 3
        </el-descriptions-item>
        <el-descriptions-item label="部署方式">
          Docker Compose
        </el-descriptions-item>
        <el-descriptions-item label="启动时间">
          {{ systemInfo.start_time || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="运行时长">
          {{ systemInfo.uptime || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 通知设置 -->
    <el-card class="settings-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>通知设置</span>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          全局通知设置优先级低于账户专属配置。请在「监控配置」页面设置飞书 Webhook URL。
        </template>
      </el-alert>

      <el-form label-width="160px">
        <el-form-item label="启用通知">
          <el-switch v-model="notificationSettings.enabled" disabled />
          <span style="margin-left: 12px; color: #909399">
            请在监控配置中设置
          </span>
        </el-form-item>
        <el-form-item label="通知类型">
          <el-checkbox-group v-model="notificationSettings.types" disabled>
            <el-checkbox label="traffic_alert">流量告警</el-checkbox>
            <el-checkbox label="shutdown_success">关机成功</el-checkbox>
            <el-checkbox label="shutdown_failed">关机失败</el-checkbox>
            <el-checkbox label="system_error">系统错误</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 监控设置 -->
    <el-card class="settings-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>监控设置</span>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          全局监控设置优先级低于账户专属配置。请在「监控配置」页面设置详细参数。
        </template>
      </el-alert>

      <el-form label-width="160px">
        <el-form-item label="默认检查间隔">
          <el-input-number v-model="monitorSettings.check_interval" :min="1" :max="1440" disabled />
          <span style="margin-left: 8px; color: #909399">分钟</span>
        </el-form-item>
        <el-form-item label="默认流量阈值">
          <el-input-number v-model="monitorSettings.traffic_threshold" :min="0.1" :step="0.5" disabled />
          <span style="margin-left: 8px; color: #909399">GB</span>
        </el-form-item>
        <el-form-item label="默认自动关机">
          <el-switch v-model="monitorSettings.auto_shutdown" disabled />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 关于 -->
    <el-card class="settings-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>关于</span>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="项目名称">
          Huawei Cloud Traffic Monitor
        </el-descriptions-item>
        <el-descriptions-item label="项目描述">
          华为云流量包监控与自动关机系统，支持多账户、自定义配置、飞书通知。
        </el-descriptions-item>
        <el-descriptions-item label="开发者">
          羊羊羊（九灵云）
        </el-descriptions-item>
        <el-descriptions-item label="开源协议">
          MIT License
        </el-descriptions-item>
        <el-descriptions-item label="文档">
          <el-link type="primary" href="/docs" target="_blank">查看文档</el-link>
        </el-descriptions-item>
        <el-descriptions-item label="API 文档">
          <el-link type="primary" href="/api/docs" target="_blank">Swagger API Docs</el-link>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { getCurrentLocalTime } from '@/utils/time'

// 系统信息
const systemInfo = reactive({
  start_time: getCurrentLocalTime(),
  uptime: '-'
})

// 通知设置
const notificationSettings = reactive({
  enabled: true,
  types: ['traffic_alert', 'shutdown_success', 'shutdown_failed', 'system_error']
})

// 监控设置
const monitorSettings = reactive({
  check_interval: 5,
  traffic_threshold: 10.0,
  auto_shutdown: true
})
</script>

<style scoped>
.settings-view {
  width: 100%;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}
</style>
