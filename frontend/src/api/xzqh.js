import request from '../utils/request'

/**
 * 获取行政区划级联树（省/市/区县/乡镇，1-4级）
 * 每节点包含: value(code), label(name), bbox, centroid, children
 */
export function getXzqhTree() {
  return request({
    url: '/api/xzqh/tree',
    method: 'get'
  })
}
