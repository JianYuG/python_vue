import request from '../utils/request'

/**
 * 上传附件（支持多文件）
 * @param {number} featureId - 要素ID
 * @param {File[]} files - 文件列表
 */
export function uploadAttachments(featureId, files) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  return request({
    url: `/api/attachments/upload/${featureId}`,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000  // 上传文件超时时间更长
  })
}

/**
 * 获取要素附件列表
 * @param {number} featureId - 要素ID
 */
export function listAttachments(featureId) {
  return request({
    url: `/api/attachments/list/${featureId}`,
    method: 'get'
  })
}

/**
 * 下载/预览附件 URL（不通过 axios，直接用浏览器打开）
 * @param {number} attachmentId - 附件ID
 * @returns {string} 下载/预览URL
 */
export function getAttachmentDownloadUrl(attachmentId) {
  // 下载/预览由浏览器直接处理，不走 axios
  // 在 URL 中附加 token 参数，以便浏览器直接访问时认证
  const token = localStorage.getItem('token') || ''
  return `/api/attachments/download/${attachmentId}?token=${encodeURIComponent(token)}`
}

/**
 * 删除附件
 * @param {number} attachmentId - 附件ID
 */
export function deleteAttachment(attachmentId) {
  return request({
    url: `/api/attachments/${attachmentId}`,
    method: 'delete'
  })
}