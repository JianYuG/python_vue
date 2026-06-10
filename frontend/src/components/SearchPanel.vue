<template>
  <div class="search-panel">
    <!-- 搜索条件区 -->
    <div class="search-form">
      <el-cascader
        v-model="xzqhSelected"
        :options="xzqhTree"
        :props="cascaderProps"
        :loading="xzqhLoading"
        clearable
        filterable
        placeholder="行政区划（选填）"
        size="small"
        @change="onXzqhChange"
      />
      <el-input
        v-model="tsmcKeyword"
        placeholder="门牌名称（选填）"
        size="small"
        clearable
        @keyup.enter="doSearch"
      >
        <template #append>
          <el-button
            type="primary"
            :loading="searchLoading"
            @click="doSearch"
          >
            搜索
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 搜索结果区 -->
    <div v-if="resultVisible" class="search-result">
      <div class="result-header">
        <span class="result-title">搜索结果 ({{ total }}条)</span>
        <button class="result-close" @click="closeResult">×</button>
      </div>

      <div v-if="searchLoading" class="result-loading">加载中...</div>
      <div v-else-if="items.length === 0" class="result-empty">无匹配数据</div>
      <template v-else>
        <div
          v-for="item in items"
          :key="item.gid"
          class="result-item"
          :class="{ active: selectedGid === item.gid }"
          @click="onItemClick(item)"
        >
          <div class="item-name">{{ item.tsmc || '—' }}</div>
          <div class="item-meta">
            <span>{{ item.xzqh || '—' }}</span>
            <span class="item-code">{{ item.districtid }}</span>
          </div>
        </div>

        <!-- 分页 -->
        <div class="result-pagination">
          <el-pagination
            small
            layout="prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :current-page="currentPage"
            @current-change="onPageChange"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useXzqhStore } from '../stores/xzqh'
import { searchDoorplate } from '../api/doorplate'

const emit = defineEmits(['locate', 'search-result', 'search-close', 'xzqh-locate'])

// 行政区划
const xzqhSelected = ref(null)
const xzqhCode = ref('')
const xzqhTree = ref([])
const xzqhLoading = ref(false)
const xzqhStore = useXzqhStore()

const cascaderProps = {
  checkStrictly: true,
  emitPath: false
}

onMounted(async () => {
  xzqhLoading.value = true
  try {
    await xzqhStore.fetchTree()
    xzqhTree.value = xzqhStore.treeData
  } finally {
    xzqhLoading.value = false
  }
})

function onXzqhChange(code) {
  if (!code) {
    xzqhCode.value = ''
    return
  }
  xzqhCode.value = code
  // 查找选中节点，获取 bbox/centroid 用于地图跳转
  const node = findNode(xzqhTree.value, code)
  if (node) {
    emit('xzqh-locate', { bbox: node.bbox, centroid: node.centroid, level: node.level })
  }
}

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

// 搜索
const tsmcKeyword = ref('')
const searchLoading = ref(false)
const resultVisible = ref(false)
const items = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const selectedGid = ref(null)

async function doSearch() {
  if (!xzqhCode.value && !tsmcKeyword.value.trim()) {
    ElMessage.warning('请至少输入一个搜索条件')
    return
  }
  currentPage.value = 1
  await fetchData()
}

async function fetchData() {
  searchLoading.value = true
  try {
    const res = await searchDoorplate({
      districtid: xzqhCode.value || '',
      tsmc: tsmcKeyword.value.trim() || '',
      page: currentPage.value,
      pageSize: pageSize.value
    })
    items.value = res.data.items || []
    total.value = res.data.total || 0
    if (res.data.hint) {
      ElMessage.info(res.data.hint)
    }
    resultVisible.value = true
    // 通知父组件渲染搜索结果到地图
    emit('search-result', items.value)
  } finally {
    searchLoading.value = false
  }
}

function onPageChange(page) {
  currentPage.value = page
  fetchData()
}

function onItemClick(item) {
  selectedGid.value = item.gid
  emit('locate', item)
}

function closeResult() {
  resultVisible.value = false
  selectedGid.value = null
  emit('search-close')
}
</script>

<style scoped>
.search-panel {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  width: 380px;
  max-height: calc(100vh - 60px);
  overflow-y: auto;
}

.search-form {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.search-form :deep(.el-cascader) {
  width: 160px;
  flex-shrink: 0;
}

.search-form :deep(.el-input) {
  flex: 1;
  min-width: 0;
}

/* 搜索结果 */
.search-result {
  margin-top: 8px;
  border-top: 1px solid #ebeef5;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0 4px;
}

.result-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.result-close {
  border: none;
  background: none;
  font-size: 16px;
  color: #909399;
  cursor: pointer;
  padding: 0 2px;
}

.result-close:hover { color: #303133; }

.result-loading,
.result-empty {
  padding: 10px;
  font-size: 13px;
  color: #909399;
  text-align: center;
}

.result-item {
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f2f5;
}

.result-item:last-child { border-bottom: none; }

.result-item:hover { background: #ecf5ff; }
.result-item.active { background: #409eff22; }

.item-name {
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
}

.item-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 6px;
  margin-top: 2px;
}

.item-code { color: #67c23a; }

.result-pagination {
  margin-top: 6px;
  display: flex;
  justify-content: center;
}
</style>