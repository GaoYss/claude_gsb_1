<template>
  <div class="page">
    <PageHeader title="树木档案" description="一树一档：登记树种、体量、保护级别与责任单位，养护措施逐次归档">
      <template #actions>
        <el-button type="primary" :icon="'Plus'" @click="formDialog.open()">新建树木档案</el-button>
      </template>
    </PageHeader>

    <div class="panel">
      <div class="filter-bar">
        <el-input v-model="filters.keyword" placeholder="编号 / 树种 / 责任单位 / 位置" clearable
                  :prefix-icon="'Search'" @keyup.enter="search" @clear="search" />
        <el-select v-model="filters.protection_level" placeholder="保护级别" clearable @change="search">
          <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.district" placeholder="所属行政区" clearable @change="search">
          <el-option v-for="item in districts" :key="item.district" :label="item.district" :value="item.district" />
        </el-select>
        <div style="width: 220px">
          <GreenSpaceSelect v-model="filters.green_space_id" placeholder="按所在绿地筛选" @update:model-value="search" />
        </div>
        <el-select v-model="filters.growth_vigor" placeholder="生长势" clearable @change="search">
          <el-option v-for="item in vigorOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" :icon="'Search'" @click="search">查询</el-button>
        <el-button :icon="'RefreshLeft'" @click="reset">重置</el-button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="建档树木" :value="formatNumber(summary?.total_count ?? 0)" unit="株"
                :hint="`覆盖 ${formatNumber(summary?.district_count ?? 0)} 个行政区`" icon="Collection" />
      <StatCard label="古树名木" :value="formatNumber(ancientCount)" unit="株"
                :hint="ancientHint" tone="warning" icon="Medal" />
      <StatCard label="一级古树" :value="formatNumber(levelCount('level1'))" unit="株"
                hint="保护级别最高，重点巡查" tone="danger" icon="FirstAidKit" />
      <StatCard label="养护措施" :value="formatNumber(summary?.maintenance_count ?? 0)" unit="次"
                hint="复壮、支撑、防腐等逐次登记" tone="info" icon="Tools" />
    </div>

    <div class="panel">
      <div class="table-toolbar">
        <span class="summary-text">
          共 <strong>{{ meta.total }}</strong> 份树木档案，
          古树名木 <strong>{{ formatNumber(ancientCount) }}</strong> 株
        </span>
        <el-button :icon="'Refresh'" text @click="load">刷新</el-button>
      </div>

      <el-table :data="items" v-loading="loading" border stripe>
        <el-table-column prop="code" label="档案编号" width="140">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="goDetail(row)">{{ row.code }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="树种" min-width="140">
          <template #default="{ row }">
            <div>{{ row.species }}</div>
            <div v-if="row.latin_name" class="cell-sub">{{ row.latin_name }}</div>
          </template>
        </el-table-column>
        <el-table-column label="胸径 / 树高 / 树龄" width="170">
          <template #default="{ row }">
            <span>{{ formatNumber(row.dbh_cm) }} cm / {{ formatNumber(row.height_m) }} m / {{ row.age_years ?? '-' }} 年</span>
          </template>
        </el-table-column>
        <el-table-column label="保护级别" width="105">
          <template #default="{ row }">
            <EnumTag group="tree_protection_level" :value="row.protection_level" :label="row.protection_level_label" />
          </template>
        </el-table-column>
        <el-table-column label="生长势" width="90">
          <template #default="{ row }">
            <EnumTag v-if="row.growth_vigor" group="tree_growth_vigor" :value="row.growth_vigor" :label="row.growth_vigor_label" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="所在绿地" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.green_space?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="行政区" width="90">
          <template #default="{ row }">{{ row.green_space?.district || '-' }}</template>
        </el-table-column>
        <el-table-column prop="responsible_unit" label="责任单位" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.responsible_unit || '-' }}</template>
        </el-table-column>
        <el-table-column label="养护措施" width="100" align="center">
          <template #default="{ row }">
            <el-badge v-if="row.statistics.maintenance_count" :value="row.statistics.maintenance_count" type="primary">
              <span class="measure-cell">措施</span>
            </el-badge>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">详情</el-button>
            <el-button link type="primary" @click="formDialog.open(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="meta.total"
        :current-page="meta.page"
        :page-size="meta.page_size"
        :page-sizes="[10, 20, 50]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <TreeFormDialog ref="formDialog" @saved="load" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { greenSpaceApi, treeApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { useListQuery } from '@/composables/useListQuery'
import { formatNumber } from '@/utils/format'

import TreeFormDialog from './TreeFormDialog.vue'

const route = useRoute()
const router = useRouter()
const formDialog = ref(null)
const districts = ref([])

const { options: levelOptions } = useEnumOptions('tree_protection_level')
const { options: vigorOptions } = useEnumOptions('tree_growth_vigor')

const { filters, meta, items, summary, loading, load, search, resetFilters, handlePageChange, handleSizeChange } =
  useListQuery(treeApi.list, {
    initialFilters: {
      keyword: '',
      protection_level: '',
      district: '',
      green_space_id: route.query.green_space_id ? Number(route.query.green_space_id) : null,
      growth_vigor: '',
    },
  })

const ANCIENT_LEVELS = ['level1', 'level2', 'level3', 'famous']

const ancientCount = computed(() =>
  (summary.value?.by_level || [])
    .filter((item) => ANCIENT_LEVELS.includes(item.value))
    .reduce((sum, item) => sum + item.count, 0),
)

const ancientHint = computed(() => {
  const rows = (summary.value?.by_level || []).filter((item) => ANCIENT_LEVELS.includes(item.value))
  return rows.map((item) => `${item.label} ${item.count}`).join('、') || '暂无数据'
})

function levelCount(level) {
  return (summary.value?.by_level || []).find((item) => item.value === level)?.count ?? 0
}

function reset() {
  resetFilters()
}

function goDetail(row) {
  router.push({ name: 'tree-detail', params: { id: row.id } })
}

async function remove(row) {
  const count = row.statistics.maintenance_count
  try {
    if (count > 0) {
      await ElMessageBox.confirm(
        `该树木已登记养护措施 ${count} 次，删除将一并清除，是否继续？`,
        '存在养护记录',
        { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
      )
    } else {
      await ElMessageBox.confirm(`确认删除树木档案「${row.code}」吗？`, '删除确认', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
    }
    await treeApi.remove(row.id, count > 0 ? { force: true } : undefined)
    ElMessage.success('树木档案已删除')
    await load()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

async function loadDistricts() {
  const data = await greenSpaceApi.districts()
  districts.value = data?.items || []
}

onMounted(loadDistricts)
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.cell-sub {
  color: #909399;
  font-size: 12px;
  font-style: italic;
}

.measure-cell {
  margin-right: 4px;
}
</style>
