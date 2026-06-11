<template>
  <div class="map-wrapper">
    <!-- 地图容器 -->
    <div ref="mapContainer" class="map-container"></div>

    <!-- 左上角：搜索面板 -->
    <div class="top-left">
      <SearchPanel @locate="onSearchLocate" @search-result="onSearchResult" @search-close="onSearchClose" @xzqh-locate="onXzqhLocate" />
    </div>

    <!-- 右上角：工具箱 -->
    <div class="top-right">
      <div class="toolbox-wrapper">
        <button class="toolbox-btn" title="工具箱" @click="toolboxVisible = !toolboxVisible">
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14.75.75 0 0 1-.14 1.49.74.74 0 0 1-.47-.17A8.5 8.5 0 1 0 20.5 12c0-.23 0-.45-.02-.67a.75.75 0 0 1 1.5-.08l.02.75zm-3.85-7.62a.75.75 0 0 1 .15 1.05l-5.5 7.5a.75.75 0 0 1-1.1.12l-3-2.5a.75.75 0 0 1 .96-1.15l2.38 1.98 5.06-6.9a.75.75 0 0 1 1.05-.1z"/>
            <path d="M4 4h4v4H4zm6 0h4v4h-4zm6 0h4v4h-4zM4 10h4v4H4zm6 0h4v4h-4zm6 0h4v4h-4zM4 16h4v4H4zm6 0h4v4h-4zm6 0h4v4h-4z" opacity="0.3"/>
          </svg>
          <span>工具箱</span>
        </button>
        <transition name="toolbox-fade">
          <div v-if="toolboxVisible" class="toolbox-panel">
            <div class="toolbox-section">
              <div class="toolbox-header">
                <span class="toolbox-title">绘制工具</span>
              </div>
              <DrawToolbar ref="drawToolbarRef" :map="map" @draw-end="onDrawEnd" />
            </div>
            <div class="toolbox-section">
              <div class="toolbox-header">
                <span class="toolbox-title">测量工具</span>
              </div>
              <MeasureTool ref="measureToolRef" :map="map" />
            </div>
            <div class="toolbox-section">
              <div class="toolbox-header">
                <span class="toolbox-title">数据导入</span>
              </div>
              <DataImport ref="dataImportRef" :map="map" :has-imported-data="hasImportedData" @import-features="onImportFeatures" @clear-import="onClearImport" />
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 右下角：地图控制按钮（放大/缩小/图层）+ 底图切换 -->
    <div class="right-controls">
      <!-- 放大缩小与图层控制 -->
      <MapControls ref="mapControlsRef" :map="map" @feature-click="onFeatureClick" @feature-close="featureDetail.visible = false; _detailCoord = null" @edit-props="onEditProps" @edit-save="onEditSave" @edit-delete="onEditDelete" />

      <!-- 底图切换：只显示一个按鈕，展示当前未激活的底图缩略图，点击即切换 -->
      <div class="layer-switcher">
        <!-- 当前为电子图，显示影像预览，点击切换到影像 -->
        <div
          v-if="currentBaseLayer === 'vec'"
          class="layer-item"
          title="切换到影像地图"
          @click="switchBaseLayer('img')"
        >
          <img :src="imgLayerImg" alt="影像地图" />
          <span class="layer-tag">影像</span>
        </div>
        <!-- 当前为影像图，显示电子预览，点击切换到电子 -->
        <div
          v-else
          class="layer-item"
          title="切换到电子地图"
          @click="switchBaseLayer('vec')"
        >
          <img :src="vecLayerImg" alt="电子地图" />
          <span class="layer-tag">电子</span>
        </div>
      </div>
    </div>

    <!-- 要素详情面板（跟随点击位置） -->
    <transition name="detail-fade">
      <div
        v-if="featureDetail.visible"
        class="feature-detail-popup"
        :style="{ left: featureDetail.x + 'px', top: featureDetail.y + 'px' }"
      >
        <div class="fdp-header">
          <span class="fdp-title">要素详情</span>
          <button class="fdp-close" @click="featureDetail.visible = false; _detailCoord = null">×</button>
        </div>
        <div class="fdp-body">
          <div class="fdp-row">
            <span class="fdp-label">名称</span>
            <span class="fdp-value">{{ featureDetail.data.name || '—' }}</span>
          </div>
          <div class="fdp-row">
            <span class="fdp-label">类型</span>
            <span class="fdp-value">{{ featureTypeLabel(featureDetail.data.type) }}</span>
          </div>
          <div class="fdp-row">
            <span class="fdp-label">行政区划</span>
            <span class="fdp-value">{{ featureDetail.data.xzqhname || '—' }}</span>
          </div>
          <div class="fdp-row">
            <span class="fdp-label">区划代码</span>
            <span class="fdp-value">{{ featureDetail.data.code || '—' }}</span>
          </div>
          <div class="fdp-row">
            <span class="fdp-label">地址</span>
            <span class="fdp-value">{{ featureDetail.data.address || '—' }}</span>
          </div>
          <div class="fdp-row">
            <span class="fdp-label">备注</span>
            <span class="fdp-value">{{ featureDetail.data.remark || '—' }}</span>
          </div>
          <div class="fdp-row">
            <span class="fdp-label">创建人</span>
            <span class="fdp-value">{{ featureDetail.data.createdBy || '—' }}</span>
          </div>
          <!-- 附件列表 -->
          <div v-if="featureAttachments.length" class="fdp-section">
            <div class="fdp-section-title">附件</div>
            <div class="fdp-attachment-list">
              <div v-for="att in featureAttachments" :key="att.id" class="fdp-att-item">
                <div class="fdp-att-info">
                  <span class="fdp-att-icon">{{ attIcon(att.file_type) }}</span>
                  <span class="fdp-att-name" :title="att.filename">{{ att.filename }}</span>
                  <span class="fdp-att-size">({{ formatSize(att.file_size) }})</span>
                </div>
                <div class="fdp-att-actions">
                  <el-button v-if="att.previewable" link type="primary" size="small" @click="previewAttachment(att)">预览</el-button>
                  <el-button link type="primary" size="small" @click="downloadAttachment(att)">下载</el-button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="fdp-row">
            <span class="fdp-label">附件</span>
            <span class="fdp-value">暂无附件</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- 图片预览对话框 -->
    <el-dialog v-model="imagePreviewVisible" title="图片预览" width="auto" :max-width="800">
      <img :src="imagePreviewUrl" style="max-width:100%;max-height:600px;display:block;margin:auto" />
    </el-dialog>

    <!-- 左下角：经纬度与层级信息 -->
    <div class="coord-bar">
      <span class="coord-item">经度: {{ coordInfo.lng }}</span>
      <span class="coord-sep">|</span>
      <span class="coord-item">纬度: {{ coordInfo.lat }}</span>
      <span class="coord-sep">|</span>
      <span class="coord-item">层级: {{ coordInfo.zoom }}</span>
    </div>

    <!-- 属性填写弹窗 -->
    <FeatureFormDialog
      ref="formDialogRef"
      v-model="dialogVisible"
      :draw-type="pendingFeature.type"
      :edit-data="editingFeature.data"
      @submit="onFormSubmit"
      @cancel="onFormCancel"
    />

    <!-- 导入数据属性查看弹框 -->
    <el-dialog
      v-model="importAttrVisible"
      title="要素属性"
      width="600px"
      class="attr-dialog"
    >
      <el-table :data="importAttrData" max-height="400" border size="small" stripe>
        <el-table-column v-for="col in importAttrColumns" :key="col" :prop="col" :label="col" min-width="120" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button @click="importAttrVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, shallowRef, onMounted, onBeforeUnmount } from 'vue'
import { markRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Map from 'ol/Map'
import View from 'ol/View'
import { transformExtent } from 'ol/proj'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import WKT from 'ol/format/WKT'
import { Style, Fill, Stroke, Circle as CircleStyle, Text } from 'ol/style'
import {
  createVecLayer,
  createCvaLayer,
  createImgLayer,
  createCiaLayer,
  getProjection4490
} from '../utils/tdtLayers'
import DrawToolbar from '../components/DrawToolbar.vue'
import MeasureTool from '../components/MeasureTool.vue'
import DataImport from '../components/DataImport.vue'
import FeatureFormDialog from '../components/FeatureFormDialog.vue'
import SearchPanel from '../components/SearchPanel.vue'
import MapControls from '../components/MapControls.vue'
import { createFeature, updateFeature, deleteFeature } from '../api/feature'
import { uploadAttachments, listAttachments, getAttachmentDownloadUrl, deleteAttachment } from '../api/attachment'

// 导入图层切换图标
import vecLayerImg from '../assets/images/vec-layer.svg'
import imgLayerImg from '../assets/images/img-layer.svg'

const mapContainer = ref(null)
// shallowRef 避免 Vue 对 OL Map 对象做深度代理（深代理会破坏 OL 内部方法）
const map = shallowRef(null)
const drawToolbarRef = ref(null)
const mapControlsRef = ref(null)
const measureToolRef = ref(null)
const dataImportRef = ref(null)
const toolboxVisible = ref(false)

// 图层实例
let vecLayer = null
let cvaLayer = null
let imgLayer = null
let ciaLayer = null

// 当前底图类型
const currentBaseLayer = ref('vec')

// 弹窗状态
const dialogVisible = ref(false)
const pendingFeature = reactive({ type: 0, geometry: '' })

// 编辑模式状态
const editingFeature = reactive({ data: null })  // 编辑属性时存放要素数据

// 要素详情面板状态
const featureDetail = reactive({ visible: false, x: 0, y: 0, data: {} })
// 记录点击时的地理坐标（地图移动时重新计算像素位置）
let _detailCoord = null

// 要素附件列表
const featureAttachments = ref([])

// 图片预览
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')

// 左下角坐标信息
const coordInfo = reactive({ lng: '—', lat: '—', zoom: '—' })

// ========== 导入数据管理（MapView 层面，不受工具箱 v-if 销毁影响） ==========
const hasImportedData = ref(false)
const importAttrVisible = ref(false)
const importAttrColumns = ref([])
const importAttrData = ref([])

// 已导入图层列表（模块级变量，持久存在）
const _importedLayers = []
let _importClickHandler = null

// 导入数据默认样式
const IMPORT_STYLE = markRaw(new Style({
  fill: new Fill({ color: 'rgba(64, 158, 255, 0.25)' }),
  stroke: new Stroke({ color: '#409eff', width: 2 }),
  image: new CircleStyle({
    radius: 6,
    fill: new Fill({ color: '#409eff' }),
    stroke: new Stroke({ color: '#fff', width: 2 })
  })
}))

/** DataImport 解析完成后的回调：创建图层、定位、注册点击 */
function onImportFeatures({ features, count }) {
  if (!map.value) return

  const source = markRaw(new VectorSource({ features }))
  const layer = markRaw(new VectorLayer({
    source,
    style: IMPORT_STYLE,
    zIndex: 60
  }))
  map.value.addLayer(layer)
  _importedLayers.push({ layer, source })

  // 定位到数据范围
  const extent = source.getExtent()
  if (extent && isFinite(extent[0])) {
    map.value.getView().fit(extent, { padding: [80, 80, 80, 80], duration: 800, maxZoom: 16 })
  }

  hasImportedData.value = true

  // 注册点击查看属性（只注册一次）
  if (!_importClickHandler) {
    _importClickHandler = (evt) => {
      if (!map.value) return
      let hitFeature = null
      map.value.forEachFeatureAtPixel(evt.pixel, (feature, layer) => {
        if (!hitFeature && _importedLayers.some(il => il.layer === layer)) {
          hitFeature = feature
        }
      })
      if (hitFeature) {
        showImportFeatureAttr(hitFeature)
      }
    }
    map.value.on('singleclick', _importClickHandler)
  }
}

/** 显示导入要素属性 */
function showImportFeatureAttr(feature) {
  const fprops = feature.getProperties()
  const keys = Object.keys(fprops).filter(k => k !== 'geometry')
  if (!keys.length) {
    ElMessage.info('该要素无属性数据')
    return
  }
  importAttrColumns.value = keys
  importAttrData.value = [fprops]
  importAttrVisible.value = true
}

/** 清除所有导入数据 */
function onClearImport() {
  if (!map.value) return
  for (const { layer } of _importedLayers) {
    map.value.removeLayer(layer)
  }
  _importedLayers.length = 0
  if (_importClickHandler) {
    map.value.un('singleclick', _importClickHandler)
    _importClickHandler = null
  }
  hasImportedData.value = false
  importAttrVisible.value = false
  ElMessage.success('已清除导入数据')
}

function featureTypeLabel(type) {
  return { 1: '点要素', 2: '线要素', 3: '面要素' }[type] || '未知'
}

/**
 * 将地理坐标转成像素坐标，计算面板安全位置
 */
function calcPanelPos(coord) {
  if (!map.value || !coord) return
  const pixel = map.value.getPixelFromCoordinate(coord)
  if (!pixel) return
  const PANEL_W = 300
  const PANEL_H = 350
  const mapEl = mapContainer.value
  const mapW = mapEl ? mapEl.clientWidth : window.innerWidth
  const mapH = mapEl ? mapEl.clientHeight : window.innerHeight
  let x = pixel[0] + 12
  let y = pixel[1] + 12
  if (x + PANEL_W > mapW) x = pixel[0] - PANEL_W - 12
  if (y + PANEL_H > mapH) y = pixel[1] - PANEL_H - 12
  if (x < 0) x = 8
  if (y < 0) y = 8
  featureDetail.x = x
  featureDetail.y = y
}

/**
 * 要素点击回调：记录地理坐标，跟随定位详情面板
 */
function onFeatureClick({ data, pixel }) {
  // 像素 → 地理坐标，供地图移动时重算
  _detailCoord = map.value ? map.value.getCoordinateFromPixel(pixel) : null
  featureDetail.data = data
  featureDetail.visible = true
  calcPanelPos(_detailCoord)
  // 加载附件列表
  loadAttachments(data.id)
}

/**
 * 初始化地图
 */
function initMap() {
  const projection = getProjection4490()

  vecLayer = createVecLayer()
  cvaLayer = createCvaLayer()
  imgLayer = createImgLayer()
  ciaLayer = createCiaLayer()

  imgLayer.setVisible(false)
  ciaLayer.setVisible(false)

  // markRaw 防止 Vue 响应式系统代理 OL Map 对象
  map.value = markRaw(new Map({
    target: mapContainer.value,
    layers: [vecLayer, cvaLayer, imgLayer, ciaLayer],
    view: new View({
      projection: projection,
      center: [116.4, 39.9],
      zoom: 10,
      minZoom: 1,
      maxZoom: 18,
      extent: [-180, -90, 180, 90],
      constrainRotation: false
    }),
    controls: []
  }))
}

/**
 * 切换底图
 */
function switchBaseLayer(type) {
  if (currentBaseLayer.value === type) return
  currentBaseLayer.value = type

  if (type === 'vec') {
    vecLayer.setVisible(true)
    cvaLayer.setVisible(true)
    imgLayer.setVisible(false)
    ciaLayer.setVisible(false)
  } else if (type === 'img') {
    vecLayer.setVisible(false)
    cvaLayer.setVisible(false)
    imgLayer.setVisible(true)
    ciaLayer.setVisible(true)
  }
}

/**
 * 搜索定位：解析搜索结果的 WKT 并定位到地图
 */
const _wktFormat = markRaw(new WKT())

// 搜索结果图层（独立图层，翻页/关闭时清除）
let _searchLayer = null
let _searchSource = null

/**
 * 渲染搜索结果到地图
 * 兼容点/线/面：点用圆形图标 + tsmc 文字标签
 */
function onSearchResult(items) {
  if (!map.value) return
  // 清除旧图层
  clearSearchLayer()

  const features = items.map(item => {
    if (!item.wkt) return null
    try {
      const geom = markRaw(_wktFormat.readGeometry(item.wkt))
      const olFeature = markRaw(new Feature({ geometry: geom }))
      olFeature.setId('doorplate_' + item.gid)
      // 属性存储到 feature 上，供样式函数读取
      olFeature.set('tsmc', item.tsmc || '')
      olFeature.set('type', geom.getType())
      return olFeature
    } catch (e) {
      console.warn('搜索结果 WKT 解析失败:', item.wkt, e)
      return null
    }
  }).filter(Boolean)

  _searchSource = markRaw(new VectorSource({ features }))
  _searchLayer = markRaw(new VectorLayer({
    source: _searchSource,
    style: searchResultStyle,
    zIndex: 50
  }))
  map.value.addLayer(_searchLayer)
}

/**
 * 搜索结果样式函数：根据几何类型动态返回样式
 */
function searchResultStyle(feature) {
  const geomType = feature.get('type') || feature.getGeometry().getType()
  const label = feature.get('tsmc') || ''

  if (geomType === 'Point') {
    return new Style({
      image: new CircleStyle({
        radius: 7,
        fill: new Fill({ color: '#e6a23c' }),
        stroke: new Stroke({ color: '#fff', width: 2 })
      }),
      text: new Text({
        text: label,
        offsetY: -18,
        font: '12px sans-serif',
        fill: new Fill({ color: '#303133' }),
        stroke: new Stroke({ color: '#fff', width: 3 }),
        padding: [2, 4, 2, 4]
      })
    })
  } else if (geomType === 'LineString' || geomType === 'MultiLineString') {
    return new Style({
      stroke: new Stroke({ color: '#e6a23c', width: 3 }),
      text: new Text({
        text: label,
        offsetY: -12,
        font: '12px sans-serif',
        fill: new Fill({ color: '#303133' }),
        stroke: new Stroke({ color: '#fff', width: 3 }),
        padding: [2, 4, 2, 4]
      })
    })
  } else {
    // Polygon / MultiPolygon
    return new Style({
      fill: new Fill({ color: '#e6a23c55' }),
      stroke: new Stroke({ color: '#e6a23c', width: 2 }),
      text: new Text({
        text: label,
        font: '12px sans-serif',
        fill: new Fill({ color: '#303133' }),
        stroke: new Stroke({ color: '#fff', width: 3 }),
        padding: [2, 4, 2, 4]
      })
    })
  }
}

/**
 * 清除搜索结果图层
 */
function clearSearchLayer() {
  if (_searchLayer && map.value) {
    map.value.removeLayer(_searchLayer)
    _searchLayer = null
    _searchSource = null
  }
}

function onSearchClose() {
  clearSearchLayer()
}

function onSearchLocate(item) {
  if (!item.wkt || !map.value) return
  try {
    const geom = _wktFormat.readGeometry(item.wkt)
    const coord = geom.getFirstCoordinate()
    const view = map.value.getView()
    view.animate({
      center: coord,
      zoom: 16,
      duration: 600
    })
  } catch (e) {
    console.error('搜索定位 WKT 解析失败:', e)
  }
}

/**
 * 搜索面板选择行政区划后，地图跳转到对应区划
 * bbox: "minx,miny,maxx,maxy" 或 centroid: "x,y"
 */
function onXzqhLocate({ bbox, centroid, level }) {
  if (!map.value) return
  const view = map.value.getView()
  if (bbox) {
    // 有 bbox 直接 fit 范围
    const parts = bbox.split(',').map(Number)
    if (parts.length === 4 && parts.every(n => !isNaN(n))) {
      const extent = parts
      view.fit(extent, { padding: [80, 80, 80, 80], duration: 600, maxZoom: 16 })
      return
    }
  }
  if (centroid) {
    // 只有中心点，根据层级设置缩放
    const parts = centroid.split(',').map(Number)
    if (parts.length === 2 && parts.every(n => !isNaN(n))) {
      const zoomMap = { 1: 6, 2: 9, 3: 12, 4: 15 }
      view.animate({
        center: parts,
        zoom: zoomMap[level] || 12,
        duration: 600
      })
    }
  }
}

/**
 * 绘制完成回调：暂存几何信息，弹出属性填写弹窗
 */
function onDrawEnd({ type, geometry }) {
  editingFeature.data = null       // 清空编辑状态，确保标题显示"新增"
  pendingFeature.type = type       // 1/2/3
  pendingFeature.geometry = geometry  // WKT
  dialogVisible.value = true
}

/**
 * 属性表单提交：调用后端接口保存（支持新增和编辑）
 */
const formDialogRef = ref(null)

async function onFormSubmit(fields) {
  const pendingFiles = fields.pendingFiles || []
  try {
    if (editingFeature.data) {
      // 编辑模式：更新几何 + 属性
      await updateFeature(editingFeature.data.id, {
        geometry: editingFeature.data.geometry,
        name: fields.name,
        xzqhname: fields.xzqhname,
        code: fields.code,
        address: fields.address,
        remark: fields.remark
      })
      // 编辑模式有要素ID，直接上传附件
      if (pendingFiles.length) {
        await formDialogRef.value?.uploadPendingAttachments(editingFeature.data.id)
      }
      ElMessage.success('属性编辑成功')
      editingFeature.data = null
      mapControlsRef.value?.deselectFeature()
    } else {
      // 新增模式：先保存要素拿到 ID
      const res = await createFeature({
        type: pendingFeature.type,       // 1/2/3
        geometry: pendingFeature.geometry, // WKT
        name: fields.name,
        xzqhname: fields.xzqhname,
        code: fields.code,
        address: fields.address,
        remark: fields.remark
      })
      // 用返回的要素 ID 上传附件
      if (pendingFiles.length && res.data?.id) {
        await formDialogRef.value?.uploadPendingAttachments(res.data.id)
      }
      ElMessage.success('要素保存成功')
      drawToolbarRef.value?.clearAll()  // 清除草稿图形并退出激活状态
    }
    dialogVisible.value = false
    mapControlsRef.value?.reloadLayers()  // 重新加载地图要素
  } catch (error) {
    ElMessage.error('保存失败，请重试')
    console.error('保存要素失败:', error)
  }
}

/**
 * 取消弹窗：清除草稿图形并退出激活状态
 */
function onFormCancel() {
  drawToolbarRef.value?.clearAll()
}

/**
 * 加载要素附件列表
 */
async function loadAttachments(featureId) {
  try {
    const res = await listAttachments(featureId)
    featureAttachments.value = res.data || []
  } catch (e) {
    featureAttachments.value = []
  }
}

/**
 * 附件图标映射
 */
function attIcon(fileType) {
  const icons = {
    image: '\u{1F4F7}',
    pdf: '\u{1F4D1}',
    document: '\u{1F4C4}',
    other: '\u{1F4CE}'
  }
  return icons[fileType] || icons.other
}

/**
 * 格式化文件大小
 */
function formatSize(bytes) {
  if (!bytes) return '0B'
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

/**
 * 预览附件（图片/PDF浏览器可预览）
 */
function previewAttachment(att) {
  const url = getAttachmentDownloadUrl(att.id)
  if (att.file_type === 'pdf') {
    // PDF 使用浏览器原生预览
    window.open(url, '_blank')
  } else if (att.file_type === 'image') {
    // 图片使用弹窗预览
    imagePreviewUrl.value = url
    imagePreviewVisible.value = true
  }
}

/**
 * 下载附件（不可预览类型或手动下载）
 */
function downloadAttachment(att) {
  const url = getAttachmentDownloadUrl(att.id)
  // 创建隐藏 a 标签触发下载
  const a = document.createElement('a')
  a.href = url
  a.download = att.filename
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

/**
 * 编辑属性：弹出属性编辑弹窗
 */
function onEditProps({ data }) {
  editingFeature.data = data
  pendingFeature.type = data.type
  dialogVisible.value = true
}

/**
 * 保存几何编辑：调用后端更新接口
 */
async function onEditSave({ id, geometry }) {
  try {
    await updateFeature(id, { geometry })
    ElMessage.success('几何数据保存成功')
    mapControlsRef.value?.deselectFeature()
    mapControlsRef.value?.reloadLayers()
  } catch (error) {
    ElMessage.error('保存失败，请重试')
    console.error('保存几何失败:', error)
  }
}

/**
 * 删除要素
 */
async function onEditDelete({ id }) {
  try {
    await ElMessageBox.confirm('确定要删除该要素吗？删除后不可恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteFeature(id)
    ElMessage.success('要素已删除')
    mapControlsRef.value?.deselectFeature()
    mapControlsRef.value?.reloadLayers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请重试')
      console.error('删除要素失败:', error)
    }
  }
}

/** 点击工具箱外部区域时关闭工具箱（绘制/测量进行中不关闭） */
function onToolboxOutsideClick(e) {
  if (!toolboxVisible.value) return
  // 正在绘制或测量中时不关闭面板
  if (drawToolbarRef.value?.activeType) return
  if (measureToolRef.value?.activeType) return
  if (!e.target.closest('.toolbox-wrapper')) {
    toolboxVisible.value = false
  }
}

onMounted(() => {
  initMap()
  // initMap 同步执行，map.value 已赋値，主动触发图层加载
  mapControlsRef.value?.initLayers()

  // 鼠标移动实时更新经纬度
  map.value.on('pointermove', (evt) => {
    const coord = evt.coordinate
    if (coord) {
      coordInfo.lng = coord[0].toFixed(6)
      coordInfo.lat = coord[1].toFixed(6)
    }
  })

  // 地图缩放/平移后更新层级
  map.value.on('moveend', () => {
    coordInfo.zoom = map.value.getView().getZoom().toFixed(1)
    if (featureDetail.visible && _detailCoord) {
      calcPanelPos(_detailCoord)
    }
  })

  // 初始层级
  coordInfo.zoom = map.value.getView().getZoom().toFixed(1)

  // 点击外部区域关闭工具箱
  document.addEventListener('click', onToolboxOutsideClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onToolboxOutsideClick)
  if (map.value) {
    map.value.setTarget(null)
    map.value = null
  }
})
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
}

/* 左上角：搜索面板 */
.top-left {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
}

/* 右上角：绘制工具 */
.top-right {
  position: absolute;
  top: 12px;
  right: 16px;
  z-index: 10;
}

/* 工具箱 */
.toolbox-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.toolbox-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  color: #303133;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}

.toolbox-btn:hover {
  background: #ecf5ff;
  color: #409eff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
}

.toolbox-panel {
  margin-top: 8px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 8px;
  padding: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  min-width: 150px;
}

.toolbox-section {
  border-bottom: 1px solid #ebeef5;
}

.toolbox-section:last-child {
  border-bottom: none;
}

.toolbox-header {
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.toolbox-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.toolbox-panel :deep(.draw-toolbar),
.toolbox-panel :deep(.measure-tool),
.toolbox-panel :deep(.data-import) {
  padding: 8px 12px;
  background: transparent;
  box-shadow: none;
  justify-content: center;
}

/* 工具箱弹出动画 */
.toolbox-fade-enter-active,
.toolbox-fade-leave-active {
  transition: opacity 0.18s, transform 0.18s;
}
.toolbox-fade-enter-from,
.toolbox-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 右下角：控制组合区域 */
.right-controls {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  z-index: 10;
}

/* 底图切换 */
.layer-switcher {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-item {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid rgba(255,255,255,0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  transition: box-shadow 0.2s, transform 0.15s;
  background: #fff;
}

.layer-item:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
  transform: scale(1.05);
}

.layer-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 图层标签（显示在图片上方） */
.layer-tag {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 10px;
  color: #fff;
  background: rgba(0,0,0,0.45);
  padding: 2px 0;
  letter-spacing: 0.5px;
}

/* 左下角：经纬度与层级信息 */
.coord-bar {
  position: absolute;
  left: 12px;
  bottom: 12px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 6px;
  padding: 6px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  font-size: 12px;
  color: #303133;
  user-select: none;
  backdrop-filter: blur(4px);
}

.coord-item {
  font-family: 'Consolas', 'Monaco', monospace;
  letter-spacing: 0.3px;
}

.coord-sep {
  color: #c0c4cc;
  font-size: 11px;
}

/* 要素详情面板（跟随点击位置） */
.feature-detail-popup {
  position: absolute;
  z-index: 100;
  min-width: 300px;
  max-width: 380px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22);
  overflow: hidden;
  pointer-events: auto;
}

.fdp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.fdp-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.fdp-close {
  border: none;
  background: none;
  font-size: 16px;
  color: #909399;
  cursor: pointer;
  line-height: 1;
  padding: 0 2px;
}

.fdp-close:hover { color: #303133; }

.fdp-body {
  padding: 4px 0;
}

.fdp-row {
  display: flex;
  align-items: flex-start;
  padding: 6px 12px;
  border-bottom: 1px solid #f0f2f5;
  gap: 8px;
}

.fdp-row:last-child { border-bottom: none; }

.fdp-label {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  width: 56px;
  padding-top: 1px;
}

.fdp-value {
  font-size: 13px;
  color: #303133;
  word-break: break-all;
  flex: 1;
}

/* 附件区块 */
.fdp-section {
  margin-top: 6px;
  border-top: 1px solid #ebeef5;
  padding-top: 6px;
}
.fdp-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.fdp-attachment-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.fdp-att-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 0;
}
.fdp-att-info {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.fdp-att-icon {
  font-size: 14px;
}
.fdp-att-name {
  font-size: 12px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fdp-att-size {
  font-size: 11px;
  color: #909399;
}
.fdp-att-actions {
  display: flex;
  gap: 2px;
}

/* 详情面板出现动画 */
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: opacity 0.18s, transform 0.18s;
}
.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>

<style>
/* 导入属性弹框样式（非 scoped，覆盖 el-dialog） */
.attr-dialog .el-dialog__header {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}
</style>
