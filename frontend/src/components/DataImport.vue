<template>
  <div class="data-import">
    <el-tooltip content="数据导入" placement="bottom">
      <el-button circle @click="showDialog = true">
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path d="M3 3v14h14V3H3zm12 12H5V5h10v10zM7 7h6v2H7V7zm0 3h6v2H7v-2z" opacity="0.4"/>
          <path d="M10 1L5 6h3v5h4V6h3L10 1z"/>
          <path d="M2 15v3h16v-3h-2v1H4v-1H2z"/>
        </svg>
      </el-button>
    </el-tooltip>
    <el-tooltip content="清除导入" placement="bottom">
      <el-button
        :disabled="!hasImportedData"
        circle
        @click="$emit('clear-import')"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
      </el-button>
    </el-tooltip>
  </div>

  <!-- 导入弹框 -->
  <el-dialog
    v-model="showDialog"
    title="Import files"
    width="520px"
    :close-on-click-modal="false"
    class="import-dialog"
    @close="onDialogClose"
  >
    <div class="import-drop-zone"
      :class="{ 'is-dragover': isDragover }"
      @dragover.prevent="isDragover = true"
      @dragleave.prevent="isDragover = false"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <div class="drop-icon">
        <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" width="48" height="48" stroke-width="1.5">
          <path d="M24 4v28M12 16l12-12 12 12" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M4 32v8a4 4 0 004 4h32a4 4 0 004-4v-8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="drop-text">
        Drop, paste or <span class="drop-link">select</span> files to import.
      </div>
      <div class="drop-formats">
        Shapefile, GeoJSON, TopoJSON,<br/>
        GeoPackage, FlatGeobuf, GeoParquet,<br/>
        GeoTIFF, KML, CSV and more are supported.<br/>
        Files can be zipped or gzipped.
      </div>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept=".geojson,.json,.topojson,.kml,.kmz,.zip,.gz,.shp,.dbf,.shx,.prj,.gpkg,.fgb,.csv,.tsv,.txt,.gpx,.gml,.wkt,.wkb"
        style="display:none"
        @change="onFileSelected"
      />
    </div>

    <!-- 已选文件列表 -->
    <div v-if="fileList.length" class="import-file-list">
      <div v-for="(f, i) in fileList" :key="i" class="import-file-item">
        <span class="file-icon">{{ fileIcon(f.name) }}</span>
        <span class="file-name" :title="f.name">{{ f.name }}</span>
        <span class="file-size">{{ formatSize(f.size) }}</span>
        <button class="file-remove" @click="removeFile(i)">×</button>
      </div>
    </div>

    <!-- 导入进度 -->
    <div v-if="importing" class="import-progress">
      <el-progress :percentage="importProgress" :format="() => importStatus" />
    </div>

    <template #footer>
      <el-button @click="showDialog = false">取消</el-button>
      <el-button type="primary" :disabled="!fileList.length || importing" @click="doImport">
        导入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import Feature from 'ol/Feature'
import GeoJSON from 'ol/format/GeoJSON'
import TopoJSON from 'ol/format/TopoJSON'
import KML from 'ol/format/KML'
import GPX from 'ol/format/GPX'
import GML3 from 'ol/format/GML3'
import WKT from 'ol/format/WKT'
import { get as getProjection } from 'ol/proj'

const props = defineProps({
  map: { type: Object, default: null },
  hasImportedData: { type: Boolean, default: false }
})

const emit = defineEmits(['import-features', 'clear-import'])

const showDialog = ref(false)
const isDragover = ref(false)
const fileList = ref([])
const fileInputRef = ref(null)
const importing = ref(false)
const importProgress = ref(0)
const importStatus = ref('')

function triggerFileInput() {
  fileInputRef.value?.click()
}

function onFileSelected(e) {
  const files = Array.from(e.target.files || [])
  addFiles(files)
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function onDrop(e) {
  isDragover.value = false
  const files = Array.from(e.dataTransfer.files || [])
  addFiles(files)
}

function addFiles(files) {
  for (const f of files) {
    if (!fileList.value.some(item => item.name === f.name && item.size === f.size)) {
      fileList.value.push(f)
    }
  }
}

function removeFile(index) {
  fileList.value.splice(index, 1)
}

function onDialogClose() {
  fileList.value = []
  importing.value = false
  importProgress.value = 0
  importStatus.value = ''
}

function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase()
  const map = { zip: '📦', gz: '📦', shp: '🗺️', geojson: '📋', json: '📋', kml: '📍', csv: '📊', gpkg: '🗃️' }
  return map[ext] || '📄'
}

function formatSize(bytes) {
  if (!bytes) return '0B'
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

function readFileAsArrayBuffer(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsArrayBuffer(file)
  })
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

/** 解析 GeoJSON/TopoJSON/KML/GPX/GML/WKT/CSV 文本格式 */
function parseTextFormat(text, fileName) {
  const ext = fileName.split('.').pop().toLowerCase()
  const projection = getProjection('EPSG:4326')

  if (ext === 'geojson' || ext === 'json') {
    try {
      const data = JSON.parse(text)
      if (data.type === 'Topology') {
        return new TopoJSON().readFeatures(text, { featureProjection: projection })
      }
      return new GeoJSON().readFeatures(text, { featureProjection: projection })
    } catch (e) {
      console.warn('GeoJSON 解析失败:', e)
      return null
    }
  }

  if (ext === 'topojson') {
    try { return new TopoJSON().readFeatures(text, { featureProjection: projection }) }
    catch (e) { console.warn('TopoJSON 解析失败:', e); return null }
  }

  if (ext === 'kml') {
    try { return new KML({ extractStyles: false }).readFeatures(text, { featureProjection: projection }) }
    catch (e) { console.warn('KML 解析失败:', e); return null }
  }

  if (ext === 'gpx') {
    try { return new GPX().readFeatures(text, { featureProjection: projection }) }
    catch (e) { console.warn('GPX 解析失败:', e); return null }
  }

  if (ext === 'gml') {
    try { return new GML3().readFeatures(text, { featureProjection: projection }) }
    catch (e) { console.warn('GML 解析失败:', e); return null }
  }

  if (ext === 'wkt') {
    try {
      const format = new WKT()
      const lines = text.trim().split('\n').filter(l => l.trim())
      const features = []
      for (const line of lines) {
        try {
          const geom = format.readGeometry(line.trim())
          features.push(new Feature({ geometry: geom }))
        } catch (_) { /* skip */ }
      }
      return features.length ? features : null
    } catch (e) { console.warn('WKT 解析失败:', e); return null }
  }

  if (ext === 'csv' || ext === 'tsv' || ext === 'txt') {
    return parseCSV(text, ext === 'tsv' ? '\t' : ',')
  }

  return null
}

function parseCSV(text, delimiter = ',') {
  const projection = getProjection('EPSG:4326')
  const lines = text.trim().split('\n')
  if (lines.length < 2) return null

  const headers = lines[0].split(delimiter).map(h => h.trim().replace(/^["']|["']$/g, '').toLowerCase())
  const lngIdx = headers.findIndex(h => ['lng', 'lon', 'longitude', 'x', '经度', 'long'].includes(h))
  const latIdx = headers.findIndex(h => ['lat', 'latitude', 'y', '纬度'].includes(h))

  if (lngIdx === -1 || latIdx === -1) {
    ElMessage.warning('CSV 文件未找到经纬度列（需包含 lng/lon/longitude/x/经度 和 lat/latitude/y/纬度 列）')
    return null
  }

  const GeoJSONFormat = new GeoJSON()
  const features = []
  for (let i = 1; i < lines.length; i++) {
    const vals = lines[i].split(delimiter).map(v => v.trim().replace(/^["']|["']$/g, ''))
    const lng = parseFloat(vals[lngIdx])
    const lat = parseFloat(vals[latIdx])
    if (!isNaN(lng) && !isNaN(lat)) {
      const geom = GeoJSONFormat.readGeometry({ type: 'Point', coordinates: [lng, lat] }, { featureProjection: projection })
      const feature = new Feature({ geometry: geom })
      headers.forEach((h, j) => { feature.set(h, vals[j] || '') })
      features.push(feature)
    }
  }
  return features.length ? features : null
}

async function parseShapefile(arrayBuffer) {
  const projection = getProjection('EPSG:4326')
  try {
    const shp = await import('shpjs')
    const geojson = await (shp.default || shp)(arrayBuffer)
    const format = new GeoJSON()
    if (Array.isArray(geojson)) {
      let allFeatures = []
      for (const gj of geojson) {
        allFeatures = allFeatures.concat(format.readFeatures(gj, { featureProjection: projection }))
      }
      return allFeatures
    }
    return format.readFeatures(geojson, { featureProjection: projection })
  } catch (e) {
    console.warn('Shapefile 解析失败:', e)
    ElMessage.error('Shapefile 解析失败: ' + e.message)
    return null
  }
}

async function parseGeoPackage() {
  ElMessage.warning('GeoPackage 格式暂不支持，请先转换为 GeoJSON 后导入')
  return null
}

/** 主导入逻辑 */
async function doImport() {
  if (!fileList.value.length) return
  importing.value = true
  importProgress.value = 10
  importStatus.value = '准备导入...'

  let totalFeatures = 0
  let allFeatures = []
  const total = fileList.value.length

  for (let i = 0; i < fileList.value.length; i++) {
    const file = fileList.value[i]
    const fileName = file.name.toLowerCase()
    importProgress.value = 10 + Math.floor((i / total) * 70)
    importStatus.value = `解析 ${file.name}...`

    try {
      let features = null

      if (fileName.endsWith('.zip') || fileName.endsWith('.gz')) {
        features = await parseShapefile(await readFileAsArrayBuffer(file))
      } else if (fileName.endsWith('.shp')) {
        ElMessage.warning('请将 Shapefile 打包为 .zip 后导入（包含 .shp/.dbf/.shx/.prj）')
        continue
      } else if (fileName.endsWith('.gpkg')) {
        features = await parseGeoPackage(await readFileAsArrayBuffer(file))
      } else if (fileName.endsWith('.csv') || fileName.endsWith('.tsv') || fileName.endsWith('.txt') ||
                 fileName.endsWith('.geojson') || fileName.endsWith('.json') ||
                 fileName.endsWith('.topojson') || fileName.endsWith('.kml') ||
                 fileName.endsWith('.gpx') || fileName.endsWith('.gml') || fileName.endsWith('.wkt')) {
        features = parseTextFormat(await readFileAsText(file), fileName)
      } else {
        try { features = parseTextFormat(await readFileAsText(file), fileName) }
        catch (_) { ElMessage.warning(`不支持的文件格式: ${file.name}`); continue }
      }

      if (features && features.length) {
        allFeatures = allFeatures.concat(features)
        totalFeatures += features.length
      }
    } catch (e) {
      console.error(`解析 ${file.name} 失败:`, e)
      ElMessage.error(`解析 ${file.name} 失败`)
    }
  }

  importProgress.value = 85
  importStatus.value = '添加到地图...'

  if (allFeatures.length === 0) {
    ElMessage.warning('未解析到有效数据，请检查文件格式')
    importing.value = false
    importProgress.value = 0
    return
  }

  importProgress.value = 100
  importStatus.value = `导入完成，共 ${totalFeatures} 个要素`

  // 将解析好的 features 传给 MapView 管理（图层创建、定位、点击属性查看均在 MapView）
  emit('import-features', { features: allFeatures, count: totalFeatures })

  ElMessage.success(`成功导入 ${totalFeatures} 个要素`)

  setTimeout(() => {
    showDialog.value = false
  }, 500)
}
</script>

<style scoped>
.data-import {
  display: flex;
  gap: 6px;
}

.import-drop-zone {
  border: 2px dashed #c0c4cc;
  border-radius: 8px;
  padding: 32px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfc;
}

.import-drop-zone:hover,
.import-drop-zone.is-dragover {
  border-color: #409eff;
  background: #ecf5ff;
}

.drop-icon {
  color: #909399;
  margin-bottom: 12px;
  transition: color 0.2s;
}

.import-drop-zone:hover .drop-icon,
.import-drop-zone.is-dragover .drop-icon {
  color: #409eff;
}

.drop-text {
  font-size: 15px;
  color: #303133;
  margin-bottom: 12px;
}

.drop-link {
  color: #409eff;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

.drop-formats {
  font-size: 12px;
  color: #909399;
  line-height: 1.7;
}

.import-file-list {
  margin-top: 12px;
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.import-file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 8px;
  border-bottom: 1px solid #f0f2f5;
  font-size: 13px;
}

.import-file-item:last-child { border-bottom: none; }

.file-icon { font-size: 16px; flex-shrink: 0; }

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
}

.file-size { color: #909399; font-size: 12px; flex-shrink: 0; }

.file-remove {
  border: none; background: none; color: #c0c4cc;
  font-size: 16px; cursor: pointer; padding: 0 4px; line-height: 1;
}
.file-remove:hover { color: #f56c6c; }

.import-progress { margin-top: 12px; }
</style>

<style>
.import-dialog .el-dialog__header {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}
.import-dialog .el-dialog__title {
  font-size: 16px;
  font-weight: 600;
}
</style>
