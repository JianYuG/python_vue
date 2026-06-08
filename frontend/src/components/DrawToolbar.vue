<template>
  <div class="draw-toolbar">
    <el-tooltip content="绘制点" placement="bottom">
      <el-button
        :type="activeType === 'Point' ? 'primary' : 'default'"
        :icon="Location"
        circle
        @click="toggleDraw('Point')"
      />
    </el-tooltip>
    <el-tooltip content="绘制线" placement="bottom">
      <el-button
        :type="activeType === 'LineString' ? 'primary' : 'default'"
        :icon="Minus"
        circle
        @click="toggleDraw('LineString')"
      />
    </el-tooltip>
    <el-tooltip content="绘制面" placement="bottom">
      <el-button
        :type="activeType === 'Polygon' ? 'primary' : 'default'"
        :icon="Grid"
        circle
        @click="toggleDraw('Polygon')"
      />
    </el-tooltip>
    <el-tooltip content="取消绘制" placement="bottom">
      <el-button
        :disabled="!activeType"
        :icon="CloseBold"
        circle
        @click="cancelDraw"
      />
    </el-tooltip>
  </div>

  <!-- 右键菜单 -->
  <teleport to="body">
    <div
      v-if="contextMenu.visible"
      class="draw-context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div class="ctx-item ctx-confirm" @click="onContextConfirm">✓ 确定</div>
      <div class="ctx-item ctx-cancel" @click="onContextCancel">✕ 取消</div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, reactive, watch, onBeforeUnmount, toRaw } from 'vue'
import { Location, Minus, Grid, CloseBold } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import Draw from 'ol/interaction/Draw'
import VectorSource from 'ol/source/Vector'
import VectorLayer from 'ol/layer/Vector'
import WKT from 'ol/format/WKT'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import DoubleClickZoom from 'ol/interaction/DoubleClickZoom'

const props = defineProps({
  map: { type: Object, default: null }
})

const emit = defineEmits(['draw-end'])

const activeType = ref(null)

// 右键菜单状态
const contextMenu = reactive({ visible: false, x: 0, y: 0 })

// 绘制用的矢量图层（显示已绘制要素草稿）
let drawSource = null
let drawLayer = null
let drawInteraction = null
let dblClickZoomInteraction = null  // 缓存 DoubleClickZoom 交互器引用
let _contextHandler = null  // 右键事件处理器
let _pointerdownHandler = null  // pointerdown 拦截处理器
let _pendingContextCount = -1  // 右键按下时缓存的点位数

/**
 * 将 OL Feature 转为 WKT 字符串
 */
function geojsonToWkt(olFeature) {
  const format = new WKT()
  return format.writeFeature(olFeature)
}

function getRawMap() {
  return toRaw(props.map)
}

function ensureDrawLayer() {
  if (drawLayer) return
  drawSource = new VectorSource()
  drawLayer = new VectorLayer({
    source: drawSource,
    style: new Style({
      fill: new Fill({ color: 'rgba(64,158,255,0.15)' }),
      stroke: new Stroke({ color: '#409eff', width: 2 }),
      image: new CircleStyle({
        radius: 6,
        fill: new Fill({ color: '#409eff' }),
        stroke: new Stroke({ color: '#fff', width: 1.5 })
      })
    }),
    zIndex: 100
  })
  getRawMap().addLayer(drawLayer)
}

/**
 * 禁用 DoubleClickZoom 交互器，防止绘制结束时地图放大
 */
function disableDblClickZoom() {
  const rawMap = getRawMap()
  rawMap.getInteractions().forEach(interaction => {
    if (interaction instanceof DoubleClickZoom) {
      dblClickZoomInteraction = interaction
      interaction.setActive(false)
    }
  })
}

/**
 * 恢复 DoubleClickZoom 交互器
 */
function enableDblClickZoom() {
  if (dblClickZoomInteraction) {
    dblClickZoomInteraction.setActive(true)
    dblClickZoomInteraction = null
  }
}

/**
 * 关闭右键菜单
 */
/**
 * 获取当前已画的有效点位数
 * 直接从 Draw 交互器的 sketchCoords_ 内部属性读取，比解析几何类型更可靠
 * - LineString: sketchCoords_ = [coord1, coord2, ..., mouseFollow]
 * - Polygon: sketchCoords_ = [[ringCoord1, ringCoord2, ..., mouseFollow]]
 * 实际已确认点数 = 坐标数 - 1（减去鼠标跟随点）
 */
function getDrawnPointCount() {
  if (!drawInteraction) return 0
  try {
    const coords = drawInteraction.sketchCoords_
    if (!coords) return 0
    if (activeType.value === 'LineString') {
      return Math.max(0, coords.length - 1)
    } else if (activeType.value === 'Polygon') {
      // Polygon 的 sketchCoords_ 是嵌套数组 [[ring]]
      if (Array.isArray(coords[0])) {
        return Math.max(0, coords[0].length - 1)
      }
      return Math.max(0, coords.length - 1)
    }
  } catch (e) {
    console.warn('getDrawnPointCount error:', e)
  }
  return 0
}

/**
 * 当前绘制类型所需最少点位数
 */
function getMinPoints() {
  if (activeType.value === 'LineString') return 2
  if (activeType.value === 'Polygon') return 3
  return 0
}

function closeContextMenu() {
  contextMenu.visible = false
}

/**
 * 绑定右键菜单事件（仅线面绘制时）
 */
function bindContextMenu() {
  const el = getRawMap().getTargetElement()

  // ★ capture 阶段拦截右键 pointerdown，阻止 OL 把该点加入草稿
  // 只用 stopPropagation，不用 preventDefault（否则会阻止 contextmenu 事件触发）
  _pointerdownHandler = (e) => {
    if (e.button !== 2) return
    _pendingContextCount = getDrawnPointCount()
    e.stopPropagation()
  }
  el.addEventListener('pointerdown', _pointerdownHandler, { capture: true })

  // contextmenu 读取 pointerdown 时缓存的点位数判断是否显示菜单
  _contextHandler = (e) => {
    e.preventDefault()
    const count = _pendingContextCount
    _pendingContextCount = -1
    if (count < getMinPoints()) {
      const need = getMinPoints()
      const typeName = activeType.value === 'LineString' ? '线' : '面'
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

/**
 * 移除右键事件
 */
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

/**
 * 右键菜单 - 确定：结束绘制
 */
function onContextConfirm() {
  closeContextMenu()
  if (drawInteraction) {
    drawInteraction.finishDrawing()
  }
}

/**
 * 右键菜单 - 取消：清除当前图形重新绘制
 */
function onContextCancel() {
  closeContextMenu()
  const type = activeType.value
  cancelDraw()
  if (type) {
    // 重新进入相同类型绘制
    setTimeout(() => toggleDraw(type), 0)
  }
}

/**
 * 切换绘制模式：同类型再点击则取消
 */
function toggleDraw(type) {
  if (activeType.value === type) {
    cancelDraw()
    return
  }
  cancelDraw()
  if (!props.map) return

  ensureDrawLayer()
  activeType.value = type

  // 绘制线面时禁用双击放大并绑定右键菜单
  disableDblClickZoom()
  if (type !== 'Point') {
    bindContextMenu()
  }

  drawInteraction = new Draw({
    source: drawSource,
    type: type
  })

  drawInteraction.on('drawend', (event) => {
    const wkt = geojsonToWkt(event.feature)
    const typeCode = { Point: 1, LineString: 2, Polygon: 3 }[type]
    emit('draw-end', { type: typeCode, geometry: wkt })
    stopDraw()
  })

  getRawMap().addInteraction(drawInteraction)
}

/**
 * 停止绘制交互但不清除图形
 */
function stopDraw() {
  unbindContextMenu()
  enableDblClickZoom()
  if (drawInteraction && props.map) {
    getRawMap().removeInteraction(drawInteraction)
    drawInteraction = null
  }
  activeType.value = null
}

/**
 * 取消绘制并清除当前草稿
 */
function cancelDraw() {
  stopDraw()
  if (drawSource) {
    drawSource.clear()
  }
}

// map prop 变化时重新初始化
watch(() => props.map, (newMap) => {
  if (!newMap) return
  if (drawLayer) {
    cancelDraw()
    drawLayer = null
    drawSource = null
  }
})

onBeforeUnmount(() => {
  cancelDraw()
  if (drawLayer && props.map) {
    getRawMap().removeLayer(drawLayer)
  }
})

// 暴露给父组件
defineExpose({
  clearAll: () => {
    stopDraw()
    if (drawSource) drawSource.clear()
  },
  deactivate: () => stopDraw()
})
</script>

<style scoped>
.draw-toolbar {
  display: flex;
  gap: 6px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 6px 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>

<style>
/* 右键菜单（挂载到 body，不能用 scoped） */
.draw-context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  min-width: 110px;
  user-select: none;
}

.ctx-item {
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
}

.ctx-item:hover {
  background: #f5f7fa;
}

.ctx-confirm {
  color: #409eff;
  font-weight: 500;
  border-bottom: 1px solid #f0f2f5;
}

.ctx-cancel {
  color: #f56c6c;
}
</style>
