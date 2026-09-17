<template>
  <div class="page" v-loading="loading">
    <PageHeader :title="tree.species ? `${tree.species} · ${tree.code}` : '树木档案'"
                :description="tree.id ? `档案编号 ${tree.code}，建档于 ${formatDateTime(tree.created_at)}` : ''">
      <template #tag>
        <EnumTag v-if="tree.protection_level" group="tree_protection_level"
                 :value="tree.protection_level" :label="tree.protection_level_label" />
        <EnumTag v-if="tree.growth_vigor" group="tree_growth_vigor"
                 :value="tree.growth_vigor" :label="tree.growth_vigor_label" />
      </template>
      <template #actions>
        <el-button :icon="'Back'" @click="router.push('/trees')">返回列表</el-button>
        <el-button type="primary" :icon="'Edit'" @click="formDialog.open(tree)">编辑档案</el-button>
        <el-button type="danger" plain :icon="'Delete'" @click="removeTree">删除档案</el-button>
      </template>
    </PageHeader>

    <div class="panel">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="所在绿地">
          <el-link v-if="tree.green_space" type="primary" :underline="false"
                   @click="router.push(`/green-spaces/${tree.green_space_id}`)">
            {{ tree.green_space.name }}
          </el-link>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="所属行政区">{{ tree.green_space?.district || '-' }}</el-descriptions-item>
        <el-descriptions-item label="责任单位">{{ tree.responsible_unit || '-' }}</el-descriptions-item>
        <el-descriptions-item label="树种">{{ tree.species || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拉丁学名">
          <span class="latin">{{ tree.latin_name || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="树龄">{{ tree.age_years != null ? `${tree.age_years} 年` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="胸径">{{ tree.dbh_cm != null ? `${formatNumber(tree.dbh_cm)} cm` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="树高">{{ tree.height_m != null ? `${formatNumber(tree.height_m)} m` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="生长势">
          <EnumTag v-if="tree.growth_vigor" group="tree_growth_vigor"
                   :value="tree.growth_vigor" :label="tree.growth_vigor_label" />
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="经度">{{ formatCoordinate(tree.longitude) }}</el-descriptions-item>
        <el-descriptions-item label="纬度">{{ formatCoordinate(tree.latitude) }}</el-descriptions-item>
        <el-descriptions-item label="位置说明">{{ tree.location_desc || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ tree.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="stat-grid">
      <StatCard label="养护措施" :value="formatNumber(statistics.maintenance_count ?? 0)" unit="次"
                hint="复壮、支撑、防腐等逐次登记" icon="Tools" />
      <StatCard label="最近措施日期" :value="formatDate(statistics.last_measure_date)"
                :hint="lastMeasureHint" icon="Calendar" />
      <StatCard label="措施类型" :value="formatNumber(measureTypes.length)" unit="类"
                :hint="measureTypes.map((item) => item.label).join('、') || '暂无记录'" tone="info" icon="Files" />
      <StatCard label="树龄" :value="tree.age_years ?? '-'" unit="年"
                :hint="tree.protection_level_label ? `保护级别：${tree.protection_level_label}` : ''"
                tone="warning" icon="Histogram" />
    </div>

    <div class="panel">
      <div class="table-toolbar">
        <span class="panel-title">养护措施记录</span>
        <div class="toolbar-right">
          <el-select v-model="measureTypeFilter" placeholder="措施类型" clearable style="width: 150px">
            <el-option v-for="item in measureOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-button type="primary" :icon="'Plus'" @click="maintenanceDialog.open(tree)">登记措施</el-button>
        </div>
      </div>

      <el-table :data="filteredMaintenances" border stripe empty-text="暂无养护措施，点击右上角登记">
        <el-table-column prop="record_no" label="编号" width="150" />
        <el-table-column label="措施类型" width="110">
          <template #default="{ row }">
            <EnumTag group="tree_measure_type" :value="row.measure_type" :label="row.measure_type_label" />
          </template>
        </el-table-column>
        <el-table-column prop="measure_date" label="实施日期" width="105" />
        <el-table-column prop="content" label="措施内容" min-width="260" show-overflow-tooltip />
        <el-table-column label="实施人" width="110">
          <template #default="{ row }">{{ row.operator || '-' }}</template>
        </el-table-column>
        <el-table-column label="登记时间" width="150">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="maintenanceDialog.open(tree, row)">编辑</el-button>
            <el-button link type="danger" @click="removeMeasure(row)">删除</el-button>
          </template>
        </el-table-column>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-detail">
              <span><b>措施内容：</b>{{ row.content }}</span>
              <span v-if="row.remark"><b>备注：</b>{{ row.remark }}</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TreeFormDialog ref="formDialog" @saved="load" />
    <TreeMaintenanceFormDialog ref="maintenanceDialog" @saved="load" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { treeApi, treeMaintenanceApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { formatDate, formatDateTime, formatNumber } from '@/utils/format'

import TreeFormDialog from './TreeFormDialog.vue'
import TreeMaintenanceFormDialog from './TreeMaintenanceFormDialog.vue'

const route = useRoute()
const router = useRouter()
const formDialog = ref(null)
const maintenanceDialog = ref(null)
const loading = ref(false)

const tree = ref({})
const statistics = ref({})
const maintenances = ref([])
const measureTypeFilter = ref('')

const { options: measureOptions } = useEnumOptions('tree_measure_type')

const measureTypes = computed(() => statistics.value.by_measure_type || [])

const filteredMaintenances = computed(() => {
  if (!measureTypeFilter.value) return maintenances.value
  return maintenances.value.filter((item) => item.measure_type === measureTypeFilter.value)
})

const lastMeasureHint = computed(() => {
  const count = statistics.value.maintenance_count ?? 0
  return count > 0 ? `累计 ${count} 次养护措施` : '尚未登记养护措施'
})

function formatCoordinate(value) {
  return value === null || value === undefined ? '-' : Number(value).toFixed(6)
}

async function load() {
  loading.value = true
  try {
    const data = await treeApi.detail(route.params.id)
    tree.value = data.tree || {}
    statistics.value = data.statistics || {}
    maintenances.value = data.maintenances || []
  } finally {
    loading.value = false
  }
}

async function removeTree() {
  const count = statistics.value.maintenance_count ?? 0
  try {
    if (count > 0) {
      await ElMessageBox.confirm(
        `该树木已登记养护措施 ${count} 次，删除档案将一并清除，是否继续？`,
        '存在养护记录',
        { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
      )
    } else {
      await ElMessageBox.confirm(`确认删除树木档案「${tree.value.code}」吗？`, '删除确认', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
    }
    await treeApi.remove(tree.value.id, count > 0 ? { force: true } : undefined)
    ElMessage.success('树木档案已删除')
    router.push('/trees')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

async function removeMeasure(row) {
  try {
    await ElMessageBox.confirm(`确认删除养护措施「${row.record_no}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await treeMaintenanceApi.remove(row.id)
    ElMessage.success('树木养护措施已删除')
    await load()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

onMounted(load)
</script>

<style scoped>
.latin {
  font-style: italic;
}

.panel-title {
  font-weight: 600;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.expand-detail {
  display: grid;
  gap: 6px;
  padding: 4px 12px;
  color: #606266;
  font-size: 13px;
}
</style>
