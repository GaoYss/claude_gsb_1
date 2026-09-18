<template>
  <div class="page">
    <PageHeader title="树木档案" description="一树一档：登记树种、胸径、树高、树龄、保护级别与责任单位，复壮支撑防腐等措施逐次留痕">
      <template #actions>
        <el-button type="primary" :icon="'Plus'" @click="formDialog.open()">树木建档</el-button>
      </template>
    </PageHeader>

    <div class="panel">
      <div class="filter-bar">
        <el-input v-model="filters.keyword" placeholder="编号 / 树种 / 点位 / 责任单位" clearable
                  :prefix-icon="'Search'" @keyup.enter="search" @clear="search" />
        <el-select v-model="filters.district" placeholder="所属行政区" clearable filterable @change="search">
          <el-option v-for="item in districts" :key="item.district"
                     :label="`${item.district}（${item.count}）`" :value="item.district" />
        </el-select>
        <div style="width: 220px">
          <GreenSpaceSelect v-model="filters.green_space_id" placeholder="按绿地筛选"
                            @update:model-value="search" />
        </div>
        <el-select v-model="filters.protection_level" placeholder="保护级别" clearable @change="search">
          <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.vigor" placeholder="生长势" clearable @change="search">
          <el-option v-for="item in vigorOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" :icon="'Search'" @click="search">查询</el-button>
        <el-button :icon="'RefreshLeft'" @click="reset">重置</el-button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard label="建档树木" :value="formatNumber(summary?.total ?? meta.total)" unit="株"
                hint="按当前筛选条件统计" icon="Coin" />
      <StatCard label="名木" :value="levelCount('famous')" unit="株" tone="danger"
                hint="具有历史文化价值的名木" icon="Trophy" />
      <StatCard label="一级 / 二级保护"
                :value="`${levelCount('level1')} / ${levelCount('level2')}`"
                :hint="`另有三级保护 ${levelCount('level3')} 株`" tone="warning" icon="Warning" />
      <StatCard label="暂无级别" :value="levelCount('none')" unit="株" tone="info"
                hint="一般建档乔木，未列入保护" icon="Files" />
    </div>

    <div class="panel">
      <div class="table-toolbar">
        <span class="summary-text">共 <strong>{{ meta.total }}</strong> 株树木档案</span>
        <el-button :icon="'Refresh'" text @click="load">刷新</el-button>
      </div>

      <el-table :data="items" v-loading="loading" border stripe>
        <el-table-column prop="tree_no" label="档案编号" width="135" />
        <el-table-column label="树种" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="cell-main">{{ row.tree_species }}</div>
            <div class="cell-sub">{{ row.scientific_name || '—' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="所属绿地 / 行政区" min-width="175" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="cell-main">{{ row.green_space?.name || '-' }}</div>
            <div class="cell-sub">{{ row.green_space?.district || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="规格" width="150">
          <template #default="{ row }">
            <div class="cell-sub">胸径 {{ formatNumber(row.dbh_cm) }} cm</div>
            <div class="cell-sub">树高 {{ formatNumber(row.height_m) }} m · 树龄 {{ formatNumber(row.age_years) }} 年</div>
          </template>
        </el-table-column>
        <el-table-column label="保护级别" width="105">
          <template #default="{ row }">
            <EnumTag group="tree_protection_level" :value="row.protection_level"
                     :label="row.protection_level_label" />
          </template>
        </el-table-column>
        <el-table-column label="生长势" width="100">
          <template #default="{ row }">
            <EnumTag group="tree_vigor" :value="row.vigor" :label="row.vigor_label" />
          </template>
        </el-table-column>
        <el-table-column label="责任单位 / 点位" min-width="190" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="cell-main">{{ row.responsible_unit }}</div>
            <div class="cell-sub">{{ row.location_desc || '未填写具体点位' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="养护措施" width="140">
          <template #default="{ row }">
            <div class="cell-sub">{{ row.maintenance_count }} 次</div>
            <div class="cell-sub">最近：{{ formatDate(row.last_care_date) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">档案</el-button>
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

    <TreeFormDialog ref="formDialog" @saved="onSaved" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { treeApi } from '@/api'
import EnumTag from '@/components/common/EnumTag.vue'
import GreenSpaceSelect from '@/components/common/GreenSpaceSelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { useEnumOptions } from '@/composables/useEnumOptions'
import { useListQuery } from '@/composables/useListQuery'
import { formatDate, formatNumber } from '@/utils/format'

import TreeFormDialog from './TreeFormDialog.vue'

const route = useRoute()
const router = useRouter()
const formDialog = ref(null)
const districts = ref([])

const { options: levelOptions } = useEnumOptions('tree_protection_level')
const { options: vigorOptions } = useEnumOptions('tree_vigor')

const { filters, meta, items, summary, loading, load, search, resetFilters, handlePageChange, handleSizeChange } =
  useListQuery(treeApi.list, {
    initialFilters: {
      keyword: '',
      district: '',
      green_space_id: route.query.green_space_id ? Number(route.query.green_space_id) : null,
      protection_level: '',
      vigor: '',
    },
  })

function levelCount(value) {
  return formatNumber(summary.value?.protection_level_summary?.[value] ?? 0)
}

async function loadDistricts() {
  const data = await treeApi.districts()
  districts.value = data?.items || []
}

function reset() {
  resetFilters()
}

async function onSaved() {
  await Promise.all([load(), loadDistricts()])
}

function goDetail(row) {
  router.push({ name: 'tree-detail', params: { id: row.id } })
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除树木档案「${row.tree_species} ${row.tree_no}」吗？该树下的 ${row.maintenance_count} 条养护措施将一并删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await treeApi.remove(row.id)
    ElMessage.success('树木档案已删除')
    await onSaved()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
  }
}

onMounted(loadDistricts)
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.cell-main {
  font-weight: 500;
}

.cell-sub {
  color: #909399;
  font-size: 12px;
}
</style>
