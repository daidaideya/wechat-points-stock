<template>
  <div class="page-stack programs-page programs-showcase-page">
    <section class="toolbar-card programs-toolbar-card showcase-toolbar-card">
      <div class="filter-shell">
        <div class="filter-search-row">
          <el-input
            v-model="searchKeyword"
            clearable
            size="large"
            class="showcase-search-input filter-search-input"
            placeholder="搜索名称 / program_id / 拼音"
            @keyup.enter="applyFilters"
            @clear="applyFilters"
          >
            <template #prefix>
              <el-icon class="filter-search-icon"><Search /></el-icon>
            </template>
            <template #append>
              <el-button class="filter-search-btn" @click="applyFilters">搜索</el-button>
            </template>
          </el-input>

          <div class="filter-search-side">
            <div class="toolbar-status-chip compact warm-chip filter-count-chip">
              <span class="toolbar-status-value">{{ programs.length }}</span>
              <span class="toolbar-status-label">已加载</span>
            </div>
            <el-button
              class="showcase-reset-button filter-reset-btn"
              plain
              :disabled="!hasActiveFilters"
              @click="resetFilters"
            >
              重置
            </el-button>
          </div>
        </div>

        <div class="filter-control-row">
          <div class="filter-group">
            <span class="filter-group-label">状态</span>
            <div class="segmented-group">
              <button type="button" class="segmented-item" :class="{ active: statusFilter === 'active' }" @click="setStatusFilter('active')">活跃</button>
              <button type="button" class="segmented-item" :class="{ active: statusFilter === 'archived' }" @click="setStatusFilter('archived')">归档</button>
              <button type="button" class="segmented-item" :class="{ active: statusFilter === 'all' }" @click="setStatusFilter('all')">全部</button>
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-group-label">收藏</span>
            <div class="segmented-group">
              <button type="button" class="segmented-item" :class="{ active: favoriteFilter === 'all' }" @click="setFavoriteFilter('all')">全部</button>
              <button type="button" class="segmented-item" :class="{ active: favoriteFilter === 'favorite' }" @click="setFavoriteFilter('favorite')">收藏</button>
              <button type="button" class="segmented-item" :class="{ active: favoriteFilter === 'unfavorite' }" @click="setFavoriteFilter('unfavorite')">未藏</button>
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-group-label">青龙</span>
            <div class="segmented-group">
              <button type="button" class="segmented-item" :class="{ active: qlStatusFilter === 'all' }" @click="setQlStatusFilter('all')">全部</button>
              <button type="button" class="segmented-item" :class="{ active: qlStatusFilter === 'enabled' }" @click="setQlStatusFilter('enabled')">启用</button>
              <button type="button" class="segmented-item" :class="{ active: qlStatusFilter === 'disabled' }" @click="setQlStatusFilter('disabled')">禁用</button>
              <button type="button" class="segmented-item" :class="{ active: qlStatusFilter === 'unknown' }" @click="setQlStatusFilter('unknown')">未关联</button>
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-group-label">排序</span>
            <div class="segmented-group">
              <button type="button" class="segmented-item" :class="{ active: sortFilter === 'default' }" @click="setSortFilter('default')">默认</button>
              <button type="button" class="segmented-item" :class="{ active: sortFilter === 'cron' }" @click="setSortFilter('cron')">定时</button>
            </div>
          </div>
        </div>

        <div class="filter-tags-panel">
          <div class="filter-tags-header">
            <span class="filter-group-label">标签</span>
            <span class="filter-tags-current">{{ currentTag || '全部标签' }}</span>
            <span v-if="availableTags.length" class="filter-tags-count">{{ availableTags.length }}</span>
          </div>

          <div class="tag-list content filter-tag-list showcase compact">
            <button
              type="button"
              class="filter-chip"
              :class="{ active: currentTag === '' }"
              @click="selectTag('')"
            >
              全部
            </button>
            <button
              v-for="tag in availableTags"
              :key="tag"
              type="button"
              class="filter-chip"
              :class="{ active: currentTag === tag }"
              @click="selectTag(tag)"
            >
              {{ tag }}
            </button>
            <span v-if="!availableTags.length" class="empty-text">暂无可筛选标签</span>
          </div>
        </div>

        <div v-if="activeFilterChips.length" class="active-filter-bar">
          <span class="active-filter-label">当前筛选</span>
          <div class="active-filter-list">
            <button
              v-for="chip in activeFilterChips"
              :key="chip.key"
              type="button"
              class="active-filter-chip"
              @click="clearFilterChip(chip.key)"
            >
              {{ chip.label }}
              <span class="active-filter-close">×</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="loading && programs.length === 0" class="showcase-grid skeleton-grid compact">
      <el-card v-for="item in 6" :key="item" shadow="hover" class="program-card showcase-program-card skeleton-card compact">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="circle" style="width: 52px; height: 52px; margin-bottom: 18px" />
            <el-skeleton-item variant="h3" style="width: 52%; height: 26px; margin-bottom: 12px" />
            <el-skeleton-item variant="text" style="width: 70%; margin-bottom: 10px" />
            <el-skeleton-item variant="text" style="width: 92%; margin-bottom: 8px" />
            <el-skeleton-item variant="text" style="width: 80%; margin-bottom: 18px" />
            <el-skeleton-item variant="text" style="width: 100%; height: 34px; margin-bottom: 10px" />
            <el-skeleton-item variant="text" style="width: 48%" />
          </template>
        </el-skeleton>
      </el-card>
    </section>

    <section v-else class="showcase-grid compact">
      <div v-if="loadError" class="program-state-card compact full-span">
        <el-result icon="error" title="列表加载失败" sub-title="请检查网络或接口状态后重试。">
          <template #extra>
            <el-button type="primary" @click="applyFilters">重新加载</el-button>
          </template>
        </el-result>
      </div>

      <div v-else-if="!programs.length" class="program-state-card compact full-span">
        <el-empty description="没有符合条件的小程序">
          <template #description>
            <p>可尝试清空关键词、标签或收藏筛选后重新查看。</p>
          </template>
          <div class="empty-state-actions">
            <el-button type="primary" plain @click="resetFilters">清空筛选</el-button>
          </div>
        </el-empty>
      </div>

      <article
        v-for="(program, index) in programs"
        v-else
        :key="program.program_id"
        class="showcase-card masonry-card"
        :class="{
          'is-favorite': program.is_favorite,
          'has-stock': program.has_stock,
          'is-archived': program.is_archived,
        }"
      >
        <div v-if="program.is_archived" class="archived-badge">已归档</div>
        <div class="showcase-card-top">
          <div class="showcase-card-brand no-avatar-brand">
            <div class="showcase-card-brand-text full-width-brand-text">
              <div class="showcase-card-title-line">
                <span class="showcase-card-index" :title="`第 ${index + 1} 个`">{{ index + 1 }}</span>
                <h3
                  class="showcase-card-title is-copyable"
                  :class="titleSizeClass(program.program_name || program.program_id)"
                  :title="`${program.program_name || program.program_id}（点击复制名称）`"
                  role="button"
                  tabindex="0"
                  @click.stop="copyProgramName(program)"
                  @keydown.enter.prevent="copyProgramName(program)"
                  @keydown.space.prevent="copyProgramName(program)"
                >
                  {{ program.program_name || program.program_id }}
                </h3>
                <el-tooltip
                  v-if="program.ql_status === 'enabled'"
                  :content="program.ql_cron_name ? `青龙已启用：${program.ql_cron_name}` : '青龙：已启用'"
                  placement="top"
                >
                  <span class="ql-status-badge is-enabled" aria-label="青龙已启用">
                    <el-icon><CircleCheck /></el-icon>
                  </span>
                </el-tooltip>
                <el-tooltip
                  v-else-if="program.ql_status === 'disabled'"
                  :content="program.ql_cron_name ? `青龙已禁用：${program.ql_cron_name}` : '青龙：已禁用'"
                  placement="top"
                >
                  <span class="ql-status-badge is-disabled" aria-label="青龙已禁用">
                    <el-icon><CircleClose /></el-icon>
                  </span>
                </el-tooltip>
              </div>
              <div class="showcase-card-meta-row compact-meta-row">
                <span class="showcase-card-dot stock-dot" :class="{ active: isUpdatedToday(program.last_update_time) }"></span>
                <span
                  class="showcase-card-id is-copyable"
                  :title="`${program.program_id}（点击复制 program_id）`"
                  role="button"
                  tabindex="0"
                  @click.stop="copyProgramId(program)"
                  @keydown.enter.prevent="copyProgramId(program)"
                  @keydown.space.prevent="copyProgramId(program)"
                >{{ program.program_id }}</span>
                <el-tooltip
                  v-if="program.ql_schedule"
                  :content="formatQlScheduleTooltip(program)"
                  placement="top"
                >
                  <span class="ql-schedule-chip" :class="`is-${program.ql_status || 'unknown'}`">
                    <span class="ql-schedule-label">定时</span>
                    <code class="ql-schedule-code">{{ program.ql_schedule }}</code>
                  </span>
                </el-tooltip>
              </div>
              <div
                class="showcase-card-tag-row"
                role="button"
                tabindex="0"
                @click.stop="openTagsDialog(program)"
                @keydown.enter.prevent="openTagsDialog(program)"
                @keydown.space.prevent="openTagsDialog(program)"
              >
                <span v-if="(program.tags || []).length" class="showcase-chip success inline-tag-chip">
                  标签：{{ (program.tags || []).join(' / ') }}
                </span>
                <span v-else class="showcase-chip warning inline-tag-chip">标签：未设置标签</span>
              </div>
              <div v-if="hasStockMetric(program) || hasPointsMetric(program) || hasCashMetric(program) || hasStockChange(program)" class="showcase-card-stock-row">
                <button
                  v-if="hasStockMetric(program)"
                  type="button"
                  class="stock-count-display stock-count-button"
                  :title="'查看库存'"
                  @click="openStockDialog(program)"
                >
                  <span class="stock-count-icon">
                    <el-icon><PriceTag /></el-icon>
                  </span>
                  <span class="stock-count-value">{{ formatProductCount(program) }}</span>
                </button>
                <span
                  v-if="hasStockMetric(program) && (hasPointsMetric(program) || hasCashMetric(program))"
                  class="stock-row-divider"
                  aria-hidden="true"
                ></span>
                <div
                  v-if="hasPointsMetric(program)"
                  class="points-count-display"
                  :title="`当前账号最高积分：${program.max_user_points}`"
                >
                  <span class="points-count-icon">
                    <el-icon><Coin /></el-icon>
                  </span>
                  <span class="points-count-value">{{ formatMaxPoints(program) }}</span>
                </div>
                <span
                  v-if="hasPointsMetric(program) && hasCashMetric(program)"
                  class="stock-row-divider"
                  aria-hidden="true"
                ></span>
                <div
                  v-if="hasCashMetric(program)"
                  class="points-count-display cash-count-display"
                  :title="`当前账号最高现金：¥${program.max_user_cash}`"
                >
                  <span class="points-count-icon cash-count-icon">
                    <el-icon><Wallet /></el-icon>
                  </span>
                  <span class="points-count-value">{{ formatMaxCash(program) }}</span>
                </div>
                <div v-if="hasStockChange(program)" class="showcase-card-change-row inline-change-row">
                  <span v-if="program.stock_change?.added_count" class="showcase-chip success stock-change-chip">+{{ program.stock_change.added_count }}</span>
                  <span v-if="program.stock_change?.removed_count" class="showcase-chip warning stock-change-chip">-{{ program.stock_change.removed_count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <p class="showcase-card-note masonry-note" :class="{ empty: !program.note }">
          {{ program.note || '暂无备注' }}
        </p>

        <div class="showcase-card-footer compact-footer">
          <div class="showcase-footer-meta">
            <span class="showcase-footer-icon">◔</span>
            <span class="showcase-footer-time">{{ formatDate(program.last_update_time) }}</span>
          </div>

          <div class="showcase-card-actions footer-actions ref-action-group">
            <el-tooltip content="编辑备注" placement="top">
              <button type="button" class="showcase-icon-button ref-action-button icon-plain-button" @click="openNoteDialog(program)">
                <el-icon><EditPen /></el-icon>
              </button>
            </el-tooltip>

            <el-tooltip :content="program.has_stock ? '查看库存' : '暂无库存可查看'" placement="top">
              <span class="action-tooltip-wrap">
                <button
                  type="button"
                  class="showcase-icon-button ref-action-button icon-plain-button"
                  :class="{ 'is-disabled-action': !program.has_stock }"
                  :disabled="!program.has_stock"
                  @click="program.has_stock ? openStockDialog(program) : undefined"
                >
                  <el-icon><Box /></el-icon>
                </button>
              </span>
            </el-tooltip>

            <el-tooltip :content="program.is_favorite ? '取消收藏' : '加入收藏'" placement="top">
              <button
                type="button"
                class="showcase-icon-button ref-action-button favorite-toggle ref-action-button-favorite icon-plain-button"
                :class="{ active: program.is_favorite }"
                @click="toggleFavorite(program)"
              >
                <el-icon v-if="updatingProgramId !== program.program_id"><Star /></el-icon>
                <span v-else class="showcase-button-loading">...</span>
              </button>
            </el-tooltip>

            <el-tooltip :content="(program.tags || []).length ? '编辑标签' : '添加标签'" placement="top">
              <button type="button" class="showcase-icon-button ref-action-button icon-plain-button" @click="openTagsDialog(program)">
                <el-icon><CollectionTag /></el-icon>
              </button>
            </el-tooltip>

            <el-tooltip content="查看详情" placement="top">
              <button type="button" class="showcase-icon-button ref-action-button icon-plain-button" @click="openDetailDialog(program)">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </el-tooltip>

            <el-dropdown trigger="click" placement="top-end" @command="(cmd) => handleProgramCommand(cmd, program)">
              <button
                type="button"
                title="更多操作"
                class="showcase-icon-button ref-action-button icon-plain-button"
                :disabled="archivingProgramId === program.program_id || deletingProgramId === program.program_id"
                @click.stop
              >
                <el-icon v-if="archivingProgramId !== program.program_id && deletingProgramId !== program.program_id"><MoreFilled /></el-icon>
                <span v-else class="showcase-button-loading">...</span>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="archive">
                    <el-icon><Box /></el-icon>
                    <span>{{ program.is_archived ? '取消归档' : '归档' }}</span>
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    <span class="dropdown-danger-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </article>
    </section>

    <div v-if="programs.length && !loadError" ref="loadMoreSentinel" class="infinite-sentinel" aria-hidden="true"></div>

    <div v-if="programs.length && !loadError" class="infinite-status-bar showcase-status-bar">
      <span v-if="loadingMore" class="infinite-status-text">正在加载更多...</span>
      <span v-else-if="!hasMore" class="infinite-status-text done">已加载全部数据</span>
      <span v-else class="infinite-status-text">继续下滑可自动加载更多</span>
    </div>

    <el-dialog v-model="noteDialogVisible" title="编辑备注" width="560px" class="showcase-dialog">
      <div class="showcase-dialog-body">
        <div class="showcase-dialog-intro">
          <div>
            <div class="showcase-dialog-title">维护小程序备注</div>
            <div class="showcase-dialog-subtitle">为当前小程序补充说明，便于后续识别、分类和管理。</div>
          </div>
          <div class="showcase-dialog-badge">{{ currentProgram?.program_name || currentProgram?.program_id || '当前小程序' }}</div>
        </div>

        <div class="dialog-panel">
          <div class="block-label">备注内容</div>
          <el-input
            v-model="editingNote"
            class="showcase-dialog-textarea"
            type="textarea"
            :rows="6"
            maxlength="200"
            show-word-limit
            placeholder="请输入备注"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="noteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNote" :loading="savingNote">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="tagsDialogVisible" title="编辑标签" width="620px" class="showcase-dialog showcase-tags-dialog">
      <div class="tags-dialog-body">
        <div class="tags-dialog-intro">
          <div>
            <div class="tags-dialog-title">维护当前小程序标签</div>
            <div class="tags-dialog-subtitle">点击下方标签即可快速添加或移除，支持自定义标签。</div>
          </div>
          <div class="tags-dialog-counter">已选 {{ editingTags.length }} 个</div>
        </div>

        <div class="dialog-section dialog-panel">
          <div class="block-label">快捷标签</div>
          <div class="tag-list content tags-dialog-list">
            <button
              v-for="tag in quickTags"
              :key="tag"
              type="button"
              class="dialog-tag-chip"
              :class="{ active: editingTags.includes(tag) }"
              @click="toggleEditingTag(tag)"
            >
              {{ tag }}
            </button>
            <button type="button" class="dialog-tag-chip add-chip" @click="promptCustomTag">+ 自定义</button>
          </div>
        </div>

        <div class="dialog-section dialog-panel">
          <div class="block-label">已选标签</div>
          <div class="tag-list content tags-dialog-list selected-tags-list">
            <el-tag
              v-for="tag in editingTags"
              :key="tag"
              class="selected-dialog-tag"
              closable
              @close="removeEditingTag(tag)"
            >
              {{ tag }}
            </el-tag>
            <div v-if="!editingTags.length" class="tags-empty-state">暂无标签，可从上方快捷标签或自定义输入中添加</div>
          </div>
        </div>

        <div class="dialog-section dialog-panel compact-tip-panel">
          <div class="block-label">自定义标签</div>
          <el-input
            v-model="customTagInput"
            class="tags-custom-input"
            maxlength="20"
            placeholder="输入自定义标签后点击添加"
            @keyup.enter="addCustomTagFromInput"
          >
            <template #append>
              <el-button class="tags-add-button" @click="addCustomTagFromInput">添加</el-button>
            </template>
          </el-input>
          <div class="tags-dialog-tip">支持增删改：点击快捷标签切换，点击已选标签右侧关闭按钮删除。</div>
        </div>
      </div>

      <template #footer>
        <el-button @click="tagsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTags" :loading="savingTags">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailDialogVisible"
      :title="detailDialogTitle"
      width="1040px"
      top="5vh"
      class="showcase-dialog showcase-detail-dialog"
    >
      <div class="showcase-dialog-body detail-dialog-body">
        <div class="showcase-dialog-intro">
          <div>
            <div class="showcase-dialog-title">小程序详情</div>
            <div class="showcase-dialog-subtitle">当前页查看积分排行与基础信息，无需跳转离开列表。</div>
          </div>
          <div class="stock-dialog-badges">
            <div class="showcase-dialog-badge stock-badge">{{ detailData?.is_favorite ? '已收藏' : '未收藏' }}</div>
            <div class="showcase-dialog-badge stock-badge">最高积分 {{ detailData?.max_user_points ?? 0 }}</div>
            <div class="showcase-dialog-badge stock-badge">排行 {{ detailRanking.length }}</div>
          </div>
        </div>

        <div v-if="detailLoading" class="stock-loading dialog-panel">
          <el-skeleton :rows="6" animated />
        </div>
        <template v-else>
          <div class="stock-summary-grid">
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">program_id</div>
              <div class="stock-summary-value mono-text detail-id-value">{{ detailData?.program_id || '—' }}</div>
            </div>
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">最近更新</div>
              <div class="stock-summary-value detail-update-value">{{ formatDate(detailData?.last_update_time) }}</div>
            </div>
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">标签数量</div>
              <div class="stock-summary-value">{{ (detailData?.tags || []).length || 0 }}</div>
            </div>
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">最高用户积分</div>
              <div class="stock-summary-value success-text">{{ detailData?.max_user_points ?? 0 }}</div>
            </div>
          </div>

          <div class="detail-info-grid">
            <div class="dialog-panel detail-info-card">
              <div class="stock-section-title">标签</div>
              <div class="detail-tag-row">
                <span v-for="tag in detailData?.tags || []" :key="tag" class="info-tag">{{ tag }}</span>
                <span v-if="!(detailData?.tags || []).length" class="info-tag empty">未设置标签</span>
              </div>
            </div>
            <div class="dialog-panel detail-info-card">
              <div class="stock-section-title">备注</div>
              <p class="detail-note-text">{{ detailData?.note || '暂无备注信息' }}</p>
            </div>
          </div>

          <div class="dialog-panel stock-table-panel">
            <div class="stock-section-title-row">
              <div class="stock-section-title">积分排行榜</div>
              <div class="stock-section-hint">展示该小程序下账号最新积分</div>
            </div>
            <el-table :data="detailRanking" stripe class="showcase-dialog-table">
              <el-table-column type="index" label="#" width="60" />
              <el-table-column prop="nickname" label="昵称" min-width="140">
                <template #default="scope">{{ scope.row.nickname || '未命名' }}</template>
              </el-table-column>
              <el-table-column prop="wechat_id" label="微信号" min-width="180" />
              <el-table-column prop="device" label="设备" min-width="120">
                <template #default="scope">{{ scope.row.device || '—' }}</template>
              </el-table-column>
              <el-table-column prop="points" label="积分" width="110">
                <template #default="scope">{{ scope.row.points ?? 0 }}</template>
              </el-table-column>
              <el-table-column prop="cash" label="现金" width="110">
                <template #default="scope">
                  {{ scope.row.cash == null || scope.row.cash === '' ? '—' : `¥${scope.row.cash}` }}
                </template>
              </el-table-column>
              <el-table-column label="更新时间" min-width="180">
                <template #default="scope">{{ formatDate(scope.row.report_time) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!detailRanking.length" description="暂无积分排行数据" :image-size="80" />
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="detailData?.has_stock"
          type="primary"
          @click="openStockFromDetail"
        >
          查看库存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="stockDialogVisible" :title="stockDialogTitle" width="1040px" top="5vh" class="showcase-dialog showcase-stock-dialog">
      <div class="showcase-dialog-body stock-dialog-body">
        <div class="showcase-dialog-intro">
          <div>
            <div class="showcase-dialog-title">库存详情总览</div>
            <div class="showcase-dialog-subtitle">
              查看当前小程序商品库存、所需积分和最高用户积分；可兑换商品会优先高亮展示。
            </div>
          </div>
          <div class="stock-dialog-badges">
            <div class="showcase-dialog-badge stock-badge">商品 {{ stockData?.product_count ?? 0 }}</div>
            <div class="showcase-dialog-badge stock-badge">最高积分 {{ stockData?.max_user_points ?? 0 }}</div>
            <div class="showcase-dialog-badge stock-badge success-badge">可兑换 {{ redeemableProductCount }}</div>
            <div v-if="stockData?.stock_change?.added_count" class="showcase-dialog-badge stock-badge success-badge">+{{ stockData.stock_change.added_count }}</div>
            <div v-if="stockData?.stock_change?.removed_count" class="showcase-dialog-badge stock-badge warning-badge">-{{ stockData.stock_change.removed_count }}</div>
          </div>
        </div>

        <div v-if="stockLoading" class="stock-loading dialog-panel">
          <el-skeleton :rows="6" animated />
        </div>
        <template v-else>
          <div class="stock-summary-grid">
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">当前商品数量</div>
              <div class="stock-summary-value">{{ stockData?.product_count ?? 0 }}</div>
            </div>
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">当前最高用户积分</div>
              <div class="stock-summary-value">{{ stockData?.max_user_points ?? 0 }}</div>
            </div>
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">较昨日新增商品</div>
              <div class="stock-summary-value success-text">{{ stockData?.stock_change?.added_count ?? 0 }}</div>
            </div>
            <div class="stock-summary-card dialog-panel">
              <div class="stock-summary-label">较昨日下架商品</div>
              <div class="stock-summary-value warning-text">{{ stockData?.stock_change?.removed_count ?? 0 }}</div>
            </div>
          </div>

          <div v-if="stockData?.changed_products?.length" class="dialog-panel stock-change-panel">
            <button
              type="button"
              class="stock-change-toggle"
              :aria-expanded="stockChangeExpanded ? 'true' : 'false'"
              @click="stockChangeExpanded = !stockChangeExpanded"
            >
              <div class="stock-change-toggle-main">
                <div class="stock-section-title">今日库存变动</div>
                <div class="stock-change-toggle-meta">
                  <el-tag size="small" type="success" effect="plain" round>
                    +{{ stockData?.stock_change?.added_count ?? 0 }}
                  </el-tag>
                  <el-tag size="small" type="warning" effect="plain" round>
                    -{{ stockData?.stock_change?.removed_count ?? 0 }}
                  </el-tag>
                  <span class="stock-change-toggle-tip">
                    {{ stockChangeExpanded ? '点击收起' : '点击展开明细' }}
                  </span>
                </div>
              </div>
              <span class="stock-change-toggle-arrow" :class="{ open: stockChangeExpanded }">▾</span>
            </button>

            <div v-show="stockChangeExpanded" class="stock-change-list">
              <div v-for="item in stockData.changed_products" :key="`${item.change_type}-${item.product_id}`" class="stock-change-item">
                <div class="stock-change-main">
                  <span class="stock-change-name">{{ item.product_name }}</span>
                  <span class="stock-change-meta">{{ item.points || 0 }} 积分</span>
                </div>
                <div class="stock-change-side">
                  <el-tag :type="item.change_type === 'added' ? 'success' : 'warning'">
                    {{ item.change_type === 'added' ? '新增' : '下架' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <div class="dialog-panel stock-table-panel">
            <div class="stock-section-title-row">
              <div class="stock-section-title">当前在架商品</div>
              <div class="stock-section-hint">
                按最高积分 {{ stockMaxUserPoints }} 判断：可兑换优先，不可兑换靠后
              </div>
            </div>
            <el-table
              :data="sortedStockProducts"
              stripe
              class="showcase-dialog-table stock-product-table"
              :row-class-name="stockRowClassName"
            >
              <el-table-column label="图片" width="96">
                <template #default="scope">
                  <el-image
                    v-if="scope.row.image_url"
                    :src="scope.row.image_url"
                    fit="cover"
                    class="product-thumb"
                    :preview-src-list="[scope.row.image_url]"
                    preview-teleported
                  />
                  <span v-else class="empty-text">无图</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="商品名称" min-width="280">
                <template #default="scope">
                  <div class="stock-product-name-cell">
                    <span>{{ scope.row.product_name || '未命名商品' }}</span>
                    <el-tag
                      v-if="isProductRedeemable(scope.row)"
                      size="small"
                      type="success"
                      effect="light"
                      round
                    >
                      可兑换
                    </el-tag>
                    <el-tag
                      v-else
                      size="small"
                      type="info"
                      effect="plain"
                      round
                    >
                      积分不足
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="points" label="所需积分" width="120" />
              <el-table-column prop="stock" label="库存" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.stock > 0 ? 'success' : 'danger'">{{ scope.row.stock }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="差额" width="120">
                <template #default="scope">
                  <span
                    class="stock-points-gap"
                    :class="isProductRedeemable(scope.row) ? 'is-ok' : 'is-short'"
                  >
                    {{ formatPointsGap(scope.row) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowRight, Box, CircleCheck, CircleClose, Coin, Delete, EditPen, CollectionTag, MoreFilled, PriceTag, Search, Star, Wallet } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const route = useRoute()
const pageSize = 20
const loadMoreSentinel = ref(null)
const PROGRAMS_PAGE_STATE_KEY = 'programs-page-state'

const loading = ref(false)
const loadingMore = ref(false)
const savingNote = ref(false)
const savingTags = ref(false)
const stockLoading = ref(false)
const stockChangeExpanded = ref(false)
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)
const loadError = ref(false)
const total = ref(0)
const page = ref(1)
const hasMore = ref(false)
const programs = ref([])
const availableTags = ref([])
const currentTag = ref('')
const searchKeyword = ref('')
const favoriteFilter = ref('all')
const statusFilter = ref('active')
const qlStatusFilter = ref('all')
const sortFilter = ref('default')
const updatingProgramId = ref('')
const deletingProgramId = ref('')
const archivingProgramId = ref('')
const noteDialogVisible = ref(false)
const tagsDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const currentProgram = ref(null)
const editingNote = ref('')
const editingTags = ref([])
const customTagInput = ref('')
const stockData = ref(null)

let observer = null
let restoringState = false

const stockDialogTitle = computed(() => {
  if (!stockData.value?.program_name) return '库存详情'
  return `${stockData.value.program_name} - 库存详情`
})

const detailDialogTitle = computed(() => {
  if (!detailData.value?.program_name && !detailData.value?.program_id) return '小程序详情'
  return `${detailData.value.program_name || detailData.value.program_id} - 详情`
})

const detailRanking = computed(() => {
  const ranking = Array.isArray(detailData.value?.ranking) ? [...detailData.value.ranking] : []
  return ranking.sort((a, b) => {
    const ap = Number(a?.points) || 0
    const bp = Number(b?.points) || 0
    if (bp !== ap) return bp - ap
    const ac = Number(a?.cash) || 0
    const bc = Number(b?.cash) || 0
    return bc - ac
  })
})

const stockMaxUserPoints = computed(() => Number(stockData.value?.max_user_points) || 0)

function isProductRedeemable(product, maxPoints = stockMaxUserPoints.value) {
  const needPoints = Number(product?.points) || 0
  const stock = Number(product?.stock) || 0
  return stock > 0 && needPoints <= maxPoints
}

const sortedStockProducts = computed(() => {
  const products = Array.isArray(stockData.value?.products) ? [...stockData.value.products] : []
  const maxPoints = stockMaxUserPoints.value

  return products.sort((a, b) => {
    const aPoints = Number(a?.points) || 0
    const bPoints = Number(b?.points) || 0
    const aStock = Number(a?.stock) || 0
    const bStock = Number(b?.stock) || 0
    const aRedeemable = isProductRedeemable(a, maxPoints)
    const bRedeemable = isProductRedeemable(b, maxPoints)

    // 可兑换优先
    if (aRedeemable !== bRedeemable) return aRedeemable ? -1 : 1
    // 有货优先于无货
    if ((aStock > 0) !== (bStock > 0)) return aStock > 0 ? -1 : 1
    // 可兑换：积分高的更“值钱”靠前；不可兑换：差额小的靠前
    if (aRedeemable && bRedeemable) {
      if (bPoints !== aPoints) return bPoints - aPoints
    } else {
      const aGap = Math.max(0, aPoints - maxPoints)
      const bGap = Math.max(0, bPoints - maxPoints)
      if (aGap !== bGap) return aGap - bGap
      if (aPoints !== bPoints) return aPoints - bPoints
    }
    return String(a?.product_name || '').localeCompare(String(b?.product_name || ''), 'zh-CN')
  })
})

const redeemableProductCount = computed(() => {
  return sortedStockProducts.value.filter((item) => isProductRedeemable(item)).length
})

const quickTags = computed(() => {
  const knownSet = new Set(availableTags.value)
  return [...availableTags.value, ...editingTags.value.filter((tag) => !knownSet.has(tag))]
})

const hasActiveFilters = computed(() => {
  return Boolean(searchKeyword.value.trim())
    || favoriteFilter.value !== 'all'
    || Boolean(currentTag.value)
    || statusFilter.value !== 'active'
    || qlStatusFilter.value !== 'all'
    || sortFilter.value !== 'default'
})

const activeFilterChips = computed(() => {
  const chips = []
  if (searchKeyword.value.trim()) {
    chips.push({ key: 'search', label: `搜索：${searchKeyword.value.trim()}` })
  }
  if (statusFilter.value !== 'active') {
    const map = { archived: '仅归档', all: '全部状态' }
    chips.push({ key: 'status', label: map[statusFilter.value] || statusFilter.value })
  }
  if (favoriteFilter.value !== 'all') {
    const map = { favorite: '仅收藏', unfavorite: '仅未收藏' }
    chips.push({ key: 'favorite', label: map[favoriteFilter.value] || favoriteFilter.value })
  }
  if (qlStatusFilter.value !== 'all') {
    const map = { enabled: '青龙启用', disabled: '青龙禁用', unknown: '青龙未关联' }
    chips.push({ key: 'ql', label: map[qlStatusFilter.value] || qlStatusFilter.value })
  }
  if (sortFilter.value !== 'default') {
    chips.push({ key: 'sort', label: '按定时排序' })
  }
  if (currentTag.value) {
    chips.push({ key: 'tag', label: `标签：${currentTag.value}` })
  }
  return chips
})

function normalizeTags(input) {
  const source = Array.isArray(input) ? input : String(input || '').split(',')
  const seen = new Set()
  return source.map((item) => String(item || '').trim()).filter((item) => {
    if (!item || seen.has(item)) return false
    seen.add(item)
    return true
  }).slice(0, 20)
}

function mergeTagsByUsage(...tagGroups) {
  const counts = new Map()

  tagGroups.flat().forEach((tag) => {
    const normalized = String(tag || '').trim()
    if (!normalized) return
    counts.set(normalized, (counts.get(normalized) || 0) + 1)
  })

  return Array.from(counts.entries())
    .sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1]
      return a[0].localeCompare(b[0], 'zh-CN')
    })
    .map(([tag]) => tag)
}

function savePageState() {
  const state = {
    searchKeyword: searchKeyword.value,
    favoriteFilter: favoriteFilter.value,
    statusFilter: statusFilter.value,
    qlStatusFilter: qlStatusFilter.value,
    sortFilter: sortFilter.value,
    currentTag: currentTag.value,
    programs: programs.value,
    availableTags: availableTags.value,
    total: total.value,
    page: page.value,
    hasMore: hasMore.value,
    scrollY: window.scrollY || window.pageYOffset || 0,
  }
  sessionStorage.setItem(PROGRAMS_PAGE_STATE_KEY, JSON.stringify(state))
}

function readPageState() {
  try {
    const raw = sessionStorage.getItem(PROGRAMS_PAGE_STATE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

async function restorePageState() {
  const state = readPageState()
  if (!state) return false

  restoringState = true
  searchKeyword.value = state.searchKeyword || ''
  favoriteFilter.value = state.favoriteFilter || 'all'
  statusFilter.value = state.statusFilter || 'active'
  qlStatusFilter.value = state.qlStatusFilter || 'all'
  sortFilter.value = state.sortFilter || 'default'
  currentTag.value = state.currentTag || ''
  programs.value = Array.isArray(state.programs) ? state.programs : []
  availableTags.value = Array.isArray(state.availableTags) ? state.availableTags : []
  total.value = Number(state.total) || 0
  page.value = Number(state.page) || 1
  hasMore.value = Boolean(state.hasMore)
  loadError.value = false
  loading.value = false
  loadingMore.value = false
  await nextTick()
  initInfiniteScroll()
  window.scrollTo({ top: Number(state.scrollY) || 0, behavior: 'auto' })
  restoringState = false
  return true
}

function goToProgramDetail(program) {
  openDetailDialog(program)
}

async function openDetailDialog(program) {
  if (!program?.program_id) return
  detailDialogVisible.value = true
  detailLoading.value = true
  detailData.value = {
    program_id: program.program_id,
    program_name: program.program_name,
    is_favorite: program.is_favorite,
    tags: program.tags || [],
    note: program.note || '',
    last_update_time: program.last_update_time,
    max_user_points: program.max_user_points,
    has_stock: program.has_stock,
    ranking: [],
  }
  try {
    const { data } = await api.get(`/programs/${program.program_id}`)
    detailData.value = {
      ...detailData.value,
      ...data,
      has_stock: data?.has_stock ?? program.has_stock,
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('加载小程序详情失败')
  } finally {
    detailLoading.value = false
  }
}

function openStockFromDetail() {
  const program = detailData.value
  if (!program?.program_id || !program.has_stock) return
  detailDialogVisible.value = false
  openStockDialog(program)
}

function formatDate(value) {
  if (!value) return '暂无数据'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatProductCount(program) {
  const count = Number(program?.product_count) || 0
  return `${count}`
}

function formatMaxPoints(program) {
  const value = Number(program?.max_user_points) || 0
  if (value <= 0) return '0'
  if (value >= 10000) return `${(value / 10000).toFixed(value % 10000 === 0 ? 0 : 1)}w`
  if (value >= 1000) return `${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}k`
  return `${value}`
}

function formatMaxCash(program) {
  if (program?.max_user_cash == null || program?.max_user_cash === '') return '—'
  const value = Number(program.max_user_cash)
  if (Number.isNaN(value)) return '—'
  if (value === 0) return '¥0'
  return `¥${value.toLocaleString('zh-CN', { maximumFractionDigits: 4 })}`
}

function hasStockMetric(program) {
  return Boolean(program?.has_stock) || Number(program?.product_count) > 0
}

function hasPointsMetric(program) {
  const value = Number(program?.max_user_points)
  return Number.isFinite(value) && value > 0
}

function hasCashMetric(program) {
  if (program?.max_user_cash == null || program?.max_user_cash === '') return false
  const value = Number(program.max_user_cash)
  return Number.isFinite(value)
}

function formatQlScheduleTooltip(program) {
  const schedule = program?.ql_schedule || ''
  const name = program?.ql_cron_name
  const statusText = program?.ql_status === 'disabled'
    ? '已禁用'
    : program?.ql_status === 'enabled'
      ? '已启用'
      : '未关联'
  if (name) return `青龙定时（${statusText}）${name}：${schedule}`
  return `青龙定时（${statusText}）：${schedule}`
}

/** Shrink title font by length so long names stay on one line in the grid card. */
function titleSizeClass(name) {
  const len = Array.from(String(name || '')).length
  if (len >= 22) return 'is-title-xs'
  if (len >= 16) return 'is-title-sm'
  if (len >= 12) return 'is-title-md'
  return ''
}

async function copyText(text, successMessage) {
  const value = String(text || '').trim()
  if (!value) {
    ElMessage.warning('没有可复制的内容')
    return
  }

  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(value)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = value
      textarea.setAttribute('readonly', 'readonly')
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success(successMessage || `已复制：${value}`)
  } catch (error) {
    console.error(error)
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function copyProgramName(program) {
  const name = program?.program_name || program?.program_id
  return copyText(name, `已复制名称：${name}`)
}

function copyProgramId(program) {
  return copyText(program?.program_id, `已复制 program_id：${program?.program_id}`)
}

function hasStockChange(program) {
  return Boolean((Number(program?.stock_change?.added_count) || 0) > 0 || (Number(program?.stock_change?.removed_count) || 0) > 0)
}

function isUpdatedToday(value) {
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false

  const now = new Date()
  return date.getFullYear() === now.getFullYear()
    && date.getMonth() === now.getMonth()
    && date.getDate() === now.getDate()
}

function getRequestParams(nextPage = 1) {
  const params = { page: nextPage, size: pageSize }
  const keyword = searchKeyword.value.trim()
  if (keyword) params.q = keyword
  if (favoriteFilter.value === 'favorite') params.is_favorite = true
  else if (favoriteFilter.value === 'unfavorite') params.is_favorite = false
  if (currentTag.value) params.tag = currentTag.value
  if (statusFilter.value && statusFilter.value !== 'active') params.status = statusFilter.value
  else params.status = 'active'
  if (qlStatusFilter.value && qlStatusFilter.value !== 'all') params.ql_status = qlStatusFilter.value
  if (sortFilter.value && sortFilter.value !== 'default') params.sort = sortFilter.value
  else params.sort = 'default'
  return params
}

async function fetchPrograms(nextPage = 1, append = false) {
  if (append) {
    if (loadingMore.value || loading.value || !hasMore.value) return
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    loadError.value = false
    const { data } = await api.get('/programs', { params: getRequestParams(nextPage) })
    total.value = data.total || 0
    hasMore.value = Boolean(data.has_more)
    page.value = data.page || nextPage
    availableTags.value = data.available_tags || []
    const items = Array.isArray(data.items) ? data.items : []
    programs.value = append ? [...programs.value, ...items] : items
    await nextTick()
    initInfiniteScroll()
  } catch (error) {
    console.error(error)
    loadError.value = true
    if (!append) programs.value = []
    ElMessage.error('加载小程序列表失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function applyFilters() {
  page.value = 1
  hasMore.value = false
  destroyInfiniteScroll()
  fetchPrograms(1, false)
}

function resetFilters() {
  searchKeyword.value = ''
  favoriteFilter.value = 'all'
  currentTag.value = ''
  statusFilter.value = 'active'
  qlStatusFilter.value = 'all'
  sortFilter.value = 'default'
  applyFilters()
}

function setStatusFilter(value) {
  if (statusFilter.value === value) return
  statusFilter.value = value
  applyFilters()
}

function setFavoriteFilter(value) {
  if (favoriteFilter.value === value) return
  favoriteFilter.value = value
  applyFilters()
}

function setQlStatusFilter(value) {
  if (qlStatusFilter.value === value) return
  qlStatusFilter.value = value
  applyFilters()
}

function setSortFilter(value) {
  if (sortFilter.value === value) return
  sortFilter.value = value
  applyFilters()
}

function selectTag(tag) {
  currentTag.value = currentTag.value === tag ? '' : tag
  applyFilters()
}

function clearFilterChip(key) {
  if (key === 'search') searchKeyword.value = ''
  if (key === 'status') statusFilter.value = 'active'
  if (key === 'favorite') favoriteFilter.value = 'all'
  if (key === 'ql') qlStatusFilter.value = 'all'
  if (key === 'sort') sortFilter.value = 'default'
  if (key === 'tag') currentTag.value = ''
  applyFilters()
}

async function loadMore() {
  if (!hasMore.value || loadingMore.value || loading.value || loadError.value) return
  await fetchPrograms(page.value + 1, true)
}

function initInfiniteScroll() {
  destroyInfiniteScroll()
  if (!loadMoreSentinel.value) return

  observer = new IntersectionObserver(
    (entries) => {
      const [entry] = entries
      if (!entry?.isIntersecting) return
      loadMore()
    },
    {
      root: null,
      rootMargin: '0px 0px 320px 0px',
      threshold: 0,
    },
  )

  observer.observe(loadMoreSentinel.value)
}

function destroyInfiniteScroll() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

function openNoteDialog(program) {
  currentProgram.value = program
  editingNote.value = program.note || ''
  noteDialogVisible.value = true
}

async function saveNote() {
  if (!currentProgram.value) return
  savingNote.value = true
  try {
    await api.put(`/programs/${currentProgram.value.program_id}`, { note: editingNote.value })
    currentProgram.value.note = editingNote.value
    noteDialogVisible.value = false
    ElMessage.success('备注已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存备注失败')
  } finally {
    savingNote.value = false
  }
}

function openTagsDialog(program) {
  currentProgram.value = program
  editingTags.value = normalizeTags(program.tags || [])
  customTagInput.value = ''
  tagsDialogVisible.value = true
}

function appendTag(tag) {
  editingTags.value = normalizeTags([...editingTags.value, tag])
}

function toggleEditingTag(tag) {
  if (editingTags.value.includes(tag)) {
    removeEditingTag(tag)
    return
  }
  appendTag(tag)
}

async function promptCustomTag() {
  try {
    const { value } = await ElMessageBox.prompt('请输入自定义标签', '新增标签', {
      confirmButtonText: '添加',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '标签不能为空',
    })
    const normalized = String(value || '').trim().slice(0, 20)
    if (normalized) appendTag(normalized)
  } catch {
    // ignore
  }
}

function addCustomTagFromInput() {
  const normalized = String(customTagInput.value || '').trim().slice(0, 20)
  if (!normalized) return
  appendTag(normalized)
  customTagInput.value = ''
}

function removeEditingTag(tag) {
  editingTags.value = editingTags.value.filter((item) => item !== tag)
}

async function saveTags() {
  if (!currentProgram.value) return
  savingTags.value = true
  try {
    const { data } = await api.put(`/programs/${currentProgram.value.program_id}`, { tags: editingTags.value })
    currentProgram.value.tags = data.tags || [...editingTags.value]
    tagsDialogVisible.value = false
    availableTags.value = mergeTagsByUsage(
      programs.value.flatMap((item) => normalizeTags(item.tags || [])),
      availableTags.value,
      currentProgram.value.tags,
    )
    ElMessage.success('标签已保存')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存标签失败')
  } finally {
    savingTags.value = false
  }
}

async function toggleFavorite(program) {
  if (updatingProgramId.value) return
  updatingProgramId.value = program.program_id
  try {
    await api.put(`/programs/${program.program_id}`, { is_favorite: !program.is_favorite })
    program.is_favorite = !program.is_favorite
    ElMessage.success(program.is_favorite ? '已加入收藏' : '已取消收藏')
  } catch (error) {
    console.error(error)
    ElMessage.error('更新收藏状态失败')
  } finally {
    updatingProgramId.value = ''
  }
}

function formatPointsGap(product) {
  const maxPoints = stockMaxUserPoints.value
  const needPoints = Number(product?.points) || 0
  const stock = Number(product?.stock) || 0
  if (stock <= 0) return '无货'
  if (needPoints <= maxPoints) return '可兑'
  return `差 ${needPoints - maxPoints}`
}

function stockRowClassName({ row }) {
  if (isProductRedeemable(row)) return 'stock-row-redeemable'
  if ((Number(row?.stock) || 0) <= 0) return 'stock-row-out'
  return 'stock-row-locked'
}

async function openStockDialog(program) {
  stockDialogVisible.value = true
  stockLoading.value = true
  stockData.value = null
  stockChangeExpanded.value = false
  try {
    const { data } = await api.get(`/programs/${program.program_id}/stock`)
    stockData.value = data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载库存详情失败')
  } finally {
    stockLoading.value = false
  }
}

async function deleteProgram(program) {
  if (deletingProgramId.value) return

  try {
    await ElMessageBox.confirm(
      `确定删除小程序“${program.program_name || program.program_id}”吗？该操作会同时删除相关库存和积分记录。`,
      '删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }

  deletingProgramId.value = program.program_id
  try {
    await api.delete(`/programs/${program.program_id}`)
    programs.value = programs.value.filter((item) => item.program_id !== program.program_id)
    total.value = Math.max(0, total.value - 1)
    availableTags.value = mergeTagsByUsage(
      programs.value.flatMap((item) => normalizeTags(item.tags || [])),
      availableTags.value,
    )
    ElMessage.success('小程序已删除')
  } catch (error) {
    console.error(error)
    ElMessage.error('删除小程序失败')
  } finally {
    deletingProgramId.value = ''
  }
}

async function archiveProgram(program) {
  if (archivingProgramId.value) return
  const willArchive = !program.is_archived
  archivingProgramId.value = program.program_id
  try {
    const { data } = await api.put(`/programs/${program.program_id}`, { is_archived: willArchive })
    program.is_archived = Boolean(data?.is_archived ?? willArchive)
    program.archived_at = data?.archived_at ?? (willArchive ? new Date().toISOString() : null)
    if (willArchive) {
      // backend auto-clears favorite when archiving
      program.is_favorite = Boolean(data?.is_favorite ?? false)
    }

    // If current view filters out this program after the change, drop it from the list
    const dropFromList =
      (statusFilter.value === 'active' && willArchive) ||
      (statusFilter.value === 'archived' && !willArchive) ||
      (favoriteFilter.value === 'favorite' && willArchive && !program.is_favorite)

    if (dropFromList) {
      programs.value = programs.value.filter((item) => item.program_id !== program.program_id)
      total.value = Math.max(0, total.value - 1)
    }

    ElMessage.success(willArchive ? '已归档' : '已取消归档')
  } catch (error) {
    console.error(error)
    ElMessage.error(willArchive ? '归档失败' : '取消归档失败')
  } finally {
    archivingProgramId.value = ''
  }
}

function handleProgramCommand(command, program) {
  if (command === 'archive') {
    archiveProgram(program)
  } else if (command === 'delete') {
    deleteProgram(program)
  }
}

watch(() => programs.value.length, async (value) => {
  if (!value || loadError.value) return
  await nextTick()
  initInfiniteScroll()
})

onMounted(async () => {
  const validStatus = new Set(['active', 'archived', 'all'])
  const queryStatus = typeof route.query.status === 'string' ? route.query.status : ''
  const hasExplicitStatusQuery = validStatus.has(queryStatus)
  const hasSavedState = Boolean(readPageState())
  const shouldRestore = !hasExplicitStatusQuery && (route.query.restore === '1' || route.query.fromDetail === '1' || hasSavedState)
  if (shouldRestore && await restorePageState()) {
    return
  }
  if (hasExplicitStatusQuery) {
    statusFilter.value = queryStatus
  }
  fetchPrograms(1, false)
})

onBeforeUnmount(() => {
  destroyInfiniteScroll()
})
</script>

<style scoped>
.programs-showcase-page {
  position: relative;
  gap: 22px;
  padding: 6px 2px 18px;
}

.programs-showcase-page::before {
  content: '';
  position: fixed;
  inset: 0 0 0 260px;
  pointer-events: none;
  z-index: -1;
  background:
    linear-gradient(rgba(229, 209, 176, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(229, 209, 176, 0.16) 1px, transparent 1px),
    linear-gradient(180deg, #fffaf0 0%, #fff7eb 100%);
  background-size: 24px 24px, 24px 24px, 100% 100%;
  background-position: 0 0, 0 0, 0 0;
}

.showcase-toolbar-card {
  border-radius: 26px;
  border: 1px solid rgba(235, 220, 194, 0.88);
  background: rgba(255, 252, 247, 0.9);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.04);
  backdrop-filter: blur(2px);
  padding: 16px 18px;
}

.filter-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filter-search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.filter-search-side {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.warm-chip {
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
}

.filter-count-chip {
  min-width: 78px;
  justify-content: center;
}

.showcase-search-input :deep(.el-input__wrapper),
.showcase-search-input :deep(.el-input-group__append) {
  background: #fffaf3;
  box-shadow: 0 0 0 1px rgba(232, 210, 184, 0.78) inset;
}

.showcase-search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #d6a96b inset;
}

.filter-search-icon {
  color: #b08958;
}

.filter-search-btn {
  color: #8b5e34 !important;
  font-weight: 700;
}

.showcase-reset-button,
.filter-reset-btn {
  flex: 0 0 auto;
  min-width: 72px;
  height: 40px;
  padding: 0 14px;
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
  font-size: 13px;
}

.filter-control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
}

.filter-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.filter-group-label {
  flex: 0 0 auto;
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.segmented-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255, 248, 236, 0.95);
  box-shadow: inset 0 0 0 1px rgba(231, 208, 176, 0.82);
}

.segmented-item {
  border: 0;
  background: transparent;
  color: #8a6c4c;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 8px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.16s ease;
  white-space: nowrap;
}

.segmented-item:hover {
  background: rgba(255, 255, 255, 0.72);
}

.segmented-item.active {
  background: linear-gradient(135deg, #f5d8a8, #efc381);
  color: #5b3b14;
  box-shadow: 0 8px 16px rgba(225, 172, 88, 0.18);
}

.filter-tags-panel {
  border-radius: 16px;
  background: rgba(255, 250, 242, 0.8);
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.72);
  padding: 10px 12px 12px;
}

.filter-tags-header {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin-bottom: 10px;
}

.filter-tags-current {
  color: #6f5a44;
  font-size: 13px;
  font-weight: 700;
}

.filter-tags-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(245, 216, 168, 0.7);
  color: #8b5e34;
  font-size: 11px;
  font-weight: 700;
}

.filter-tag-list.showcase {
  gap: 8px;
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}

.filter-chip {
  border: 0;
  padding: 8px 12px;
  border-radius: 999px;
  background: #fff8ef;
  color: #8a6c4c;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(231, 208, 176, 0.86);
  transition: all 0.2s ease;
}

.filter-chip:hover {
  transform: translateY(-1px);
  background: #fff3de;
}

.filter-chip.active {
  background: linear-gradient(135deg, #f5d8a8, #efc381);
  color: #5b3b14;
  box-shadow: 0 10px 18px rgba(225, 172, 88, 0.18);
}

.active-filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.active-filter-label {
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 700;
}

.active-filter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filter-chip {
  border: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 244, 221, 0.95);
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.active-filter-close {
  font-size: 14px;
  line-height: 1;
  opacity: 0.75;
}

/* Row-first grid so infinite-scroll order stays left→right, top→bottom
   (CSS multi-column fills top→bottom per column and breaks reading order on page 2+). */
.showcase-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 22px;
  align-items: start;
}

.full-span {
  grid-column: 1 / -1;
}

.showcase-card {
  position: relative;
  display: flex;
  width: 100%;
  flex-direction: column;
  min-height: 0;
  margin: 0;
  padding: 22px;
  border-radius: 24px;
  background: #fffdf9;
  border: 1px solid rgba(239, 226, 208, 0.95);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.masonry-card:nth-child(3n) {
  background: #fffdf9;
}

.masonry-card:nth-child(4n) {
  background: #fffdf9;
}

.showcase-card::before {
  display: none;
}

.showcase-card:hover {
  transform: translateY(-2px);
  border-color: rgba(230, 196, 154, 0.98);
  box-shadow: 0 10px 24px rgba(126, 98, 63, 0.07);
}

.showcase-card.is-favorite {
  border-color: rgba(240, 196, 113, 0.72);
}

.showcase-card.is-archived {
  opacity: 0.62;
  filter: grayscale(0.55);
  background: rgba(248, 244, 235, 0.92);
}

.showcase-card.is-archived:hover {
  opacity: 0.85;
  filter: grayscale(0.2);
}

.archived-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 1;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(120, 113, 108, 0.92);
  color: #f5f5f4;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 10px rgba(68, 64, 60, 0.18);
  pointer-events: none;
}

.dropdown-danger-text {
  color: #c2410c;
  font-weight: 600;
}

.showcase-card.has-stock {
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.05);
}

.showcase-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.showcase-card-brand {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
  flex: 1;
}

.no-avatar-brand {
  gap: 0;
}

.full-width-brand-text,
.showcase-card-brand-text {
  min-width: 0;
  width: 100%;
}

.showcase-card-title-line {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  min-width: 0;
  width: 100%;
}

.showcase-card-title {
  margin: 0;
  flex: 1 1 auto;
  min-width: 0;
  color: #2f2418;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.showcase-card-title.is-title-md {
  font-size: 16px;
}

.showcase-card-title.is-title-sm {
  font-size: 14px;
}

.showcase-card-title.is-title-xs {
  font-size: 12px;
  letter-spacing: -0.02em;
}

.showcase-card-title.is-copyable,
.showcase-card-id.is-copyable {
  cursor: pointer;
}

.showcase-card-title.is-copyable:hover {
  color: #a16207;
}

.showcase-card-id.is-copyable:hover {
  color: #b7791f;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.showcase-card-title.is-copyable:focus-visible,
.showcase-card-id.is-copyable:focus-visible {
  outline: 2px solid rgba(214, 169, 107, 0.55);
  outline-offset: 2px;
  border-radius: 6px;
}

/* 序号角标：横向排列在标题行最前，便于跟踪浏览进度 */
.showcase-card-index {
  flex: 0 0 auto;
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  margin-top: 3px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.showcase-card-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
  min-width: 0;
  width: 100%;
}

.compact-meta-row {
  margin-right: 0;
}

.showcase-card-id {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.showcase-card-stock-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.showcase-card-tag-row {
  display: flex;
  justify-content: flex-start;
  margin-top: 6px;
  min-width: 0;
  cursor: pointer;
}

.showcase-card-change-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.inline-change-row {
  margin-top: 0;
}

.stock-count-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #7c5833;
}

.stock-count-button {
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.stock-count-button:hover {
  transform: translateY(-1px);
}

.stock-count-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.stock-count-button:focus-visible {
  outline: 2px solid rgba(223, 159, 80, 0.45);
  outline-offset: 4px;
  border-radius: 12px;
}

.stock-count-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #b7791f;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-count-value {
  font-size: 22px;
  line-height: 1;
  font-weight: 800;
  color: #a16207;
}

.ql-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  flex: 0 0 auto;
  flex-shrink: 0;
  font-size: 14px;
}

.ql-status-badge.is-enabled {
  color: #15803d;
  background: rgba(220, 252, 231, 0.95);
  box-shadow: inset 0 0 0 1px rgba(34, 197, 94, 0.35);
}

.ql-status-badge.is-disabled {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.95);
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.4);
}

.ql-schedule-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  min-width: 0;
  margin-left: 4px;
  padding: 2px 8px 2px 6px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.95);
  color: #475569;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.35);
  cursor: default;
}

.ql-schedule-chip.is-enabled {
  background: rgba(236, 253, 245, 0.95);
  color: #047857;
  box-shadow: inset 0 0 0 1px rgba(52, 211, 153, 0.35);
}

.ql-schedule-chip.is-disabled {
  background: rgba(254, 242, 242, 0.95);
  color: #b91c1c;
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.35);
}

.ql-schedule-label {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  opacity: 0.85;
}

.ql-schedule-code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  background: transparent;
  color: inherit;
}

.cash-count-icon {
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.96), rgba(209, 250, 229, 0.9)) !important;
  color: #047857 !important;
  box-shadow: inset 0 0 0 1px rgba(110, 231, 183, 0.72) !important;
}

.cash-count-display .points-count-value {
  color: #047857;
}

/* 最高积分指标，紧挨商品数量按钮，配色用蓝绿调与橙色商品块区分 */
.points-count-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #1d6f6c;
}

.points-count-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(214, 240, 230, 0.96), rgba(189, 226, 220, 0.9));
  color: #0f766e;
  box-shadow: inset 0 0 0 1px rgba(155, 209, 198, 0.78);
}

.points-count-value {
  font-size: 22px;
  line-height: 1;
  font-weight: 800;
  color: #0f766e;
  font-variant-numeric: tabular-nums;
}

.points-count-display.is-empty {
  opacity: 0.45;
}

.points-count-display.is-empty .points-count-value {
  color: #6b7280;
}

.stock-row-divider {
  width: 1px;
  height: 22px;
  background: linear-gradient(180deg, transparent, rgba(199, 169, 130, 0.45), transparent);
  margin: 0 4px;
  flex: 0 0 auto;
}

.showcase-card-tag-inline {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  cursor: pointer;
}

.meta-tag-inline {
  margin-left: auto;
  max-width: calc(100% - 118px);
}

.inline-tag-chip {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 8px;
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
}

.stock-count-chip {
  font-weight: 700;
}

.stock-change-chip {
  min-width: 40px;
  justify-content: center;
}

.showcase-card-id {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 0 1 auto;
  min-width: 0;
}

.showcase-card-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(172, 133, 83, 0.45);
}

.stock-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 10px;
  background: #cfd5dd;
  box-shadow: 0 0 0 2px rgba(207, 213, 221, 0.18);
}

.stock-dot.active {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.16);
}

.showcase-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex: 0 0 auto;
}

.danger-action-button {
  color: #c2410c;
}

.danger-action-button:hover,
.danger-action-button:focus-visible {
  color: #dc2626;
  background: rgba(254, 226, 226, 0.92);
}

.danger-action-button:disabled {
  color: #caa27a;
  cursor: not-allowed;
}

.clickable-chip-group {
  display: flex;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.clickable-chip-group:focus-visible {
  outline: 2px solid rgba(214, 169, 107, 0.5);
  outline-offset: 4px;
  border-radius: 16px;
}

.clickable-chip-group:hover .showcase-chip {
  filter: brightness(0.98);
  box-shadow: 0 8px 18px rgba(126, 98, 63, 0.08);
}

.showcase-dialog-body,
.tags-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.showcase-dialog-intro,
.tags-dialog-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 2px 2px 6px;
}

.showcase-dialog-title,
.tags-dialog-title {
  color: #3a2a1d;
  font-size: 16px;
  font-weight: 700;
}

.showcase-dialog-subtitle,
.tags-dialog-subtitle {
  margin-top: 6px;
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
}

.showcase-dialog-badge,
.tags-dialog-counter {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.96), rgba(255, 237, 213, 0.9));
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(231, 202, 163, 0.72);
}

.stock-badge {
  color: #a16207;
}

.stock-dialog-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.success-badge {
  color: #15803d;
}

.warning-badge {
  color: #b45309;
}

.dialog-panel {
  padding: 16px 16px 14px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(255, 247, 235, 0.94));
  box-shadow: inset 0 0 0 1px rgba(235, 220, 194, 0.88);
}

.compact-tip-panel {
  padding-bottom: 16px;
}

.tags-dialog-list {
  gap: 10px;
}

.dialog-tag-chip {
  border: 0;
  padding: 9px 15px;
  border-radius: 999px;
  background: #fffaf3;
  color: #8a6c4c;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.82);
  transition: all 0.2s ease;
}

.dialog-tag-chip:hover {
  transform: translateY(-1px);
  background: #fff2df;
  color: #7a5530;
}

.dialog-tag-chip.active {
  background: linear-gradient(135deg, #d8f2e5, #c4ead6);
  color: #21684f;
  box-shadow: 0 10px 22px rgba(103, 170, 136, 0.16);
}

.dialog-tag-chip.add-chip {
  background: linear-gradient(135deg, rgba(243, 248, 255, 0.96), rgba(230, 241, 255, 0.94));
  color: #2563eb;
  box-shadow: inset 0 0 0 1px rgba(174, 205, 255, 0.86);
}

.dialog-tag-chip.add-chip:hover {
  background: linear-gradient(135deg, rgba(233, 243, 255, 0.98), rgba(219, 235, 255, 0.96));
  color: #1d4ed8;
}

.selected-tags-list {
  min-height: 44px;
}

.selected-dialog-tag {
  --el-tag-bg-color: rgba(214, 241, 230, 0.96);
  --el-tag-border-color: rgba(155, 209, 182, 0.88);
  --el-tag-hover-color: rgba(198, 233, 217, 1);
  --el-tag-text-color: #21684f;
  padding-inline: 10px;
  border-radius: 999px;
  font-weight: 600;
}

.tags-empty-state {
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  color: #9b7e5c;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(238, 225, 204, 0.92);
}

.showcase-dialog-textarea :deep(.el-textarea__inner),
.tags-custom-input :deep(.el-input__wrapper),
.tags-custom-input :deep(.el-input-group__append) {
  background: #fffaf3;
  box-shadow: 0 0 0 1px rgba(232, 210, 184, 0.78) inset;
}

.showcase-dialog-textarea :deep(.el-textarea__inner) {
  min-height: 148px;
  border-radius: 18px;
  color: #5f4932;
  line-height: 1.75;
}

.tags-custom-input :deep(.el-input__wrapper.is-focus),
.showcase-dialog-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #d6a96b inset;
}

.tags-add-button {
  color: #8b5e34;
  font-weight: 700;
}

.tags-dialog-tip {
  margin-top: 10px;
  color: #a0815d;
  font-size: 12px;
  line-height: 1.7;
}

.stock-dialog-body,
.detail-dialog-body {
  gap: 14px;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-info-card {
  min-height: 110px;
}

.detail-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.info-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 244, 221, 0.95);
  color: #8b5e34;
  font-size: 12px;
  font-weight: 700;
}

.info-tag.empty {
  background: rgba(248, 250, 252, 0.95);
  color: #94a3b8;
}

.detail-note-text {
  margin: 0;
  color: #4a3623;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-id-value,
.detail-update-value {
  font-size: 15px !important;
}

.mono-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-all;
}

.stock-summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.stock-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stock-section-title {
  margin-bottom: 12px;
  color: #7b5a37;
  font-size: 14px;
  font-weight: 700;
}

.stock-section-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.stock-section-title-row .stock-section-title {
  margin-bottom: 0;
}

.stock-section-hint {
  color: #9b7e5c;
  font-size: 12px;
  line-height: 1.4;
  text-align: right;
}

.stock-product-name-cell {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-points-gap {
  font-size: 12px;
  font-weight: 700;
}

.stock-points-gap.is-ok {
  color: #15803d;
}

.stock-points-gap.is-short {
  color: #b45309;
}

.stock-product-table :deep(.stock-row-redeemable > td.el-table__cell) {
  background: rgba(220, 252, 231, 0.55) !important;
}

.stock-product-table :deep(.stock-row-locked > td.el-table__cell) {
  background: rgba(255, 247, 237, 0.5) !important;
}

.stock-product-table :deep(.stock-row-out > td.el-table__cell) {
  background: rgba(248, 250, 252, 0.85) !important;
  color: #94a3b8;
}

.stock-product-table :deep(.stock-row-redeemable:hover > td.el-table__cell) {
  background: rgba(187, 247, 208, 0.72) !important;
}

.stock-product-table :deep(.stock-row-locked:hover > td.el-table__cell) {
  background: rgba(254, 243, 199, 0.7) !important;
}

.stock-change-panel {
  padding-top: 14px;
}

.stock-change-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.stock-change-toggle-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.stock-change-toggle .stock-section-title {
  margin-bottom: 0;
}

.stock-change-toggle-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.stock-change-toggle-tip {
  color: #9b7e5c;
  font-size: 12px;
}

.stock-change-toggle-arrow {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 248, 236, 0.95);
  color: #8b5e34;
  font-size: 14px;
  transition: transform 0.18s ease;
}

.stock-change-toggle-arrow.open {
  transform: rotate(180deg);
}

.stock-change-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.stock-change-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}

.stock-change-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-change-name {
  color: #4a3623;
  font-size: 14px;
  font-weight: 700;
}

.stock-change-meta {
  color: #9b7e5c;
  font-size: 12px;
}

.stock-change-side {
  flex: 0 0 auto;
}

.stock-summary-label {
  color: #9b7e5c;
  font-size: 13px;
  font-weight: 600;
}

.stock-summary-value {
  color: #a16207;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
}

.success-text {
  color: #15803d;
}

.warning-text {
  color: #b45309;
}

.stock-table-panel {
  padding-top: 12px;
}

.showcase-dialog-table :deep(.el-table) {
  --el-table-border-color: rgba(236, 221, 199, 0.92);
  --el-table-header-bg-color: rgba(255, 248, 238, 0.96);
  --el-table-tr-bg-color: rgba(255, 253, 249, 0.96);
  --el-table-row-hover-bg-color: rgba(255, 245, 229, 0.92);
  --el-table-text-color: #57412d;
  --el-table-header-text-color: #8b5e34;
}

.showcase-dialog-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.showcase-dialog-table :deep(th.el-table__cell) {
  font-weight: 700;
}

.showcase-dialog-table :deep(.el-table__cell) {
  padding: 14px 0;
}

.product-thumb {
  width: 62px;
  height: 62px;
  border-radius: 16px;
  box-shadow: 0 6px 16px rgba(126, 98, 63, 0.12);
}

.stock-loading {
  padding: 16px;
}

.showcase-dialog :deep(.el-dialog) {
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 253, 249, 0.98), rgba(255, 248, 238, 0.98));
  box-shadow: 0 26px 60px rgba(97, 72, 43, 0.16);
}

.showcase-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 24px 28px 10px;
}

.showcase-dialog :deep(.el-dialog__title) {
  color: #2f2418;
  font-size: 22px;
  font-weight: 800;
}

.showcase-dialog :deep(.el-dialog__body) {
  padding: 8px 28px 18px;
}

.showcase-dialog :deep(.el-dialog__footer) {
  padding: 10px 28px 26px;
}

.showcase-dialog :deep(.el-dialog__headerbtn) {
  top: 24px;
  right: 24px;
}

.showcase-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #a18461;
}

.showcase-dialog :deep(.el-dialog__footer .el-button) {
  min-width: 92px;
  height: 40px;
  border-radius: 14px;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--default) {
  border-color: rgba(219, 183, 141, 0.74);
  color: #8b5e34;
  background: #fff9f2;
}

.showcase-dialog :deep(.el-dialog__footer .el-button--primary) {
  border: 0;
  background: linear-gradient(135deg, #f0c37c, #d9a25f);
  box-shadow: 0 12px 24px rgba(219, 162, 88, 0.22);
}

.footer-actions {
  padding: 4px;
  border-radius: 14px;
  background: rgba(255, 248, 236, 0.88);
  box-shadow: inset 0 0 0 1px rgba(232, 210, 184, 0.72);
}

.ref-action-group {
  gap: 6px;
}

.showcase-icon-button {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8a6c4c;
  box-shadow: none;
  cursor: pointer;
  transition: color 0.18s ease, transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.ref-action-button {
  padding: 0;
  background: transparent;
  color: #6f7783;
  box-shadow: none;
}

.icon-plain-button {
  min-width: 36px;
  line-height: 1;
  opacity: 1;
}

.icon-plain-button :deep(.el-icon) {
  font-size: 18px;
}

.ref-action-button:hover {
  color: #4b5563;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 14px rgba(126, 98, 63, 0.08);
  transform: translateY(-1px);
}

.action-tooltip-wrap {
  display: inline-flex;
}

.ref-action-button:disabled,
.ref-action-button.is-disabled-action,
.ref-action-button:disabled:hover,
.ref-action-button.is-disabled-action:hover {
  color: #c4b5a0;
  background: rgba(245, 240, 232, 0.9);
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
  opacity: 0.72;
}

.ref-action-button-favorite.active {
  color: #e5a22d;
  background: rgba(255, 248, 230, 0.98);
  opacity: 1;
}

.ref-action-button-favorite.active:hover {
  color: #d99623;
  background: rgba(255, 244, 214, 0.98);
}

.showcase-button-loading {
  font-size: 12px;
  letter-spacing: 0.2em;
}

.showcase-card-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.compact-card-chips {
  margin-top: 14px;
}

.showcase-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.showcase-chip.muted {
  background: rgba(255, 242, 225, 0.92);
  color: #966537;
}

.showcase-chip.success {
  background: rgba(211, 239, 227, 0.92);
  color: #21684f;
}

.showcase-chip.warning {
  background: rgba(252, 237, 214, 0.92);
  color: #a16207;
}

.showcase-card-note {
  margin: 12px 0 0;
  color: #6f5a44;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow: hidden;
  max-height: calc(1.8em * 6);
}

.masonry-note.empty {
  min-height: 56px;
}

.showcase-card-note.empty {
  color: #a0896e;
}

.showcase-endpoint-block {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(236, 221, 199, 0.92);
}

.compact-endpoint-block {
  padding: 12px 14px;
}

.showcase-block-label {
  color: #b08a5b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.showcase-endpoint-value {
  margin-top: 8px;
  color: #3e2f22;
  font-size: 14px;
  font-weight: 600;
  word-break: break-all;
}

.showcase-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.compact-tag-row {
  gap: 7px;
}

.showcase-tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 249, 239, 0.94);
  color: #7a6143;
  font-size: 12px;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(233, 215, 191, 0.92);
}

.showcase-tag.empty {
  color: #a0896e;
}

.showcase-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(236, 220, 196, 0.75);
}

.compact-footer {
  align-items: center;
  flex-wrap: wrap;
}

.showcase-footer-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: nowrap;
  white-space: nowrap;
  color: #8e7454;
  font-size: 12px;
}

.showcase-footer-time {
  white-space: nowrap;
}

.showcase-footer-icon {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 243, 225, 0.92);
  color: #a16207;
  font-size: 12px;
}

.showcase-footer-actions {
  display: flex;
  align-items: center;
}

.compact-footer-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.showcase-mini-action {
  border: 0;
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 249, 240, 0.98);
  color: #7b5d3d;
  font-size: 12px;
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(232, 211, 183, 0.96);
  cursor: pointer;
  transition: all 0.2s ease;
}

.showcase-mini-action:hover {
  transform: translateY(-1px);
  background: #fff3df;
}

.stock-mini-action.active {
  background: linear-gradient(135deg, #def7e7, #c3f0d1);
  color: #166534;
  box-shadow: inset 0 0 0 1px rgba(134, 239, 172, 0.9);
}

.tag-mini-action:hover {
  color: #7c3aed;
  box-shadow: inset 0 0 0 1px rgba(196, 181, 253, 0.92);
}

.favorite-mini-action.active {
  background: linear-gradient(135deg, #f7d88f, #f0bc65);
  color: #6b430d;
  box-shadow: inset 0 0 0 1px rgba(239, 186, 89, 0.94);
}

.showcase-action-pill {
  border: 0;
  padding: 10px 16px;
  border-radius: 999px;
  background: linear-gradient(135deg, #f4d39e, #ebb96f);
  color: #5d3a11;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(233, 183, 99, 0.22);
}

.showcase-action-pill.muted {
  background: #fff6ea;
  color: #8a6c4c;
  box-shadow: inset 0 0 0 1px rgba(230, 204, 167, 0.92);
}

.showcase-status-bar {
  padding-bottom: 10px;
}

@media (max-width: 1280px) {
  .showcase-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .programs-showcase-page::before {
    inset: 0;
  }

  .showcase-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .filter-search-row {
    grid-template-columns: 1fr;
  }

  .filter-search-side {
    justify-content: space-between;
  }

  .filter-control-row {
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .showcase-toolbar-card,
  .showcase-card {
    border-radius: 22px;
  }

  .filter-group {
    width: 100%;
    justify-content: space-between;
  }

  .segmented-group {
    flex: 1 1 auto;
    justify-content: space-between;
  }

  .showcase-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .showcase-card-top,
  .showcase-card-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .showcase-card-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
    width: 100%;
  }

  .ref-action-group {
    gap: 8px;
  }

  .compact-footer,
  .compact-footer-actions {
    align-items: stretch;
    justify-content: flex-start;
  }

  .footer-actions {
    justify-content: flex-start;
  }

  .detail-info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
