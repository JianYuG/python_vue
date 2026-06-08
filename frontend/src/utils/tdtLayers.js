/**
 * 天地图 EPSG:4490 (CGCS2000) 图层工具类
 *
 * 使用 ol.source.WMTS + ol.tilegrid.WMTS 加载天地图 _c 瓦片
 * 这是加载天地图经纬度投影瓦片的正确方式
 *
 * 图层类型（_c 后缀 = CGCS2000 经纬度）：
 *   vec_c  矢量底图    cva_c  矢量注记
 *   img_c  影像底图    cia_c  影像注记
 */

import TileLayer from 'ol/layer/Tile'
import WMTS from 'ol/source/WMTS'
import WMTSTileGrid from 'ol/tilegrid/WMTS'
import { addProjection } from 'ol/proj'
import Projection from 'ol/proj/Projection'
import { getTopLeft, getWidth } from 'ol/extent'

// 天地图 Token
const TIANDITU_TOKEN = '2c2a1bc8a5853ce3ba6fe856d5600db6'

/**
 * 注册 EPSG:4490 投影
 */
const projection4490 = new Projection({
  code: 'EPSG:4490',
  extent: [-180, -90, 180, 90],
  worldExtent: [-180, -90, 180, 90],
  global: true,
  units: 'degrees',
  axisOrientation: 'enu'
})
addProjection(projection4490)

/**
 * 生成分辨率数组和矩阵 ID 数组
 *
 * 参考天地图 WMTS GetCapabilities：
 *   第 1 级：全球 2×1 张瓦片，resolution = extent宽度 / 256 / 2
 *   第 z 级：resolution = size / 2^z
 */
const size = getWidth(projection4490.getExtent()) / 256
const resolutions = new Array(19)
const matrixIds = new Array(19)
for (let z = 1; z < 19; ++z) {
  resolutions[z] = size / Math.pow(2, z)
  matrixIds[z] = z
}

/**
 * 共享 WMTS TileGrid 实例
 */
const wmtsTileGrid = new WMTSTileGrid({
  origin: getTopLeft(projection4490.getExtent()),
  resolutions: resolutions,
  matrixIds: matrixIds
})

/**
 * 创建天地图 WMTS Source
 *
 * @param {string} layerType - 图层类型: vec / cva / img / cia
 * @param {boolean} visible - 是否可见
 */
function createTiandituSource(layerType, visible) {
  return new WMTS({
    url: `http://t{0-7}.tianditu.gov.cn/${layerType}_c/wmts?tk=${TIANDITU_TOKEN}`,
    layer: layerType,
    matrixSet: 'c',
    format: 'tiles',
    projection: projection4490,
    tileGrid: wmtsTileGrid,
    style: 'default',
    wrapX: true
  })
}

// ==================== 图层工厂函数 ====================

/** 创建天地图矢量底图图层 */
export function createVecLayer() {
  return new TileLayer({
    source: createTiandituSource('vec'),
    className: 'tianditu-vec'
  })
}

/** 创建天地图矢量注记图层 */
export function createCvaLayer() {
  return new TileLayer({
    source: createTiandituSource('cva'),
    className: 'tianditu-cva'
  })
}

/** 创建天地图影像底图图层 */
export function createImgLayer() {
  return new TileLayer({
    source: createTiandituSource('img'),
    className: 'tianditu-img'
  })
}

/** 创建天地图影像注记图层 */
export function createCiaLayer() {
  return new TileLayer({
    source: createTiandituSource('cia'),
    className: 'tianditu-cia'
  })
}

/** 获取 EPSG:4490 投影对象 */
export function getProjection4490() {
  return projection4490
}

/** 获取天地图瓦片分辨率数组 */
export function getResolutions() {
  return resolutions
}
