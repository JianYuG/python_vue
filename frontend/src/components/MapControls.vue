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
import { ref, watch, defineExpose, markRaw, onBeforeUnmount } from 'vue'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import WKT from 'ol/format/WKT'
import { Style, Fill, Stroke, Circle as CircleStyle } from 'ol/style'
import Modify from 'ol/interaction/Modify'
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
})

// 暴露 initLayers/reloadLayers/deselectFeature 供父组件调用
defineExpose({ initLayers, reloadLayers, deselectFeature })
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
