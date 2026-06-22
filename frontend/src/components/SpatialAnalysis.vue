<template>
  <div class="spatial-analysis">
    <!-- 分析类型选择 -->
    <div class="sa-row">
      <el-select
        v-model="analysisType"
        size="small"
        placeholder="选择分析类型"
        style="width:100%"
        @change="onTypeChange"
      >
        <el-option label="缓冲区分析" value="buffer" />
        <el-option label="最邻近分析" value="nearest" />
        <el-option label="空间查询" value="spatial_query" />
        <el-option label="叠加分析" value="overlay" />
        <el-option label="凸包分析" value="convex_hull" />
        <el-option label="质心提取" value="centroid" />
      </el-select>
    </div>

    <!-- 参数区域 -->
    <div v-if="analysisType" class="sa-params">

      <!-- 图层A（大多数分析都需要） -->
      <div v-if="analysisType !== 'overlay'" class="sa-row">
        <span class="sa-label">选择图层</span>
        <el-select
          v-model="tableA"
          size="small"
          placeholder="请选择入库图层"
          style="width:100%"
          :loading="tablesLoading"
        >
          <el-option
            v-for="t in geomTables"
            :key="t.table_name"
            :label="`${t.original_filename} (${t.row_count}条)`"
            :value="t.table_name"
          />
        </el-select>
      </div>

      <!-- 叠加分析：两个图层 -->
      <template v-if="analysisType === 'overlay'">
        <div class="sa-row">
          <span class="sa-label">图层 A</span>
          <el-select v-model="tableA" size="small" placeholder="选择图层A" style="width:100%" :loading="tablesLoading">
            <el-option v-for="t in geomTables" :key="t.table_name" :label="`${t.original_filename}`" :value="t.table_name" />
          </el-select>
        </div>
        <div class="sa-row">
          <span class="sa-label">图层 B</span>
          <el-select v-model="tableB" size="small" placeholder="选择图层B" style="width:100%" :loading="tablesLoading">
            <el-option v-for="t in geomTables" :key="t.table_name" :label="`${t.original_filename}`" :value="t.table_name" />
          </el-select>
        </div>
        <div class="sa-row">
          <span class="sa-label">叠加方式</span>
          <el-select v-model="overlayOp" size="small" style="width:100%">
            <el-option label="交集（Intersection）" value="intersection" />
            <el-option label="并集（Union）" value="union" />
            <el-option label="差集（Difference）" value="difference" />
          </el-select>
        </div>
      </template>

      <!-- 缓冲区分析参数 -->
      <template v-if="analysisType === 'buffer'">
        <div class="sa-row">
          <span class="sa-label">缓冲距离(米)</span>
          <el-input-number
            v-model="bufferDist"
            :min="1"
            :max="100000"
            :step="100"
            size="small"
            style="width:100%"
            controls-position="right"
          />
        </div>
        <div class="sa-row sa-checkbox-row">
          <el-checkbox v-model="bufferUnion" size="small">合并所有缓冲区</el-checkbox>
        </div>
      </template>

      <!-- 最邻近分析参数 -->
      <template v-if="analysisType === 'nearest'">
        <div class="sa-row">
          <span class="sa-label">查询中心</span>
          <div class="sa-coord-row">
            <el-input
              v-model="nearestLng"
              size="small"
              placeholder="经度"
              style="width:48%"
              :readonly="pickingPoint"
            />
            <el-input
              v-model="nearestLat"
              size="small"
              placeholder="纬度"
              style="width:48%"
              :readonly="pickingPoint"
            />
          </div>
        </div>
        <div class="sa-row">
          <el-button
            size="small"
            :type="pickingPoint ? 'warning' : 'default'"
            style="width:100%"
            @click="togglePickPoint"
          >
            {{ pickingPoint ? '请在地图上点击取点...' : '在地图上拾取坐标' }}
          </el-button>
        </div>
        <div class="sa-row">
          <span class="sa-label">返回条数</span>
          <el-input-number
            v-model="nearestLimit"
            :min="1"
            :max="100"
            size="small"
            style="width:100%"
            controls-position="right"
          />
        </div>
      </template>

      <!-- 空间查询参数 -->
      <template v-if="analysisType === 'spatial_query'">
        <div class="sa-row">
          <span class="sa-label">空间关系</span>
          <el-select v-model="queryRelation" size="small" style="width:100%">
            <el-option label="相交（Intersects）" value="intersects" />
            <el-option label="包含于（Within）" value="within" />
            <el-option label="包含（Contains）" value="contains" />
          </el-select>
        </div>
        <div class="sa-row">
          <span class="sa-label">查询范围</span>
          <el-button
            size="small"
            :type="drawingBbox ? 'warning' : 'default'"
            style="width:100%"
            @click="toggleDrawBbox"
          >
            {{ drawingBbox ? '请在地图上拉框选择范围...' : '在地图上框选范围' }}
          </el-button>
        </div>
        <div v-if="queryBbox.length === 4" class="sa-row sa-bbox-tip">
          已选范围：[{{ queryBbox.map(v => v.toFixed(4)).join(', ') }}]
        </div>
      </template>

    </div>

    <!-- 执行按钮 -->
    <div class="sa-row sa-actions">
      <el-button
        type="primary"
        size="small"
        style="width:100%"
        :loading="running"
        :disabled="!analysisType"
        @click="runAnalysis"
      >
        执行分析
      </el-button>
    </div>

    <!-- 结果摘要 -->
    <div v-if="resultCount !== null" class="sa-result-bar">
      <span class="sa-result-count">已渲染 {{ resultCount }} 条到地图</span>
      <div class="sa-result-btns">
        <el-button
          v-if="resultAttrs.length"
          link
          type="primary"
          size="small"
          @click="emit('show-attr-table')"
        >属性表</el-button>
        <el-button link type="danger" size="small" @click="clearResult">清除</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listGeomTables,
  bufferAnalysis,
  nearestAnalysis,
  spatialQuery,
  overlayAnalysis,
  convexHullAnalysis,
  centroidAnalysis,
} from '../api/spatialAnalysis'

// ─── 暴露给父组件（MapView）的事件 ───────────────────────────────────────────
const emit = defineEmits([
  'analysis-result',    // { features, title, analysisType }
  'clear-result',       // 清除分析结果图层
  'request-pick-point', // 请求地图上拾取一个点，回调 fn(lng, lat)
  'request-draw-bbox',  // 请求地图上拉框，回调 fn(bbox)
  'cancel-draw-bbox',   // 用户主动取消框选
  'show-attr-table',    // 请求父组件打开属性表弹框
])

// ─── 图层数据 ─────────────────────────────────────────────────────────────────
const geomTables = ref([])
const tablesLoading = ref(false)

async function loadTables() {
  tablesLoading.value = true
  try {
    const res = await listGeomTables()
    geomTables.value = res.data || []
  } catch (e) {
    // ignore
  } finally {
    tablesLoading.value = false
  }
}

onMounted(loadTables)

// ─── 分析类型与参数 ───────────────────────────────────────────────────────────
const analysisType = ref('')
const tableA = ref('')
const tableB = ref('')

// 缓冲区
const bufferDist = ref(500)
const bufferUnion = ref(false)

// 最邻近
const nearestLng = ref('')
const nearestLat = ref('')
const nearestLimit = ref(5)
const pickingPoint = ref(false)

// 空间查询
const queryRelation = ref('intersects')
const queryBbox = ref([])
const drawingBbox = ref(false)

// 叠加
const overlayOp = ref('intersection')

// ─── 运行状态 & 结果 ──────────────────────────────────────────────────────────
const running = ref(false)
const resultCount = ref(null)
const resultAttrs = ref([])

function onTypeChange() {
  // 切换类型时刷新图层列表
  loadTables()
  clearResult()
  pickingPoint.value = false
  drawingBbox.value = false
  queryBbox.value = []
}

// ─── 地图拾取点 ───────────────────────────────────────────────────────────────
function togglePickPoint() {
  if (pickingPoint.value) {
    pickingPoint.value = false
    return
  }
  pickingPoint.value = true
  emit('request-pick-point', (lng, lat) => {
    nearestLng.value = lng.toFixed(6)
    nearestLat.value = lat.toFixed(6)
    pickingPoint.value = false
  })
}

// ─── 地图框选 bbox ─────────────────────────────────────────────────────────────
function toggleDrawBbox() {
  if (drawingBbox.value) {
    // 用户主动取消框选，通知父组件清理 DragBox 交互
    drawingBbox.value = false
    emit('cancel-draw-bbox')
    return
  }
  drawingBbox.value = true
  emit('request-draw-bbox', (bbox) => {
    queryBbox.value = bbox
    drawingBbox.value = false
  })
}

// ─── 执行分析 ─────────────────────────────────────────────────────────────────
async function runAnalysis() {
  if (!analysisType.value) return

  // 参数校验
  if (analysisType.value !== 'overlay' && !tableA.value) {
    ElMessage.warning('请先选择图层')
    return
  }
  if (analysisType.value === 'overlay') {
    if (!tableA.value || !tableB.value) {
      ElMessage.warning('请选择两个图层')
      return
    }
    if (tableA.value === tableB.value) {
      ElMessage.warning('两个图层不能相同')
      return
    }
  }
  if (analysisType.value === 'nearest') {
    if (!nearestLng.value || !nearestLat.value) {
      ElMessage.warning('请先拾取查询中心点')
      return
    }
  }
  if (analysisType.value === 'spatial_query') {
    if (queryBbox.value.length !== 4) {
      ElMessage.warning('请先在地图上框选查询范围')
      return
    }
  }

  running.value = true
  clearResult()

  try {
    let res
    let title = ''

    switch (analysisType.value) {
      case 'buffer':
        res = await bufferAnalysis(tableA.value, bufferDist.value, bufferUnion.value)
        title = `缓冲区分析 — ${bufferDist.value}m`
        break
      case 'nearest':
        res = await nearestAnalysis(
          tableA.value,
          parseFloat(nearestLng.value),
          parseFloat(nearestLat.value),
          nearestLimit.value
        )
        title = `最邻近分析 — Top${nearestLimit.value}`
        break
      case 'spatial_query':
        res = await spatialQuery(tableA.value, queryBbox.value, queryRelation.value)
        title = `空间查询 — ${queryRelation.value}`
        break
      case 'overlay':
        res = await overlayAnalysis(tableA.value, tableB.value, overlayOp.value)
        title = `叠加分析 — ${overlayOp.value}`
        break
      case 'convex_hull':
        res = await convexHullAnalysis(tableA.value)
        title = '凸包分析'
        break
      case 'centroid':
        res = await centroidAnalysis(tableA.value)
        title = '质心提取'
        break
    }

    const data = res?.data
    if (!data) return

    const geojson = data.geojson
    resultCount.value = data.count || 0

    // 提取属性：优先用后端返回的 attributes，否则从 features.properties 提取
    if (data.attributes && data.attributes.length) {
      resultAttrs.value = data.attributes
    } else if (geojson?.features?.length) {
      resultAttrs.value = geojson.features
        .map(f => f.properties || {})
        .filter(p => Object.keys(p).length > 0)
    } else {
      resultAttrs.value = []
    }

    if (resultCount.value === 0) {
      ElMessage.info('分析完成，无结果要素')
      return
    }

    ElMessage.success(`${title}完成，共 ${resultCount.value} 条结果`)

    // 通知父组件渲染到地图（父组件会自动弹出属性表）
    emit('analysis-result', {
      geojson,
      title,
      analysisType: analysisType.value,
      attributes: resultAttrs.value,
    })
  } catch (e) {
    ElMessage.error(`分析失败: ${e.message || e}`)
  } finally {
    running.value = false
  }
}

// ─── 清除结果 ─────────────────────────────────────────────────────────────────
function clearResult() {
  resultCount.value = null
  resultAttrs.value = []
  emit('clear-result')
}

defineExpose({ resultAttrs })
</script>

<style scoped>
.spatial-analysis {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sa-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sa-label {
  flex-shrink: 0;
  font-size: 12px;
  color: #606266;
  width: 72px;
}

.sa-params {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 2px;
}

.sa-checkbox-row {
  padding-left: 78px;
}

.sa-coord-row {
  display: flex;
  gap: 4%;
  width: 100%;
}

.sa-bbox-tip {
  font-size: 11px;
  color: #909399;
  word-break: break-all;
}

.sa-actions {
  margin-top: 4px;
}

.sa-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f0f9eb;
  border: 1px solid #b3e19d;
  border-radius: 4px;
  padding: 4px 8px;
  margin-top: 4px;
}

.sa-result-count {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.sa-result-btns {
  display: flex;
  gap: 4px;
}
</style>
