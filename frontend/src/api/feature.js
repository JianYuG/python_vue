import request from '../utils/request'

/**
 * 新增地图要素
 * @param {{
 *   type: number,      // 1=点 2=线 3=面
 *   geometry: string,  // WKT 字符串
 *   name?: string,
 *   xzqhname?: string,
 *   code?: string,
 *   address?: string,
 *   remark?: string
 * }} data
 */
export function createFeature(data) {
  return request({
    url: '/api/features',
    method: 'post',
    data
  })
}

/**
 * 获取所有地图要素（用于图层显示）
 */
export function getAllFeatures() {
  return request({
    url: '/api/features/all',
    method: 'get'
  })
}

/**
 * 编辑地图要素（属性 + 几何）
 * @param {number} id
 * @param {{
 *   type?: number,
 *   geometry?: string,
 *   name?: string,
 *   xzqhname?: string,
 *   code?: string,
 *   address?: string,
 *   remark?: string
 * }} data
 */
export function updateFeature(id, data) {
  return request({
    url: `/api/features/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除地图要素
 * @param {number} id
 */
export function deleteFeature(id) {
  return request({
    url: `/api/features/${id}`,
    method: 'delete'
  })
}
