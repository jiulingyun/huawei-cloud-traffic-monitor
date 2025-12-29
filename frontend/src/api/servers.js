/**
 * 服务器管理 API
 */
import request from '@/utils/request'

/**
 * 获取服务器列表
 * @param {number} accountId - 账户 ID
 * @param {Object} params - 查询参数
 */
export function getServers(accountId, params) {
  return request({
    url: `/v1/servers/${accountId}`,
    method: 'get',
    params
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
