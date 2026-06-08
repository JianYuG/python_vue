import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getXzqhTree } from '../api/xzqh'

export const useXzqhStore = defineStore('xzqh', () => {
  const treeData = ref([])
  const loading = ref(false)
  let _promise = null  // 缓存中的请求 Promise，避免并发重复调用

  /**
   * 获取行政区划树数据（仅首次调用时请求接口，后续直接返回缓存）
   * 并发调用时共享同一个 Promise，保证只发一次请求
   */
  function fetchTree() {
    // 已有缓存，直接返回
    if (treeData.value.length) return Promise.resolve(treeData.value)

    // 正在请求中，复用同一个 Promise
    if (_promise) return _promise

    loading.value = true
    _promise = getXzqhTree()
      .then(res => {
        treeData.value = res.data || []
        return treeData.value
      })
      .finally(() => {
        loading.value = false
        // 请求失败时清除 Promise，允许重试
        if (!treeData.value.length) _promise = null
      })

    return _promise
  }

  return { treeData, loading, fetchTree }
})
