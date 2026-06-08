import request from '../utils/request'

/**
 * 门牌搜索（分页）
 * @param {{
 *   districtid?: string,
 *   tsmc?: string,
 *   page?: number,
 *   pageSize?: number
 * }} params
 */
export function searchDoorplate(params) {
  return request({
    url: '/api/doorplate/search',
    method: 'get',
    params
  })
}