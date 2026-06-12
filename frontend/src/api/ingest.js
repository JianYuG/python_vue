import request from '../utils/request'

/**
 * 上传结构化数据文件入库
 * @param {File} file - 文件对象（csv/xls/xlsx/shp zip/dbf）
 */
export function uploadIngest(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/ingest/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000  // 大文件处理超时时间更长
  })
}

/**
 * 查询所有入库记录
 */
export function listIngest() {
  return request({
    url: '/api/ingest/list',
    method: 'get'
  })
}

/**
 * 删除入库记录及对应数据库表
 * @param {number} id - 入库记录ID
 */
export function deleteIngest(id) {
  return request({
    url: `/api/ingest/${id}`,
    method: 'delete'
  })
}
