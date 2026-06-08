<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="480px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入名称" clearable />
      </el-form-item>
      <el-form-item label="行政区划">
        <el-cascader
          v-model="xzqhSelected"
          :options="xzqhTree"
          :props="cascaderProps"
          :loading="xzqhLoading"
          clearable
          filterable
          placeholder="请选择行政区划（可搜索）"
          style="width: 100%"
          @change="onXzqhChange"
        />
      </el-form-item>
      <el-form-item label="地址" prop="address">
        <el-input v-model="form.address" placeholder="请输入详细地址" clearable />
      </el-form-item>
      <el-form-item label="备注">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="2"
          placeholder="备注信息（选填）"
        />
      </el-form-item>
      <el-form-item label="附件">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          :file-list="fileList"
          :limit="5"
          :on-exceed="onExceed"
          :accept="acceptTypes"
          multiple
        >
          <el-button size="small" type="primary">选择文件</el-button>
          <template #tip>
            <div class="upload-tip">支持图片/Word/PDF等，最多5个，单个不超过50MB</div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取 消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ loading ? '保存中...' : '保 存' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useXzqhStore } from '../stores/xzqh'
import { uploadAttachments, listAttachments, deleteAttachment, getAttachmentDownloadUrl } from '../api/attachment'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  drawType: { type: Number, default: 1 },  // 1=点 2=线 3=面
  editData: { type: Object, default: null }  // 编辑模式时传入的要素数据
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel', 'attachments-uploaded'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const typeLabel = computed(() => ({
  1: '点',
  2: '线',
  3: '面'
}[props.drawType] || ''))

const dialogTitle = computed(() => {
  const label = typeLabel.value
  return props.editData ? `编辑${label}要素` : `新增${label}要素`
})

const formRef = ref(null)
const uploadRef = ref(null)
const loading = ref(false)

// 附件相关
const fileList = ref([])          // el-upload 展示用的文件列表
const existingAttachments = ref([])  // 已上传的附件列表（编辑模式从后端加载）
const pendingFiles = ref([])         // 待上传的原始文件对象
const acceptTypes = '.jpg,.jpeg,.png,.gif,.bmp,.webp,.svg,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.pdf,.txt,.csv,.zip,.rar'

const form = reactive({
  name: '',
  address: '',
  remark: ''
})

// 行政区划级联选择器状态
const xzqhSelected = ref(null)   // 选中的 code
const xzqhName = ref('')          // 选中的名称（用于保存）
const xzqhCode = ref('')          // 选中的代码（用于保存）
const xzqhTree = ref([])
const xzqhLoading = ref(false)
const xzqhStore = useXzqhStore()

const cascaderProps = {
  checkStrictly: true,  // 允许选中任意一级
  emitPath: false       // 只返回最后一级 value(code)
}

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

// 加载行政区划树（从 store 获取，仅首次调接口）
onMounted(async () => {
  xzqhLoading.value = true
  try {
    await xzqhStore.fetchTree()
    xzqhTree.value = xzqhStore.treeData
  } finally {
    xzqhLoading.value = false
  }
})

// 弹窗打开时重置/回填表单
watch(() => props.modelValue, (val) => {
  if (val) {
    if (props.editData) {
      fillForm(props.editData)
    } else {
      resetForm()
    }
  }
})

function fillForm(data) {
  form.name = data.name || ''
  form.address = data.address || ''
  form.remark = data.remark || ''
  xzqhSelected.value = data.code || null
  xzqhName.value = data.xzqhname || ''
  xzqhCode.value = data.code || ''
  // 清空待上传文件
  pendingFiles.value = []
  // 编辑模式：从后端加载已有附件列表
  if (data.id) {
    loadExistingAttachments(data.id)
  } else {
    existingAttachments.value = []
    fileList.value = []
  }
  formRef.value?.clearValidate()
}

/** 从后端加载已有附件并回显 */
async function loadExistingAttachments(featureId) {
  try {
    const res = await listAttachments(featureId)
    existingAttachments.value = res.data || []
    // 将已有附件转为 el-upload 的 fileList 格式用于展示
    fileList.value = existingAttachments.value.map(att => ({
      name: att.filename,
      url: getAttachmentDownloadUrl(att.id),
      status: 'success',
      uid: -att.id,  // 用负数ID避免和新增文件冲突
      response: att  // 保存附件元信息
    }))
  } catch (e) {
    existingAttachments.value = []
    fileList.value = []
  }
}

function resetForm() {
  form.name = ''
  form.address = ''
  form.remark = ''
  xzqhSelected.value = null
  xzqhName.value = ''
  xzqhCode.value = ''
  fileList.value = []
  pendingFiles.value = []
  existingAttachments.value = []
  formRef.value?.clearValidate()
}

/** 附件文件选择/移除 */
function onFileChange(file) {
  pendingFiles.value.push(file.raw)
}
function onFileRemove(file) {
  // 区分已有附件和新上传附件
  if (file.response) {
    // 已有附件：调用后端删除
    const att = file.response
    existingAttachments.value = existingAttachments.value.filter(a => a.id !== att.id)
    deleteAttachment(att.id).catch(e => console.warn('删除附件失败:', e))
  } else {
    // 新上传附件：从待上传列表移除
    const idx = pendingFiles.value.findIndex(f => f === file.raw)
    if (idx > -1) pendingFiles.value.splice(idx, 1)
  }
}
function onExceed() {
  ElMessage.warning('最多上传5个附件')
}

/** 行政区划选中时，记录 name 和 code */
function onXzqhChange(code) {
  if (!code) {
    xzqhName.value = ''
    xzqhCode.value = ''
    return
  }
  const node = findNode(xzqhTree.value, code)
  if (node) {
    xzqhName.value = node.fullname || node.label
    xzqhCode.value = node.code || node.value
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

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    emit('submit', {
      name: form.name,
      xzqhname: xzqhName.value,
      code: xzqhCode.value,
      address: form.address,
      remark: form.remark,
      pendingFiles: pendingFiles.value  // 传给父组件，由父组件在保存要素后上传
    })
  } finally {
    loading.value = false
  }
}

/** 供父组件调用：要素保存成功后上传附件 */
async function uploadPendingAttachments(featureId) {
  if (!pendingFiles.value.length) return
  try {
    const res = await uploadAttachments(featureId, pendingFiles.value)
    emit('attachments-uploaded', res.data)
    pendingFiles.value = []
    fileList.value = []
  } catch (e) {
    console.error('附件上传失败:', e)
  }
}

function handleClose() {
  emit('cancel')
  emit('update:modelValue', false)
}

// 暴露 setLoading / uploadPendingAttachments 让父组件控制
defineExpose({
  setLoading: (val) => { loading.value = val },
  uploadPendingAttachments
})
</script>

<style scoped>
.upload-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 4px;
}
</style>
