<template>
  <div class="page" v-loading="loading">
    <PageHeader :title="`${tree.tree_species || '树木'} · ${tree.tree_no || ''}`"
                :description="tree.scientific_name || '树木单独档案'">
      <template #tag>
        <EnumTag v-if="tree.protection_level" group="tree_protection_level"
                 :value="tree.protection_level" :label="tree.protection_level_label" />
      </template>
      <template #actions>
        <el-button :icon="'Back'" @click="router.push('/trees')">返回档案列表</el-button>
        <el-button type="primary" :icon="'Edit'" @click="formDialog.open(tree)">编辑档案</el-button>
      </template>
    </PageHeader>

    <div class="panel">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="所属绿地">
          <el-link type="primary" :underline="false" @click="openGreenSpace">
            {{ tree.green_space?.name || '-' }}
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="行政区">{{ tree.green_space?.district || '-' }}</el-descriptions-item>
        <el-descriptions-item label="生长势">
          <EnumTag group="tree_vigor" :value="tree.vigor" :label="tree.vigor_label" />
        </el-descriptions-item>
        <el-descriptions-item label="胸径">{{ formatNumber(tree.dbh_cm) }} cm</el-descriptions-item>
        <el-descriptions-item label="树高">{{ formatNumber(tree.height_m) }} m</el-descriptions-item>
        <el-descriptions-item label="冠幅">{{ formatNumber(tree.crown_width_m) }} m</el-descriptions-item>
        <el-descriptions-item label="树龄">{{ formatNumber(tree.age_years) }} 年</el-descriptions-item>
        <el-descriptions-item label="栽植日期">{{ formatDate(tree.planted_date) }}</el-descriptions-item>
        <el-descriptions-item label="建档日期">{{ formatDate(tree.register_date) }}</el-descriptions-item>
        <el-descriptions-item label="责任单位" :span="2">{{ tree.responsible_unit || '-' }}</el-descriptions-item>
        <el-descriptions-item label="责任人">{{ tree.responsible_person || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ tree.contact_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="具体点位" :span="2">
          {{ tree.location_desc || '-' }}
          <el-button v-if="hasCoordinate" link type="primary" :icon="'Location'"
                     @click="openMap">地图定位</el-button>
        </el-descriptions-item>
        <el-descriptions-item label="经纬度">
          <template v-if="hasCoordinate">
            {{ tree.longitude }}, {{ tree.latitude }}
          </template>
          <template v-else>-</template>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ tree.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="stat-grid">
      <StatCard label="累计养护措施" :value="formatNumber(statistics.maintenance_count)" unit="次"
                :hint="`最近一次：${formatDate(statistics.last_care_date)}`" icon="SetUp" />
      <StatCard label="养护费用合计" :value="formatCurrency(statistics.total_cost)"
                hint="按已登记措施费用汇总" tone="info" icon="Money" />
      <StatCard label="措施类型" :value="careSummary.length" unit="类"
                :hint="careSummary.map((item) => item.care_type_label).join('、') || '暂无记录'"
                icon="Operation" />
      <StatCard label="保护级别" :value="tree.protection_level_label || '-'"
                :hint="`生长势：${tree.vigor_label || '-'}`" tone="warning" icon="Warning" />
    </div>

    <div class="panel">
      <div class="table-toolbar">
        <span class="panel-title">养护措施记录</span>
        <el-button type="primary" :icon="'Plus'" @click="careDialog.open(tree)">登记养护措施</el-button>
      </div>

      <el-table :data="tree.maintenances || []" size="small" border stripe
                empty-text="暂无养护措施，可登记复壮、支撑、防腐等记录">
        <el-table-column prop="care_date" label="实施日期" width="115" />
        <el-table-column label="措施类型" width="120">
          <template #default="{ row }">
            <EnumTag group="tree_care_type" :value="row.care_type" :label="row.care_type_label" />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="措施内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="operator" label="实施人员" width="130">
          <template #default="{ row }">{{ row.operator || '-' }}</template>
        </el-table-column>
        <el-table-column prop="result" label="实施效果" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.result || '-' }}</template>
        </el-table-column>
        <el-table-column label="费用" width="110" align="right">
          <template #default="{ row }">{{ formatCurrency(row.cost) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="careDialog.open(tree, row)">编辑</el-button>
            <el-button link type="danger" @click="removeCare(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <TreeFormDialog ref="formDialog" @saved="load" />
    <TreeMaintenanceDialog ref="careDialog" @saved="load" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { treeApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { formatCurrency, formatDate, formatNumber } from '@/utils/format'

import TreeFormDialog from './TreeFormDialog.vue'
import TreeMaintenanceDialog from './TreeMaintenanceDialog.vue'

const route = useRoute()
const router = useRouter()
const formDialog = ref(null)
const careDialog = ref(null)
const loading = ref(false)

const tree = ref({ maintenances: [] })
const statistics = ref({ maintenance_count: 0, total_cost: 0, last_care_date: null })
const careSummary = ref([])

const hasCoordinate = computed(
  () => tree.value.longitude !== null && tree.value.longitude !== undefined
    && tree.value.latitude !== null && tree.value.latitude !== undefined,
)

async function load() {
  loading.value = true
  try {
    const data = await treeApi.profile(route.params.id)
    tree.value = data.tree || { maintenances: [] }
    statistics.value = data.statistics || {}
    careSummary.value = data.care_summary || []
  } finally {
    loading.value = false
  }
}

function openGreenSpace() {
  if (tree.value.green_space_id) {
    router.push({ name: 'green-space-detail', params: { id: tree.value.green_space_id } })
  }
}

function openMap() {
  const { longitude, latitude } = tree.value
  window.open(`https://uri.amap.com/marker?position=${longitude},${latitude}&src=green-care`, '_blank')
}

async function removeCare(row) {
  try {
    await ElMessageBox.confirm(`确认删除 ${row.care_date} 的「${row.care_type_label}」记录吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await treeApi.removeMaintenance(tree.value.id, row.id)
    ElMessage.success('养护措施已删除')
    await load()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

onMounted(load)
</script>

<style scoped>
.panel-title {
  font-weight: 600;
}
</style>
