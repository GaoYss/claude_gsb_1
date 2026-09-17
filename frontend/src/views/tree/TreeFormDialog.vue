<template>
  <el-dialog :model-value="visible"
             :title="isEdit ? `编辑树木档案 · ${form.code}` : '新建树木档案'"
             width="760px" top="6vh" destroy-on-close @update:model-value="close">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="所在绿地" prop="green_space_id" :error="fieldErrors.green_space_id">
        <GreenSpaceSelect v-model="form.green_space_id" :preset="spacePreset" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="树种" prop="species" :error="fieldErrors.species">
            <el-input v-model="form.species" placeholder="如：香樟" maxlength="96" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="拉丁学名" :error="fieldErrors.latin_name">
            <el-input v-model="form.latin_name" placeholder="如：Cinnamomum camphora" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="保护级别" prop="protection_level" :error="fieldErrors.protection_level">
            <el-select v-model="form.protection_level" placeholder="请选择" style="width: 100%">
              <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="生长势" :error="fieldErrors.growth_vigor">
            <el-select v-model="form.growth_vigor" clearable placeholder="请选择" style="width: 100%">
              <el-option v-for="item in vigorOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="胸径（cm）" :error="fieldErrors.dbh_cm">
            <el-input-number v-model="form.dbh_cm" :min="0" :max="9999" :precision="2"
                             :controls="false" placeholder="胸高直径" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="树高（m）" :error="fieldErrors.height_m">
            <el-input-number v-model="form.height_m" :min="0" :max="200" :precision="2"
                             :controls="false" placeholder="树冠顶端至地面高度" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="树龄（年）" :error="fieldErrors.age_years">
            <el-input-number v-model="form.age_years" :min="0" :max="9999" :precision="0"
                             :controls="false" placeholder="估测树龄" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="责任单位" :error="fieldErrors.responsible_unit">
            <el-input v-model="form.responsible_unit" placeholder="如：杭州市绿化管理站" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="经度" :error="fieldErrors.longitude">
            <el-input-number v-model="form.longitude" :min="-180" :max="180" :precision="6"
                             :controls="false" placeholder="如：120.155100" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="纬度" :error="fieldErrors.latitude">
            <el-input-number v-model="form.latitude" :min="-90" :max="90" :precision="6"
                             :controls="false" placeholder="如：30.274200" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="位置说明" :error="fieldErrors.location_desc">
        <el-input v-model="form.location_desc" placeholder="补充描述点位，如：主入口东侧约 30 米" maxlength="255" />
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
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'

const emit = defineEmits(['saved'])

const { options: levelOptions } = useEnumOptions('tree_protection_level')
const { options: vigorOptions } = useEnumOptions('tree_growth_vigor')

const formRef = ref(null)
const visible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const fieldErrors = ref({})
const spacePreset = ref(null)
const form = reactive(emptyForm())

const isEdit = computed(() => editingId.value !== null)

const rules = {
  green_space_id: [{ required: true, message: '请选择所在绿地', trigger: 'change' }],
  species: [{ required: true, message: '请输入树种', trigger: 'blur' }],
  protection_level: [{ required: true, message: '请选择保护级别', trigger: 'change' }],
}

function emptyForm() {
  return {
    code: '',
    green_space_id: null,
    species: '',
    latin_name: '',
    dbh_cm: null,
    height_m: null,
    age_years: null,
    protection_level: 'ordinary',
    growth_vigor: '',
    responsible_unit: '',
    longitude: null,
    latitude: null,
    location_desc: '',
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

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  fieldErrors.value = {}
  const payload = { ...form }
  if (!payload.code) delete payload.code
  if (!payload.growth_vigor) payload.growth_vigor = null
  try {
    if (isEdit.value) {
      await treeApi.update(editingId.value, payload)
      ElMessage.success('树木档案已更新')
    } else {
      await treeApi.create(payload)
      ElMessage.success('树木档案创建成功')
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
