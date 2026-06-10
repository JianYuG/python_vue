<template>
  <div class="map-controls">
    <!-- 放大按钮 -->
    <button class="ctrl-btn" title="放大" @click="zoomIn">
      <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
        <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
      </svg>
    </button>

    <!-- 缩小按钮 -->
    <button class="ctrl-btn" title="缩小" @click="zoomOut">
      <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
        <path fill-rule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
      </svg>
    </button>

    <!-- 区域绘制按钮 -->
    <button
      class="ctrl-btn"
      :class="{ active: areaDrawActive }"
      title="区域绘制"
      @click="toggleAreaDrawMenu"
    >
      <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
        <path d="M3 5v14h18V5H3zm16 12H5V7h14v10z"/>
        <path d="M7 9h4v4H7zm6 0h4v4h-4z" opacity="0.5"/>
      </svg>
    </button>

    <!-- 导出全图按钮 -->
    <button class="ctrl-btn" title="导出全图" @click="exportFullMap">
      <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
        <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
      </svg>
    </button>

    <!-- 区域绘制下拉菜单 -->
    <transition name="menu-fade">
      <div v-if="areaDrawMenuVisible" class="area-draw-menu">
        <div class="adm-item" @click="startAreaDraw('Polygon')">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path d="M4 4l6 12L20 4z" opacity="0.5"/><path d="M3 3l7 14L21 3" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          <span>多边形</span>
        </div>
        <div class="adm-item" @click="startAreaDraw('Box')">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><rect x="3" y="5" width="14" height="10" fill="none" stroke="currentColor" stroke-width="2" rx="1"/></svg>
          <span>矩形</span>
        </div>
        <div class="adm-item" @click="startAreaDraw('Circle')">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          <span>圆形</span>
        </div>
        <div v-if="areaDrawActive" class="adm-divider"></div>
        <div v-if="areaDrawActive" class="adm-item adm-export" @click="exportMapImage">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path d="M3 17h14v-2H3v2zm4-6l3 3 3-3h-2V3H9v8H7z"/></svg>
          <span>导出图片</span>
        </div>
        <div v-if="areaDrawActive" class="adm-item adm-clear" @click="clearAreaDraw">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
          <span>清除绘制</span>
        </div>
      </div>
    </transition>

    <!-- 查询按钮 -->
    <button
      class="ctrl-btn"
      :class="{ active: queryMode }"
      title="点击查询（开启/关闭）"
      @click="toggleQueryMode"
    >
      <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
        <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
      </svg>
    </button>

    <!-- 编辑按钮 -->
    <button
      class="ctrl-btn"
      :class="{ active: editMode }"
      title="编辑要素（开启/关闭）"
      @click="toggleEditMode"
    >
      <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
        <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
      </svg>
    </button>

    <!-- 图层控制按钮 -->
    <button
      class="ctrl-btn"
      :class="{ active: layerPanelVisible }"
      title="图层控制"
      @click="toggleLayerPanel"
    >
      <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
        <path d="M3 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 5a1 1 0 000 2h14a1 1 0 100-2H3zm0 5a1 1 0 000 2h14a1 1 0 100-2H3z"/>
      </svg>
    </button>

    <!-- 图层控制面板 -->
    <transition name="panel-slide">
      <div v-if="layerPanelVisible" class="layer-panel">
        <div class="panel-header">
          <span class="panel-title">图层控制</span>
          <button class="close-btn" @click="layerPanelVisible = false">×</button>
        </div>
        <div class="panel-body">
          <div v-if="loading" class="panel-loading">加载中...</div>
          <div v-else-if="layers.length === 0" class="panel-empty">暂无要素数据</div>
          <template v-else>
            <div
              v-for="layer in layers"
              :key="layer.type"
              class="layer-item"
            >
              <label class="layer-label">
                <input
                  type="checkbox"
                  :checked="layer.visible"
                  @change="toggleLayer(layer)"
                />
                <span
                  class="layer-icon"
                  :style="{ background: layer.color }"
                ></span>
                <span class="layer-name">{{ layer.label }}</span>
                <span class="layer-count">{{ layer.features.length }}</span>
              </label>
            </div>
          </template>
        </div>
      </div>
    </transition>
  </div>

  <!-- 编辑模式右键菜单 -->
  <teleport to="body">
    <div
      v-if="editContextMenu.visible"
      class="edit-context-menu"
      :style="{ left: editContextMenu.x + 'px', top: editContextMenu.y + 'px' }"
    >
      <div class="ectx-item ectx-edit" @click="onCtxEditProps">编辑属性</div>
      <div class="ectx-item ectx-save" @click="onCtxSave">保存</div>
      <div class="ectx-item ectx-delete" @click="onCtxDelete">删除</div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch, defineExpose, markRaw, onBeforeUnmount, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { toPng } from 'html-to-image'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import WKT from 'ol/format/WKT'
import Draw, { createBox } from 'ol/interaction/Draw'
import Modify from 'ol/interaction/Modify'
import { Style, Fill, Stroke, Circle as CircleStyle, RegularShape } from 'ol/style'
import Polygon from 'ol/geom/Polygon'
import Circle from 'ol/geom/Circle'
import Point from 'ol/geom/Point'
import LineString from 'ol/geom/LineString'
import { getArea, getLength } from 'ol/sphere'
import { transform } from 'ol/proj'
import { getWidth, getHeight } from 'ol/extent'
import { getAllFeatures } from '../api/feature'

// ★ OL 对象放在 setup 之外（模块级），完全脱离 Vue 响应式追踪
const _wktFormat = markRaw(new WKT())
const _olLayers = {} // type → VectorLayer 映射

// 模块级要素属性缓存（id → featureData）
const _featureMap = {}

const props = defineProps({
  map: { type: Object, default: null }
})

const emit = defineEmits(['feature-click', 'feature-close', 'edit-props', 'edit-save', 'edit-delete'])

// ============ 区域绘制逻辑 ============
const areaDrawMenuVisible = ref(false)
const areaDrawActive = ref(false)
let _areaDrawInteraction = null
let _areaModifyInteraction = null
let _areaSource = null
let _areaLayer = null
let _areaDrawType = null   // 记录当前绘制类型: 'Box' / 'Polygon' / 'Circle'
let _edgeDragHandler = null  // 矩形边拖拽事件

/** 区域绘制样式 */
const AREA_DRAW_STYLE = new Style({
  fill: new Fill({ color: 'rgba(64,158,255,0.15)' }),
  stroke: new Stroke({ color: '#409eff', width: 2, lineDash: [6, 4] })
})

/** 矩形边中点样式（4条边的中点标记，用于拖拽调整） */
const AREA_EDGE_STYLE = new Style({
  image: new RegularShape({
    points: 4,
    radius: 6,
    radius2: 0,
    fill: new Fill({ color: '#fff' }),
    stroke: new Stroke({ color: '#409eff', width: 2 }),
    angle: 0
  })
})

const AREA_VERTEX_STYLE = new Style({
  image: new CircleStyle({
    radius: 5,
    fill: new Fill({ color: '#409eff' }),
    stroke: new Stroke({ color: '#fff', width: 2 })
  })
})

function areaStyleFunction(feature) {
  return [AREA_DRAW_STYLE, AREA_VERTEX_STYLE]
}

/** 矩形专用样式：边框 + 角点 + 边中点 */
function boxStyleFunction(feature) {
  const styles = [AREA_DRAW_STYLE, AREA_VERTEX_STYLE]
  // 如果是已完成的矩形（4个顶点），在每条边中点添加拖拽手柄
  const geom = feature.getGeometry()
  if (geom && geom.getType() === 'Polygon') {
    const coords = geom.getCoordinates()[0]
    if (coords && coords.length >= 5) {
      // 4条边的中点：top, right, bottom, left
      const midpoints = [
        [(coords[0][0] + coords[1][0]) / 2, (coords[0][1] + coords[1][1]) / 2], // top
        [(coords[1][0] + coords[2][0]) / 2, (coords[1][1] + coords[2][1]) / 2], // right
        [(coords[2][0] + coords[3][0]) / 2, (coords[2][1] + coords[3][1]) / 2], // bottom
        [(coords[3][0] + coords[0][0]) / 2, (coords[3][1] + coords[0][1]) / 2]  // left
      ]
      midpoints.forEach((pt, idx) => {
        const s = new Style({
          geometry: new Point(pt),
          image: new RegularShape({
            points: 4,
            radius: 7,
            radius2: 0,
            fill: new Fill({ color: '#fff' }),
            stroke: new Stroke({ color: '#e6a23c', width: 2 }),
            angle: idx % 2 === 0 ? Math.PI / 4 : 0  // 上下=菱形, 左右=菱形
          })
        })
        styles.push(s)
      })
    }
  }
  return styles
}

function toggleAreaDrawMenu() {
  areaDrawMenuVisible.value = !areaDrawMenuVisible.value
}

/** 开始绘制指定类型的区域 */
function startAreaDraw(type) {
  if (!props.map) return
  areaDrawMenuVisible.value = false

  // 先清除上一次的绘制交互
  cleanupAreaDrawInteraction()

  // 确保有区域矢量图层
  if (!_areaLayer) {
    _areaSource = markRaw(new VectorSource())
    _areaLayer = markRaw(new VectorLayer({
      source: _areaSource,
      style: areaStyleFunction,
      zIndex: 60
    }))
    props.map.addLayer(_areaLayer)
  }

  // 记录绘制类型
  _areaDrawType = type

  // OpenLayers Draw 类型映射
  let olType
  if (type === 'Box') {
    olType = 'Circle' // 矩形用 Circle 交互 + createBox 几何函数
  } else if (type === 'Polygon') {
    olType = 'Polygon'
  } else {
    olType = 'Circle'
  }

  const drawOpts = {
    source: _areaSource,
    type: olType,
    style: AREA_DRAW_STYLE
  }

  // 矩形：用 Circle 交互 + createBox() 几何函数
  if (type === 'Box') {
    drawOpts.geometryFunction = createBox()
  }

  _areaDrawInteraction = markRaw(new Draw(drawOpts))

  _areaDrawInteraction.on('drawend', (evt) => {
    // 绘制完成
    areaDrawActive.value = true
    const drawType = type
    // 先移除 Draw 交互，否则会和 Modify 冲突
    setTimeout(() => {
      cleanupAreaDrawInteraction()
      if (drawType === 'Box') {
        // 矩形：使用自定义边拖拽交互
        _areaLayer.setStyle(boxStyleFunction)
        attachBoxEdgeModify()
      } else {
        // 多边形/圆形：使用标准 Modify
        attachAreaModify()
      }
      // 恢复默认光标
      if (props.map) props.map.getTargetElement().style.cursor = ''
    }, 100)
  })

  props.map.addInteraction(_areaDrawInteraction)
  props.map.getTargetElement().style.cursor = 'crosshair'
  ElMessage.info(`请在地图上绘制${type === 'Box' ? '矩形' : type === 'Polygon' ? '多边形' : '圆形'}区域`)
}

/** 为区域绘制图层挂载 Modify 交互（多边形/圆形用） */
function attachAreaModify() {
  if (!_areaSource || !props.map) return
  cleanupAreaModify()
  _areaModifyInteraction = markRaw(new Modify({
    source: _areaSource,
    style: AREA_VERTEX_STYLE
  }))
  props.map.addInteraction(_areaModifyInteraction)
}

/**
 * 矩形边拖拽交互
 * 拖拽矩形四条边整体移动，保持矩形形状
 * 边中点手柄标识：上(0)、右(1)、下(2)、左(3)
 */
function attachBoxEdgeModify() {
  if (!_areaSource || !props.map) return
  cleanupBoxEdgeModify()

  const map = props.map
  let dragging = false
  let dragEdge = -1       // 0=top, 1=right, 2=bottom, 3=left
  let startPixel = null
  let startCoords = null  // 矩形初始坐标

  // pointerdown：检测并开始拖拽
  const onPointerDown = function (evt) {
    if (dragging) return
    const features = _areaSource.getFeatures()
    if (!features.length) return
    const feature = features[features.length - 1]
    const geom = feature.getGeometry()
    if (!geom || geom.getType() !== 'Polygon') return

    const pixel = evt.pixel
    const coords = geom.getCoordinates()[0]
    if (!coords || coords.length < 5) return

    const midpoints = [
      [(coords[0][0] + coords[1][0]) / 2, (coords[0][1] + coords[1][1]) / 2], // top
      [(coords[1][0] + coords[2][0]) / 2, (coords[1][1] + coords[2][1]) / 2], // right
      [(coords[2][0] + coords[3][0]) / 2, (coords[2][1] + coords[3][1]) / 2], // bottom
      [(coords[3][0] + coords[0][0]) / 2, (coords[3][1] + coords[0][1]) / 2]  // left
    ]

    // 检查是否点击了边中点区域（12像素容差）
    for (let i = 0; i < midpoints.length; i++) {
      const midPixel = map.getPixelFromCoordinate(midpoints[i])
      if (!midPixel) continue
      const dx = pixel[0] - midPixel[0]
      const dy = pixel[1] - midPixel[1]
      if (Math.sqrt(dx * dx + dy * dy) < 12) {
        dragging = true
        dragEdge = i
        startPixel = pixel.slice()
        startCoords = coords.map(c => c.slice())
        evt.stopPropagation()
        return
      }
    }

    // 检查是否靠近边线（6像素容差）
    for (let i = 0; i < 4; i++) {
      const p1 = coords[i]
      const p2 = coords[i + 1]
      const p1Px = map.getPixelFromCoordinate(p1)
      const p2Px = map.getPixelFromCoordinate(p2)
      if (!p1Px || !p2Px) continue
      const dist = pointToSegmentDist(pixel[0], pixel[1], p1Px[0], p1Px[1], p2Px[0], p2Px[1])
      if (dist < 6) {
        dragging = true
        dragEdge = i
        startPixel = pixel.slice()
        startCoords = coords.map(c => c.slice())
        evt.stopPropagation()
        return
      }
    }
  }

  // pointermove：拖拽中更新矩形
  const onPointerMove = function (evt) {
    if (!dragging) return
    const features = _areaSource.getFeatures()
    if (!features.length) return
    const feature = features[features.length - 1]
    const geom = feature.getGeometry()
    if (!geom || geom.getType() !== 'Polygon') return

    const coord = evt.coordinate
    const dx = coord[0] - map.getCoordinateFromPixel(startPixel)[0]
    const dy = coord[1] - map.getCoordinateFromPixel(startPixel)[1]
    const newCoords = startCoords.map(c => c.slice())

    switch (dragEdge) {
      case 0: // top边：移动 vertex[0] 和 vertex[1] 的 y
        newCoords[0][1] = startCoords[0][1] + dy
        newCoords[1][1] = startCoords[1][1] + dy
        break
      case 1: // right边：移动 vertex[1] 和 vertex[2] 的 x
        newCoords[1][0] = startCoords[1][0] + dx
        newCoords[2][0] = startCoords[2][0] + dx
        break
      case 2: // bottom边：移动 vertex[2] 和 vertex[3] 的 y
        newCoords[2][1] = startCoords[2][1] + dy
        newCoords[3][1] = startCoords[3][1] + dy
        break
      case 3: // left边：移动 vertex[3] 和 vertex[0] 的 x
        newCoords[3][0] = startCoords[3][0] + dx
        newCoords[0][0] = startCoords[0][0] + dx
        break
    }
    newCoords[4] = newCoords[0].slice()
    geom.setCoordinates([newCoords])
    feature.changed()
  }

  // 结束拖拽
  const stopDrag = function () {
    if (dragging) {
      dragging = false
      dragEdge = -1
      startPixel = null
      startCoords = null
    }
  }

  map.on('pointerdown', onPointerDown)
  map.on('pointermove', onPointerMove)
  map.on('pointerup', stopDrag)
  // 鼠标离开地图区域也要能释放
  document.addEventListener('mouseup', stopDrag)

  // 保存清理引用
  _edgeDragCleanup = () => {
    map.un('pointerdown', onPointerDown)
    map.un('pointermove', onPointerMove)
    map.un('pointerup', stopDrag)
    document.removeEventListener('mouseup', stopDrag)
  }
}

let _edgeDragCleanup = null

function cleanupBoxEdgeModify() {
  if (_edgeDragCleanup) {
    _edgeDragCleanup()
    _edgeDragCleanup = null
  }
  _edgeDragHandler = null
}

/** 点到线段的距离 */
function pointToSegmentDist(px, py, x1, y1, x2, y2) {
  const A = px - x1
  const B = py - y1
  const C = x2 - x1
  const D = y2 - y1
  const dot = A * C + B * D
  const lenSq = C * C + D * D
  let param = lenSq !== 0 ? dot / lenSq : -1
  param = Math.max(0, Math.min(1, param))
  const xx = x1 + param * C
  const yy = y1 + param * D
  return Math.sqrt((px - xx) * (px - xx) + (py - yy) * (py - yy))
}

/** 清除绘制交互（保留图层和 Modify） */
function cleanupAreaDrawInteraction() {
  if (_areaDrawInteraction && props.map) {
    props.map.removeInteraction(_areaDrawInteraction)
    _areaDrawInteraction = null
  }
}

/** 清除 Modify 交互 */
function cleanupAreaModify() {
  if (_areaModifyInteraction && props.map) {
    props.map.removeInteraction(_areaModifyInteraction)
    _areaModifyInteraction = null
  }
}

/** 清除全部区域绘制 */
function clearAreaDraw() {
  cleanupAreaDrawInteraction()
  cleanupAreaModify()
  cleanupBoxEdgeModify()
  if (_areaSource) _areaSource.clear()
  // 恢复默认样式
  if (_areaLayer) _areaLayer.setStyle(areaStyleFunction)
  areaDrawActive.value = false
  areaDrawMenuVisible.value = false
  _areaDrawType = null
  if (props.map) props.map.getTargetElement().style.cursor = ''
  ElMessage.success('已清除绘制区域')
}

/** 截图导出：将绘制区域范围内的地图画面（所见即所得）保存为图片
 *  矩形：直接裁剪矩形区域
 *  圆形/多边形：先用 canvas clip 按实际形状裁剪，导出对应形状的图片
 */
async function exportMapImage() {
  if (!props.map) return
  areaDrawMenuVisible.value = false

  if (!_areaSource || _areaSource.getFeatures().length === 0) {
    ElMessage.warning('请先绘制一个区域再导出')
    return
  }

  try {
    const map = props.map
    const drawFeature = _areaSource.getFeatures()[_areaSource.getFeatures().length - 1]
    const drawGeom = drawFeature.getGeometry()
    const drawExtent = drawGeom.getExtent()

    // 计算绘制区域的像素范围（包围盒）
    const bl = map.getPixelFromCoordinate([drawExtent[0], drawExtent[1]])
    const tr = map.getPixelFromCoordinate([drawExtent[2], drawExtent[3]])
    if (!bl || !tr) { ElMessage.error('无法获取区域坐标'); return }

    const pr = window.devicePixelRatio || 1
    const sx = Math.round(Math.min(bl[0], tr[0]) * pr)
    const sy = Math.round(Math.min(bl[1], tr[1]) * pr)
    const sw = Math.round(Math.abs(tr[0] - bl[0]) * pr)
    const sh = Math.round(Math.abs(tr[1] - bl[1]) * pr)
    if (sw <= 0 || sh <= 0) { ElMessage.error('绘制区域过小'); return }

    // 隐藏绘制框，截图不应包含选择框
    if (_areaLayer) _areaLayer.setVisible(false)
    map.renderSync()

    // OL 为每个图层创建独立的 canvas，需要合并所有 canvas
    const mapEl = map.getTargetElement()
    const allCanvases = mapEl.querySelectorAll('canvas')

    // 先合并所有图层 canvas 到一个完整的地图 canvas
    const mergedCanvas = document.createElement('canvas')
    mergedCanvas.width = mapEl.offsetWidth * pr
    mergedCanvas.height = mapEl.offsetHeight * pr
    const mergedCtx = mergedCanvas.getContext('2d')

    let useHtmlToImage = false
    for (const srcCanvas of allCanvases) {
      try {
        mergedCtx.drawImage(srcCanvas, 0, 0, mergedCanvas.width, mergedCanvas.height)
      } catch (e) {
        console.warn('canvas 合并失败，使用 html-to-image 兜底:', e)
        useHtmlToImage = true
        break
      }
    }

    // 兜底方案：html-to-image 截取整个地图 DOM
    if (useHtmlToImage) {
      const fullDataUrl = await toPng(mapEl, {
        quality: 1,
        pixelRatio: pr,
        width: mapEl.offsetWidth,
        height: mapEl.offsetHeight
      })
      const img = new Image()
      await new Promise((resolve, reject) => {
        img.onload = resolve
        img.onerror = reject
        img.src = fullDataUrl
      })
      mergedCtx.drawImage(img, 0, 0, mergedCanvas.width, mergedCanvas.height)
    }

    // 创建裁剪 canvas
    const clipCanvas = document.createElement('canvas')
    clipCanvas.width = sw
    clipCanvas.height = sh
    const ctx = clipCanvas.getContext('2d')

    // 根据绘制类型决定裁剪方式
    const geomType = drawGeom.getType()

    if (geomType === 'Circle') {
      // 圆形：用椭圆 clip 路径裁剪
      const center = drawGeom.getCenter()
      const radius = drawGeom.getRadius()
      // 圆心像素坐标
      const centerPx = map.getPixelFromCoordinate(center)
      // 圆半径在像素上的映射（取 x 方向和 y 方向的半径）
      const edgeCoord = [center[0] + radius, center[1]]
      const edgePx = map.getPixelFromCoordinate(edgeCoord)
      const rx = Math.abs(edgePx[0] - centerPx[0]) * pr  // x方向像素半径
      const ry = Math.abs(edgePx[1] - centerPx[1]) * pr   // 暂用x方向近似（地理投影下圆可能呈椭圆）
      // 由于投影变形，圆在屏幕上可能呈椭圆，需要同时计算y方向半径
      const edgeCoordY = [center[0], center[1] + radius]
      const edgePxY = map.getPixelFromCoordinate(edgeCoordY)
      const ryActual = Math.abs(edgePxY[1] - centerPx[1]) * pr
      // 圆心在裁剪 canvas 上的相对位置
      const cx = (centerPx[0] * pr) - sx
      const cy = (centerPx[1] * pr) - sy

      ctx.beginPath()
      ctx.ellipse(cx, cy, rx, ryActual, 0, 0, Math.PI * 2)
      ctx.clip()
      ctx.drawImage(mergedCanvas, sx, sy, sw, sh, 0, 0, sw, sh)
    } else if (geomType === 'Polygon' && _areaDrawType === 'Polygon') {
      // 多边形（非矩形）：用多边形 clip 路径裁剪
      const coords = drawGeom.getCoordinates()[0] // 外环坐标
      ctx.beginPath()
      coords.forEach((coord, i) => {
        const px = map.getPixelFromCoordinate(coord)
        if (!px) return
        // 转换为裁剪 canvas 上的相对坐标
        const x = px[0] * pr - sx
        const y = px[1] * pr - sy
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.closePath()
      ctx.clip()
      ctx.drawImage(mergedCanvas, sx, sy, sw, sh, 0, 0, sw, sh)
    } else {
      // 矩形或 Box：直接裁剪矩形区域（无需 clip 路径）
      ctx.drawImage(mergedCanvas, sx, sy, sw, sh, 0, 0, sw, sh)
    }

    if (_areaLayer) _areaLayer.setVisible(true)
    const dataUrl = clipCanvas.toDataURL('image/png')
    downloadDataUrl(dataUrl)
  } catch (e) {
    console.error('导出失败:', e)
    if (_areaLayer) _areaLayer.setVisible(true)
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  }
}

/** 下载 dataUrl 为 PNG 文件 */
function downloadDataUrl(dataUrl) {
  const link = document.createElement('a')
  const ts = new Date().toLocaleString().replace(/[/\s]/g, '_').replace(/:/g, '')
  link.download = `地图导出_${ts}.png`
  link.href = dataUrl
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('地图已导出为图片')
}

/** 导出全图：将当前窗口中的整个地图（所见即所得）保存为图片 */
async function exportFullMap() {
  if (!props.map) return
  try {
    const map = props.map
    map.renderSync()

    const mapEl = map.getTargetElement()
    const pr = window.devicePixelRatio || 1
    const w = mapEl.offsetWidth * pr
    const h = mapEl.offsetHeight * pr

    // 合并所有图层 canvas
    const allCanvases = mapEl.querySelectorAll('canvas')
    let exported = false

    if (allCanvases.length > 0) {
      try {
        const fullCanvas = document.createElement('canvas')
        fullCanvas.width = w
        fullCanvas.height = h
        const ctx = fullCanvas.getContext('2d')
        for (const srcCanvas of allCanvases) {
          ctx.drawImage(srcCanvas, 0, 0, w, h, 0, 0, w, h)
        }
        const dataUrl = fullCanvas.toDataURL('image/png')
        downloadDataUrl(dataUrl)
        exported = true
      } catch (e) {
        console.warn('canvas 合并导出失败，使用 html-to-image 兜底:', e)
      }
    }

    // 兜底：html-to-image
    if (!exported) {
      const fullDataUrl = await toPng(mapEl, {
        quality: 1,
        pixelRatio: pr,
        width: mapEl.offsetWidth,
        height: mapEl.offsetHeight
      })
      downloadDataUrl(fullDataUrl)
    }
  } catch (e) {
    console.error('导出全图失败:', e)
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  }
}

// 点击其他区域关闭菜单
onMounted(() => {
  document.addEventListener('click', (e) => {
    if (areaDrawMenuVisible.value && !e.target.closest('.map-controls')) {
      areaDrawMenuVisible.value = false
    }
  })
})

// 图层面板显示状态
const layerPanelVisible = ref(false)
const loading = ref(false)

// 查询模式状态
const queryMode = ref(false)

// 编辑模式状态
const editMode = ref(false)
const editContextMenu = ref({ visible: false, x: 0, y: 0 })
let _selectedFeature = null       // 当前选中的 OL Feature
let _selectedFeatureData = null   // 当前选中的要素属性数据
let _modifyInteraction = null     // Modify 交互
let _editClickHandler = null      // 编辑模式点击事件
let _editContextHandler = null    // 编辑模式右键事件
let _editPointerdownHandler = null

// 选中要素的高亮样式
const _selectStyleCache = {}
function getSelectStyle(type) {
  if (_selectStyleCache[type]) return _selectStyleCache[type]
  const highlightColor = '#e6a23c'
  if (type === 1) {
    _selectStyleCache[type] = new Style({
      image: new CircleStyle({
        radius: 8,
        fill: new Fill({ color: highlightColor }),
        stroke: new Stroke({ color: '#fff', width: 2 })
      })
    })
  } else if (type === 2) {
    _selectStyleCache[type] = new Style({
      stroke: new Stroke({ color: highlightColor, width: 4 })
    })
  } else {
    _selectStyleCache[type] = new Style({
      fill: new Fill({ color: highlightColor + '55' }),
      stroke: new Stroke({ color: highlightColor, width: 3 })
    })
  }
  return _selectStyleCache[type]
}

// 图层配置：type 1=点 2=线 3=面
const LAYER_CONFIG = [
  { type: 1, label: '点要素', color: '#f56c6c' },
  { type: 2, label: '线要素', color: '#409eff' },
  { type: 3, label: '面要素', color: '#67c23a' }
]

// 图层状态列表（仅存轻量 UI 数据）
const layers = ref([])

// 类型标签
function typeLabel(type) {
  return { 1: '点要素', 2: '线要素', 3: '面要素' }[type] || '未知'
}

function makeStyle(type, color) {
  if (type === 1) {
    return new Style({
      image: new CircleStyle({
        radius: 6,
        fill: new Fill({ color }),
        stroke: new Stroke({ color: '#fff', width: 1.5 })
      })
    })
  } else if (type === 2) {
    return new Style({
      stroke: new Stroke({ color, width: 2.5 })
    })
  } else {
    return new Style({
      fill: new Fill({ color: color + '55' }),
      stroke: new Stroke({ color, width: 2 })
    })
  }
}

/**
 * 初始化图层并加载数据
 */
async function initLayers() {
  if (!props.map) return
  // 防止重复初始化
  if (layers.value.length > 0) return
  await loadLayers()
}

/**
 * 强制重新加载图层（保存新要素后调用）
 */
async function reloadLayers() {
  if (!props.map) return
  // 将旧图层从地图移除
  Object.keys(_olLayers).forEach(type => {
    props.map.removeLayer(_olLayers[type])
    delete _olLayers[type]
  })
  // 清空要素缓存
  Object.keys(_featureMap).forEach(k => delete _featureMap[k])
  // 重置 UI 状态
  layers.value = []
  await loadLayers()
}

/**
 * 内部：实际加载逻辑
 */
async function loadLayers() {
  loading.value = true
  try {
    const res = await getAllFeatures()
    const allFeatures = res.data || []

    layers.value = LAYER_CONFIG.map(cfg => {
      const features = allFeatures.filter(f => f.type === cfg.type)

      // ★ 用模块级 _wktFormat 解析，全程 markRaw 保护
      const olFeatures = features
        .map(f => {
          try {
            const geom = markRaw(_wktFormat.readGeometry(f.geometry))
            const olFeature = markRaw(new Feature({ geometry: geom }))
            olFeature.setId(f.id)
            // 缓存要素属性
            _featureMap[f.id] = f
            return olFeature
          } catch (e) {
            console.warn('WKT 解析失败:', f.geometry, e)
            return null
          }
        })
        .filter(Boolean)

      // 创建矢量图层
      const source = markRaw(new VectorSource({ features: olFeatures }))
      const layer = markRaw(new VectorLayer({
        source,
        style: makeStyle(cfg.type, cfg.color),
        zIndex: 10 + cfg.type
      }))
      props.map.addLayer(layer)
      _olLayers[cfg.type] = layer

      return {
        type: cfg.type,
        label: cfg.label,
        color: cfg.color,
        visible: true,
        features
      }
    })
  } catch (e) {
    console.error('加载要素图层失败:', e)
  } finally {
    loading.value = false
  }
}

/**
 * 切换图层显示/隐藏
 */
function toggleLayer(layer) {
  layer.visible = !layer.visible
  const olLayer = _olLayers[layer.type]
  if (olLayer) olLayer.setVisible(layer.visible)
}

/**
 * 地图点击回调（查询模式）
 */
let _clickHandler = null

function onMapClick(evt) {
  if (!props.map) return
  const hit = props.map.forEachFeatureAtPixel(
    evt.pixel,
    (feature) => feature,
    { hitTolerance: 6 }
  )
  if (hit) {
    const id = hit.getId()
    const data = _featureMap[id]
    if (data) {
      // 将像素坐标传给父组件定位弹框
      emit('feature-click', { data, pixel: evt.pixel })
    }
  } else {
    emit('feature-close')
  }
}

/**
 * 开启/关闭点击查询模式
 */
function toggleQueryMode() {
  queryMode.value = !queryMode.value
  if (!props.map) return
  // 关闭编辑模式
  if (queryMode.value && editMode.value) {
    toggleEditMode()
  }
  if (queryMode.value) {
    _clickHandler = onMapClick
    props.map.on('click', _clickHandler)
    // 开启查询时鼠标变十字
    props.map.getTargetElement().style.cursor = 'pointer'
  } else {
    if (_clickHandler) {
      props.map.un('click', _clickHandler)
      _clickHandler = null
    }
    emit('feature-close')
    props.map.getTargetElement().style.cursor = ''
  }
}

// ============ 编辑模式逻辑 ============

/**
 * 编辑模式下点击要素：选中 → 高亮 → 挂载 Modify 交互
 */
function onEditClick(evt) {
  if (!props.map) return
  closeEditContextMenu()

  const hit = props.map.forEachFeatureAtPixel(
    evt.pixel,
    (feature) => feature,
    { hitTolerance: 6 }
  )

  if (hit && hit.getId() != null) {
    selectFeature(hit)
  } else {
    deselectFeature()
  }
}

/**
 * 选中一个要素：高亮 + 挂载 Modify
 */
function selectFeature(olFeature) {
  // 如果点击了其他要素，先取消之前的选中
  if (_selectedFeature && _selectedFeature !== olFeature) {
    deselectFeature(false)
  }
  _selectedFeature = olFeature
  const id = olFeature.getId()
  _selectedFeatureData = _featureMap[id] || null

  // 高亮样式
  const featureType = _selectedFeatureData ? _selectedFeatureData.type : 1
  olFeature.setStyle(getSelectStyle(featureType))

  // 挂载 Modify 交互（支持点线面编辑）
  if (!_modifyInteraction) {
    const source = olFeature.getGeometry() ? getFeatureSource(olFeature) : null
    if (source) {
      _modifyInteraction = markRaw(new Modify({ source }))
      props.map.addInteraction(_modifyInteraction)
    }
  }
}

/**
 * 获取要素所在的 VectorSource
 */
function getFeatureSource(olFeature) {
  for (const type in _olLayers) {
    const layer = _olLayers[type]
    const source = layer.getSource()
    if (source && source.hasFeature(olFeature)) {
      return source
    }
  }
  // fallback: 如果 source 里没有（可能要素未同步），返回第一个图层 source
  for (const type in _olLayers) {
    return _olLayers[type].getSource()
  }
  return null
}

/**
 * 取消选中：还原样式 + 卸载 Modify
 */
function deselectFeature(clearMenu = true) {
  if (_selectedFeature && _selectedFeatureData) {
    // 还原原始样式
    const cfg = LAYER_CONFIG.find(c => c.type === _selectedFeatureData.type)
    if (cfg) {
      _selectedFeature.setStyle(makeStyle(cfg.type, cfg.color))
    }
  }
  _selectedFeature = null
  _selectedFeatureData = null

  // 卸载 Modify
  if (_modifyInteraction && props.map) {
    props.map.removeInteraction(_modifyInteraction)
    _modifyInteraction = null
  }
  if (clearMenu) {
    closeEditContextMenu()
  }
}

/**
 * 开启/关闭编辑模式
 */
function toggleEditMode() {
  editMode.value = !editMode.value
  if (!props.map) return
  // 关闭查询模式
  if (editMode.value && queryMode.value) {
    toggleQueryMode()
  }

  if (editMode.value) {
    // 绑定编辑模式事件
    _editClickHandler = onEditClick
    props.map.on('click', _editClickHandler)

    // 右键菜单
    const el = props.map.getTargetElement()
    _editPointerdownHandler = (e) => {
      if (e.button !== 2) return
      e.stopPropagation()
    }
    el.addEventListener('pointerdown', _editPointerdownHandler, { capture: true })

    _editContextHandler = (e) => {
      e.preventDefault()
      // 没有选中要素则不弹菜单
      if (!_selectedFeature) {
        return
      }
      editContextMenu.value = {
        visible: true,
        x: e.clientX,
        y: e.clientY
      }
    }
    el.addEventListener('contextmenu', _editContextHandler)
    document.addEventListener('click', closeEditContextMenu)

    props.map.getTargetElement().style.cursor = 'crosshair'
  } else {
    // 退出编辑模式：清理所有状态
    deselectFeature()
    if (_editClickHandler) {
      props.map.un('click', _editClickHandler)
      _editClickHandler = null
    }
    const el = props.map.getTargetElement()
    if (_editContextHandler) {
      el.removeEventListener('contextmenu', _editContextHandler)
      _editContextHandler = null
    }
    if (_editPointerdownHandler) {
      el.removeEventListener('pointerdown', _editPointerdownHandler, { capture: true })
      _editPointerdownHandler = null
    }
    document.removeEventListener('click', closeEditContextMenu)
    props.map.getTargetElement().style.cursor = ''
  }
}

function closeEditContextMenu() {
  editContextMenu.value = { visible: false, x: 0, y: 0 }
}

/**
 * 右键菜单 - 编辑属性
 */
function onCtxEditProps() {
  closeEditContextMenu()
  if (!_selectedFeatureData) return
  // 从 OL Feature 读取 Modify 后的最新 WKT，而非缓存中的原始 geometry
  const currentWkt = _selectedFeature
    ? _wktFormat.writeFeature(_selectedFeature)
    : _selectedFeatureData.geometry
  emit('edit-props', { data: { ..._selectedFeatureData, geometry: currentWkt } })
}

/**
 * 右键菜单 - 保存（几何数据）
 */
function onCtxSave() {
  closeEditContextMenu()
  if (!_selectedFeature || !_selectedFeatureData) return
  // 从 Modify 后的 Feature 获取最新 WKT
  const wkt = _wktFormat.writeFeature(_selectedFeature)
  emit('edit-save', {
    id: _selectedFeatureData.id,
    geometry: wkt
  })
}

/**
 * 右键菜单 - 删除
 */
function onCtxDelete() {
  closeEditContextMenu()
  if (!_selectedFeatureData) return
  emit('edit-delete', { id: _selectedFeatureData.id })
}

function toggleLayerPanel() {
  layerPanelVisible.value = !layerPanelVisible.value
}

/**
 * 放大
 */
function zoomIn() {
  if (!props.map) return
  const view = props.map.getView()
  view.animate({ zoom: view.getZoom() + 1, duration: 250 })
}

/**
 * 缩小
 */
function zoomOut() {
  if (!props.map) return
  const view = props.map.getView()
  view.animate({ zoom: view.getZoom() - 1, duration: 250 })
}

// 地图实例就绪时自动加载所有要素图层
watch(() => props.map, (val) => {
  if (val && layers.value.length === 0) {
    initLayers()
  }
}, { immediate: true })

// 组件销毁时清理地图点击监听
onBeforeUnmount(() => {
  if (_clickHandler && props.map) {
    props.map.un('click', _clickHandler)
    _clickHandler = null
  }
  if (editMode.value) {
    toggleEditMode()
  }
  // 清理区域绘制
  cleanupAreaDrawInteraction()
  cleanupAreaModify()
  cleanupBoxEdgeModify()
  if (_areaLayer && props.map) {
    props.map.removeLayer(_areaLayer)
    _areaLayer = null
    _areaSource = null
  }
})

// 暴露 initLayers/reloadLayers/deselectFeature 供父组件调用
defineExpose({ initLayers, reloadLayers, deselectFeature, clearAreaDraw })
</script>

<style scoped>
.map-controls {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
}

/* 控制按钮 */
.ctrl-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 6px;
  background: #fff;
  color: #333;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}

.ctrl-btn:hover {
  background: #ecf5ff;
  color: #409eff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
}

.ctrl-btn.active {
  background: #409eff;
  color: #fff;
  box-shadow: 0 3px 10px rgba(64, 158, 255, 0.4);
}

/* 图层面板 */
.layer-panel {
  position: absolute;
  right: 44px;
  bottom: 0;
  width: 190px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  z-index: 20;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.close-btn {
  border: none;
  background: none;
  font-size: 16px;
  color: #909399;
  cursor: pointer;
  line-height: 1;
  padding: 0 2px;
}

.close-btn:hover {
  color: #303133;
}

.panel-body {
  padding: 8px 0;
}

.panel-loading,
.panel-empty {
  padding: 12px 14px;
  font-size: 13px;
  color: #909399;
  text-align: center;
}

/* 图层条目 */
.layer-item {
  padding: 0;
}

.layer-label {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.layer-label:hover {
  background: #f5f7fa;
}

.layer-label input[type='checkbox'] {
  width: 14px;
  height: 14px;
  cursor: pointer;
  flex-shrink: 0;
  accent-color: #409eff;
}

.layer-icon {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.layer-name {
  flex: 1;
  font-size: 13px;
  color: #303133;
}

.layer-count {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 1px 6px;
  border-radius: 10px;
}

/* 面板滑入动画 */
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

/* 区域绘制下拉菜单 */
.area-draw-menu {
  position: absolute;
  right: 44px;
  bottom: 108px;
  min-width: 140px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  z-index: 25;
  user-select: none;
}

.adm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 13px;
  color: #303133;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f2f5;
}

.adm-item:last-child {
  border-bottom: none;
}

.adm-item:hover {
  background: #ecf5ff;
}

.adm-divider {
  height: 1px;
  background: #ebeef5;
  margin: 0 12px;
}

.adm-export {
  color: #67c23a !important;
  font-weight: 500;
}

.adm-clear {
  color: #f56c6c !important;
  font-weight: 500;
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

/* 详情面板 */
.detail-panel {
  position: absolute;
  right: 44px;
  bottom: 80px;
  width: 220px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  z-index: 20;
}

.detail-body {
  padding: 4px 0;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  padding: 6px 14px;
  border-bottom: 1px solid #f0f2f5;
  gap: 8px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  width: 56px;
  padding-top: 1px;
}

.detail-value {
  font-size: 13px;
  color: #303133;
  word-break: break-all;
  flex: 1;
}
</style>

<style>
/* 编辑模式右键菜单（挂载到 body，不能用 scoped） */
.edit-context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  min-width: 120px;
  user-select: none;
}

.ectx-item {
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f2f5;
}

.ectx-item:last-child {
  border-bottom: none;
}

.ectx-item:hover {
  background: #f5f7fa;
}

.ectx-edit {
  color: #409eff;
  font-weight: 500;
}

.ectx-save {
  color: #67c23a;
  font-weight: 500;
}

.ectx-delete {
  color: #f56c6c;
  font-weight: 500;
}
</style>
