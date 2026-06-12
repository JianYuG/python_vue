<template>
  <div class="data-ingest">
    <!-- 上传按钮 -->
    <div class="ingest-actions">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        :accept="ACCEPT"
        :on-change="onFileChange"
      >
        <el-button size="small" type="primary" :loading="uploading">
          <span v-if="!uploading">上传入库</span>
          <span v-else>入库中...</span>
        </el-button>
      </el-upload>

      <el-button size="small" @click="openList">查看列表</el-button>
    </div>

    <!-- 支持格式提示 -->
    <div class="ingest-tip">支持 CSV / Excel / SHP(zip) / DBF</div>

    <!-- 入库记录列表对话框 -->
    <el-dialog
      v-model="listVisible"
      title="数据入库记录"
      width="720px"
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="list-toolbar">
        <el-button size="small" @click="loadList" :loading="listLoading">刷新</el-button>
      </div>

      <el-table
        :data="records"
        v-loading="listLoading"
        border
        stripe
        size="small"
        max-height="420"
        style="width: 100%; margin-top: 8px;"
      >
        <el-table-column prop="original_filename" label="文件名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="table_name" label="数据表名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="row_count" label="行数" width="80" align="center" />
        <el-table-column label="字段数" width="80" align="center">
          <template #default="{ row }">{{ row.columns ? row.columns.length : 0 }}</template>
        </el-table-column>
        <el-table-column prop="created_by" label="入库人" width="100" show-overflow-tooltip />
        <el-table-column label="入库时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="showColumns(row)"
            >字段</el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="listVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 字段详情对话框 -->
    <el-dialog
      v-model="colVisible"
      :title="`字段信息 - ${currentRecord?.original_filename || ''}`"
      width="400px"
      append-to-body
    >
      <el-table
        :data="currentRecord?.columns || []"
        border
        size="small"
        max-height="360"
      >
        <el-table-column prop="name" label="字段名" min-width="160" />
        <el-table-column prop="type" label="类型" width="120" />
      </el-table>
      <template #footer>
        <el-button @click="colVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uploadIngest, listIngest, deleteIngest } from '../api/ingest'

// 支持的文件格式
const ACCEPT = '.csv,.xls,.xlsx,.zip,.dbf'

const uploadRef = ref(null)
const uploading = ref(false)

// 列表相关
const listVisible = ref(false)
const listLoading = ref(false)
const records = ref([])

// 字段详情
const colVisible = ref(false)
const currentRecord = ref(null)

/** 选择文件后立即触发上传 */
async function onFileChange(uploadFile) {
  const file = uploadFile.raw
  if (!file) return

  uploading.value = true
  try {
    const res = await uploadIngest(file)
    if (res.code === 200) {
      ElMessage.success(`"${file.name}" 入库成功，共 ${res.data?.row_count || 0} 行`)
    } else {
      ElMessage.error(res.message || '入库失败')
    }
  } catch (e) {
    ElMessage.error('入库失败: ' + (e?.message || '网络错误'))
  } finally {
    uploading.value = false
    // 重置 el-upload 内部文件列表，使同名文件可重复上传
    uploadRef.value?.clearFiles()
  }
}

/** 打开列表对话框并加载数据 */
async function openList() {
  listVisible.value = true
  await loadList()
}

/** 加载入库记录列表 */
async function loadList() {
  listLoading.value = true
  try {
    const res = await listIngest()
    records.value = res.data || []
  } catch (e) {
    ElMessage.error('加载记录失败')
  } finally {
    listLoading.value = false
  }
}

/** 查看字段信息 */
function showColumns(row) {
  currentRecord.value = row
  colVisible.value = true
}

/** 删除入库记录 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除"${row.original_filename}"的入库记录？\n数据库中对应的表 ${row.table_name} 也将被删除，操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  try {
    const res = await deleteIngest(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      await loadList()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (e) {
    ElMessage.error('删除失败: ' + (e?.message || '网络错误'))
  }
}

/** 格式化时间 */
function formatTime(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return isoStr
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<style scoped>
.data-ingest {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ingest-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ingest-tip {
  font-size: 11px;
  color: #909399;
  line-height: 1.4;
}

.list-toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
