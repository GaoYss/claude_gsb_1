<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑养护措施' : '登记养护措施'"
    width="640px"
    top="8vh"
    destroy-on-close
    @update:model-value="close"
    @closed="fieldErrors = {}"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="措施类型" prop="care_type" :error="fieldErrors.care_type">
        <el-select v-model="form.care_type" placeholder="如：复壮、支撑、防腐" style="width: 100%">
          <el-option v-for="item in careOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="实施日期" prop="care_date" :error="fieldErrors.care_date">
        <el-date-picker v-model="form.care_date" type="date" value-format="YYYY-MM-DD"
                        placeholder="选择日期" style="width: 100%" />
      </el-form-item>
      <el-form-item label="措施内容" prop="content" :error="fieldErrors.content">
        <el-input v-model="form.content" type="textarea" :rows="3" maxlength="2000" show-word-limit
                  placeholder="如：清理腐烂木质部，涂布杀菌剂与防腐剂后做防腐封闭" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="实施人员" :error="fieldErrors.operator">
            <el-input v-model="form.operator" placeholder="如：李建民 / 古树名木保护班组" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="费用(元)" :error="fieldErrors.cost">
            <el-input-number v-model="form.cost" :min="0" :precision="2" :controls="false"
                             placeholder="可留空" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="实施效果" :error="fieldErrors.result">
        <el-input v-model="form.result" placeholder="如：支撑牢固，树势有所恢复" maxlength="255" />
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

import { treeApi } from '@/api'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { today } from '@/utils/format'

const emit = defineEmits(['saved'])

const { options: careOptions } = useEnumOptions('tree_care_type')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const treeId = ref(null)
const editingId = ref(null)
const fieldErrors = ref({})

const form = reactive(emptyForm())
const isEdit = computed(() => editingId.value !== null)

const rules = {
  care_type: [{ required: true, message: '请选择措施类型', trigger: 'change' }],
  care_date: [{ required: true, message: '请选择实施日期', trigger: 'change' }],
  content: [{ required: true, message: '请填写措施内容', trigger: 'blur' }],
}

function emptyForm() {
  return {
    care_type: 'rejuvenate',
    care_date: today(),
    content: '',
    operator: '',
    result: '',
    cost: null,
    remark: '',
  }
}

function open(tree, row = null) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  treeId.value = tree?.id ?? null
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
  const payload = { ...form }
  try {
    if (isEdit.value) {
      await treeApi.updateMaintenance(treeId.value, editingId.value, payload)
      ElMessage.success('养护措施已更新')
    } else {
      await treeApi.createMaintenance(treeId.value, payload)
      ElMessage.success('养护措施已登记')
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
