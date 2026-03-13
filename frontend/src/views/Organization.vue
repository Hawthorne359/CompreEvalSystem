<template>
  <div class="page-shell" @click="clearHighlight">
    <h3 class="app-page-title hidden md:block">组织架构</h3>

    <!-- ===== 架构总览 ===== -->
    <section class="dash-section">
      <div class="dash-section__header">
        <div class="flex items-center gap-2 flex-shrink-0 min-w-0">
          <svg class="h-5 w-5 text-brand-500 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="5" rx="1"/><rect x="2" y="17" width="6" height="5" rx="1"/><rect x="16" y="17" width="6" height="5" rx="1"/><path d="M12 7v5M5 17v-3a2 2 0 012-2h10a2 2 0 012 2v3"/></svg>
          <span class="whitespace-nowrap">架构总览</span>
        </div>
        <button
          type="button"
          class="text-xs text-slate-500 hover:text-slate-700"
          @click="treeCollapsed = !treeCollapsed"
        >
          {{ treeCollapsed ? '展开' : '收起' }}
        </button>
      </div>
      <transition name="tree-slide">
        <div v-if="!treeCollapsed">

          <!-- ── 院系架构 ── -->
          <div class="org-section-block">
            <div class="org-section-title">
              <svg class="h-4 w-4 text-brand-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="9" rx="1"/><rect x="8" y="14" width="8" height="7" rx="1"/><path d="M6.5 12v2M17.5 12v2"/></svg>
              <span>院系架构</span>
              <button type="button" class="ml-auto text-xs text-slate-400 hover:text-slate-600" @click="orgTreeCollapsed = !orgTreeCollapsed">
                {{ orgTreeCollapsed ? '展开' : '收起' }}
              </button>
            </div>
            <div v-if="!orgTreeCollapsed" class="p-4 overflow-x-auto">
              <div v-if="unifiedTreeLoading" class="py-4 text-center text-sm text-slate-500">加载中…</div>
              <div v-else-if="unifiedTree.length === 0" class="py-4 text-center text-sm text-slate-500">暂无组织数据</div>
              <div v-else class="org-tree-root flex flex-wrap justify-center gap-6">
                <div
                  v-for="dept in unifiedTree"
                  :key="`org-dept-${dept.id}`"
                  class="org-tree-dept"
                >
                  <div class="org-node org-node--dept" @click="toggleTreeDept(dept.id)">
                    <div class="org-node__icon org-node__icon--dept">
                      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="9" rx="1"/><rect x="8" y="14" width="8" height="7" rx="1"/><path d="M6.5 12v2M17.5 12v2"/></svg>
                    </div>
                    <span class="org-node__label">{{ dept.name }}</span>
                    <svg v-if="dept.majors.length" class="org-node__arrow" :class="expandedDepts.has(dept.id) ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
                  </div>
                  <div v-if="expandedDepts.has(dept.id) && dept.majors.length" class="org-tree-children">
                    <div v-for="major in dept.majors" :key="`org-major-${major.id}`" class="org-tree-major">
                      <div class="org-connector"></div>
                      <div class="org-node org-node--major" @click="toggleTreeMajor(major.id)">
                        <div class="org-node__icon org-node__icon--major">
                          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
                        </div>
                        <span class="org-node__label">{{ major.name }}</span>
                        <span v-if="major.grades?.length" class="org-node__badge">{{ major.grades.length }}个年级</span>
                        <svg v-if="major.classes?.length" class="org-node__arrow" :class="expandedMajors.has(major.id) ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
                      </div>
                      <div v-if="expandedMajors.has(major.id) && major.classes?.length" class="org-tree-leaves">
                        <div v-for="cls in major.classes" :key="`org-cls-${cls.id}`" class="org-tree-leaf">
                          <div class="org-connector org-connector--sm"></div>
                          <div class="org-node org-node--class" @click="selectClass(cls)">
                            <div class="org-node__icon org-node__icon--class">
                              <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
                            </div>
                            <span class="org-node__label">{{ cls.name }}</span>
                            <span v-if="cls.grade" class="org-node__badge">{{ cls.grade }}级</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── 人员架构 ── -->
          <div class="org-section-block">
            <div class="org-section-title">
              <svg class="h-4 w-4 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
              <span>人员架构</span>
              <button type="button" class="ml-auto text-xs text-slate-400 hover:text-slate-600" @click="staffTreeCollapsed = !staffTreeCollapsed">
                {{ staffTreeCollapsed ? '展开' : '收起' }}
              </button>
            </div>
            <div v-if="!staffTreeCollapsed" class="p-4 overflow-x-auto">
              <div v-if="unifiedTreeLoading" class="py-4 text-center text-sm text-slate-500">加载中…</div>
              <div v-else-if="personnelDepts.length === 0" class="py-4 text-center text-sm text-slate-500">暂无人员数据</div>
              <div v-else class="org-tree-root flex flex-wrap justify-center gap-6">
                <div
                  v-for="dept in personnelDepts"
                  :key="`staff-dept-${dept.id}`"
                  class="org-tree-dept"
                >
                  <div class="org-node org-node--dept" @click="toggleStaffDept(dept.id)">
                    <div class="org-node__icon org-node__icon--dept">
                      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="9" rx="1"/><rect x="8" y="14" width="8" height="7" rx="1"/><path d="M6.5 12v2M17.5 12v2"/></svg>
                    </div>
                    <span class="org-node__label">{{ dept.name }}</span>
                    <span class="org-node__badge">{{ dept.personCount }}人</span>
                    <svg v-if="dept.personCount" class="org-node__arrow" :class="expandedStaffDepts.has(dept.id) ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
                  </div>

                  <div v-if="expandedStaffDepts.has(dept.id)" class="org-tree-children">
                    <!-- 院系负责人 -->
                    <div v-for="dir in dept.directors" :key="`staff-dir-${dir.id}`" class="org-tree-major">
                      <div class="org-connector"></div>
                      <div class="org-node org-node--director">
                        <div class="org-node__icon org-node__icon--director">
                          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                        </div>
                        <span class="org-node__label">{{ dir.name }}</span>
                        <span class="org-node__badge">{{ dir.role_name }}</span>
                      </div>
                    </div>

                    <!-- 辅导员/评审老师 -->
                    <div v-for="coun in dept.counselors" :key="`staff-coun-${coun.id}`" class="org-tree-major">
                      <div class="org-connector"></div>
                      <div class="org-node org-node--counselor" @click="toggleStaffCounselor(coun.id)">
                        <div class="org-node__icon org-node__icon--counselor">
                          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
                        </div>
                        <span class="org-node__label">{{ coun.name }}</span>
                        <span class="org-node__badge">{{ coun.role_name }}</span>
                        <span v-for="cn in coun.classNames" :key="cn" class="org-node__badge">{{ cn }}</span>
                        <svg v-if="coun.assistants.length" class="org-node__arrow" :class="expandedStaffCounselors.has(coun.id) ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
                      </div>

                      <!-- 学生助理 -->
                      <div v-if="expandedStaffCounselors.has(coun.id) && coun.assistants.length" class="org-tree-leaves">
                        <div v-for="asst in coun.assistants" :key="`staff-asst-${asst.id}-${asst.class_id}`" class="org-tree-leaf">
                          <div class="org-connector org-connector--sm"></div>
                          <div class="org-node org-node--assistant">
                            <div class="org-node__icon org-node__icon--assistant">
                              <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                            </div>
                            <span class="org-node__label">{{ asst.name }}</span>
                            <span class="org-node__badge">{{ asst.role_name }}</span>
                            <span v-if="asst.class_name" class="org-node__badge">{{ asst.class_name }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </transition>
    </section>

    <!-- ===== 院系列表 ===== -->
    <section>
      <div class="mb-3 flex items-center justify-between">
        <h4 class="text-base font-medium text-slate-700">院系列表</h4>
        <button
          v-if="isAdmin"
          type="button"
          class="app-btn app-btn-primary app-btn-sm"
          @click="openDeptModal('create')"
        >
          新建院系
        </button>
      </div>
      <div
        v-if="isAdmin && deptBulkActionVisible"
        class="mb-3 hidden md:flex items-center gap-2 rounded border border-brand-200 bg-brand-50 px-3 py-2 text-sm"
      >
        <span class="text-slate-700">
          已选 <span class="font-semibold text-slate-900">{{ selectedDeptCount }}</span> 个院系
        </span>
        <button
          type="button"
          class="ml-auto rounded border border-red-200 bg-white px-2.5 py-1 text-xs text-red-600 hover:bg-red-50"
          @click="openBatchDeleteDialog('dept')"
        >
          批量删除
        </button>
      </div>
      <div v-if="deptLoading" class="rounded border border-slate-200 bg-white py-8 text-center text-slate-500">加载中…</div>
      <div v-else-if="deptError" class="rounded border border-red-200 bg-red-50 py-3 px-4 text-sm text-red-700">{{ deptError }}</div>
      <div v-else>
        <!-- 移动端院系卡片 -->
        <div class="mobile-card-list">
          <div
            v-for="row in departmentRows"
            :key="`mobile-dept-${row.id}`"
            class="mobile-card"
            :class="row.id === lastHighlightDeptId ? 'bg-blue-50' : ''"
          >
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <div class="mobile-card-title">{{ row.name }}</div>
                <div class="mobile-card-sub">编码：{{ row.code || '—' }}</div>
                <div class="mobile-card-meta">
                  专业：{{ majorsByDept[row.id]?.length ? majorsByDept[row.id].map((m) => m.name).join('、') : '暂无' }}
                </div>
              </div>
            </div>
            <div v-if="isAdmin" class="mt-2 flex gap-3 text-xs">
              <button type="button" class="app-action app-action-default" @click.stop="openDeptModal('edit', row)">编辑</button>
              <button type="button" class="app-action app-action-danger" @click.stop="openConfirmDel('dept', row.id, row.name)">删除</button>
            </div>
          </div>
          <div v-if="departmentRows.length === 0" class="text-center py-6 text-sm text-slate-500">暂无院系数据</div>
        </div>
        <!-- 桌面端院系表格 -->
        <div class="app-table-wrap hidden md:block">
        <table class="app-table">
          <thead>
            <tr class="border-b border-slate-200 bg-slate-50">
              <th v-if="isAdmin" class="px-4 py-2.5 text-left font-medium text-slate-700 w-12">
                <input
                  type="checkbox"
                  class="rounded border-slate-300"
                  :checked="allDeptSelected"
                  :disabled="departmentRows.length === 0"
                  @change="toggleSelectAllDept($event.target.checked)"
                />
              </th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">院系名称</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">编码</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">包含专业</th>
              <th v-if="isAdmin" class="px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="row in departmentRows" :key="row.id">
              <tr class="border-b border-slate-100" :class="row.id === lastHighlightDeptId ? 'bg-blue-50' : 'hover:bg-slate-50'">
                <td v-if="isAdmin" class="px-4 py-2.5">
                  <input
                    type="checkbox"
                    class="rounded border-slate-300"
                    :checked="isDeptSelected(row.id)"
                    @change="toggleDeptSelection(row.id, $event.target.checked)"
                  />
                </td>
                <td class="px-4 py-2.5 text-slate-800">{{ row.name }}</td>
                <td class="px-4 py-2.5 text-slate-600">{{ row.code || '—' }}</td>
                <td class="px-4 py-2.5 text-slate-600">
                  <span v-if="majorsByDept[row.id]?.length">
                    {{ majorsByDept[row.id].map((m) => m.name).join('、') }}
                  </span>
                  <span v-else class="text-slate-400">暂无</span>
                </td>
                <td v-if="isAdmin" class="px-4 py-2.5">
                  <div class="flex gap-3">
                    <button type="button" class="app-action app-action-default" @click="openDeptModal('edit', row)">编辑</button>
                    <button type="button" class="app-action app-action-danger" @click="openConfirmDel('dept', row.id, row.name)">删除</button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="departmentRows.length === 0">
              <td :colspan="isAdmin ? 5 : 3" class="px-4 py-6 text-center text-slate-500">暂无院系数据</td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>
    </section>

    <!-- ===== 班级列表 ===== -->
    <section>
      <div class="mb-3 flex items-center justify-between">
        <h4 class="text-base font-medium text-slate-700">班级列表</h4>
        <button v-if="isAdmin" type="button" class="app-btn app-btn-primary app-btn-sm" @click="openClassModal('create')">
          新建班级
        </button>
      </div>
      <div class="app-surface p-3 md:p-4 mb-3">
        <div class="app-filter-wrap">
        <label class="flex flex-col gap-1 text-sm text-slate-600">
          <span>院系</span>
          <select v-model="filterDepartment" class="app-select" @change="onFilterDepartmentChange">
            <option value="">全部</option>
            <option v-for="d in flatDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1 text-sm text-slate-600">
          <span>专业</span>
          <select v-model="filterMajor" class="app-select">
            <option value="">全部</option>
            <option v-for="m in majorList" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1 text-sm text-slate-600">
          <span>年级</span>
          <input v-model="filterGrade" type="text" placeholder="如 2021" class="app-input" />
        </label>
        <button type="button" class="self-end rounded-lg bg-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-300" @click="classPage = 1; loadClasses()">查询</button>
        </div>
      </div>
      <div
        v-if="isAdmin && classBulkActionVisible"
        class="mb-3 hidden md:flex items-center gap-2 rounded border border-brand-200 bg-brand-50 px-3 py-2 text-sm"
      >
        <span class="text-slate-700">
          已选 <span class="font-semibold text-slate-900">{{ selectedClassCount }}</span> 个班级
        </span>
        <button
          type="button"
          class="ml-auto rounded border border-red-200 bg-white px-2.5 py-1 text-xs text-red-600 hover:bg-red-50"
          @click="openBatchDeleteDialog('class')"
        >
          批量删除
        </button>
      </div>
      <div v-if="classLoading" class="rounded border border-slate-200 bg-white py-8 text-center text-slate-500">加载中…</div>
      <div v-else-if="classError" class="rounded border border-red-200 bg-red-50 py-3 px-4 text-sm text-red-700">{{ classError }}</div>
      <div v-else>
        <!-- 移动端班级卡片 -->
        <div class="mobile-card-list">
          <div
            v-for="c in pagedClassList"
            :key="`mobile-class-${c.id}`"
            class="mobile-card"
            :class="(c.id === selectedClassId || c.id === lastHighlightClassId) ? 'bg-blue-50' : ''"
          >
            <div class="flex items-start gap-3" @click="selectClass(c)">
              <div class="flex-1 min-w-0">
                <div class="mobile-card-title">{{ c.name }}</div>
                <div class="mobile-card-sub">{{ c.department_name || '—' }} · {{ c.major_name || '—' }}</div>
                <div class="mobile-card-meta">{{ c.grade || '—' }}级 · {{ c.academic_year || '—' }}</div>
              </div>
              <svg class="mobile-card-arrow mt-1 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
            </div>
            <div class="mt-2 flex gap-2 border-t border-slate-100 pt-2">
              <button type="button" class="app-action app-action-primary flex-1" @click.stop="selectClass(c)">查看学生</button>
              <template v-if="isAdmin">
                <button type="button" class="app-action app-action-default flex-1" @click.stop="openClassModal('edit', c)">编辑</button>
                <button type="button" class="app-action app-action-danger flex-1" @click.stop="openConfirmDel('class', c.id, c.name)">删除</button>
              </template>
            </div>
          </div>
          <div v-if="classList.length === 0" class="text-center py-6 text-sm text-slate-500">暂无班级数据，可调整筛选条件后查询</div>
        </div>
        <!-- 桌面端班级表格 -->
        <div class="app-table-wrap hidden md:block">
        <table class="app-table">
          <thead>
            <tr class="border-b border-slate-200 bg-slate-50">
              <th v-if="isAdmin" class="px-4 py-2.5 text-left font-medium text-slate-700 w-12">
                <input
                  type="checkbox"
                  class="rounded border-slate-300"
                  :checked="allClassSelected"
                  :disabled="pagedClassList.length === 0"
                  @change="toggleSelectAllClass($event.target.checked)"
                />
              </th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">班级名称</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">院系</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">专业</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">年级</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">学年</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in pagedClassList"
              :key="c.id"
              class="border-b border-slate-100"
              :class="(c.id === selectedClassId || c.id === lastHighlightClassId) ? 'bg-blue-50' : 'hover:bg-slate-50'"
            >
              <td v-if="isAdmin" class="px-4 py-2.5">
                <input
                  type="checkbox"
                  class="rounded border-slate-300"
                  :checked="isClassSelected(c.id)"
                  @change="toggleClassSelection(c.id, $event.target.checked)"
                />
              </td>
              <td class="px-4 py-2.5 text-slate-800">{{ c.name }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ c.department_name || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ c.major_name || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ c.grade || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ c.academic_year || '—' }}</td>
              <td class="px-4 py-2.5">
                <div class="flex gap-3">
                  <button type="button" class="app-action app-action-primary" @click="selectClass(c)">查看学生</button>
                  <template v-if="isAdmin">
                    <button type="button" class="app-action app-action-default" @click="openClassModal('edit', c)">编辑</button>
                    <button type="button" class="app-action app-action-danger" @click="openConfirmDel('class', c.id, c.name)">删除</button>
                  </template>
                </div>
              </td>
            </tr>
            <tr v-if="classList.length === 0">
              <td :colspan="isAdmin ? 7 : 6" class="px-4 py-6 text-center text-slate-500">暂无班级数据，可调整筛选条件后查询</td>
            </tr>
          </tbody>
        </table>
        </div>
        <!-- 分页 -->
        <div v-if="classList.length > CLASS_PAGE_SIZE" class="flex items-center justify-between border-t border-slate-200 px-4 py-2.5 text-sm text-slate-600">
          <span>共 {{ classList.length }} 个班级</span>
          <div class="flex items-center gap-2">
            <button type="button" class="rounded border border-slate-300 px-2.5 py-1 hover:bg-slate-50 disabled:opacity-50" :disabled="classPage <= 1" @click="classPage--">上一页</button>
            <span class="px-2">{{ classPage }} / {{ classPageCount }}</span>
            <button type="button" class="rounded border border-slate-300 px-2.5 py-1 hover:bg-slate-50 disabled:opacity-50" :disabled="classPage >= classPageCount" @click="classPage++">下一页</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== 班级学生列表 ===== -->
    <section v-if="selectedClassId" ref="studentSectionRef">
      <h4 class="mb-3 text-base font-medium text-slate-700">
        学生列表
        <span v-if="classDetail?.name" class="font-normal text-slate-600">（{{ classDetail.name }}）</span>
      </h4>
      <div v-if="studentLoading" class="rounded border border-slate-200 bg-white py-8 text-center text-slate-500">加载中…</div>
      <div v-else-if="studentError" class="rounded border border-red-200 bg-red-50 py-3 px-4 text-sm text-red-700">{{ studentError }}</div>
      <div v-else>
        <!-- 移动端学生卡片 -->
        <div class="mobile-card-list">
          <div v-for="s in students" :key="`mobile-stu-${s.id}`" class="mobile-card">
            <div class="mobile-card-title">{{ studentDisplayName(s) }}</div>
            <div class="mobile-card-sub">{{ s.student_no || '—' }} · {{ s.username }}</div>
            <div class="mobile-card-meta">{{ s.class_major_name || '—' }} · {{ s.class_grade || '—' }}级</div>
          </div>
          <div v-if="students.length === 0" class="text-center py-6 text-sm text-slate-500">该班级暂无学生</div>
        </div>
        <!-- 桌面端学生表格 -->
        <div class="app-table-wrap hidden md:block">
        <table class="app-table">
          <thead>
            <tr class="border-b border-slate-200 bg-slate-50">
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">学号</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">姓名</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">专业</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">年级</th>
              <th class="px-4 py-2.5 text-left font-medium text-slate-700">用户名</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id" class="border-b border-slate-100 hover:bg-slate-50">
              <td class="px-4 py-2.5 text-slate-800">{{ s.student_no || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-800">{{ studentDisplayName(s) }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ s.class_major_name || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ s.class_grade || '—' }}</td>
              <td class="px-4 py-2.5 text-slate-600">{{ s.username }}</td>
            </tr>
            <tr v-if="students.length === 0">
              <td colspan="5" class="px-4 py-6 text-center text-slate-500">该班级暂无学生</td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>
    </section>

    <!-- ===== 院系 新建/编辑 弹窗 ===== -->
    <div
      v-if="deptModal.visible"
      class="fixed inset-0 z-30 flex items-start justify-center overflow-y-auto bg-black/30 py-10"
      @click.self="closeDeptModal"
    >
      <div class="app-modal w-full max-w-lg p-6" @click.stop>
        <h3 class="mb-5 text-base font-semibold text-slate-800">
          {{ deptModal.mode === 'edit' ? '编辑院系' : '新建院系' }}
        </h3>
        <form @submit.prevent="submitDeptModal">
          <!-- 院系基本信息 -->
          <div class="grid grid-cols-2 gap-4">
            <label class="col-span-2 block text-sm text-slate-700">
              院系名称 <span class="text-red-500">*</span>
              <input
                v-model="deptModal.form.name"
                type="text"
                required
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
                placeholder="如：计算机学院"
              />
            </label>
            <label class="col-span-2 block text-sm text-slate-700">
              编码（唯一，可选）
              <input
                v-model="deptModal.form.code"
                type="text"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
                placeholder="如：CS"
              />
            </label>
          </div>

          <!-- 专业管理 -->
          <div class="mt-5">
            <p class="mb-3 text-sm font-medium text-slate-700">包含专业</p>

            <!-- 已有专业（编辑模式） -->
            <div v-if="deptModal.mode === 'edit'" class="mb-3 space-y-2">
              <p v-if="!deptModal.existingMajors.length" class="text-xs text-slate-400">该院系暂无专业</p>
              <div
                v-for="m in deptModal.existingMajors"
                :key="m.id"
                class="rounded border px-3 py-2.5"
                :class="m.markedForDelete ? 'border-red-200 bg-red-50 opacity-60' : 'border-slate-200 bg-slate-50'"
              >
                <!-- 专业名称行 -->
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium" :class="m.markedForDelete ? 'text-red-500 line-through' : 'text-slate-800'">
                    {{ m.name }}
                    <span v-if="m.code" class="ml-1 text-xs font-normal text-slate-500">（{{ m.code }}）</span>
                  </span>
                  <button
                    v-if="!m.markedForDelete"
                    type="button"
                    class="text-xs text-red-500 hover:underline"
                    @click="m.markedForDelete = true"
                  >
                    标记删除
                  </button>
                  <button
                    v-else
                    type="button"
                    class="text-xs text-slate-600 hover:underline"
                    @click="m.markedForDelete = false"
                  >
                    撤销
                  </button>
                </div>
                <!-- 年级 chips -->
                <div v-if="!m.markedForDelete" class="mt-2 flex flex-wrap items-center gap-1">
                  <span
                    v-for="(g, gi) in m.grades"
                    :key="gi"
                    class="inline-flex items-center gap-0.5 rounded bg-brand-100 px-2 py-0.5 text-xs text-brand-800"
                  >
                    {{ g }} 级
                    <button
                      type="button"
                      class="ml-0.5 text-brand-400 hover:text-red-500"
                      @click="removeExistingMajorGrade(m, gi)"
                    >
                      ×
                    </button>
                  </span>
                  <span v-if="!m.grades.length" class="text-xs text-slate-400">暂无年级</span>
                  <!-- 添加年级输入 -->
                  <div class="inline-flex items-center gap-1">
                    <input
                      v-model="m._gradeInput"
                      type="text"
                      placeholder="添加年级"
                      maxlength="10"
                      class="w-20 rounded border border-dashed border-slate-300 px-1.5 py-0.5 text-xs text-slate-800 focus:border-brand-400 focus:outline-none"
                      @keydown.enter.prevent="addExistingMajorGrade(m)"
                    />
                    <button
                      v-if="m._gradeInput?.trim()"
                      type="button"
                      class="rounded bg-brand-100 px-1.5 py-0.5 text-xs text-brand-700 hover:bg-brand-200"
                      @click="addExistingMajorGrade(m)"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 待新增专业列表 -->
            <div v-if="deptModal.newMajors.length" class="mb-3 space-y-2">
              <div
                v-for="(m, idx) in deptModal.newMajors"
                :key="m._key"
                class="rounded border border-brand-200 bg-brand-50 px-3 py-2.5"
              >
                <div class="flex items-start justify-between">
                  <div>
                    <span class="text-sm font-medium text-brand-900">{{ m.name }}</span>
                    <span v-if="m.code" class="ml-1 text-xs text-brand-700">（{{ m.code }}）</span>
                    <span class="ml-1 text-xs text-brand-500">待添加</span>
                    <!-- 年级 chips -->
                    <div class="mt-1 flex flex-wrap gap-1">
                      <span
                        v-for="(g, gi) in m.grades"
                        :key="gi"
                        class="inline-flex items-center gap-0.5 rounded bg-brand-200 px-1.5 py-0.5 text-xs text-brand-800"
                      >
                        {{ g }} 级
                        <button type="button" class="ml-0.5 text-brand-500 hover:text-red-500" @click="m.grades.splice(gi, 1)">×</button>
                      </span>
                      <span v-if="!m.grades.length" class="text-xs text-brand-400">尚未添加年级</span>
                    </div>
                  </div>
                  <button type="button" class="ml-2 text-xs text-red-500 hover:underline shrink-0" @click="deptModal.newMajors.splice(idx, 1)">移除</button>
                </div>
              </div>
            </div>

            <!-- 添加专业输入区 -->
            <div class="rounded border border-dashed border-slate-300 bg-slate-50 p-3">
              <p class="mb-2 text-xs font-medium text-slate-600">新增专业</p>
              <div class="grid grid-cols-2 gap-2">
                <input
                  v-model="newMajorInput.name"
                  type="text"
                  placeholder="专业名称（必填）"
                  class="rounded border border-slate-300 px-2.5 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <input
                  v-model="newMajorInput.code"
                  type="text"
                  placeholder="编码（可选）"
                  class="rounded border border-slate-300 px-2.5 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
              </div>
              <!-- 年级输入 -->
              <div class="mt-2">
                <div class="flex flex-wrap items-center gap-1 mb-1.5">
                  <span
                    v-for="(g, gi) in newMajorInput.grades"
                    :key="gi"
                    class="inline-flex items-center gap-0.5 rounded bg-brand-100 px-2 py-0.5 text-xs text-brand-800"
                  >
                    {{ g }} 级
                    <button type="button" class="ml-0.5 text-brand-400 hover:text-red-500" @click="newMajorInput.grades.splice(gi, 1)">×</button>
                  </span>
                  <span v-if="!newMajorInput.grades.length" class="text-xs text-slate-400">尚未添加年级</span>
                </div>
                <input
                  v-model="newMajorInput.gradeInput"
                  type="text"
                  placeholder="输入年级如 2022，按回车添加"
                  maxlength="10"
                  class="w-full rounded border border-slate-300 px-2.5 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                  @keydown.enter.prevent="addGradeToNewMajor"
                />
              </div>
              <p v-if="newMajorInputError" class="mt-1 text-xs text-red-600">{{ newMajorInputError }}</p>
              <button
                type="button"
                class="mt-2 rounded bg-slate-700 px-3 py-1.5 text-sm text-white hover:bg-slate-800"
                @click="addNewMajor"
              >
                添加至待保存列表
              </button>
            </div>
          </div>

          <p v-if="deptModal.error" class="mt-4 text-sm text-red-600 whitespace-pre-line">{{ deptModal.error }}</p>
          <div class="mt-5 flex justify-end gap-2">
            <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="closeDeptModal">取消</button>
            <button type="submit" class="app-btn app-btn-primary app-btn-sm disabled:opacity-60" :disabled="deptModal.loading">
              {{ deptModal.loading ? '保存中…' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== 班级 新建/编辑 弹窗 ===== -->
    <div
      v-if="classModal.visible"
      class="fixed inset-0 z-30 flex items-center justify-center bg-black/30"
      @click.self="closeClassModal"
    >
      <div class="app-modal w-full max-w-md p-6" @click.stop>
        <h3 class="mb-4 text-base font-semibold text-slate-800">{{ classModal.mode === 'edit' ? '编辑班级' : '新建班级' }}</h3>
        <form class="space-y-4" @submit.prevent="submitClassModal">
          <label class="block text-sm text-slate-700">
            班级名称 <span class="text-red-500">*</span>
            <input
              v-model="classModal.form.name"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：计算机22级1班"
            />
          </label>
          <label class="block text-sm text-slate-700">
            院系 <span class="text-red-500">*</span>
            <select
              v-model="classModal.form.department"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onClassModalDeptChange"
            >
              <option value="">请选择院系</option>
              <option v-for="d in flatDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </label>
          <label class="block text-sm text-slate-700">
            专业（可选）
            <select
              v-model="classModal.form.major"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="">无</option>
              <option v-for="m in classModal.majorOptions" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </label>

          <!-- 年级：有专业年级时显示下拉，否则文本输入 -->
          <label class="block text-sm text-slate-700">
            年级
            <template v-if="classModalGradeOptions.length">
              <select
                v-model="classModal.form.grade"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              >
                <option value="">请选择年级</option>
                <option v-for="g in classModalGradeOptions" :key="g" :value="g">{{ g }} 级</option>
              </select>
              <p class="mt-0.5 text-xs text-slate-400">年级来源于所选专业的已定义年级</p>
            </template>
            <input
              v-else
              v-model="classModal.form.grade"
              type="text"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如 2022（选择专业后可从专业年级中选择）"
            />
          </label>

          <p v-if="classModal.error" class="text-sm text-red-600">{{ classModal.error }}</p>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="closeClassModal">取消</button>
            <button type="submit" class="app-btn app-btn-primary app-btn-sm disabled:opacity-60" :disabled="classModal.loading">
              {{ classModal.loading ? '保存中…' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== 删除确认（院系 / 班级共用） ===== -->
    <div
      v-if="confirmDel.visible"
      class="fixed inset-0 z-40 flex items-center justify-center bg-black/30"
      @click.self="closeConfirmDel"
    >
      <div class="app-modal w-full max-w-sm p-6" @click.stop>
        <h3 class="text-base font-semibold text-slate-800">确认删除</h3>
        <p class="mt-2 text-sm text-slate-600">
          确定要删除 <strong class="text-slate-800">「{{ confirmDel.label }}」</strong> 吗？
          <template v-if="confirmDel.type === 'dept'">删除院系将同时删除其所有专业和班级，此操作不可恢复。</template>
          <template v-else>删除班级后，关联学生的班级信息将被清空，此操作不可恢复。</template>
        </p>
        <p v-if="confirmDel.error" class="mt-2 text-sm text-red-600">{{ confirmDel.error }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="closeConfirmDel">取消</button>
          <button type="button" class="rounded bg-red-600 px-4 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-60" :disabled="confirmDel.loading" @click="doDelete">
            {{ confirmDel.loading ? '删除中…' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ===== 批量删除确认（院系 / 班级） ===== -->
    <div
      v-if="batchDel.visible"
      class="fixed inset-0 z-40 flex items-center justify-center bg-black/30"
      @click.self="closeBatchDeleteDialog"
    >
      <div class="app-modal w-full max-w-sm p-6" @click.stop>
        <h3 class="text-base font-semibold text-slate-800">确认批量删除</h3>
        <p class="mt-2 text-sm text-slate-600">
          确定要删除
          <strong class="text-slate-800"> {{ batchDel.count }} </strong>
          个{{ batchDel.type === 'dept' ? '院系' : '班级' }}吗？
          <template v-if="batchDel.type === 'dept'">删除院系将同时删除其所有专业和班级，此操作不可恢复。</template>
          <template v-else>删除班级后，关联学生的班级信息将被清空，此操作不可恢复。</template>
        </p>
        <p v-if="batchDel.error" class="mt-2 text-sm text-red-600">{{ batchDel.error }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="closeBatchDeleteDialog">取消</button>
          <button type="button" class="rounded bg-red-600 px-4 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-60" :disabled="batchDel.loading" @click="doBatchDelete">
            {{ batchDel.loading ? '删除中…' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 组织架构页：院系 / 班级增删改查 + 班级学生查看。
 * 院系弹窗内含专业管理（专业名称、编码、年级列表），年级以 chips 形式添加/删除。
 * 班级弹窗中，若所选专业已定义年级，则年级字段自动变为下拉选择（继承专业年级）。
 */
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'

const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)

/** 架构树可视化状态 */
const treeCollapsed = ref(false)
const orgTreeCollapsed = ref(false)
const staffTreeCollapsed = ref(false)

/** 院系架构展开状态 */
const expandedDepts = ref(new Set())
const expandedMajors = ref(new Set())

/** 人员架构展开状态 */
const expandedStaffDepts = ref(new Set())
const expandedStaffCounselors = ref(new Set())

/** 统一架构树数据（含组织结构 + 人员信息） */
const unifiedTree = ref([])
const unifiedTreeLoading = ref(false)

/**
 * 从统一数据中提取人员架构视图：院系→系主任→辅导员→助理。
 * 按院系聚合辅导员（同一辅导员可管理多个班级，这里去重合并）。
 */
const personnelDepts = computed(() => {
  return unifiedTree.value
    .map(dept => {
      const seen = {}
      for (const major of dept.majors) {
        for (const cls of (major.classes || [])) {
          for (const coun of (cls.counselors || [])) {
            if (!coun.id) continue
            if (!seen[coun.id]) {
              seen[coun.id] = { ...coun, classNames: [], assistants: [] }
            }
            seen[coun.id].classNames.push(cls.name)
            for (const a of (coun.assistants || [])) {
              const key = `${a.id}-${a.class_id}`
              if (!seen[coun.id]._akeys) seen[coun.id]._akeys = new Set()
              if (!seen[coun.id]._akeys.has(key)) {
                seen[coun.id]._akeys.add(key)
                seen[coun.id].assistants.push(a)
              }
            }
          }
        }
      }
      const counselors = Object.values(seen).map(c => {
        const { _akeys, ...rest } = c
        return rest
      })
      const assistantCount = counselors.reduce((sum, c) => sum + c.assistants.length, 0)
      const personCount = (dept.directors?.length || 0) + counselors.length + assistantCount
      return { id: dept.id, name: dept.name, directors: dept.directors || [], counselors, personCount }
    })
    .filter(d => d.personCount > 0)
})

/** @returns {Promise<void>} */
async function loadUnifiedTree() {
  unifiedTreeLoading.value = true
  try {
    const { data } = await api.get('/departments/personnel-tree/')
    unifiedTree.value = data
  } catch (e) {
    console.error('加载架构树失败', e)
  } finally {
    unifiedTreeLoading.value = false
  }
}

/** @param {number} deptId */
function toggleTreeDept(deptId) {
  if (expandedDepts.value.has(deptId)) expandedDepts.value.delete(deptId)
  else expandedDepts.value.add(deptId)
}

/** @param {number} majorId */
function toggleTreeMajor(majorId) {
  if (expandedMajors.value.has(majorId)) expandedMajors.value.delete(majorId)
  else expandedMajors.value.add(majorId)
}

/** @param {number} deptId */
function toggleStaffDept(deptId) {
  if (expandedStaffDepts.value.has(deptId)) expandedStaffDepts.value.delete(deptId)
  else expandedStaffDepts.value.add(deptId)
}

/** @param {number} counselorId */
function toggleStaffCounselor(counselorId) {
  if (expandedStaffCounselors.value.has(counselorId)) expandedStaffCounselors.value.delete(counselorId)
  else expandedStaffCounselors.value.add(counselorId)
}

/** 最近编辑的院系 ID，用于行高亮 */
const lastHighlightDeptId = ref(null)
/** 最近编辑的班级 ID，用于行高亮 */
const lastHighlightClassId = ref(null)

// ─── 院系 ────────────────────────────────────────────────────
const deptLoading = ref(false)
const deptError = ref('')
const departmentRows = ref([])
const selectedDeptIds = ref([])
/** 全部专业按 deptId 分组：{ [deptId]: [{id,name,code,grades,...}] } */
const majorsByDept = ref({})
const selectedDeptCount = computed(() => selectedDeptIds.value.length)
const deptBulkActionVisible = computed(() => selectedDeptCount.value >= 2)
const allDeptSelected = computed(() => departmentRows.value.length > 0 && selectedDeptIds.value.length === departmentRows.value.length)

// ─── 班级 ────────────────────────────────────────────────────
const classLoading = ref(false)
const classError = ref('')
const classList = ref([])
const CLASS_PAGE_SIZE = 20
const classPage = ref(1)
const classPageCount = computed(() => Math.max(1, Math.ceil(classList.value.length / CLASS_PAGE_SIZE)))
const pagedClassList = computed(() => {
  const start = (classPage.value - 1) * CLASS_PAGE_SIZE
  return classList.value.slice(start, start + CLASS_PAGE_SIZE)
})
const selectedClassIds = ref([])
const filterDepartment = ref('')
const filterMajor = ref('')
const filterGrade = ref('')
const majorList = ref([])
const selectedClassCount = computed(() => selectedClassIds.value.length)
const classBulkActionVisible = computed(() => selectedClassCount.value >= 2)
const allClassSelected = computed(() => pagedClassList.value.length > 0 && pagedClassList.value.every(c => selectedClassIds.value.includes(c.id)))

// ─── 班级学生 ────────────────────────────────────────────────
const selectedClassId = ref(null)
const classDetail = ref(null)
const studentLoading = ref(false)
const studentError = ref('')
const students = ref([])
const studentSectionRef = ref(null)

// ─── 院系弹窗 ────────────────────────────────────────────────
const deptModal = reactive({
  visible: false,
  mode: 'create',
  editId: null,
  form: { name: '', code: '' },
  /**
   * 编辑模式下从接口加载的已有专业。
   * 每项形如：{ id, name, code, grades: [...], _gradeInput: '', markedForDelete: false, _originalGrades: [...] }
   */
  existingMajors: [],
  /** 本次新增（待保存）的专业列表：{ _key, name, code, grades: [...] } */
  newMajors: [],
  loading: false,
  error: '',
})

/** 添加新专业的临时输入 */
const newMajorInput = reactive({ name: '', code: '', grades: [], gradeInput: '' })
const newMajorInputError = ref('')

// ─── 班级弹窗 ────────────────────────────────────────────────
const classModal = reactive({
  visible: false,
  mode: 'create',
  editId: null,
  form: { name: '', department: '', major: '', grade: '' },
  loading: false,
  error: '',
  majorOptions: [],
})

/**
 * 班级弹窗中年级下拉选项：从所选专业的 grades 字段获取。
 * 若未选专业或专业无预设年级，返回空数组（此时退化为文本输入）。
 */
const classModalGradeOptions = computed(() => {
  if (!classModal.form.major) return []
  const major = classModal.majorOptions.find((m) => String(m.id) === String(classModal.form.major))
  return major?.grades ?? []
})

// ─── 删除确认 ────────────────────────────────────────────────
const confirmDel = reactive({ visible: false, type: '', id: null, label: '', loading: false, error: '' })
const batchDel = reactive({ visible: false, type: '', count: 0, loading: false, error: '' })

// ─── 工具函数 ─────────────────────────────────────────────────

function flattenTree(nodes, depth = 0) {
  const rows = []
  for (const node of nodes) {
    rows.push({ id: node.id, name: node.name, code: node.code, depth })
    if (node.children?.length) rows.push(...flattenTree(node.children, depth + 1))
  }
  return rows
}

const flatDepartments = computed(() => departmentRows.value.map((r) => ({ id: r.id, name: r.name })))

function studentDisplayName(s) {
  return s.name || s.username || '—'
}

function parseApiError(e) {
  const data = e.response?.data
  if (!data) return '操作失败，请稍后重试'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.entries(data).map(([k, v]) => `${k}：${Array.isArray(v) ? v.join('；') : v}`).join('\n') || '操作失败'
}

/**
 * 判断院系是否已勾选。
 * @param {number} deptId
 * @returns {boolean}
 */
function isDeptSelected(deptId) {
  return selectedDeptIds.value.includes(deptId)
}

/**
 * 勾选/取消勾选单个院系。
 * @param {number} deptId
 * @param {boolean} checked
 */
function toggleDeptSelection(deptId, checked) {
  if (checked) {
    if (!selectedDeptIds.value.includes(deptId)) {
      selectedDeptIds.value = [...selectedDeptIds.value, deptId]
    }
    return
  }
  selectedDeptIds.value = selectedDeptIds.value.filter((id) => id !== deptId)
}

/**
 * 全选/取消全选当前院系列表。
 * @param {boolean} checked
 */
function toggleSelectAllDept(checked) {
  if (checked) {
    selectedDeptIds.value = departmentRows.value.map((item) => item.id)
    return
  }
  selectedDeptIds.value = []
}

/**
 * 判断班级是否已勾选。
 * @param {number} classId
 * @returns {boolean}
 */
function isClassSelected(classId) {
  return selectedClassIds.value.includes(classId)
}

/**
 * 勾选/取消勾选单个班级。
 * @param {number} classId
 * @param {boolean} checked
 */
function toggleClassSelection(classId, checked) {
  if (checked) {
    if (!selectedClassIds.value.includes(classId)) {
      selectedClassIds.value = [...selectedClassIds.value, classId]
    }
    return
  }
  selectedClassIds.value = selectedClassIds.value.filter((id) => id !== classId)
}

/**
 * 全选/取消全选当前班级列表。
 * @param {boolean} checked
 */
function toggleSelectAllClass(checked) {
  const pageIds = new Set(pagedClassList.value.map((item) => item.id))
  if (checked) {
    selectedClassIds.value = [...new Set([...selectedClassIds.value, ...pageIds])]
    return
  }
  selectedClassIds.value = selectedClassIds.value.filter((id) => !pageIds.has(id))
}

// ─── 数据加载 ─────────────────────────────────────────────────

async function loadDepartments() {
  deptLoading.value = true
  deptError.value = ''
  try {
    const { data } = await api.get('/departments/', { params: { tree: 1 } })
    departmentRows.value = flattenTree(Array.isArray(data) ? data : (data?.results ?? []))
    const idSet = new Set(departmentRows.value.map((item) => item.id))
    selectedDeptIds.value = selectedDeptIds.value.filter((id) => idSet.has(id))
  } catch (e) {
    deptError.value = parseApiError(e)
    departmentRows.value = []
    selectedDeptIds.value = []
  } finally {
    deptLoading.value = false
  }
}

/** 加载全部专业，按 deptId 分组存入 majorsByDept（含 grades 字段） */
async function loadAllMajors() {
  try {
    const { data } = await api.get('/majors/')
    const list = Array.isArray(data) ? data : (data?.results ?? [])
    const map = {}
    for (const m of list) {
      if (!map[m.department]) map[m.department] = []
      map[m.department].push(m)
    }
    majorsByDept.value = map
  } catch {
    majorsByDept.value = {}
  }
}

function onFilterDepartmentChange() {
  filterMajor.value = ''
  loadFilterMajors()
}

async function loadFilterMajors() {
  try {
    const params = {}
    if (filterDepartment.value) params.department = filterDepartment.value
    const { data } = await api.get('/majors/', { params })
    majorList.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    majorList.value = []
  }
}

async function loadClasses() {
  classLoading.value = true
  classError.value = ''
  try {
    const params = {}
    if (filterDepartment.value) params.department = filterDepartment.value
    if (filterMajor.value) params.major = filterMajor.value
    if (filterGrade.value) params.grade = filterGrade.value.trim()
    const { data } = await api.get('/classes/', { params })
    classList.value = Array.isArray(data) ? data : (data?.results ?? [])
    if (classPage.value > classPageCount.value) classPage.value = classPageCount.value
    const idSet = new Set(classList.value.map((item) => item.id))
    selectedClassIds.value = selectedClassIds.value.filter((id) => idSet.has(id))
    if (selectedClassId.value && !idSet.has(selectedClassId.value)) {
      selectedClassId.value = null
      classDetail.value = null
      students.value = []
    }
  } catch (e) {
    classError.value = parseApiError(e)
    classList.value = []
    selectedClassIds.value = []
  } finally {
    classLoading.value = false
  }
}

function selectClass(cls) {
  selectedClassId.value = cls.id
  classDetail.value = cls
  studentError.value = ''
  students.value = []
  fetchClassStudents(cls.id)
  nextTick(() => {
    studentSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

async function fetchClassStudents(classId) {
  studentLoading.value = true
  studentError.value = ''
  try {
    const { data } = await api.get(`/classes/${classId}/students/`)
    classDetail.value = data.class ?? classDetail.value
    students.value = data.students ?? []
  } catch (e) {
    studentError.value = parseApiError(e)
    students.value = []
  } finally {
    studentLoading.value = false
  }
}

// ─── 院系弹窗逻辑 ─────────────────────────────────────────────

async function openDeptModal(mode, row = null) {
  deptModal.mode = mode
  deptModal.error = ''
  deptModal.loading = false
  deptModal.newMajors = []
  newMajorInput.name = ''
  newMajorInput.code = ''
  newMajorInput.grades = []
  newMajorInput.gradeInput = ''
  newMajorInputError.value = ''

  if (mode === 'edit' && row) {
    deptModal.editId = row.id
    deptModal.form.name = row.name
    deptModal.form.code = row.code || ''
    try {
      const { data } = await api.get('/majors/', { params: { department: row.id } })
      const list = Array.isArray(data) ? data : (data?.results ?? [])
      deptModal.existingMajors = list.map((m) => ({
        ...m,
        grades: Array.isArray(m.grades) ? [...m.grades] : [],
        _gradeInput: '',
        markedForDelete: false,
        _originalGrades: Array.isArray(m.grades) ? [...m.grades] : [],
      }))
    } catch {
      deptModal.existingMajors = []
    }
  } else {
    deptModal.editId = null
    deptModal.form.name = ''
    deptModal.form.code = ''
    deptModal.existingMajors = []
  }
  deptModal.visible = true
}

function closeDeptModal() {
  deptModal.visible = false
}

/** 为新专业输入区添加年级 chip */
function addGradeToNewMajor() {
  const g = newMajorInput.gradeInput.trim()
  if (!g) return
  if (newMajorInput.grades.includes(g)) {
    newMajorInputError.value = `年级 ${g} 已添加`
    return
  }
  newMajorInput.grades.push(g)
  newMajorInput.gradeInput = ''
  newMajorInputError.value = ''
}

/**
 * 为某个已存在专业添加年级 chip。
 * @param {Object} m - existingMajors 中的专业对象
 */
function addExistingMajorGrade(m) {
  const g = (m._gradeInput ?? '').trim()
  if (!g) return
  if (m.grades.includes(g)) {
    m._gradeInput = ''
    return
  }
  m.grades.push(g)
  m._gradeInput = ''
}

/**
 * 删除某个已存在专业的某年级 chip。
 * @param {Object} m - existingMajors 中的专业对象
 * @param {number} gi - 年级索引
 */
function removeExistingMajorGrade(m, gi) {
  m.grades.splice(gi, 1)
}

/** 将输入区填好的专业追加到待新增列表 */
function addNewMajor() {
  newMajorInputError.value = ''
  const name = newMajorInput.name.trim()
  if (!name) {
    newMajorInputError.value = '请填写专业名称'
    return
  }
  const isDuplicate =
    deptModal.existingMajors.some((m) => m.name === name && !m.markedForDelete) ||
    deptModal.newMajors.some((m) => m.name === name)
  if (isDuplicate) {
    newMajorInputError.value = '该专业名称已存在'
    return
  }
  deptModal.newMajors.push({
    _key: Date.now(),
    name,
    code: newMajorInput.code.trim(),
    grades: [...newMajorInput.grades],
  })
  newMajorInput.name = ''
  newMajorInput.code = ''
  newMajorInput.grades = []
  newMajorInput.gradeInput = ''
}

/**
 * 提交院系保存：① 保存/更新院系 → ② 删除标记删除的专业 → ③ 更新年级有变化的专业 → ④ 新增专业。
 */
async function submitDeptModal() {
  deptModal.error = ''
  deptModal.loading = true
  try {
    let deptId = deptModal.editId
    const deptPayload = { name: deptModal.form.name.trim(), code: deptModal.form.code.trim(), parent: null }
    if (deptModal.mode === 'create') {
      const { data } = await api.post('/departments/', deptPayload)
      deptId = data.id
    } else {
      await api.patch(`/departments/${deptId}/`, deptPayload)
    }

    // 处理已有专业：删除 or 更新年级
    for (const m of deptModal.existingMajors) {
      if (m.markedForDelete) {
        await api.delete(`/majors/${m.id}/`)
      } else if (JSON.stringify(m.grades) !== JSON.stringify(m._originalGrades)) {
        await api.patch(`/majors/${m.id}/`, { grades: m.grades })
      }
    }

    // 新增专业
    for (const m of deptModal.newMajors) {
      await api.post('/majors/', { name: m.name, code: m.code, department: deptId, grades: m.grades })
    }

    lastHighlightDeptId.value = deptId
    closeDeptModal()
    await Promise.all([loadDepartments(), loadAllMajors(), loadFilterMajors()])
  } catch (e) {
    deptModal.error = parseApiError(e)
  } finally {
    deptModal.loading = false
  }
}

// ─── 班级弹窗逻辑 ─────────────────────────────────────────────

/** 班级弹窗院系变化 → 刷新专业，清空专业/年级 */
async function onClassModalDeptChange() {
  classModal.form.major = ''
  classModal.form.grade = ''
  classModal.majorOptions = []
  if (!classModal.form.department) return
  try {
    const { data } = await api.get('/majors/', { params: { department: classModal.form.department } })
    classModal.majorOptions = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    classModal.majorOptions = []
  }
}

async function openClassModal(mode, cls = null) {
  classModal.mode = mode
  classModal.error = ''
  classModal.loading = false
  classModal.majorOptions = []
  if (mode === 'edit' && cls) {
    classModal.editId = cls.id
    classModal.form.name = cls.name
    classModal.form.department = cls.department ?? ''
    classModal.form.major = cls.major ?? ''
    classModal.form.grade = cls.grade || ''
    if (cls.department) {
      try {
        const { data } = await api.get('/majors/', { params: { department: cls.department } })
        classModal.majorOptions = Array.isArray(data) ? data : (data?.results ?? [])
      } catch {
        classModal.majorOptions = []
      }
    }
  } else {
    classModal.editId = null
    classModal.form.name = ''
    classModal.form.department = ''
    classModal.form.major = ''
    classModal.form.grade = ''
  }
  classModal.visible = true
}

function closeClassModal() {
  classModal.visible = false
}

async function submitClassModal() {
  classModal.error = ''
  classModal.loading = true
  try {
    const payload = {
      name: classModal.form.name.trim(),
      department: classModal.form.department || null,
      major: classModal.form.major || null,
      grade: classModal.form.grade.trim ? classModal.form.grade.trim() : classModal.form.grade,
    }
    let savedId = classModal.editId
    if (classModal.mode === 'edit') {
      await api.patch(`/classes/${classModal.editId}/`, payload)
    } else {
      const { data } = await api.post('/classes/', payload)
      savedId = data?.id ?? savedId
    }
    lastHighlightClassId.value = savedId
    closeClassModal()
    await loadClasses()
  } catch (e) {
    classModal.error = parseApiError(e)
  } finally {
    classModal.loading = false
  }
}

// ─── 删除确认逻辑 ─────────────────────────────────────────────

function openConfirmDel(type, id, label) {
  Object.assign(confirmDel, { type, id, label, error: '', loading: false, visible: true })
}

function closeConfirmDel() {
  confirmDel.visible = false
}

/**
 * 打开批量删除确认框。
 * @param {'dept'|'class'} type
 */
function openBatchDeleteDialog(type) {
  const count = type === 'dept' ? selectedDeptCount.value : selectedClassCount.value
  if (count < 2) return
  Object.assign(batchDel, { visible: true, type, count, loading: false, error: '' })
}

function closeBatchDeleteDialog() {
  batchDel.visible = false
}

/**
 * 清除院系/班级最后编辑行高亮（点击页面任意位置时调用）。
 */
function clearHighlight() {
  lastHighlightDeptId.value = null
  lastHighlightClassId.value = null
}

async function doBatchDelete() {
  batchDel.error = ''
  batchDel.loading = true
  try {
    if (batchDel.type === 'dept') {
      await api.post('/departments/batch-delete/', { department_ids: selectedDeptIds.value })
      selectedDeptIds.value = []
      closeBatchDeleteDialog()
      selectedClassId.value = null
      classDetail.value = null
      students.value = []
      await Promise.all([loadDepartments(), loadAllMajors(), loadFilterMajors(), loadClasses()])
      return
    }
    await api.post('/classes/batch-delete/', { class_ids: selectedClassIds.value })
    const deletedIdSet = new Set(selectedClassIds.value)
    selectedClassIds.value = []
    closeBatchDeleteDialog()
    if (selectedClassId.value && deletedIdSet.has(selectedClassId.value)) {
      selectedClassId.value = null
      classDetail.value = null
      students.value = []
    }
    await loadClasses()
  } catch (e) {
    batchDel.error = parseApiError(e)
  } finally {
    batchDel.loading = false
  }
}

async function doDelete() {
  confirmDel.error = ''
  confirmDel.loading = true
  try {
    if (confirmDel.type === 'dept') {
      await api.delete(`/departments/${confirmDel.id}/`)
      closeConfirmDel()
      selectedDeptIds.value = selectedDeptIds.value.filter((id) => id !== confirmDel.id)
      selectedClassId.value = null
      await Promise.all([loadDepartments(), loadAllMajors(), loadClasses()])
    } else {
      await api.delete(`/classes/${confirmDel.id}/`)
      closeConfirmDel()
      selectedClassIds.value = selectedClassIds.value.filter((id) => id !== confirmDel.id)
      if (selectedClassId.value === confirmDel.id) {
        selectedClassId.value = null
        classDetail.value = null
        students.value = []
      }
      await loadClasses()
    }
  } catch (e) {
    confirmDel.error = parseApiError(e)
  } finally {
    confirmDel.loading = false
  }
}

onMounted(() => {
  loadDepartments()
  loadAllMajors()
  loadFilterMajors()
  loadClasses()
  loadUnifiedTree()
})

useRealtimeRefresh(['department', 'major', 'class'], () => {
  loadDepartments()
  loadAllMajors()
  loadFilterMajors()
  loadClasses()
  loadUnifiedTree()
})
</script>

<style scoped>
/* 架构树过渡动画 */
.tree-slide-enter-active,
.tree-slide-leave-active {
  transition: max-height .3s ease, opacity .25s ease;
  overflow: hidden;
}
.tree-slide-enter-from,
.tree-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
.tree-slide-enter-to,
.tree-slide-leave-from {
  max-height: 2000px;
  opacity: 1;
}

/* 架构区块 */
.org-section-block {
  border-bottom: 1px solid rgba(148, 163, 184, .12);
}
.org-section-block:last-child {
  border-bottom: none;
}
.org-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #475569;
  background: rgba(248, 250, 252, .6);
  border-bottom: 1px solid rgba(148, 163, 184, .10);
}

/* 树节点容器 */
.org-tree-root {
  contain: layout style;
}
.org-tree-dept {
  min-width: 180px;
}
.org-tree-children {
  padding-left: 20px;
  margin-top: 4px;
}
.org-tree-major {
  position: relative;
  margin-top: 4px;
}
.org-tree-leaves {
  padding-left: 20px;
  margin-top: 2px;
}
.org-tree-leaf {
  position: relative;
  margin-top: 2px;
}

/* 连接线 */
.org-connector {
  position: absolute;
  left: -14px;
  top: 0;
  width: 14px;
  height: 50%;
  border-left: 1.5px solid rgba(200, 16, 46, .18);
  border-bottom: 1.5px solid rgba(200, 16, 46, .18);
  border-radius: 0 0 0 6px;
}
.org-connector--sm {
  left: -12px;
  width: 12px;
  border-color: rgba(148, 163, 184, .3);
}

/* 节点卡片 */
.org-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all .18s ease;
  border: 1px solid transparent;
}
.org-node:hover {
  background: rgba(255, 255, 255, .7);
  border-color: rgba(148, 163, 184, .2);
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.org-node--dept {
  background: rgba(200, 16, 46, .06);
  border-color: rgba(200, 16, 46, .12);
}
.org-node--dept:hover {
  background: rgba(200, 16, 46, .10);
}
.org-node--major {
  background: rgba(37, 99, 235, .05);
  border-color: rgba(37, 99, 235, .10);
}
.org-node--major:hover {
  background: rgba(37, 99, 235, .10);
}
.org-node--class {
  background: rgba(5, 150, 105, .05);
  border-color: rgba(5, 150, 105, .10);
  padding: 6px 10px;
}
.org-node--class:hover {
  background: rgba(5, 150, 105, .10);
}

/* 节点图标 */
.org-node__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
}
.org-node__icon--dept {
  background: rgba(200, 16, 46, .12);
  color: #c8102e;
}
.org-node__icon--major {
  background: rgba(37, 99, 235, .10);
  color: #2563eb;
  width: 28px;
  height: 28px;
}
.org-node__icon--class {
  background: rgba(5, 150, 105, .10);
  color: #059669;
  width: 24px;
  height: 24px;
}

.org-node__label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #334155;
  white-space: nowrap;
}
.org-node--dept .org-node__label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b;
}

.org-node__badge {
  font-size: 0.625rem;
  padding: 1px 6px;
  border-radius: 9999px;
  background: rgba(148, 163, 184, .15);
  color: #64748b;
  white-space: nowrap;
}

.org-node__arrow {
  width: 14px;
  height: 14px;
  color: #94a3b8;
  transition: transform .2s ease;
  flex-shrink: 0;
  margin-left: auto;
}

/* ── 人员架构节点样式 ── */
.org-node--director {
  background: rgba(217, 119, 6, .06);
  border-color: rgba(217, 119, 6, .14);
  cursor: default;
}
.org-node--director:hover {
  background: rgba(217, 119, 6, .10);
}
.org-node__icon--director {
  background: rgba(217, 119, 6, .12);
  color: #d97706;
  width: 28px;
  height: 28px;
}
.org-node--counselor {
  background: rgba(37, 99, 235, .05);
  border-color: rgba(37, 99, 235, .10);
}
.org-node--counselor:hover {
  background: rgba(37, 99, 235, .10);
}
.org-node__icon--counselor {
  background: rgba(37, 99, 235, .10);
  color: #2563eb;
  width: 28px;
  height: 28px;
}
.org-node--assistant {
  background: rgba(5, 150, 105, .05);
  border-color: rgba(5, 150, 105, .10);
  padding: 6px 10px;
  cursor: default;
}
.org-node--assistant:hover {
  background: rgba(5, 150, 105, .10);
}
.org-node__icon--assistant {
  background: rgba(5, 150, 105, .10);
  color: #059669;
  width: 24px;
  height: 24px;
}
</style>
