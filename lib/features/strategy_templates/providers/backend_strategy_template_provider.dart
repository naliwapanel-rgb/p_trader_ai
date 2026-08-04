import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../../bots/data/backend_trading_bot.dart';
import '../data/backend_strategy_template.dart';
import '../data/strategy_template_remote_data_source.dart';
import '../data/strategy_template_repository_impl.dart';
import '../domain/strategy_template_repository.dart';
import 'backend_strategy_template_state.dart';

final backendStrategyTemplateRemoteDataSourceProvider =
    Provider<StrategyTemplateRemoteDataSource>((ref) {
      return DioStrategyTemplateRemoteDataSource(
        ref.watch(backendDioClientProvider).dio,
      );
    });

final backendStrategyTemplateRepositoryProvider =
    Provider<StrategyTemplateRepository>((ref) {
      return StrategyTemplateRepositoryImpl(
        ref.watch(backendStrategyTemplateRemoteDataSourceProvider),
      );
    });

final backendStrategyTemplateProvider =
    NotifierProvider<
      BackendStrategyTemplateNotifier,
      BackendStrategyTemplateState
    >(BackendStrategyTemplateNotifier.new);

class BackendStrategyTemplateNotifier
    extends Notifier<BackendStrategyTemplateState> {
  @override
  BackendStrategyTemplateState build() {
    return const BackendStrategyTemplateState.initial();
  }

  Future<void> loadOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
  }) async {
    if (state.isLoadingOwned) {
      return;
    }

    state = state.copyWith(
      isLoadingOwned: true,
      clearError: true,
      clearInfo: true,
    );

    try {
      final templates = await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .listOwned(status: status, visibility: visibility);

      state = state.copyWith(
        ownedTemplates: _sortedTemplates(templates),
        isLoadingOwned: false,
        hasLoadedOwned: true,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(
        isLoadingOwned: false,
        hasLoadedOwned: true,
        errorMessage: error.message,
      );
    } catch (_) {
      state = state.copyWith(
        isLoadingOwned: false,
        hasLoadedOwned: true,
        errorMessage: 'Strategy templates could not be loaded.',
      );
    }
  }

  Future<void> loadPublic() async {
    if (state.isLoadingPublic) {
      return;
    }

    state = state.copyWith(
      isLoadingPublic: true,
      clearError: true,
      clearInfo: true,
    );

    try {
      final templates = await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .listPublic();

      state = state.copyWith(
        publicTemplates: _sortedTemplates(templates),
        isLoadingPublic: false,
        hasLoadedPublic: true,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(
        isLoadingPublic: false,
        hasLoadedPublic: true,
        errorMessage: error.message,
      );
    } catch (_) {
      state = state.copyWith(
        isLoadingPublic: false,
        hasLoadedPublic: true,
        errorMessage: 'Public strategy templates could not be loaded.',
      );
    }
  }

  Future<BackendStrategyTemplate?> createTemplate(
    StrategyTemplateCreateRequest request,
  ) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final template = await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .createTemplate(request);

      state = state.copyWith(
        ownedTemplates: _upsertTemplate(state.ownedTemplates, template),
        publicTemplates: _syncPublicTemplate(state.publicTemplates, template),
        isMutating: false,
        hasLoadedOwned: true,
        infoMessage: 'Strategy template created successfully.',
        clearError: true,
      );

      return template;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);

      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The strategy template could not be created.',
      );

      return null;
    }
  }

  Future<BackendStrategyTemplate?> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  }) async {
    if (state.isTemplateBusy(templateId)) {
      return null;
    }

    _setTemplateBusy(templateId, true);

    try {
      final template = await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .updateTemplate(templateId: templateId, request: request);

      state = state.copyWith(
        ownedTemplates: _upsertTemplate(state.ownedTemplates, template),
        publicTemplates: _syncPublicTemplate(state.publicTemplates, template),
        busyTemplateIds: _withoutBusyTemplate(templateId),
        infoMessage: 'Strategy template updated successfully.',
        clearError: true,
      );

      return template;
    } on AppException catch (error) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: error.message,
      );

      return null;
    } catch (_) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: 'The strategy template could not be updated.',
      );

      return null;
    }
  }

  Future<bool> deleteTemplate(int templateId) async {
    if (state.isTemplateBusy(templateId)) {
      return false;
    }

    _setTemplateBusy(templateId, true);

    try {
      await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .deleteTemplate(templateId);

      state = state.copyWith(
        ownedTemplates: state.ownedTemplates
            .where((template) => template.id != templateId)
            .toList(growable: false),
        publicTemplates: state.publicTemplates
            .where((template) => template.id != templateId)
            .toList(growable: false),
        busyTemplateIds: _withoutBusyTemplate(templateId),
        infoMessage: 'Strategy template deleted successfully.',
        clearError: true,
      );

      return true;
    } on AppException catch (error) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: error.message,
      );

      return false;
    } catch (_) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: 'The strategy template could not be deleted.',
      );

      return false;
    }
  }

  Future<StrategyTemplateActionResult?> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  }) async {
    if (state.isTemplateBusy(templateId)) {
      return null;
    }

    _setTemplateBusy(templateId, true);

    try {
      final result = await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .performAction(templateId: templateId, action: action);

      state = state.copyWith(
        ownedTemplates: _upsertTemplate(state.ownedTemplates, result.template),
        publicTemplates: _syncPublicTemplate(
          state.publicTemplates,
          result.template,
        ),
        busyTemplateIds: _withoutBusyTemplate(templateId),
        infoMessage: result.changed
            ? _actionSuccessMessage(action)
            : 'The strategy template was already '
                  '${result.status.backendValue.toLowerCase()}.',
        clearError: true,
      );

      return result;
    } on AppException catch (error) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: error.message,
      );

      return null;
    } catch (_) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: 'The strategy-template action could not be completed.',
      );

      return null;
    }
  }

  Future<BackendTradingBot?> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  }) async {
    if (state.isTemplateBusy(templateId)) {
      return null;
    }

    _setTemplateBusy(templateId, true);

    try {
      final bot = await ref
          .read(backendStrategyTemplateRepositoryProvider)
          .createBotFromTemplate(templateId: templateId, request: request);

      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        infoMessage: 'Trading bot created from template successfully.',
        clearError: true,
      );

      return bot;
    } on AppException catch (error) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: error.message,
      );

      return null;
    } catch (_) {
      state = state.copyWith(
        busyTemplateIds: _withoutBusyTemplate(templateId),
        errorMessage: 'The trading bot could not be created from the template.',
      );

      return null;
    }
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearInfo: true);
  }

  void _setTemplateBusy(int templateId, bool busy) {
    final busyIds = Set<int>.from(state.busyTemplateIds);

    if (busy) {
      busyIds.add(templateId);
    } else {
      busyIds.remove(templateId);
    }

    state = state.copyWith(
      busyTemplateIds: Set<int>.unmodifiable(busyIds),
      clearError: true,
      clearInfo: true,
    );
  }

  Set<int> _withoutBusyTemplate(int templateId) {
    final busyIds = Set<int>.from(state.busyTemplateIds)..remove(templateId);

    return Set<int>.unmodifiable(busyIds);
  }

  List<BackendStrategyTemplate> _upsertTemplate(
    Iterable<BackendStrategyTemplate> templates,
    BackendStrategyTemplate replacement,
  ) {
    final withoutReplacement = templates
        .where((template) => template.id != replacement.id)
        .toList(growable: false);

    return _sortedTemplates(<BackendStrategyTemplate>[
      ...withoutReplacement,
      replacement,
    ]);
  }

  List<BackendStrategyTemplate> _syncPublicTemplate(
    Iterable<BackendStrategyTemplate> templates,
    BackendStrategyTemplate replacement,
  ) {
    final withoutReplacement = templates
        .where((template) => template.id != replacement.id)
        .toList(growable: false);

    final isPublicAndPublished =
        replacement.visibility == StrategyTemplateVisibility.publicTemplate &&
        replacement.status == StrategyTemplateStatus.published;

    if (!isPublicAndPublished) {
      return List<BackendStrategyTemplate>.unmodifiable(withoutReplacement);
    }

    return _sortedTemplates(<BackendStrategyTemplate>[
      ...withoutReplacement,
      replacement,
    ]);
  }

  List<BackendStrategyTemplate> _sortedTemplates(
    Iterable<BackendStrategyTemplate> templates,
  ) {
    final sorted = templates.toList();

    sorted.sort((first, second) => second.createdAt.compareTo(first.createdAt));

    return List<BackendStrategyTemplate>.unmodifiable(sorted);
  }

  String _actionSuccessMessage(StrategyTemplateAction action) {
    return switch (action) {
      StrategyTemplateAction.publish =>
        'Strategy template published successfully.',
      StrategyTemplateAction.unpublish =>
        'Strategy template unpublished successfully.',
      StrategyTemplateAction.archive =>
        'Strategy template archived successfully.',
      StrategyTemplateAction.restore =>
        'Strategy template restored successfully.',
    };
  }
}
