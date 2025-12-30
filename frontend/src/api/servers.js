/**
 * 服务器管理 API (Flexus L 实例)
 */
import request from '@/utils/request'

/**
 * 获取所有账户的 Flexus L 实例列表
 */
export function getAllServers() {
  return request({
    url: '/v1/servers',
    method: 'get'
  })
}

/**
 * 获取指定账户的 Flexus L 实例列表
 * @param {number} accountId - 账户 ID
 */
export function getServers(accountId) {
  return request({
    url: `/v1/servers/${accountId}`,
    method: 'get'
  })
}

/**
 * 获取指定账户的流量汇总
 * @param {number} accountId - 账户 ID
 */
export function getAccountTraffic(accountId) {
  return request({
    url: `/v1/servers/${accountId}/traffic`,
    method: 'get'
  })
}

/**
 * 获取指定实例的流量使用情况
 * @param {number} accountId - 账户 ID
 * @param {string} instanceId - 实例 ID
 */
export function getInstanceTraffic(accountId, instanceId) {
  return request({
    url: `/v1/servers/${accountId}/instance/${instanceId}/traffic`,
    method: 'get'
  })
}

/**
 * 获取云主机实时状态
 * @param {number} accountId - 账户 ID
 * @param {string} serverId - 云主机 ID (server_id)
 * @param {string} region - 区域 ID
 */
export function getServerStatus(accountId, serverId, region) {
  return request({
    url: `/v1/servers/${accountId}/server/${serverId}/status`,
    method: 'get',
    params: { region }
  })
}

/**
 * 启动云主机
 * @param {number} accountId - 账户 ID
 * @param {string} serverId - 云主机 ID
 * @param {string} region - 区域 ID
 */
export function startServer(accountId, serverId, region) {
  return request({
    url: `/v1/servers/${accountId}/server/start`,
    method: 'post',
    data: { server_id: serverId, region }
  })
}

/**
 * 关闭云主机
 * @param {number} accountId - 账户 ID
 * @param {string} serverId - 云主机 ID
 * @param {string} region - 区域 ID
 * @param {string} actionType - SOFT/HARD
 */
export function stopServer(accountId, serverId, region, actionType = 'SOFT') {
  return request({
    url: `/v1/servers/${accountId}/server/stop`,
    method: 'post',
    data: { server_id: serverId, region, action_type: actionType }
  })
}

/**
 * 重启云主机
 * @param {number} accountId - 账户 ID
 * @param {string} serverId - 云主机 ID
 * @param {string} region - 区域 ID
 * @param {string} actionType - SOFT/HARD
 */
export function rebootServer(accountId, serverId, region, actionType = 'SOFT') {
  return request({
    url: `/v1/servers/${accountId}/server/reboot`,
    method: 'post',
    data: { server_id: serverId, region, action_type: actionType }
  })
}

/**
 * 查询任务状态
 * @param {number} accountId - 账户 ID
 * @param {string} jobId - 任务 ID
 * @param {string} region - 区域 ID
 */
export function getJobStatus(accountId, jobId, region) {
  return request({
    url: `/v1/servers/${accountId}/jobs/${jobId}`,
    method: 'get',
    params: { region }
  })
}

/**
 * 获取监控日志
 * @param {Object} params - 查询参数
 */
export function getMonitorLogs(params) {
  return request({
    url: '/v1/monitor/logs',
    method: 'get',
    params
  })
}

/**
 * 获取监控统计
 * @param {Object} params - 查询参数
 */
export function getMonitorStats(params) {
  return request({
    url: '/v1/monitor/stats',
    method: 'get',
    params
  })
}

/**
 * 手动触发监控
 * @param {number} accountId - 账户 ID
 */
export function triggerMonitor(accountId) {
  return request({
    url: '/v1/monitor/trigger',
    method: 'post',
    data: { account_id: accountId }
  })
}
