<template>
  <div class="measure-tool">
    <el-tooltip content="长度测量" placement="bottom">
      <el-button
        :type="activeType === 'length' ? 'primary' : 'default'"
        circle
        @click="toggleMeasure('length')"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path d="M1 16h18v2H1v-2zm1-3l1.5-1.5L5 13l1.5-1.5L8 13l1.5-1.5L11 13l1.5-1.5L14 13l1.5-1.5L17 13l1-1V4h-2v5h-1V4h-2v5h-1V4h-2v5h-1V4H7v5H6V4H4v5H3V4H1v9z"/>
        </svg>
      </el-button>
    </el-tooltip>
    <el-tooltip content="面积测量" placement="bottom">
      <el-button
        :type="activeType === 'area' ? 'primary' : 'default'"
        circle
        @click="toggleMeasure('area')"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path d="M3 3v14h14V3H3zm12 12H5V5h10v10zM7 7h6v6H7V7z" opacity="0.4"/>
          <path d="M3 3h14v14H3V3zm2 2v10h10V5H5z"/>
        </svg>
      </el-button>
    </el-tooltip>
    <el-tooltip content="清除测量" placement="bottom">
      <el-button
        :disabled="!hasMeasureResult"
        circle
        @click="clearMeasure"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
      </el-button>
    </el-tooltip>
  </div>

  <!-- 测量结果提示（跟随鼠标） -->
  <teleport to="body">
    <div
      v-if="measureTip.show"
      class="measure-tip"
      :style="{ left: measureTip.x + 'px', top: measureTip.y + 'px' }"
    >
      {{ measureTip.text }}
    </div>
  </teleport>

  <!-- 右键菜单 -->
  <teleport to="body">
    <div
      v-if="contextMenu.visible"
      class="measure-context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div class="mctx-item mctx-confirm" @click="onContextConfirm">✓ 确定</div>
      <div class="mctx-item mctx-cancel" @click="onContextCancel">✕ 取消</div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, reactive, watch, onBeforeUnmount, toRaw } from 'vue'
import { ElMessage } from 'element-plus'
import Draw from 'ol/interaction/Draw'
import VectorSource from 'ol/source/Vector'
import VectorLayer from 'ol/layer/Vector'
import { Style, Fill, Stroke, Circle as CircleStyle, Text } from 'ol/style'
import { getLength, getArea } from 'ol/sphere'
import DoubleClickZoom from 'ol/interaction/DoubleClickZoom'
import LineString from 'ol/geom/LineString'
import Polygon from 'ol/geom/Polygon'
import { get as getProjection } from 'ol/proj'

const props = defineProps({
  map: { type: Object, default: null }
})

const activeType = ref(null)       // 'length' | 'area' | null
const hasMeasureResult = ref(false)

// 测量结果提示
const measureTip = reactive({ show: false, x: 0, y: 0, text: '' })

// 右键菜单
const contextMenu = reactive({ visible: false, x: 0, y: 0 })

// 测量图层
let measureSource = null
let measureLayer = null
let drawInteraction = null
let dblClickZoomInteraction = null
let _pointerMoveHandler = null
let _contextHandler = null
let _pointerdownHandler = null
let _pendingContextCount = -1

// 测量绘制样式
const MEASURE_DRAW_STYLE = new Style({
  fill: new Fill({ color: 'rgba(230, 162, 60, 0.2)' }),
  stroke: new Stroke({ color: '#e6a23c', width: 2, lineDash: [8, 4] }),
  image: new CircleStyle({
    radius: 5,
    fill: new Fill({ color: '#e6a23c' }),
    stroke: new Stroke({ color: '#fff', width: 2 })
  })
})

/** 格式化长度 */
function formatLength(length) {
  if (!length || !isFinite(length)) return '0 m'
  if (length > 1000) {
    return (length / 1000).toFixed(2) + ' km'
  }
  return length.toFixed(1) + ' m'
}

/** 格式化面积 */
function formatArea(area) {
  if (!area || !isFinite(area)) return '0 m²'
  if (area > 1000000) {
    return (area / 1000000).toFixed(2) + ' km²'
  }
  return area.toFixed(1) + ' m²'
}

/** 为已完成的测量要素创建样式（图形 + 测量值标签） */
function createMeasureStyles(geom) {
  // EPSG:4490 坐标与 EPSG:4326 完全一致（经纬度），用 4326 做测量计算
  const projection = getProjection('EPSG:4326')

  let label = ''
  let offsetY = -10  // 标签垂直偏移（像素）

  if (geom instanceof LineString) {
    const length = getLength(geom, { projection })
    label = '总长: ' + formatLength(length)
  } else if (geom instanceof Polygon) {
    const area = getArea(geom, { projection })
    label = '面积: ' + formatArea(area)
    offsetY = 0
  }

  // 图形样式（线/面 + 文字标签，不使用 geometry 属性避免投影错误）
  const textOpts = label ? {
    text: label,
    font: 'bold 13px sans-serif',
    offsetY: offsetY,
    fill: new Fill({ color: '#303133' }),
    stroke: new Stroke({ color: '#fff', width: 3 }),
    padding: [3, 6, 3, 6],
    backgroundFill: new Fill({ color: 'rgba(255,255,255,0.9)' })
  } : undefined

  return [new Style({
    fill: new Fill({ color: 'rgba(230, 162, 60, 0.2)' }),
    stroke: new Stroke({ color: '#e6a23c', width: 2, lineDash: [8, 4] }),
    image: new CircleStyle({
      radius: 5,
      fill: new Fill({ color: '#e6a23c' }),
      stroke: new Stroke({ color: '#fff', width: 2 })
    }),
    text: textOpts ? new Text(textOpts) : undefined
  })]
}

function getRawMap() {
  return toRaw(props.map)
}

function ensureMeasureLayer() {
  if (measureLayer) return
  measureSource = new VectorSource()
  measureLayer = new VectorLayer({
    source: measureSource,
    zIndex: 110
  })
  getRawMap().addLayer(measureLayer)
}

/** 禁用双击放大 */
function disableDblClickZoom() {
  const rawMap = getRawMap()
  rawMap.getInteractions().forEach(interaction => {
    if (interaction instanceof DoubleClickZoom) {
      dblClickZoomInteraction = interaction
      interaction.setActive(false)
    }
  })
}

/** 恢复双击放大 */
function enableDblClickZoom() {
  if (dblClickZoomInteraction) {
    dblClickZoomInteraction.setActive(true)
    dblClickZoomInteraction = null
  }
}

/** 获取已画点数 */
function getDrawnPointCount() {
  if (!drawInteraction) return 0
  try {
    const coords = drawInteraction.sketchCoords_
    if (!coords) return 0
    const olType = activeType.value === 'length' ? 'LineString' : 'Polygon'
    if (olType === 'LineString') {
      return Math.max(0, coords.length - 1)
    } else {
      if (Array.isArray(coords[0])) {
        return Math.max(0, coords[0].length - 1)
      }
      return Math.max(0, coords.length - 1)
    }
  } catch (e) {
    return 0
  }
}

function getMinPoints() {
  return activeType.value === 'length' ? 2 : 3
}

/** 绑定鼠标移动事件：实时显示测量值 */
function bindPointerMove() {
  const map = getRawMap()
  _pointerMoveHandler = (evt) => {
    if (!drawInteraction) return
    try {
      const sketchFeature = drawInteraction.sketchFeature_
      if (!sketchFeature) return
      const geom = sketchFeature.getGeometry()
      if (!geom) return

      const projection = getProjection('EPSG:4326')
      let text = ''
      if (geom instanceof LineString) {
        text = '总长: ' + formatLength(getLength(geom, { projection }))
      } else if (geom instanceof Polygon) {
        text = '面积: ' + formatArea(getArea(geom, { projection }))
      }

      measureTip.show = true
      measureTip.x = evt.pixel[0] + 16
      measureTip.y = evt.pixel[1] - 12
      measureTip.text = text
    } catch (e) {
      // ignore
    }
  }
  map.on('pointermove', _pointerMoveHandler)
}

function unbindPointerMove() {
  if (_pointerMoveHandler && props.map) {
    getRawMap().un('pointermove', _pointerMoveHandler)
    _pointerMoveHandler = null
  }
  measureTip.show = false
}

/** 绑定右键菜单 */
function bindContextMenu() {
  const el = getRawMap().getTargetElement()

  _pointerdownHandler = (e) => {
    if (e.button !== 2) return
    _pendingContextCount = getDrawnPointCount()
    e.stopPropagation()
  }
  el.addEventListener('pointerdown', _pointerdownHandler, { capture: true })

  _contextHandler = (e) => {
    e.preventDefault()
    const count = _pendingContextCount
    _pendingContextCount = -1
    if (count < getMinPoints()) {
      const need = getMinPoints()
      const typeName = activeType.value === 'length' ? '线' : '面'
      ElMessage.warning(`点位不足，绘制${typeName}需要至少 ${need} 个点，请继续绘制`)
      return
    }
    contextMenu.x = e.clientX
    contextMenu.y = e.clientY
    contextMenu.visible = true
  }
  el.addEventListener('contextmenu', _contextHandler)
  document.addEventListener('click', closeContextMenu)
}

function unbindContextMenu() {
  const el = props.map ? getRawMap().getTargetElement() : null
  if (el) {
    if (_contextHandler) {
      el.removeEventListener('contextmenu', _contextHandler)
      _contextHandler = null
    }
    if (_pointerdownHandler) {
      el.removeEventListener('pointerdown', _pointerdownHandler, { capture: true })
      _pointerdownHandler = null
    }
  }
  document.removeEventListener('click', closeContextMenu)
  contextMenu.visible = false
  _pendingContextCount = -1
}

function closeContextMenu() {
  contextMenu.visible = false
}

function onContextConfirm() {
  closeContextMenu()
  if (drawInteraction) {
    drawInteraction.finishDrawing()
  }
}

function onContextCancel() {
  closeContextMenu()
  const type = activeType.value
  stopMeasure()
  if (type) {
    setTimeout(() => toggleMeasure(type), 0)
  }
}

/** 切换测量模式 */
function toggleMeasure(type) {
  if (activeType.value === type) {
    stopMeasure()
    return
  }
  stopMeasure()
  if (!props.map) return

  ensureMeasureLayer()
  activeType.value = type
  disableDblClickZoom()

  const olType = type === 'length' ? 'LineString' : 'Polygon'

  drawInteraction = new Draw({
    source: measureSource,
    type: olType,
    style: MEASURE_DRAW_STYLE
  })

  drawInteraction.on('drawend', (evt) => {
    // ★ 关键：延迟清理交互，确保要素先完成添加到 source
    const feature = evt.feature
    const geom = feature.getGeometry()
    // 给要素设置带测量标签的完整样式
    if (geom) {
      feature.setStyle(createMeasureStyles(geom))
    }
    hasMeasureResult.value = true
    // 延迟停止交互，让 Draw 完成内部添加要素流程
    setTimeout(() => {
      stopDrawInteraction()
    }, 100)
  })

  bindPointerMove()
  bindContextMenu()
  getRawMap().addInteraction(drawInteraction)
  getRawMap().getTargetElement().style.cursor = 'crosshair'
  ElMessage.info(type === 'length' ? '请在地图上绘制线段测量长度，右键确定' : '请在地图上绘制多边形测量面积，右键确定')
}

/** 停止绘制交互但不清除测量结果 */
function stopDrawInteraction() {
  unbindPointerMove()
  unbindContextMenu()
  enableDblClickZoom()
  if (drawInteraction && props.map) {
    getRawMap().removeInteraction(drawInteraction)
    drawInteraction = null
  }
  activeType.value = null
  if (props.map) getRawMap().getTargetElement().style.cursor = ''
}

/** 停止测量（含绘制交互） */
function stopMeasure() {
  stopDrawInteraction()
}

/** 清除所有测量结果 */
function clearMeasure() {
  stopMeasure()
  if (measureSource) {
    measureSource.clear()
  }
  hasMeasureResult.value = false
  ElMessage.success('已清除测量结果')
}

// map prop 变化时重新初始化
watch(() => props.map, (newMap) => {
  if (!newMap) return
  if (measureLayer) {
    stopMeasure()
    measureLayer = null
    measureSource = null
  }
})

onBeforeUnmount(() => {
  stopMeasure()
  if (measureLayer && props.map) {
    getRawMap().removeLayer(measureLayer)
    measureLayer = null
    measureSource = null
  }
})

defineExpose({
  activeType,
  clearMeasure,
  stopMeasure
})
</script>

<style scoped>
.measure-tool {
  display: flex;
  gap: 6px;
}
</style>

<style>
/* 测量结果提示（挂载到 body） */
.measure-tip {
  position: fixed;
  z-index: 9998;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e6a23c;
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

/* 测量右键菜单 */
.measure-context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  min-width: 110px;
  user-select: none;
}

.mctx-item {
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
}

.mctx-item:hover {
  background: #f5f7fa;
}

.mctx-confirm {
  color: #409eff;
  font-weight: 500;
  border-bottom: 1px solid #f0f2f5;
}

.mctx-cancel {
  color: #f56c6c;
}
</style>
