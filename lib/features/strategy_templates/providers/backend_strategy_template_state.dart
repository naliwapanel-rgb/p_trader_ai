import '../data/backend_strategy_template.dart';

class BackendStrategyTemplateState {
  const BackendStrategyTemplateState({
    required this.ownedTemplates,
    required this.publicTemplates,
    required this.busyTemplateIds,
    required this.isLoadingOwned,
    required this.isLoadingPublic,
    required this.isMutating,
    required this.hasLoadedOwned,
    required this.hasLoadedPublic,
    this.errorMessage,
    this.infoMessage,
  });

  const BackendStrategyTemplateState.initial()
    : ownedTemplates = const <BackendStrategyTemplate>[],
      publicTemplates = const <BackendStrategyTemplate>[],
      busyTemplateIds = const <int>{},
      isLoadingOwned = false,
      isLoadingPublic = false,
      isMutating = false,
      hasLoadedOwned = false,
      hasLoadedPublic = false,
      errorMessage = null,
      infoMessage = null;

  final List<BackendStrategyTemplate> ownedTemplates;
  final List<BackendStrategyTemplate> publicTemplates;
  final Set<int> busyTemplateIds;

  final bool isLoadingOwned;
  final bool isLoadingPublic;
  final bool isMutating;
  final bool hasLoadedOwned;
  final bool hasLoadedPublic;

  final String? errorMessage;
  final String? infoMessage;

  bool get isLoading {
    return isLoadingOwned || isLoadingPublic;
  }

  List<BackendStrategyTemplate> get draftTemplates {
    return ownedTemplates
        .where((template) => template.status == StrategyTemplateStatus.draft)
        .toList(growable: false);
  }

  List<BackendStrategyTemplate> get publishedTemplates {
    return ownedTemplates
        .where(
          (template) => template.status == StrategyTemplateStatus.published,
        )
        .toList(growable: false);
  }

  List<BackendStrategyTemplate> get archivedTemplates {
    return ownedTemplates
        .where((template) => template.status == StrategyTemplateStatus.archived)
        .toList(growable: false);
  }

  BackendStrategyTemplate? findOwnedById(int templateId) {
    for (final template in ownedTemplates) {
      if (template.id == templateId) {
        return template;
      }
    }

    return null;
  }

  BackendStrategyTemplate? findPublicById(int templateId) {
    for (final template in publicTemplates) {
      if (template.id == templateId) {
        return template;
      }
    }

    return null;
  }

  bool isTemplateBusy(int templateId) {
    return busyTemplateIds.contains(templateId);
  }

  BackendStrategyTemplateState copyWith({
    List<BackendStrategyTemplate>? ownedTemplates,
    List<BackendStrategyTemplate>? publicTemplates,
    Set<int>? busyTemplateIds,
    bool? isLoadingOwned,
    bool? isLoadingPublic,
    bool? isMutating,
    bool? hasLoadedOwned,
    bool? hasLoadedPublic,
    String? errorMessage,
    String? infoMessage,
    bool clearError = false,
    bool clearInfo = false,
  }) {
    return BackendStrategyTemplateState(
      ownedTemplates: ownedTemplates ?? this.ownedTemplates,
      publicTemplates: publicTemplates ?? this.publicTemplates,
      busyTemplateIds: busyTemplateIds ?? this.busyTemplateIds,
      isLoadingOwned: isLoadingOwned ?? this.isLoadingOwned,
      isLoadingPublic: isLoadingPublic ?? this.isLoadingPublic,
      isMutating: isMutating ?? this.isMutating,
      hasLoadedOwned: hasLoadedOwned ?? this.hasLoadedOwned,
      hasLoadedPublic: hasLoadedPublic ?? this.hasLoadedPublic,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearInfo ? null : infoMessage ?? this.infoMessage,
    );
  }
}
