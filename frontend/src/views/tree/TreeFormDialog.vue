<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? `编辑树木档案 · ${form.tree_no}` : '树木建档'"
    width="820px"
    top="5vh"
    destroy-on-close
    @update:model-value="close"
    @closed="fieldErrors = {}"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="所属绿地" prop="green_space_id" :error="fieldErrors.green_space_id">
            <GreenSpaceSelect v-model="form.green_space_id" :preset="spacePreset" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="树木编号" :error="fieldErrors.tree_no">
            <el-input v-model="form.tree_no" :disabled="isEdit" placeholder="留空自动生成，如 TR-2026-0001" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="树种名称" prop="tree_species" :error="fieldErrors.tree_species">
            <el-input v-model="form.tree_species" placeholder="如：香樟、银杏" maxlength="96" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="拉丁学名" :error="fieldErrors.scientific_name">
            <el-input v-model="form.scientific_name" placeholder="如：Cinnamomum camphora" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="胸径(cm)" :error="fieldErrors.dbh_cm">
            <el-input-number v-model="form.dbh_cm" :min="0" :max="1000" :precision="1"
                             :controls="false" placeholder="距地 1.3m" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="树高(m)" :error="fieldErrors.height_m">
            <el-input-number v-model="form.height_m" :min="0" :max="200" :precision="1"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="冠幅(m)" :error="fieldErrors.crown_width_m">
            <el-input-number v-model="form.crown_width_m" :min="0" :max="100" :precision="1"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="树龄(年)" :error="fieldErrors.age_years">
            <el-input-number v-model="form.age_years" :min="0" :max="5000"
                             :controls="false" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="保护级别" prop="protection_level" :error="fieldErrors.protection_level">
            <el-select v-model="form.protection_level" style="width: 100%">
              <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="生长势" prop="vigor" :error="fieldErrors.vigor">
            <el-select v-model="form.vigor" style="width: 100%">
              <el-option v-for="item in vigorOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="责任单位" prop="responsible_unit" :error="fieldErrors.responsible_unit">
            <el-input v-model="form.responsible_unit" placeholder="如：杭州市园林文物局" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="责任人" :error="fieldErrors.responsible_person">
            <el-input v-model="form.responsible_person" placeholder="如：沈建国" maxlength="64" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话" :error="fieldErrors.contact_phone">
            <el-input v-model="form.contact_phone" placeholder="如：0571-85112233" maxlength="32" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="建档日期" prop="register_date" :error="fieldErrors.register_date">
            <el-date-picker v-model="form.register_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="具体点位" :error="fieldErrors.location_desc">
            <el-input v-model="form.location_desc"
                      placeholder="如：广场中轴北端喷泉西侧 / 主步道东侧第 2 株" maxlength="255" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="经度" :error="fieldErrors.longitude">
            <el-input-number v-model="form.longitude" :min="-180" :max="180" :precision="8"
                             :controls="false" :step="0.000001" placeholder="可留空" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="纬度" :error="fieldErrors.latitude">
            <el-input-number v-model="form.latitude" :min="-90" :max="90" :precision="8"
                             :controls="false" :step="0.000001" placeholder="可留空" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="栽植日期" :error="fieldErrors.planted_date">
            <el-date-picker v-model="form.planted_date" type="date" value-format="YYYY-MM-DD"
                            placeholder="可留空" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="备注" :error="fieldErrors.remark">
            <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="2000"
                      placeholder="保护要求、历史沿革、监测情况等" />
          </el-form-item>
        </el-col>
      </el-row>
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
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { today } from '@/utils/format'

const emit = defineEmits(['saved'])

const { options: levelOptions } = useEnumOptions('tree_protection_level')
const { options: vigorOptions } = useEnumOptions('tree_vigor')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const fieldErrors = ref({})
const spacePreset = ref(null)

const form = reactive(emptyForm())
const isEdit = computed(() => editingId.value !== null)

const rules = {
  green_space_id: [{ required: true, message: '请选择所属绿地', trigger: 'change' }],
  tree_species: [{ required: true, message: '请输入树种名称', trigger: 'blur' }],
  responsible_unit: [{ required: true, message: '请输入责任单位', trigger: 'blur' }],
  protection_level: [{ required: true, message: '请选择保护级别', trigger: 'change' }],
  register_date: [{ required: true, message: '请选择建档日期', trigger: 'change' }],
}

function emptyForm() {
  return {
    tree_no: '',
    green_space_id: null,
    tree_species: '',
    scientific_name: '',
    dbh_cm: null,
    height_m: null,
    crown_width_m: null,
    age_years: null,
    protection_level: 'none',
    vigor: 'vigorous',
    responsible_unit: '',
    responsible_person: '',
    contact_phone: '',
    location_desc: '',
    longitude: null,
    latitude: null,
    planted_date: '',
    register_date: today(),
    remark: '',
  }
}

function open(row = null) {
  Object.assign(form, emptyForm())
  fieldErrors.value = {}
  spacePreset.value = null
  editingId.value = row?.id ?? null
  if (row) {
    Object.keys(form).forEach((key) => {
      if (row[key] !== undefined && row[key] !== null) form[key] = row[key]
    })
    spacePreset.value = row.green_space || null
  }
  visible.value = true
}

function close() {
  visible.value = false
}

function buildPayload() {
  const payload = { ...form }
  if (!payload.tree_no) delete payload.tree_no
  if (!payload.planted_date) delete payload.planted_date
  return payload
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  fieldErrors.value = {}
  try {
    if (isEdit.value) {
      await treeApi.update(editingId.value, buildPayload())
      ElMessage.success('树木档案已更新')
    } else {
      await treeApi.create(buildPayload())
      ElMessage.success('树木档案建档成功')
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
