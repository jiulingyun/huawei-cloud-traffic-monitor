/**
 * 日志管理 API
 */
import request from '@/utils/request'

/**
 * 获取所有日志（监控日志 + 关机日志）
 * @param {Object} params - 查询参数
 */
export function getAllLogs(params) {
  return request({
    url: '/v1/logs',
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
    url: '/v1/logs/monitor',
    method: 'get',
    params
  })
}

/**
 * 获取关机日志
 * @param {Object} params - 查询参数
 */
export function getShutdownLogs(params) {
  return request({
    url: '/v1/logs/shutdown',
    method: 'get',
    params
  })
}

/**
 * 获取日志统计
 */
export function getLogStats() {
  return request({
    url: '/v1/logs/stats',
    method: 'get'
  })
}

/**
 * 清理旧日志
 * @param {number} days - 保留天数
 */
export function cleanOldLogs(days = 30) {
  return request({
    url: '/v1/logs/clean',
    method: 'post',
    data: { days }
  })
}
