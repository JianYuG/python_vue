import request from '../utils/request'

/**
 * 获取所有含 geom 字段的入库表列表
 */
export function listGeomTables() {
  return request.get('/api/spatial/tables')
}

/**
 * 缓冲区分析
 * @param {string} table_name 入库表名
 * @param {number} distance   缓冲距离（米）
 * @param {boolean} union_result 是否合并所有缓冲区
 */
export function bufferAnalysis(table_name, distance, union_result = false) {
  return request.post('/api/spatial/buffer', { table_name, distance, union_result })
}

/**
 * 最邻近分析
 * @param {string} table_name 入库表名
 * @param {number} lng        查询中心经度
 * @param {number} lat        查询中心纬度
 * @param {number} limit      返回条数
 */
export function nearestAnalysis(table_name, lng, lat, limit = 5) {
  return request.post('/api/spatial/nearest', { table_name, lng, lat, limit })
}

/**
 * 空间查询
 * @param {string}   table_name 入库表名
 * @param {number[]} bbox       [minx, miny, maxx, maxy]
 * @param {string}   relation   intersects | within | contains
 */
export function spatialQuery(table_name, bbox, relation = 'intersects') {
  return request.post('/api/spatial/spatial_query', { table_name, bbox, relation })
}

/**
 * 叠加分析
 * @param {string} table_a    图层 A 表名
 * @param {string} table_b    图层 B 表名
 * @param {string} operation  intersection | union | difference
 */
export function overlayAnalysis(table_a, table_b, operation = 'intersection') {
  return request.post('/api/spatial/overlay', { table_a, table_b, operation })
}

/**
 * 凸包分析
 * @param {string} table_name 入库表名
 */
export function convexHullAnalysis(table_name) {
  return request.post('/api/spatial/convex_hull', { table_name })
}

/**
 * 质心提取
 * @param {string} table_name 入库表名
 */
export function centroidAnalysis(table_name) {
  return request.post('/api/spatial/centroid', { table_name })
}
