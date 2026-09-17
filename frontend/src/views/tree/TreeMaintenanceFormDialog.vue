<template>
  <el-dialog :model-value="visible"
             :title="isEdit ? `编辑养护措施 · ${form.record_no}` : '登记养护措施'"
             width="640px" top="8vh" destroy-on-close @update:model-value="close">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="措施类型" prop="measure_type" :error="fieldErrors.measure_type">
            <el-select v-model="form.measure_type" placeholder="请选择" style="width: 100%">
              <el-option v-for="item in measureOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实施日期" prop="measure_date" :error="fieldErrors.measure_date">
            <el-date-picker v-model="form.measure_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="措施内容" prop="content" :error="fieldErrors.content">
        <el-input v-model="form.content" type="textarea" :rows="3" maxlength="2000"
                  placeholder="如：开挖放射状复壮沟 4 条，回填腐殖土并施生物有机肥" />
      </el-form-item>
      <el-form-item label="实施人" :error="fieldErrors.operator">
        <el-input v-model="form.operator" placeholder="作业人员或班组" maxlength="64" />
      </el-form-item>
      <el-form-item label="备注" :error="fieldErrors.remark">
        <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="2000" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { treeMaintenanceApi } from '@/api'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { today } from '@/utils/format'

const emit = defineEmits(['saved'])

const { options: measureOptions } = useEnumOptions('tree_measure_type')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const treeId = ref(null)
const fieldErrors = ref({})
const form = reactive(emptyForm())

const isEdit = computed(() => editingId.value !== null)

const rules = {
  measure_type: [{ required: true, message: '请选择措施类型', trigger: 'change' }],
  measure_date: [{ required: true, message: '请选择实施日期', trigger: 'change' }],
  content: [{ required: true, message: '请填写措施内容', trigger: 'blur' }],
}

function emptyForm() {
  return {
    record_no: '',
    measure_type: '',
    measure_date: today(),
    content: '',
    operator: '',
    remark: '',
  }
}

function open(tree, row = null) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  treeId.value = tree?.id ?? row?.tree_id ?? null
  editingId.value = row?.id ?? null
  if (row) {
    Object.keys(form).forEach((key) => {
      if (row[key] !== undefined && row[key] !== null) form[key] = row[key]
    })
  }
  visible.value = true
}

function close() {
  visible.value = false
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  fieldErrors.value = {}
  const payload = { ...form, tree_id: treeId.value }
  delete payload.record_no
  try {
    if (isEdit.value) {
      await treeMaintenanceApi.update(editingId.value, payload)
      ElMessage.success('树木养护措施已更新')
    } else {
      await treeMaintenanceApi.create(payload)
      ElMessage.success('树木养护措施登记成功')
    }
    emit('saved')
    close()
  } catch (error) {
    fieldErrors.value = error?.details || {}
  } finally {
    submitting.value = false
  }
}

defineExpose({ open })
</script>
