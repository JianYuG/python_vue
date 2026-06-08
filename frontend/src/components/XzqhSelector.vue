<template>
  <div class="xzqh-selector">
    <el-cascader
      v-model="selected"
      :options="treeData"
      :props="cascaderProps"
      :loading="loading"
      clearable
      filterable
      placeholder="请选择行政区划"
      size="default"
      style="width: 260px"
      @change="handleChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useXzqhStore } from '../stores/xzqh'

const emit = defineEmits(['locate'])

const selected = ref(null)
const loading = ref(false)
const treeData = ref([])

const cascaderProps = {
  checkStrictly: true,   // 允许选中任意一级（不必选到末级）
  emitPath: false        // onChange 只返回最后一级的 value
}

const xzqhStore = useXzqhStore()

onMounted(async () => {
  loading.value = true
  try {
    await xzqhStore.fetchTree()
    treeData.value = xzqhStore.treeData
  } finally {
    loading.value = false
  }
})

/**
 * 用户选中某级行政区划时触发
 * 通过遍历树找到对应节点的 bbox/centroid，emit 给父组件
 */
function handleChange(code) {
  if (!code) {
    emit('locate', null)
    return
  }
  const node = findNode(treeData.value, code)
  if (!node) return

  // bbox: "minX,minY,maxX,maxY"
  const bboxParts = node.bbox ? node.bbox.split(',').map(Number) : null
  // centroid: "lon,lat"
  const centroidParts = node.centroid ? node.centroid.split(',').map(Number) : null

  emit('locate', {
    code: node.code,
    name: node.label,
    fullname: node.fullname,
    level: node.level,
    bbox: bboxParts,        // [minX, minY, maxX, maxY]
    centroid: centroidParts // [lon, lat]
  })
}

/** 递归查找 code 对应节点 */
function findNode(nodes, code) {
  for (const n of nodes) {
    if (n.value === code) return n
    if (n.children && n.children.length) {
      const found = findNode(n.children, code)
      if (found) return found
    }
  }
  return null
}
</script>

<style scoped>
.xzqh-selector {
  display: flex;
  align-items: center;
}
</style>
