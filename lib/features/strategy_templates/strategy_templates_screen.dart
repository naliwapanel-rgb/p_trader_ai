import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../bots/data/backend_trading_bot.dart';
import 'data/backend_strategy_template.dart';
import 'providers/backend_strategy_template_provider.dart';
import 'providers/backend_strategy_template_state.dart';
import 'widgets/add_strategy_template_dialog.dart';
import 'widgets/edit_strategy_template_dialog.dart';

enum _OwnedTemplateFilter { all, draft, published, archived }

class StrategyTemplatesScreen extends ConsumerStatefulWidget {
  const StrategyTemplatesScreen({super.key});

  @override
  ConsumerState<StrategyTemplatesScreen> createState() {
    return _StrategyTemplatesScreenState();
  }
}

class _StrategyTemplatesScreenState
    extends ConsumerState<StrategyTemplatesScreen> {
  _OwnedTemplateFilter _ownedFilter = _OwnedTemplateFilter.all;
  String? _loadErrorMessage;

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      _loadInitialTemplates();
    });
  }

  Future<void> _loadInitialTemplates() async {
    final initialState = ref.read(backendStrategyTemplateProvider);

    await _loadTemplates(
      loadOwned: !initialState.hasLoadedOwned && !initialState.isLoadingOwned,
      loadPublic:
          !initialState.hasLoadedPublic && !initialState.isLoadingPublic,
    );
  }

  Future<void> _refreshAll() {
    return _loadTemplates(loadOwned: true, loadPublic: true);
  }

  Future<void> _loadTemplates({
    required bool loadOwned,
    required bool loadPublic,
  }) async {
    final notifier = ref.read(backendStrategyTemplateProvider.notifier);

    String? firstError;

    if (mounted) {
      setState(() {
        _loadErrorMessage = null;
      });
    }

    if (loadOwned) {
      await notifier.loadOwned();

      firstError = ref.read(backendStrategyTemplateProvider).errorMessage;
    }

    if (loadPublic) {
      await notifier.loadPublic();

      firstError ??= ref.read(backendStrategyTemplateProvider).errorMessage;
    }

    final currentError = ref.read(backendStrategyTemplateProvider).errorMessage;

    if (!mounted) {
      return;
    }

    setState(() {
      _loadErrorMessage = currentError ?? firstError;
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendStrategyTemplateProvider);

    final displayedError = state.errorMessage ?? _loadErrorMessage;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Strategy Templates'),
          actions: [
            IconButton(
              key: const Key('create-strategy-template-screen-button'),
              tooltip: 'Create strategy template',
              onPressed: state.isMutating ? null : _showCreateDialog,
              icon: const Icon(Icons.add_circle_outline),
            ),
            IconButton(
              key: const Key('refresh-strategy-templates-button'),
              tooltip: 'Refresh strategy templates',
              onPressed: state.isLoading ? null : _refreshAll,
              icon: const Icon(Icons.refresh),
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(
                key: Key('owned-templates-tab'),
                icon: Icon(Icons.folder_copy_outlined),
                text: 'My Templates',
              ),
              Tab(
                key: Key('public-templates-tab'),
                icon: Icon(Icons.public_outlined),
                text: 'Public Templates',
              ),
            ],
          ),
        ),
        body: Column(
          children: [
            if (displayedError != null)
              _messageBanner(
                message: displayedError,
                color: AppColors.danger,
                icon: Icons.error_outline,
              ),
            if (state.infoMessage != null)
              _messageBanner(
                message: state.infoMessage!,
                color: AppColors.success,
                icon: Icons.check_circle_outline,
              ),
            Expanded(
              child: TabBarView(
                children: [_ownedTab(state), _publicTab(state)],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showCreateDialog() async {
    final request = await showDialog<StrategyTemplateCreateRequest>(
      context: context,
      builder: (_) => const AddStrategyTemplateDialog(),
    );

    if (request == null || !mounted) {
      return;
    }

    setState(() {
      _loadErrorMessage = null;
    });

    await ref
        .read(backendStrategyTemplateProvider.notifier)
        .createTemplate(request);
  }

  Widget _ownedTab(BackendStrategyTemplateState state) {
    final templates = switch (_ownedFilter) {
      _OwnedTemplateFilter.all => state.ownedTemplates,
      _OwnedTemplateFilter.draft => state.draftTemplates,
      _OwnedTemplateFilter.published => state.publishedTemplates,
      _OwnedTemplateFilter.archived => state.archivedTemplates,
    };

    return Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.md,
            AppSpacing.md,
            AppSpacing.md,
            AppSpacing.sm,
          ),
          child: Row(
            children: [
              _filterChip(
                filter: _OwnedTemplateFilter.all,
                label: 'All',
                count: state.ownedTemplates.length,
              ),
              const SizedBox(width: AppSpacing.sm),
              _filterChip(
                filter: _OwnedTemplateFilter.draft,
                label: 'Draft',
                count: state.draftTemplates.length,
              ),
              const SizedBox(width: AppSpacing.sm),
              _filterChip(
                filter: _OwnedTemplateFilter.published,
                label: 'Published',
                count: state.publishedTemplates.length,
              ),
              const SizedBox(width: AppSpacing.sm),
              _filterChip(
                filter: _OwnedTemplateFilter.archived,
                label: 'Archived',
                count: state.archivedTemplates.length,
              ),
            ],
          ),
        ),
        Expanded(
          child: _templateList(
            templates: templates,
            canEdit: true,
            loading: state.isLoadingOwned,
            loaded: state.hasLoadedOwned,
            emptyTitle: _ownedEmptyTitle(_ownedFilter),
            emptyMessage: _ownedEmptyMessage(_ownedFilter),
            onRefresh: () => _loadTemplates(loadOwned: true, loadPublic: false),
          ),
        ),
      ],
    );
  }

  Widget _publicTab(BackendStrategyTemplateState state) {
    return _templateList(
      templates: state.publicTemplates,
      canEdit: false,
      loading: state.isLoadingPublic,
      loaded: state.hasLoadedPublic,
      emptyTitle: 'No public templates',
      emptyMessage: 'Published public templates will appear here.',
      onRefresh: () => _loadTemplates(loadOwned: false, loadPublic: true),
    );
  }

  Widget _filterChip({
    required _OwnedTemplateFilter filter,
    required String label,
    required int count,
  }) {
    return ChoiceChip(
      key: Key('owned-filter-${filter.name}'),
      selected: _ownedFilter == filter,
      onSelected: (_) {
        setState(() {
          _ownedFilter = filter;
        });
      },
      label: Text('$label ($count)'),
    );
  }

  Widget _templateList({
    required List<BackendStrategyTemplate> templates,
    required bool canEdit,
    required bool loading,
    required bool loaded,
    required String emptyTitle,
    required String emptyMessage,
    required Future<void> Function() onRefresh,
  }) {
    if (loading && !loaded) {
      return const Center(child: CircularProgressIndicator());
    }

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          if (loading)
            const Padding(
              padding: EdgeInsets.only(bottom: AppSpacing.md),
              child: LinearProgressIndicator(),
            ),
          if (templates.isEmpty)
            _emptyState(title: emptyTitle, message: emptyMessage)
          else
            ...templates.map(
              (template) => _templateCard(template, canEdit: canEdit),
            ),
          const SizedBox(height: AppSpacing.xl),
        ],
      ),
    );
  }

  Widget _emptyState({required String title, required String message}) {
    return GlassCard(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.xl),
        child: Column(
          children: [
            const Icon(
              Icons.description_outlined,
              size: 58,
              color: AppColors.textSecondary,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              title,
              style: AppTextStyles.title,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              message,
              style: AppTextStyles.body,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _templateCard(
    BackendStrategyTemplate template, {
    required bool canEdit,
  }) {
    final statusColor = _statusColor(template.status);
    final state = ref.watch(backendStrategyTemplateProvider);
    final isBusy = state.isTemplateBusy(template.id);

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 23,
                  backgroundColor: statusColor.withValues(alpha: 0.15),
                  child: Icon(Icons.description_outlined, color: statusColor),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(template.name, style: AppTextStyles.title),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        '${template.symbol} • '
                        '${template.timeframe.backendValue} • '
                        '${template.category.backendValue.toUpperCase()}',
                        style: AppTextStyles.body,
                      ),
                    ],
                  ),
                ),
                _statusChip(template.status.backendValue, statusColor),
              ],
            ),
            if (template.description != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(template.description!, style: AppTextStyles.body),
            ],
            const SizedBox(height: AppSpacing.md),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                _metricChip(
                  'Strategy',
                  _humanize(template.strategyType.backendValue),
                  AppColors.primary,
                ),
                _metricChip(
                  'Visibility',
                  _humanize(template.visibility.backendValue),
                  _visibilityColor(template.visibility),
                ),
                _metricChip(
                  'Version',
                  '${template.version}',
                  AppColors.primary,
                ),
                _metricChip(
                  'Risk',
                  '${template.riskPerTradePercent.toStringAsFixed(2)}%',
                  AppColors.warning,
                ),
                _metricChip(
                  'Max Position',
                  '\$${template.maxPositionValueUsd.toStringAsFixed(2)}',
                  AppColors.success,
                ),
                if (template.paperTrading)
                  _metricChip('Mode', 'Paper', AppColors.primary),
                if (template.dryRun)
                  _metricChip('Safety', 'Dry Run', AppColors.success),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            OutlinedButton.icon(
              key: Key('template-${template.id}-details-button'),
              onPressed: () =>
                  _showDetails(template, canEdit: canEdit, isBusy: isBusy),
              icon: const Icon(Icons.info_outline),
              label: const Text('Details'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricChip(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        '$label: $value',
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _statusChip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _messageBanner({
    required String message,
    required Color color,
    required IconData icon,
  }) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.md,
        AppSpacing.md,
        0,
      ),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.sm),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          border: Border.all(color: color.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            Icon(icon, color: color),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(message, style: TextStyle(color: color)),
            ),
            IconButton(
              tooltip: 'Dismiss message',
              onPressed: () {
                ref
                    .read(backendStrategyTemplateProvider.notifier)
                    .clearMessages();

                setState(() {
                  _loadErrorMessage = null;
                });
              },
              icon: const Icon(Icons.close),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showEditDialog(BackendStrategyTemplate template) async {
    final request = await showDialog<StrategyTemplateUpdateRequest>(
      context: context,
      builder: (_) => EditStrategyTemplateDialog(template: template),
    );

    if (request == null || !mounted) {
      return;
    }

    setState(() {
      _loadErrorMessage = null;
    });

    await ref
        .read(backendStrategyTemplateProvider.notifier)
        .updateTemplate(templateId: template.id, request: request);
  }

  Future<void> _confirmDelete(BackendStrategyTemplate template) async {
    ref.read(backendStrategyTemplateProvider.notifier).clearMessages();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete Strategy Template?'),
        content: Text(
          'Delete "${template.name}" permanently? '
          'This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancel'),
          ),
          FilledButton.icon(
            key: const Key('confirm-delete-template-button'),
            onPressed: () => Navigator.pop(dialogContext, true),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.danger,
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.delete_outline),
            label: const Text('Delete Template'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) {
      return;
    }

    await ref
        .read(backendStrategyTemplateProvider.notifier)
        .deleteTemplate(template.id);
  }

  Future<void> _showDetails(
    BackendStrategyTemplate template, {
    required bool canEdit,
    required bool isBusy,
  }) {
    return showDialog<void>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(template.name),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                _detailRow('Status', _humanize(template.status.backendValue)),
                _detailRow(
                  'Visibility',
                  _humanize(template.visibility.backendValue),
                ),
                _detailRow(
                  'Strategy',
                  _humanize(template.strategyType.backendValue),
                ),
                _detailRow('Market', template.symbol),
                _detailRow('Timeframe', template.timeframe.backendValue),
                _detailRow('Category', template.category.backendValue),
                _detailRow('Version', '${template.version}'),
                _detailRow(
                  'Risk per trade',
                  '${template.riskPerTradePercent.toStringAsFixed(2)}%',
                ),
                _detailRow(
                  'Maximum position',
                  '\$${template.maxPositionValueUsd.toStringAsFixed(2)}',
                ),
                _detailRow(
                  'Maximum daily loss',
                  '${template.maxDailyLossPercent.toStringAsFixed(2)}%',
                ),
                _detailRow(
                  'Maximum drawdown',
                  '${template.maxDrawdownPercent.toStringAsFixed(2)}%',
                ),
                _detailRow(
                  'Paper trading',
                  template.paperTrading ? 'Enabled' : 'Disabled',
                ),
                _detailRow('Dry run', template.dryRun ? 'Enabled' : 'Disabled'),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
            if (canEdit)
              TextButton.icon(
                key: Key('template-${template.id}-delete-button'),
                onPressed: isBusy
                    ? null
                    : () async {
                        Navigator.of(context).pop();
                        await _confirmDelete(template);
                      },
                icon: const Icon(Icons.delete_outline),
                label: Text(isBusy ? 'Deleting...' : 'Delete'),
                style: TextButton.styleFrom(foregroundColor: AppColors.danger),
              ),
            if (canEdit)
              FilledButton.icon(
                key: Key('template-${template.id}-edit-button'),
                onPressed: isBusy
                    ? null
                    : () async {
                        Navigator.of(context).pop();
                        await _showEditDialog(template);
                      },
                icon: const Icon(Icons.edit_outlined),
                label: Text(isBusy ? 'Updating...' : 'Edit'),
              ),
          ],
        );
      },
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Color _statusColor(StrategyTemplateStatus status) {
    return switch (status) {
      StrategyTemplateStatus.draft => AppColors.warning,
      StrategyTemplateStatus.published => AppColors.success,
      StrategyTemplateStatus.archived => AppColors.textSecondary,
    };
  }

  Color _visibilityColor(StrategyTemplateVisibility visibility) {
    return switch (visibility) {
      StrategyTemplateVisibility.privateTemplate => AppColors.warning,
      StrategyTemplateVisibility.publicTemplate => AppColors.success,
    };
  }

  String _humanize(String value) {
    return value
        .toLowerCase()
        .split('_')
        .map(
          (part) => part.isEmpty
              ? part
              : '${part[0].toUpperCase()}'
                    '${part.substring(1)}',
        )
        .join(' ');
  }

  String _ownedEmptyTitle(_OwnedTemplateFilter filter) {
    return switch (filter) {
      _OwnedTemplateFilter.all => 'No strategy templates',
      _OwnedTemplateFilter.draft => 'No draft templates',
      _OwnedTemplateFilter.published => 'No published templates',
      _OwnedTemplateFilter.archived => 'No archived templates',
    };
  }

  String _ownedEmptyMessage(_OwnedTemplateFilter filter) {
    return switch (filter) {
      _OwnedTemplateFilter.all =>
        'Your authenticated strategy templates '
            'will appear here.',
      _OwnedTemplateFilter.draft =>
        'You do not currently have any draft templates.',
      _OwnedTemplateFilter.published =>
        'You do not currently have any published templates.',
      _OwnedTemplateFilter.archived =>
        'You do not currently have any archived templates.',
    };
  }
}
