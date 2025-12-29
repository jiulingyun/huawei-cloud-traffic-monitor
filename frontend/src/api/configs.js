/**
 * 监控配置 API
 */
import request from '@/utils/request'

/**
 * 获取配置列表
 * @param {Object} params - 查询参数
 */
export function getConfigs(params) {
  return request({
    url: '/v1/configs',
    method: 'get',
    params
  })
}

/**
 * 获取全局配置
 */
export function getGlobalConfig() {
  return request({
    url: '/v1/configs/global',
    method: 'get'
  })
}

/**
 * 获取有效配置
 * @param {Object} params - 查询参数
 */
export function getEffectiveConfig(params) {
  return request({
    url: '/v1/configs/effective',
    method: 'get',
    params
  })
}

/**
 * 获取配置详情
 * @param {number} configId - 配置 ID
 */
export function getConfigDetail(configId) {
  return request({
    url: `/v1/configs/${configId}`,
    method: 'get'
  })
}

/**
 * 创建配置
 * @param {Object} data - 配置数据
 */
export function createConfig(data) {
  return request({
    url: '/v1/configs',
    method: 'post',
    data
  })
}

/**
 * 更新配置
 * @param {number} configId - 配置 ID
 * @param {Object} data - 更新数据
 */
export function updateConfig(configId, data) {
  return request({
    url: `/v1/configs/${configId}`,
    method: 'put',
    data
  })
}

/**
 * 删除配置
 * @param {number} configId - 配置 ID
 */
export function deleteConfig(configId) {
  return request({
    url: `/v1/configs/${configId}`,
    method: 'delete'
  })
}
