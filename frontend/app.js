/**
 * TestForge — Autonomous Agentic Test Hardening
 * Frontend Application Controller (Vanilla ES6+ JavaScript)
 * Authors: Sourabh & Shreshth
 */

document.addEventListener('DOMContentLoaded', () => {
  // =========================================================================
  // Application State
  // =========================================================================
  const state = {
    activeTarget: {
      mode: 'Mode A',
      filePath: 'samples/discount.py',
      moduleName: 'samples.discount',
      sourceCode: '',
      sourceSha: '',
      functions: [],
      classes: [],
      methods: [],
      allCallables: [],
      lineCount: 0,
      dependencies: [],
      metadata: null,
    },
    gitDiff: {
      enabled: false,
      modifiedLines: [],
    },
    blastRadius: {
      definedFunctions: [],
      selectedTarget: null,
      impact: null,
      graphData: null,
    },
    hardening: {
      jobId: null,
      pollTimer: null,
      status: 'IDLE',
      progress: 0,
      finalState: null,
      mutants: [],
      selectedMutant: null,
      filter: 'ALL',
      testHardenedCode: '',
    },
    settings: {
      engineMode: 'auto',
      modelName: 'gemini-3.6-flash',
      maxIterations: 3,
      targetMutationScore: 85,
      geminiApiKey: '',
      openrouterApiKey: '',
    },
    checkpoints: {
      items: [],
      totalCount: 0,
      selectedId: null,
      diffBaseId: null,
      diffTargetId: null,
      currentDiff: null,
      loading: false,
      restoringId: null,
    },
    a2a: {
      card: null,
      rawJson: '',
      loading: false,
      error: null,
    },
    mcp: {
      status: null,
      rawJson: '',
      loading: false,
      error: null,
    },
    ws: {
      socket: null,
      isConnected: false,
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimer: null,
      pollingInterval: null,
      seenEventIds: new Set(),
      streamingEvents: [],
    },
  };
  window.__testforge_state = state;

  // =========================================================================
  // DOM Elements Cache
  // =========================================================================
  const dom = {
    toastContainer: document.getElementById('toast-container'),

    // Status Pills
    pillHardware: document.getElementById('pill-hardware'),
    labelHardware: document.getElementById('label-hardware'),
    dotOllama: document.getElementById('dot-ollama'),
    labelOllama: document.getElementById('label-ollama'),
    dotGemini: document.getElementById('dot-gemini'),
    labelGemini: document.getElementById('label-gemini'),
    dotOpenrouter: document.getElementById('dot-openrouter'),
    labelOpenrouter: document.getElementById('label-openrouter'),

    // A2A Card Modal
    btnA2aCard: document.getElementById('btn-a2a-card'),
    a2aModalBackdrop: document.getElementById('a2a-modal-backdrop'),
    btnCloseA2aModal: document.getElementById('btn-close-a2a-modal'),
    btnCloseA2aFooter: document.getElementById('btn-close-a2a-footer'),
    btnViewRawA2a: document.getElementById('btn-view-raw-a2a'),
    btnCopyA2aJson: document.getElementById('btn-copy-a2a-json'),
    a2aLoadingState: document.getElementById('a2a-loading-state'),
    a2aErrorState: document.getElementById('a2a-error-state'),
    a2aErrorMessage: document.getElementById('a2a-error-message'),
    a2aEmptyState: document.getElementById('a2a-empty-state'),
    a2aCardContent: document.getElementById('a2a-card-content'),

    // MCP Tools Modal
    btnMcpStatus: document.getElementById('btn-mcp-status'),
    mcpToolCount: document.getElementById('mcp-tool-count'),
    mcpModalBackdrop: document.getElementById('mcp-modal-backdrop'),
    btnCloseMcpModal: document.getElementById('btn-close-mcp-modal'),
    btnCloseMcpFooter: document.getElementById('btn-close-mcp-footer'),
    btnViewRawMcp: document.getElementById('btn-view-raw-mcp'),
    btnCopyMcpJson: document.getElementById('btn-copy-mcp-json'),
    mcpLoadingState: document.getElementById('mcp-loading-state'),
    mcpErrorState: document.getElementById('mcp-error-state'),
    mcpErrorMessage: document.getElementById('mcp-error-message'),
    mcpCardContent: document.getElementById('mcp-card-content'),

    // Settings Modal
    btnToggleSettings: document.getElementById('btn-toggle-settings'),
    btnCloseSettings: document.getElementById('btn-close-settings'),
    btnCancelSettings: document.getElementById('btn-cancel-settings'),
    btnSaveSettings: document.getElementById('btn-save-settings'),
    settingsBackdrop: document.getElementById('settings-modal-backdrop'),
    selectEngineMode: document.getElementById('engine-mode-select'),
    selectModelName: document.getElementById('model-name-select'),
    sliderIterations: document.getElementById('slider-iterations'),
    valIterations: document.getElementById('val-iterations'),
    sliderMutationScore: document.getElementById('slider-mutation-score'),
    valMutationScore: document.getElementById('val-mutation-score'),
    inputGeminiKey: document.getElementById('input-gemini-key'),
    inputOpenrouterKey: document.getElementById('input-openrouter-key'),

    // Target Hero Card
    targetModeBadge: document.getElementById('target-mode-badge'),
    targetModuleTitle: document.getElementById('target-module-title'),
    tagFilePath: document.getElementById('tag-file-path'),
    tagSha: document.getElementById('tag-sha'),
    tagFuncs: document.getElementById('tag-funcs'),
    tagClasses: document.getElementById('tag-classes'),
    tagLines: document.getElementById('tag-lines'),
    btnScrollToHardening: document.getElementById('btn-scroll-to-hardening'),

    // Tabs
    tabNav: document.getElementById('main-tab-nav'),
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),

    // Mode A Elements
    radioSourceSample: document.getElementById('radio-source-sample'),
    radioSourceUpload: document.getElementById('radio-source-upload'),
    groupSampleSelect: document.getElementById('group-sample-select'),
    groupFileUpload: document.getElementById('group-file-upload'),
    sampleFileSelect: document.getElementById('sample-file-select'),
    btnLoadSample: document.getElementById('btn-load-sample'),
    fileDropzone: document.getElementById('file-dropzone'),
    fileUploadInput: document.getElementById('file-upload-input'),
    uploadFilenamePreview: document.getElementById('upload-filename-preview'),
    btnSubmitUpload: document.getElementById('btn-submit-upload'),
    toggleGitDiff: document.getElementById('toggle-git-diff'),
    gitDiffAlert: document.getElementById('git-diff-alert'),
    modeAModuleName: document.getElementById('mode-a-module-name'),
    modeAFuncsList: document.getElementById('mode-a-funcs-list'),
    modeAClassesList: document.getElementById('mode-a-classes-list'),
    modeACodeDisplay: document.getElementById('mode-a-code-display'),
    btnCopyModeACode: document.getElementById('btn-copy-mode-a-code'),

    // Mode B Elements
    synthPromptInput: document.getElementById('synth-prompt-input'),
    btnSynthesizeModule: document.getElementById('btn-synthesize-module'),
    synthStatusBox: document.getElementById('synth-status-box'),
    synthCodeContainer: document.getElementById('synth-code-container'),
    synthCodeDisplay: document.getElementById('synth-code-display'),
    synthFileTitle: document.getElementById('synth-file-title'),
    btnCopySynthCode: document.getElementById('btn-copy-synth-code'),

    // Mode C Elements
    githubUrlInput: document.getElementById('github-url-input'),
    btnFetchGithub: document.getElementById('btn-fetch-github'),
    urlValidationBadge: document.getElementById('url-validation-badge'),
    urlValidationText: document.getElementById('url-validation-text'),
    modeCEmptyState: document.getElementById('mode-c-empty-state'),
    modeCDetails: document.getElementById('mode-c-details'),
    mcRepo: document.getElementById('mc-repo'),
    mcBranch: document.getElementById('mc-branch'),
    mcPath: document.getElementById('mc-path'),
    mcModule: document.getElementById('mc-module'),
    mcSha: document.getElementById('mc-sha'),
    mcLines: document.getElementById('mc-lines'),
    mcClassesCnt: document.getElementById('mc-classes-cnt'),
    mcCallablesCnt: document.getElementById('mc-callables-cnt'),
    mcClassChips: document.getElementById('mc-class-chips'),
    modeCCodeDisplay: document.getElementById('mode-c-code-display'),
    btnCopyModeCCode: document.getElementById('btn-copy-mode-c-code'),
    btnActivateModeC: document.getElementById('btn-activate-mode-c'),

    // Blast Radius Elements
    blastFuncSelect: document.getElementById('blast-func-select'),
    blastRiskBadge: document.getElementById('blast-risk-badge'),
    blastAffectedCount: document.getElementById('blast-affected-count'),
    blastImpactRatio: document.getElementById('blast-impact-ratio'),
    blastCalleesCount: document.getElementById('blast-callees-count'),
    blastTreeDisplay: document.getElementById('blast-tree-display'),
    callGraphCanvas: document.getElementById('call-graph-canvas'),

    // Hardening Lab Elements
    hardenTargetLbl: document.getElementById('harden-target-lbl'),
    hardenModelLbl: document.getElementById('harden-model-lbl'),
    hardenIterLbl: document.getElementById('harden-iter-lbl'),
    hardenScoreLbl: document.getElementById('harden-score-lbl'),
    btnRunHardening: document.getElementById('btn-run-hardening'),
    btnCancelHardening: document.getElementById('btn-cancel-hardening'),
    hardeningProgressBox: document.getElementById('hardening-progress-box'),
    hardeningStatusText: document.getElementById('hardening-status-text'),
    hardeningPercentText: document.getElementById('hardening-percent-text'),
    hardeningProgressBar: document.getElementById('hardening-progress-bar'),
    hardeningVerdictBanner: document.getElementById('hardening-verdict-banner'),

    // KPIs Row 1
    kpiBaseGen: document.getElementById('kpi-base-gen'),
    kpiBaseExec: document.getElementById('kpi-base-exec'),
    kpiBasePass: document.getElementById('kpi-base-pass'),
    kpiBaseFail: document.getElementById('kpi-base-fail'),
    kpiBaseVerdict: document.getElementById('kpi-base-verdict'),

    // KPIs Row 2
    kpiLinesCov: document.getElementById('kpi-lines-cov'),
    kpiCovPct: document.getElementById('kpi-cov-pct'),
    kpiMutGen: document.getElementById('kpi-mut-gen'),
    kpiMutExec: document.getElementById('kpi-mut-exec'),
    kpiMutKill: document.getElementById('kpi-mut-kill'),
    kpiMutSurv: document.getElementById('kpi-mut-surv'),
    kpiMutErr: document.getElementById('kpi-mut-err'),

    // KPIs Row 3
    kpiMutScore: document.getElementById('kpi-mut-score'),
    kpiCyclesDone: document.getElementById('kpi-cycles-done'),
    kpiFinalStatus: document.getElementById('kpi-final-status'),

    // History Table
    historyTableBody: document.getElementById('history-table-body'),

    // Mutant Audit & Diff
    cntAllMut: document.getElementById('cnt-all-mut'),
    cntKillMut: document.getElementById('cnt-kill-mut'),
    cntSurvMut: document.getElementById('cnt-surv-mut'),
    cntEquivMut: document.getElementById('cnt-equiv-mut'),
    mutantsTableBody: document.getElementById('mutants-table-body'),
    diffSelectedMutantTitle: document.getElementById('diff-selected-mutant-title'),
    diffStatusBadge: document.getElementById('diff-status-badge'),
    diffCodeDisplay: document.getElementById('diff-code-display'),

    // Hardened Suite Export
    hardenedSuiteCode: document.getElementById('hardened-suite-code'),
    btnCopyHardenedSuite: document.getElementById('btn-copy-hardened-suite'),
    btnDownloadHardenedSuite: document.getElementById('btn-download-hardened-suite'),

    // Wiretap Elements
    btnRefreshWiretap: document.getElementById('btn-refresh-wiretap'),
    wiretapWsStatusBadge: document.getElementById('wiretap-ws-status-badge'),
    wiretapKpiHandoffs: document.getElementById('wiretap-kpi-handoffs'),
    wiretapKpiAgents: document.getElementById('wiretap-kpi-agents'),
    wiretapKpiAdk: document.getElementById('wiretap-kpi-adk'),
    wiretapKpiLoops: document.getElementById('wiretap-kpi-loops'),
    wiretapTimelineContainer: document.getElementById('wiretap-timeline-container'),

    // Telemetry Elements
    btnRefreshTelemetry: document.getElementById('btn-refresh-telemetry'),
    telemKpiEvents: document.getElementById('telem-kpi-events'),
    telemKpiTokens: document.getElementById('telem-kpi-tokens'),
    telemetryTableBody: document.getElementById('telemetry-table-body'),

    // Benchmark Elements
    btnRunBenchmark: document.getElementById('btn-run-benchmark'),
    btnRefreshBenchmark: document.getElementById('btn-refresh-benchmark'),
    benchTargetSelect: document.getElementById('bench-target-select'),
    benchRepetitions: document.getElementById('bench-repetitions'),
    benchScBaseline: document.getElementById('bench-sc-baseline'),
    benchScZeroshot: document.getElementById('bench-sc-zeroshot'),
    benchScRefl: document.getElementById('bench-sc-refl'),
    benchStatusAlert: document.getElementById('benchmark-status-alert'),
    benchmarkSummaryTableBody: document.getElementById('benchmark-summary-table-body'),
    benchMeasuredDetails: document.getElementById('bench-measured-details'),
    benchCalculatedDetails: document.getElementById('bench-calculated-details'),
    benchEstimatedDetails: document.getElementById('bench-estimated-details'),
    benchMarkdownPreview: document.getElementById('bench-markdown-preview'),
    btnBenchMdRendered: document.getElementById('btn-bench-md-rendered'),
    btnBenchMdRaw: document.getElementById('btn-bench-md-raw'),
    benchRenderedMarkdownView: document.getElementById('bench-rendered-markdown-view'),
    benchRawMarkdownContainer: document.getElementById('bench-raw-markdown-container'),

    // Checkpoint Timeline & Diff Elements
    btnRefreshCheckpoints: document.getElementById('btn-refresh-checkpoints'),
    btnTriggerDiffModal: document.getElementById('btn-trigger-diff-modal'),
    cpStageFilter: document.getElementById('cp-stage-filter'),
    cpStatusFilter: document.getElementById('cp-status-filter'),
    cpJobFilter: document.getElementById('cp-job-filter'),
    cpSortOrder: document.getElementById('cp-sort-order'),
    labelDiffBase: document.getElementById('label-diff-base'),
    labelDiffTarget: document.getElementById('label-diff-target'),
    btnSwapDiffSelection: document.getElementById('btn-swap-diff-selection'),
    btnClearDiffSelection: document.getElementById('btn-clear-diff-selection'),
    checkpointsErrorAlert: document.getElementById('checkpoints-error-alert'),
    checkpointsRestoreAlert: document.getElementById('checkpoints-restore-alert'),
    cpCountBadge: document.getElementById('cp-count-badge'),
    cpPaginationInfo: document.getElementById('cp-pagination-info'),
    checkpointsLoadingState: document.getElementById('checkpoints-loading-state'),
    checkpointsEmptyState: document.getElementById('checkpoints-empty-state'),
    checkpointCardsStream: document.getElementById('checkpoint-cards-stream'),
    btnSubtabDetail: document.getElementById('btn-subtab-detail'),
    btnSubtabDiff: document.getElementById('btn-subtab-diff'),
    btnSubtabJson: document.getElementById('btn-subtab-json'),
    viewCpDetail: document.getElementById('view-cp-detail'),
    viewCpDiff: document.getElementById('view-cp-diff'),
    viewCpJson: document.getElementById('view-cp-json'),
    cpDetailEmptyPlaceholder: document.getElementById('cp-detail-empty-placeholder'),
    cpDetailContent: document.getElementById('cp-detail-content'),
    cpDiffEmptyPlaceholder: document.getElementById('cp-diff-empty-placeholder'),
    cpDiffContent: document.getElementById('cp-diff-content'),
    rawJsonTitle: document.getElementById('raw-json-title'),
    btnCopyCheckpointJson: document.getElementById('btn-copy-checkpoint-json'),
    checkpointRawJsonDisplay: document.getElementById('checkpoint-raw-json-display'),

    // Restore Modal
    restoreModalBackdrop: document.getElementById('restore-modal-backdrop'),
    btnCloseRestoreModal: document.getElementById('btn-close-restore-modal'),
    btnCancelRestore: document.getElementById('btn-cancel-restore'),
    btnConfirmRestore: document.getElementById('btn-confirm-restore'),
    restoreTargetId: document.getElementById('restore-target-id'),
    restoreTargetStage: document.getElementById('restore-target-stage'),
    restoreTargetRev: document.getElementById('restore-target-rev'),
    restoreTargetTime: document.getElementById('restore-target-time'),
  };

  // =========================================================================
  // Toast Notification System
  // =========================================================================
  function showToast(message, type = 'info', duration = 3500) {
    if (!dom.toastContainer) return;

    // Dismiss conflicting success toasts when an error or warning arrives (TF-DEF-003 fix)
    if (type === 'error' || type === 'warning') {
      const existingSuccess = dom.toastContainer.querySelectorAll('.toast-success');
      existingSuccess.forEach(t => t.remove());
    }

    // Limit concurrent toasts to 2 to prevent stacking collisions
    while (dom.toastContainer.children.length >= 2) {
      dom.toastContainer.removeChild(dom.toastContainer.firstChild);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '⚡';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-message">${escapeHtml(message)}</span>
    `;

    dom.toastContainer.appendChild(toast);

    // Auto dismiss
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, duration);
  }

  function copyTextToClipboard(text, btnElement, defaultLabel = '📋 Copy') {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      showToast('Copied to clipboard!', 'success');
      if (btnElement) {
        const originalHtml = btnElement.innerHTML;
        btnElement.innerHTML = '✅ Copied!';
        btnElement.style.borderColor = 'var(--emerald)';
        btnElement.style.color = '#fff';
        setTimeout(() => {
          btnElement.innerHTML = originalHtml || defaultLabel;
          btnElement.style.borderColor = '';
          btnElement.style.color = '';
        }, 1800);
      }
    }).catch(err => {
      showToast('Failed to copy', 'error');
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // =========================================================================
  // Tab Navigation Handling
  // =========================================================================
  function switchTab(tabId) {
    dom.tabButtons.forEach(btn => {
      const isTarget = btn.getAttribute('data-tab') === tabId;
      btn.classList.toggle('active', isTarget);
      btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });

    dom.tabPanes.forEach(pane => {
      const isTarget = pane.id === tabId;
      pane.classList.toggle('active', isTarget);
    });

    // Lazy load tab contents when switched
    if (tabId === 'tab-blast') {
      triggerBlastRadiusAnalysis();
    } else if (tabId === 'tab-wiretap') {
      fetchWiretap();
    } else if (tabId === 'tab-telemetry') {
      fetchTelemetry();
    } else if (tabId === 'tab-benchmark') {
      fetchBenchmarkResults();
    } else if (tabId === 'tab-checkpoints') {
      fetchCheckpoints();
    }
  }

  dom.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  if (dom.btnScrollToHardening) {
    dom.btnScrollToHardening.addEventListener('click', () => {
      switchTab('tab-hardening');
      const hardenPane = document.getElementById('tab-hardening');
      if (hardenPane) {
        hardenPane.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  // =========================================================================
  // Settings Modal Controls
  // =========================================================================
  function openSettings() {
    dom.settingsBackdrop.classList.remove('hidden');
    dom.selectEngineMode.value = state.settings.engineMode;
    dom.selectModelName.value = state.settings.modelName;
    dom.sliderIterations.value = state.settings.maxIterations;
    dom.valIterations.textContent = state.settings.maxIterations;
    dom.sliderMutationScore.value = state.settings.targetMutationScore;
    dom.valMutationScore.textContent = `${state.settings.targetMutationScore}%`;
  }

  function closeSettings() {
    dom.settingsBackdrop.classList.add('hidden');
  }

  if (dom.btnToggleSettings) dom.btnToggleSettings.addEventListener('click', openSettings);
  if (dom.btnCloseSettings) dom.btnCloseSettings.addEventListener('click', closeSettings);
  if (dom.btnCancelSettings) dom.btnCancelSettings.addEventListener('click', closeSettings);

  dom.settingsBackdrop.addEventListener('click', (e) => {
    if (e.target === dom.settingsBackdrop) closeSettings();
  });

  // =========================================================================
  // A2A Agent Card Discovery Modal Controls
  // =========================================================================
  async function openA2aModal() {
    if (!dom.a2aModalBackdrop) return;
    dom.a2aModalBackdrop.classList.remove('hidden');
    await fetchAndRenderA2aCard();
  }

  function closeA2aModal() {
    if (!dom.a2aModalBackdrop) return;
    dom.a2aModalBackdrop.classList.add('hidden');
  }

  async function fetchAndRenderA2aCard() {
    if (dom.a2aLoadingState) dom.a2aLoadingState.classList.remove('hidden');
    if (dom.a2aErrorState) dom.a2aErrorState.classList.add('hidden');
    if (dom.a2aEmptyState) dom.a2aEmptyState.classList.add('hidden');
    if (dom.a2aCardContent) {
      dom.a2aCardContent.classList.add('hidden');
      dom.a2aCardContent.replaceChildren();
    }

    try {
      const resp = await fetch('/.well-known/agent-card.json', { cache: 'no-store' });
      if (!resp.ok) {
        throw new Error(`Endpoint returned HTTP ${resp.status} (${resp.statusText})`);
      }
      const data = await resp.json();
      state.a2a.card = data;
      state.a2a.rawJson = JSON.stringify(data, null, 2);

      if (!data || Object.keys(data).length === 0) {
        if (dom.a2aEmptyState) dom.a2aEmptyState.classList.remove('hidden');
      } else {
        renderA2aCard(data);
        if (dom.a2aCardContent) dom.a2aCardContent.classList.remove('hidden');
      }
    } catch (err) {
      state.a2a.error = err.message;
      if (dom.a2aErrorMessage) dom.a2aErrorMessage.textContent = `Failed to load A2A AgentCard: ${err.message}`;
      if (dom.a2aErrorState) dom.a2aErrorState.classList.remove('hidden');
    } finally {
      if (dom.a2aLoadingState) dom.a2aLoadingState.classList.add('hidden');
    }
  }

  function renderA2aCard(card) {
    if (!dom.a2aCardContent) return;
    dom.a2aCardContent.replaceChildren();

    // 1. Header Hero Card with Name, Protocol Version, and Agent Version
    const heroBox = document.createElement('div');
    heroBox.style.cssText = 'background: rgba(15, 23, 42, 0.6); padding: 1rem 1.25rem; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;';

    const heroLeft = document.createElement('div');
    const nameEl = document.createElement('h3');
    nameEl.style.cssText = 'margin: 0 0 0.25rem 0; font-size: 1.15rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 0.5rem;';
    nameEl.textContent = card.name || 'TestForge Agent';

    const descEl = document.createElement('p');
    descEl.style.cssText = 'margin: 0; font-size: 0.85rem; color: #cbd5e1; line-height: 1.4;';
    descEl.textContent = card.description || 'Autonomous Agentic Test Hardening System';

    heroLeft.appendChild(nameEl);
    heroLeft.appendChild(descEl);

    const heroRight = document.createElement('div');
    heroRight.style.cssText = 'display: flex; gap: 0.5rem; flex-wrap: wrap;';

    const protoBadge = document.createElement('span');
    protoBadge.className = 'badge';
    protoBadge.style.cssText = 'background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid #6366f1;';
    protoBadge.textContent = `A2A v${card.protocolVersion || card.protocol_version || '0.3.0'}`;

    const verBadge = document.createElement('span');
    verBadge.className = 'badge';
    verBadge.style.cssText = 'background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981;';
    verBadge.textContent = `Agent v${card.version || '1.0.0'}`;

    heroRight.appendChild(protoBadge);
    heroRight.appendChild(verBadge);

    heroBox.appendChild(heroLeft);
    heroBox.appendChild(heroRight);
    dom.a2aCardContent.appendChild(heroBox);

    // 2. Metadata Key-Value Grid
    const grid = document.createElement('div');
    grid.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem;';

    const metaFields = [
      { label: 'Endpoint URL', val: card.url || '-' },
      { label: 'Preferred Transport', val: card.preferredTransport || card.preferred_transport || 'JSONRPC' },
      { label: 'Provider Organization', val: card.provider?.organization || 'TestForge Systems' },
      { label: 'Streaming', val: card.capabilities?.streaming ? 'Enabled' : 'Disabled (Batch RPC)' },
      { label: 'Push Notifications', val: card.capabilities?.pushNotifications ? 'Enabled' : 'Disabled' },
      { label: 'Input / Output Modes', val: `${(card.defaultInputModes || ['text', 'json']).join(', ')} → ${(card.defaultOutputModes || ['text', 'json']).join(', ')}` },
    ];

    metaFields.forEach(f => {
      const cardEl = document.createElement('div');
      cardEl.style.cssText = 'background: rgba(0, 0, 0, 0.35); padding: 0.6rem 0.8rem; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.06);';
      const lbl = document.createElement('span');
      lbl.style.cssText = 'color: #94a3b8; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; display: block; margin-bottom: 0.2rem;';
      lbl.textContent = f.label;
      const val = document.createElement('strong');
      val.style.cssText = 'color: #f1f5f9; font-size: 0.85rem; word-break: break-all;';
      val.textContent = f.val;
      cardEl.appendChild(lbl);
      cardEl.appendChild(val);
      grid.appendChild(cardEl);
    });
    dom.a2aCardContent.appendChild(grid);

    // 3. Declared Agent Skills
    const skillsHeading = document.createElement('h4');
    skillsHeading.style.cssText = 'font-size: 0.95rem; font-weight: 600; color: #f1f5f9; margin: 0 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;';
    const skills = Array.isArray(card.skills) ? card.skills : [];
    skillsHeading.textContent = `Declared Skills & Capabilities (${skills.length})`;
    dom.a2aCardContent.appendChild(skillsHeading);

    const skillsContainer = document.createElement('div');
    skillsContainer.style.cssText = 'display: flex; flex-direction: column; gap: 0.75rem;';

    if (skills.length === 0) {
      const noSkills = document.createElement('p');
      noSkills.style.cssText = 'font-size: 0.85rem; color: #94a3b8; margin: 0;';
      noSkills.textContent = 'No skills declared on this agent card.';
      skillsContainer.appendChild(noSkills);
    } else {
      skills.forEach(skill => {
        const skillCard = document.createElement('div');
        skillCard.style.cssText = 'background: rgba(15, 23, 42, 0.5); padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.06);';

        const titleRow = document.createElement('div');
        titleRow.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;';

        const sTitle = document.createElement('strong');
        sTitle.style.cssText = 'color: #38bdf8; font-size: 0.9rem;';
        sTitle.textContent = skill.name || skill.id;

        const sId = document.createElement('code');
        sId.style.cssText = 'font-size: 0.72rem; color: #94a3b8; background: rgba(0,0,0,0.4); padding: 2px 6px; border-radius: 4px;';
        sId.textContent = skill.id;

        titleRow.appendChild(sTitle);
        titleRow.appendChild(sId);
        skillCard.appendChild(titleRow);

        const sDesc = document.createElement('p');
        sDesc.style.cssText = 'margin: 0 0 0.5rem 0; font-size: 0.82rem; color: #cbd5e1; line-height: 1.35;';
        sDesc.textContent = skill.description || 'No description provided.';
        skillCard.appendChild(sDesc);

        const tags = Array.isArray(skill.tags) ? skill.tags : [];
        if (tags.length > 0) {
          const tagsRow = document.createElement('div');
          tagsRow.style.cssText = 'display: flex; gap: 0.35rem; flex-wrap: wrap;';
          tags.forEach(t => {
            const tagChip = document.createElement('span');
            tagChip.style.cssText = 'font-size: 0.7rem; background: rgba(255,255,255,0.06); color: #94a3b8; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.08);';
            tagChip.textContent = `#${t}`;
            tagsRow.appendChild(tagChip);
          });
          skillCard.appendChild(tagsRow);
        }

        skillsContainer.appendChild(skillCard);
      });
    }
    dom.a2aCardContent.appendChild(skillsContainer);
  }

  async function copyA2aJson() {
    if (!state.a2a.rawJson) {
      showToast('No A2A card data available to copy', 'warning');
      return;
    }
    let copied = false;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(state.a2a.rawJson);
        copied = true;
      } catch (e) {
        copied = false;
      }
    }
    if (!copied) {
      try {
        const ta = document.createElement('textarea');
        ta.value = state.a2a.rawJson;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        copied = document.execCommand('copy');
        document.body.removeChild(ta);
      } catch (e) {
        copied = false;
      }
    }
    if (dom.btnCopyA2aJson) {
      const originalHtml = dom.btnCopyA2aJson.innerHTML;
      dom.btnCopyA2aJson.innerHTML = '✅ Copied!';
      setTimeout(() => {
        dom.btnCopyA2aJson.innerHTML = originalHtml;
      }, 1800);
    }
    showToast('A2A AgentCard JSON copied to clipboard!', 'success');
  }

  // =========================================================================
  // MCP (Model Context Protocol) Tools Status Controls
  // =========================================================================
  async function openMcpModal() {
    if (!dom.mcpModalBackdrop) return;
    dom.mcpModalBackdrop.classList.remove('hidden');
    await fetchAndRenderMcpStatus();
  }

  function closeMcpModal() {
    if (!dom.mcpModalBackdrop) return;
    dom.mcpModalBackdrop.classList.add('hidden');
  }

  async function fetchAndRenderMcpStatus(backgroundOnly = false) {
    if (!backgroundOnly) {
      if (dom.mcpLoadingState) dom.mcpLoadingState.classList.remove('hidden');
      if (dom.mcpErrorState) dom.mcpErrorState.classList.add('hidden');
      if (dom.mcpCardContent) {
        dom.mcpCardContent.classList.add('hidden');
        dom.mcpCardContent.replaceChildren();
      }
    }

    try {
      const resp = await fetch('/api/mcp/status', { cache: 'no-store' });
      if (!resp.ok) {
        throw new Error(`Endpoint returned HTTP ${resp.status} (${resp.statusText})`);
      }
      const data = await resp.json();
      state.mcp.status = data;
      state.mcp.rawJson = JSON.stringify(data, null, 2);

      if (dom.mcpToolCount && typeof data.total_tools_registered === 'number') {
        dom.mcpToolCount.textContent = data.total_tools_registered;
      }

      if (!backgroundOnly) {
        renderMcpStatus(data);
        if (dom.mcpCardContent) dom.mcpCardContent.classList.remove('hidden');
      }
    } catch (err) {
      state.mcp.error = err.message;
      if (!backgroundOnly) {
        if (dom.mcpErrorMessage) dom.mcpErrorMessage.textContent = `Failed to load MCP status: ${err.message}`;
        if (dom.mcpErrorState) dom.mcpErrorState.classList.remove('hidden');
      }
    } finally {
      if (!backgroundOnly && dom.mcpLoadingState) {
        dom.mcpLoadingState.classList.add('hidden');
      }
    }
  }

  function renderMcpStatus(data) {
    if (!dom.mcpCardContent) return;
    dom.mcpCardContent.replaceChildren();

    const root = document.createElement('div');
    root.style.display = 'flex';
    root.style.flexDirection = 'column';
    root.style.gap = '1rem';

    // Summary header
    const summaryCard = document.createElement('div');
    summaryCard.className = 'glass-card';
    summaryCard.style.padding = '0.75rem 1rem';
    summaryCard.style.background = 'rgba(15, 23, 42, 0.6)';
    summaryCard.style.borderRadius = '8px';
    summaryCard.style.border = '1px solid rgba(255, 255, 255, 0.08)';

    const h = document.createElement('div');
    h.style.display = 'flex';
    h.style.justifyContent = 'space-between';
    h.style.alignItems = 'center';
    h.style.marginBottom = '0.5rem';

    const title = document.createElement('strong');
    title.textContent = data.protocol || 'Model Context Protocol';
    title.style.fontSize = '0.95rem';

    const statusBadge = document.createElement('span');
    statusBadge.className = 'badge badge-green';
    statusBadge.textContent = data.status === 'operational' ? '⚡ Operational' : data.status;

    h.appendChild(title);
    h.appendChild(statusBadge);
    summaryCard.appendChild(h);

    const desc = document.createElement('p');
    desc.style.fontSize = '0.8rem';
    desc.style.color = '#94a3b8';
    desc.style.margin = '0';
    desc.innerHTML = `SDK: <span>${escapeHtml(data.sdk || 'FastMCP')}</span> | Transport: <span>${escapeHtml(data.transport || 'stdio JSON-RPC')}</span> | Total Registered Tools: <span id="mcp-total-tools" style="font-weight:600; color:#38bdf8;">${data.total_tools_registered || 0}</span>`;
    summaryCard.appendChild(desc);
    root.appendChild(summaryCard);

    // List of servers
    if (Array.isArray(data.servers)) {
      data.servers.forEach((srv) => {
        const srvCard = document.createElement('div');
        srvCard.className = 'glass-card';
        srvCard.style.padding = '0.75rem 1rem';
        srvCard.style.background = 'rgba(30, 41, 59, 0.5)';
        srvCard.style.borderRadius = '8px';
        srvCard.style.border = '1px solid rgba(255, 255, 255, 0.06)';

        const srvH = document.createElement('div');
        srvH.style.display = 'flex';
        srvH.style.justifyContent = 'space-between';
        srvH.style.alignItems = 'center';
        srvH.style.marginBottom = '0.5rem';

        const srvName = document.createElement('strong');
        srvName.textContent = `🖥️ Server: ${srv.server_id}`;
        srvName.style.fontSize = '0.88rem';

        const srvBadge = document.createElement('span');
        srvBadge.className = 'badge badge-cyan';
        srvBadge.textContent = `${srv.tools_count} Tool(s)`;

        srvH.appendChild(srvName);
        srvH.appendChild(srvBadge);
        srvCard.appendChild(srvH);

        if (srv.confinement) {
          const conf = document.createElement('div');
          conf.style.fontSize = '0.75rem';
          conf.style.color = '#38bdf8';
          conf.style.marginBottom = '0.5rem';
          conf.textContent = `🛡️ Security Confinement: ${srv.confinement} (path traversal & credentials blocked)`;
          srvCard.appendChild(conf);
        }

        if (Array.isArray(srv.tools)) {
          const toolList = document.createElement('div');
          toolList.style.display = 'flex';
          toolList.style.flexDirection = 'column';
          toolList.style.gap = '0.4rem';

          srv.tools.forEach((t) => {
            const row = document.createElement('div');
            row.style.background = 'rgba(15, 23, 42, 0.4)';
            row.style.padding = '0.4rem 0.6rem';
            row.style.borderRadius = '4px';
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.alignItems = 'center';

            const left = document.createElement('div');
            const toolName = document.createElement('code');
            toolName.textContent = t.name;
            toolName.style.color = '#e2e8f0';
            toolName.style.fontSize = '0.8rem';
            const toolDesc = document.createElement('div');
            toolDesc.textContent = t.description;
            toolDesc.style.fontSize = '0.72rem';
            toolDesc.style.color = '#94a3b8';

            left.appendChild(toolName);
            left.appendChild(toolDesc);

            const toolStatus = document.createElement('span');
            toolStatus.className = 'badge badge-outline';
            toolStatus.style.fontSize = '0.7rem';
            toolStatus.textContent = t.status || 'ready';

            row.appendChild(left);
            row.appendChild(toolStatus);
            toolList.appendChild(row);
          });
          srvCard.appendChild(toolList);
        }
        root.appendChild(srvCard);
      });
    }

    dom.mcpCardContent.appendChild(root);
  }

  async function copyMcpJson() {
    if (!state.mcp.rawJson) return;
    let copied = false;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(state.mcp.rawJson);
        copied = true;
      } catch (e) {
        copied = false;
      }
    }
    if (!copied) {
      try {
        const ta = document.createElement('textarea');
        ta.value = state.mcp.rawJson;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        copied = document.execCommand('copy');
        document.body.removeChild(ta);
      } catch (e) {
        copied = false;
      }
    }
    if (dom.btnCopyMcpJson) {
      const originalHtml = dom.btnCopyMcpJson.innerHTML;
      dom.btnCopyMcpJson.innerHTML = '✅ Copied!';
      setTimeout(() => {
        dom.btnCopyMcpJson.innerHTML = originalHtml;
      }, 1800);
    }
    showToast('MCP Status JSON copied to clipboard!', 'success');
  }

  if (dom.btnA2aCard) dom.btnA2aCard.addEventListener('click', openA2aModal);
  if (dom.btnCloseA2aModal) dom.btnCloseA2aModal.addEventListener('click', closeA2aModal);
  if (dom.btnCloseA2aFooter) dom.btnCloseA2aFooter.addEventListener('click', closeA2aModal);
  if (dom.btnCopyA2aJson) dom.btnCopyA2aJson.addEventListener('click', copyA2aJson);

  if (dom.btnMcpStatus) dom.btnMcpStatus.addEventListener('click', openMcpModal);
  if (dom.btnCloseMcpModal) dom.btnCloseMcpModal.addEventListener('click', closeMcpModal);
  if (dom.btnCloseMcpFooter) dom.btnCloseMcpFooter.addEventListener('click', closeMcpModal);
  if (dom.btnCopyMcpJson) dom.btnCopyMcpJson.addEventListener('click', copyMcpJson);

  if (dom.mcpModalBackdrop) {
    dom.mcpModalBackdrop.addEventListener('click', (e) => {
      if (e.target === dom.mcpModalBackdrop) closeMcpModal();
    });
  }

  if (dom.a2aModalBackdrop) {
    dom.a2aModalBackdrop.addEventListener('click', (e) => {
      if (e.target === dom.a2aModalBackdrop) closeA2aModal();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (dom.settingsBackdrop && !dom.settingsBackdrop.classList.contains('hidden')) {
        closeSettings();
      }
      if (dom.a2aModalBackdrop && !dom.a2aModalBackdrop.classList.contains('hidden')) {
        closeA2aModal();
      }
      if (dom.mcpModalBackdrop && !dom.mcpModalBackdrop.classList.contains('hidden')) {
        closeMcpModal();
      }
      if (dom.restoreModalBackdrop && !dom.restoreModalBackdrop.classList.contains('hidden')) {
        closeRestoreModal();
      }
    }
  });

  dom.sliderIterations.addEventListener('input', (e) => {
    dom.valIterations.textContent = e.target.value;
  });

  dom.sliderMutationScore.addEventListener('input', (e) => {
    dom.valMutationScore.textContent = `${e.target.value}%`;
  });

  dom.btnSaveSettings.addEventListener('click', async () => {
    state.settings.engineMode = dom.selectEngineMode.value;
    state.settings.modelName = dom.selectModelName.value;
    state.settings.maxIterations = parseInt(dom.sliderIterations.value, 10);
    state.settings.targetMutationScore = parseFloat(dom.sliderMutationScore.value);

    // Update config in hardening panel
    dom.hardenModelLbl.textContent = state.settings.modelName;
    dom.hardenIterLbl.textContent = state.settings.maxIterations;
    dom.hardenScoreLbl.textContent = `${state.settings.targetMutationScore}%`;

    const gKey = dom.inputGeminiKey.value.trim();
    const orKey = dom.inputOpenrouterKey.value.trim();

    if (gKey || orKey) {
      try {
        const res = await fetch('/api/config/keys', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            gemini_api_key: gKey || null,
            openrouter_api_key: orKey || null,
          }),
        });
        const data = await res.json();
        showToast('API Configuration saved successfully!', 'success');
      } catch (err) {
        showToast(`Failed to update keys: ${err.message}`, 'error');
      }
    } else {
      showToast('Settings saved successfully!', 'success');
    }

    closeSettings();
    fetchSystemStatus();
  });

  // =========================================================================
  // System Health & Hardware Polling
  // =========================================================================
  async function fetchSystemStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) throw new Error('Status endpoint returned error');
      const data = await res.json();

      // Hardware
      if (data.hardware) {
        const { machine, os_system, cpu_count, total_memory_gb } = data.hardware;
        dom.labelHardware.textContent = `${os_system} ${machine} (${cpu_count} cores, ${total_memory_gb}GB)`;
      }

      // Providers
      if (data.providers) {
        const { ollama_online, has_gemini, has_openrouter } = data.providers;

        // Ollama
        dom.dotOllama.className = `indicator-dot ${ollama_online ? 'green' : 'red'}`;
        dom.labelOllama.textContent = ollama_online ? 'Ollama (Online)' : 'Ollama (Offline)';

        // Gemini
        dom.dotGemini.className = `indicator-dot ${has_gemini ? 'green' : 'amber'}`;
        dom.labelGemini.textContent = has_gemini ? 'Gemini (Active)' : 'Gemini (No Key)';

        // OpenRouter
        dom.dotOpenrouter.className = `indicator-dot ${has_openrouter ? 'green' : 'gray'}`;
        dom.labelOpenrouter.textContent = has_openrouter ? 'OpenRouter (Active)' : 'OpenRouter (Idle)';
      }

      // Refresh MCP status pill in background
      fetchAndRenderMcpStatus(true);
    } catch (err) {
      console.warn('System status fetch failed:', err);
    }
  }

  // =========================================================================
  // Active Target Synchronization
  // =========================================================================
  function updateTargetBanner(analysisData) {
    state.activeTarget.mode = analysisData.mode || state.activeTarget.mode;
    state.activeTarget.filePath = analysisData.target_file_path || state.activeTarget.filePath;
    state.activeTarget.moduleName = analysisData.module_name || state.activeTarget.moduleName;
    state.activeTarget.sourceCode = analysisData.source_code || state.activeTarget.sourceCode;
    state.activeTarget.sourceSha = analysisData.source_sha || state.activeTarget.sourceSha;
    state.activeTarget.functions = analysisData.functions || [];
    state.activeTarget.classes = analysisData.classes || [];
    state.activeTarget.methods = analysisData.methods || [];
    state.activeTarget.allCallables = analysisData.all_callables || [];
    state.activeTarget.lineCount = analysisData.line_count || 0;
    state.activeTarget.dependencies = analysisData.dependencies || [];
    state.activeTarget.metadata = analysisData.metadata || null;

    // UI Banner
    dom.targetModeBadge.textContent = `Active Target: ${state.activeTarget.mode}`;
    dom.targetModuleTitle.textContent = state.activeTarget.moduleName;
    dom.tagFilePath.textContent = `📁 ${state.activeTarget.filePath}`;
    dom.tagSha.textContent = `🔑 SHA: ${state.activeTarget.sourceSha ? state.activeTarget.sourceSha.substring(0, 8) : 'unknown'}`;
    dom.tagFuncs.textContent = `⚡ ${state.activeTarget.functions.length} Function${state.activeTarget.functions.length === 1 ? '' : 's'}`;
    dom.tagClasses.textContent = `🏛️ ${state.activeTarget.classes.length} Class${state.activeTarget.classes.length === 1 ? '' : 'es'}`;
    dom.tagLines.textContent = `📄 ${state.activeTarget.lineCount} Lines`;

    // Hardening panel summary
    dom.hardenTargetLbl.textContent = state.activeTarget.moduleName;

    // Update function dropdown in Blast Radius tab
    populateBlastFunctionDropdown();

    // Check Git Diff if enabled
    if (state.gitDiff.enabled) {
      checkGitDiff();
    }
  }

  // =========================================================================
  // Mode A: Workspace Samples & File Upload
  // =========================================================================
  async function loadSampleFilesList() {
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      if (data.samples && data.samples.length > 0) {
        dom.sampleFileSelect.innerHTML = '';
        data.samples.forEach(file => {
          const opt = document.createElement('option');
          opt.value = file;
          opt.textContent = file;
          if (file === 'discount.py') opt.selected = true;
          dom.sampleFileSelect.appendChild(opt);
        });
      }
    } catch (err) {
      console.warn('Could not fetch sample list:', err);
    }
  }

  async function loadSampleModule(filename) {
    try {
      dom.btnLoadSample.disabled = true;
      dom.btnLoadSample.textContent = 'Loading...';

      const res = await fetch('/api/ingest/sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Sample load failed');
      }

      const data = await res.json();
      updateTargetBanner(data);

      // Populate Mode A view
      dom.modeAModuleName.textContent = data.module_name;
      dom.modeAFuncsList.textContent = data.functions.length > 0 ? data.functions.join(', ') : 'None';
      dom.modeAClassesList.textContent = data.classes.length > 0 ? data.classes.join(', ') : 'None';
      dom.modeACodeDisplay.textContent = data.source_code;

      showToast(`Loaded sample module ${filename}`, 'success');
    } catch (err) {
      showToast(`Error loading sample: ${err.message}`, 'error');
    } finally {
      dom.btnLoadSample.disabled = false;
      dom.btnLoadSample.textContent = 'Load Sample';
    }
  }

  if (dom.btnLoadSample) {
    dom.btnLoadSample.addEventListener('click', () => {
      const selected = dom.sampleFileSelect.value;
      if (selected) loadSampleModule(selected);
    });
  }

  // Source switcher (Built-in vs Upload)
  dom.radioSourceSample.addEventListener('change', () => {
    dom.groupSampleSelect.classList.remove('hidden');
    dom.groupFileUpload.classList.add('hidden');
  });

  dom.radioSourceUpload.addEventListener('change', () => {
    dom.groupSampleSelect.classList.add('hidden');
    dom.groupFileUpload.classList.remove('hidden');
  });

  // File Dropzone Handling
  let selectedUploadFile = null;

  dom.fileDropzone.addEventListener('click', () => {
    dom.fileUploadInput.click();
  });

  dom.fileUploadInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleSelectedUploadFile(e.target.files[0]);
    }
  });

  dom.fileDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dom.fileDropzone.classList.add('drag-over');
  });

  dom.fileDropzone.addEventListener('dragleave', () => {
    dom.fileDropzone.classList.remove('drag-over');
  });

  dom.fileDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dom.fileDropzone.classList.remove('drag-over');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSelectedUploadFile(e.dataTransfer.files[0]);
    }
  });

  function handleSelectedUploadFile(file) {
    if (!file.name.endsWith('.py')) {
      showToast('Please select a valid Python (.py) file', 'error');
      return;
    }
    selectedUploadFile = file;
    dom.uploadFilenamePreview.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    dom.btnSubmitUpload.disabled = false;
  }

  dom.btnSubmitUpload.addEventListener('click', async () => {
    if (!selectedUploadFile) return;

    try {
      dom.btnSubmitUpload.disabled = true;
      dom.btnSubmitUpload.textContent = 'Ingesting & Parsing AST...';

      const formData = new FormData();
      formData.append('file', selectedUploadFile);

      const res = await fetch('/api/ingest/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload ingestion failed');
      }

      const data = await res.json();
      updateTargetBanner(data);

      dom.modeAModuleName.textContent = data.module_name;
      dom.modeAFuncsList.textContent = data.functions.length > 0 ? data.functions.join(', ') : 'None';
      dom.modeAClassesList.textContent = data.classes.length > 0 ? data.classes.join(', ') : 'None';
      dom.modeACodeDisplay.textContent = data.source_code;

      showToast(`Uploaded and ingested ${selectedUploadFile.name}!`, 'success');
    } catch (err) {
      showToast(`Upload failed: ${err.message}`, 'error');
    } finally {
      dom.btnSubmitUpload.disabled = false;
      dom.btnSubmitUpload.textContent = 'Ingest Uploaded File';
    }
  });

  // Git Diff Toggle
  dom.toggleGitDiff.addEventListener('change', async (e) => {
    state.gitDiff.enabled = e.target.checked;
    if (state.gitDiff.enabled) {
      await checkGitDiff();
    } else {
      dom.gitDiffAlert.classList.add('hidden');
      state.gitDiff.modifiedLines = [];
    }
  });

  async function checkGitDiff() {
    if (!state.activeTarget.filePath) return;
    try {
      const res = await fetch('/api/analysis/git-diff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_file_path: state.activeTarget.filePath }),
      });
      const data = await res.json();
      state.gitDiff.modifiedLines = data.modified_lines || [];

      dom.gitDiffAlert.classList.remove('hidden');
      if (data.has_changes) {
        dom.gitDiffAlert.className = 'git-diff-status active';
        dom.gitDiffAlert.innerHTML = `
          <strong>Git Diff Detected:</strong> Modified lines: <code>[${data.modified_lines.join(', ')}]</code>. 
          Hardening will restrict mutations strictly to these lines.
        `;
      } else {
        dom.gitDiffAlert.className = 'git-diff-status clean';
        dom.gitDiffAlert.innerHTML = `
          <strong>Clean Working Tree:</strong> No uncommitted git modifications found in <code>${state.activeTarget.filePath}</code>. Full file targeted.
        `;
      }
    } catch (err) {
      console.warn('Git diff check failed:', err);
    }
  }

  // Copy code button
  if (dom.btnCopyModeACode) {
    dom.btnCopyModeACode.addEventListener('click', () => {
      copyTextToClipboard(state.activeTarget.sourceCode, dom.btnCopyModeACode);
    });
  }

  // =========================================================================
  // Mode B: AI Module Synthesis
  // =========================================================================
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      const url = chip.getAttribute('data-url');
      if (prompt) {
        dom.synthPromptInput.value = prompt;
      }
      if (url) {
        dom.githubUrlInput.value = url;
      }
    });
  });

  if (dom.btnSynthesizeModule) {
    dom.btnSynthesizeModule.addEventListener('click', async () => {
      const prompt = dom.synthPromptInput.value.trim();
      if (!prompt) {
        showToast('Please enter an algorithm or module specification', 'warning');
        return;
      }

      try {
        dom.btnSynthesizeModule.disabled = true;
        dom.btnSynthesizeModule.innerHTML = '<span class="icon">⏳</span> Synthesizing & Verifying AST...';
        dom.synthStatusBox.className = 'info-callout warning';
        dom.synthStatusBox.innerHTML = 'Synthesizing module with TargetManagerAgent and validating AST safety...';

        const res = await fetch('/api/ingest/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt,
            model_name: state.settings.modelName,
          }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Synthesis failed');
        }

        const data = await res.json();
        updateTargetBanner(data);

        dom.synthStatusBox.className = 'info-callout success';
        dom.synthStatusBox.innerHTML = `
          ✅ Successfully synthesized <strong>${data.module_name}</strong> (${data.line_count} lines)!
          Validated AST with ${data.functions.length} functions and ${data.classes.length} classes.
        `;

        dom.synthCodeContainer.classList.remove('hidden');
        dom.synthFileTitle.textContent = data.target_file_path;
        dom.synthCodeDisplay.textContent = data.source_code;

        showToast('AI module synthesized and active!', 'success');
      } catch (err) {
        dom.synthStatusBox.className = 'info-callout error';
        dom.synthStatusBox.innerHTML = `❌ Synthesis Error: ${escapeHtml(err.message)}`;
        showToast(`Synthesis failed: ${err.message}`, 'error');
      } finally {
        dom.btnSynthesizeModule.disabled = false;
        dom.btnSynthesizeModule.innerHTML = '<span class="icon">🚀</span> Synthesize Module';
      }
    });
  }

  if (dom.btnCopySynthCode) {
    dom.btnCopySynthCode.addEventListener('click', () => {
      copyTextToClipboard(dom.synthCodeDisplay.textContent, dom.btnCopySynthCode);
    });
  }

  // =========================================================================
  // Mode C: Direct GitHub File Ingestion
  // =========================================================================
  let lastIngestedGithubData = null;

  if (dom.btnFetchGithub) {
    dom.btnFetchGithub.addEventListener('click', async () => {
      const rawUrl = dom.githubUrlInput.value.trim();
      if (!rawUrl) {
        showToast('Please enter a GitHub file URL', 'warning');
        return;
      }

      try {
        dom.btnFetchGithub.disabled = true;
        dom.btnFetchGithub.innerHTML = '<span class="icon">⏳</span> Fetching & Ingesting...';
        dom.urlValidationBadge.classList.add('hidden');

        const res = await fetch('/api/ingest/github', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: rawUrl }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'GitHub Ingestion failed');
        }

        const data = await res.json();
        lastIngestedGithubData = data;

        // Show validation badge
        dom.urlValidationBadge.classList.remove('hidden');
        dom.urlValidationText.textContent = `Normalized: ${data.metadata.raw_github_url}`;

        // Populate Mode C metadata
        dom.modeCEmptyState.classList.add('hidden');
        dom.modeCDetails.classList.remove('hidden');

        dom.mcRepo.textContent = data.metadata.repository;
        dom.mcBranch.textContent = data.metadata.branch;
        dom.mcPath.textContent = data.metadata.file_path;
        dom.mcModule.textContent = data.module_name;
        dom.mcSha.textContent = data.source_sha;

        dom.mcLines.textContent = data.line_count;
        dom.mcClassesCnt.textContent = data.classes.length;
        dom.mcCallablesCnt.textContent = data.all_callables.length;

        // Classes chips
        dom.mcClassChips.innerHTML = '';
        if (data.classes.length > 0) {
          data.classes.forEach(cls => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = cls;
            dom.mcClassChips.appendChild(chip);
          });
        } else {
          dom.mcClassChips.innerHTML = '<span class="text-muted">None detected</span>';
        }

        // Source code preview
        dom.modeCCodeDisplay.textContent = data.source_code;

        // Automatically activate as target
        updateTargetBanner(data);

        if (dom.btnActivateModeC) {
          dom.btnActivateModeC.classList.add('btn-primary', 'btn-glow');
          dom.btnActivateModeC.classList.remove('btn-secondary');
          dom.btnActivateModeC.innerHTML = '<span class="icon">🎯</span> Target Confirmed for Hardening (Click to Proceed)';
        }

        showToast(`Ingested ${data.filename} from GitHub!`, 'success');
      } catch (err) {
        showToast(`GitHub Ingestion Error: ${err.message}`, 'error');
        dom.modeCEmptyState.classList.remove('hidden');
        dom.modeCEmptyState.className = 'info-callout error';
        dom.modeCEmptyState.innerHTML = `<strong>Error fetching GitHub file:</strong> ${escapeHtml(err.message)}`;
      } finally {
        dom.btnFetchGithub.disabled = false;
        dom.btnFetchGithub.innerHTML = '<span class="icon">⬇️</span> Fetch & Ingest';
      }
    });
  }

  if (dom.btnActivateModeC) {
    dom.btnActivateModeC.addEventListener('click', () => {
      if (lastIngestedGithubData) {
        updateTargetBanner(lastIngestedGithubData);
        showToast('Target confirmed for hardening!', 'success');
        switchTab('tab-hardening');
      }
    });
  }

  if (dom.btnCopyModeCCode) {
    dom.btnCopyModeCCode.addEventListener('click', () => {
      copyTextToClipboard(dom.modeCCodeDisplay.textContent, dom.btnCopyModeCCode);
    });
  }

  // =========================================================================
  // Blast Radius & Static Call Graph Analysis
  // =========================================================================
  function populateBlastFunctionDropdown() {
    dom.blastFuncSelect.innerHTML = '';
    const funcs = state.activeTarget.functions;
    if (funcs.length === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'No top-level functions defined';
      dom.blastFuncSelect.appendChild(opt);
      return;
    }

    funcs.forEach(fn => {
      const opt = document.createElement('option');
      opt.value = fn;
      opt.textContent = fn;
      dom.blastFuncSelect.appendChild(opt);
    });

    state.blastRadius.selectedTarget = funcs[0];
  }

  dom.blastFuncSelect.addEventListener('change', (e) => {
    state.blastRadius.selectedTarget = e.target.value;
    triggerBlastRadiusAnalysis();
  });

  async function triggerBlastRadiusAnalysis() {
    const code = state.activeTarget.sourceCode;
    if (!code) return;

    try {
      const targetFn = state.blastRadius.selectedTarget || dom.blastFuncSelect.value;
      const res = await fetch('/api/analysis/blast-radius', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_code: code,
          target_function: targetFn || null,
        }),
      });

      if (!res.ok) throw new Error('Blast radius computation failed');
      const data = await res.json();
      state.blastRadius.impact = data.impact;
      state.blastRadius.graphData = data.graph_data;

      // Update KPIs
      const impact = data.impact;
      if (impact) {
        dom.blastRiskBadge.textContent = impact.blast_radius_risk || '🟢 LOW';
        if (impact.blast_radius_risk && impact.blast_radius_risk.includes('HIGH')) {
          dom.blastRiskBadge.className = 'stat-num text-red';
        } else if (impact.blast_radius_risk && impact.blast_radius_risk.includes('MEDIUM')) {
          dom.blastRiskBadge.className = 'stat-num text-amber';
        } else {
          dom.blastRiskBadge.className = 'stat-num text-green';
        }

        dom.blastAffectedCount.textContent = `${impact.affected_functions_count || 0} / ${impact.total_functions || 0}`;
        dom.blastImpactRatio.textContent = `${impact.impact_percentage || 0}%`;
        dom.blastCalleesCount.textContent = (impact.downstream_callees || []).length;

        // Render ASCII Call Tree
        renderAsciiCallTree(impact);
      }

      // Render Visual Call Graph
      renderCallGraphVisualizer(data.graph_data);
    } catch (err) {
      console.warn('Blast radius analysis error:', err);
    }
  }

  function renderAsciiCallTree(impact) {
    if (!impact) {
      dom.blastTreeDisplay.textContent = 'No impact data available.';
      return;
    }

    const target = impact.target_function || 'target';
    const upstream = impact.upstream_callers || [];
    const downstream = impact.downstream_callees || [];

    let lines = [];
    lines.push(`Root Target: [${target}] (Risk: ${impact.blast_radius_risk})`);
    lines.push(`│`);

    lines.push(`├── ⬆️ Upstream Callers (${upstream.length}):`);
    if (upstream.length === 0) {
      lines.push(`│   └── (None - Module Entrypoint)`);
    } else {
      upstream.forEach((u, i) => {
        const isLast = i === upstream.length - 1;
        lines.push(`│   ${isLast ? '└──' : '├──'} ${u}`);
      });
    }

    lines.push(`│`);
    lines.push(`└── ⬇️ Downstream Callees (${downstream.length}):`);
    if (downstream.length === 0) {
      lines.push(`    └── (None - Leaf Function)`);
    } else {
      downstream.forEach((d, i) => {
        const isLast = i === downstream.length - 1;
        lines.push(`    ${isLast ? '└──' : '├──'} ${d}`);
      });
    }

    dom.blastTreeDisplay.textContent = lines.join('\n');
  }

  function renderCallGraphVisualizer(graphData) {
    if (!dom.callGraphCanvas) return;
    dom.callGraphCanvas.innerHTML = '';

    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      dom.callGraphCanvas.innerHTML = '<div class="text-center text-muted" style="padding: 2rem;">No call graph relationships detected for this module.</div>';
      return;
    }

    // Render node pills with connected badges
    const container = document.createElement('div');
    container.className = 'graph-nodes-flex';

    graphData.nodes.forEach(node => {
      const nodeEl = document.createElement('div');
      nodeEl.className = `graph-node ${node.is_target ? 'is-target' : ''}`;

      // Find callees
      const outgoing = graphData.edges.filter(e => e.from === node.id).map(e => e.to);
      const incoming = graphData.edges.filter(e => e.to === node.id).map(e => e.from);

      nodeEl.innerHTML = `
        <div class="node-header">
          <span class="node-icon">${node.is_target ? '🎯' : '⚡'}</span>
          <span class="node-title">${escapeHtml(node.label)}</span>
        </div>
        <div class="node-meta">
          <span>In: ${incoming.length}</span> &bull; <span>Out: ${outgoing.length}</span>
        </div>
      `;

      nodeEl.addEventListener('click', () => {
        dom.blastFuncSelect.value = node.id;
        state.blastRadius.selectedTarget = node.id;
        triggerBlastRadiusAnalysis();
      });

      container.appendChild(nodeEl);
    });

    dom.callGraphCanvas.appendChild(container);
  }

  // =========================================================================
  // Hardening Pipeline Execution & Polling
  // =========================================================================
  if (dom.btnRunHardening) {
    dom.btnRunHardening.addEventListener('click', startHardeningPipeline);
  }
  if (dom.btnCancelHardening) {
    dom.btnCancelHardening.addEventListener('click', cancelHardeningJob);
  }

  async function cancelHardeningJob() {
    let jobId = state.hardening.jobId;
    if (!jobId) {
      // If start request is currently in-flight, await jobId briefly
      for (let i = 0; i < 15 && !state.hardening.jobId; i++) {
        await new Promise(r => setTimeout(r, 100));
      }
      jobId = state.hardening.jobId;
    }

    if (!jobId) {
      showToast('No active hardening job to cancel.', 'warning');
      return;
    }

    try {
      if (dom.btnCancelHardening) {
        dom.btnCancelHardening.disabled = true;
        dom.btnCancelHardening.innerHTML = '<span class="icon">⏳</span> Cancelling...';
      }
      if (dom.hardeningStatusText) {
        dom.hardeningStatusText.textContent = 'Cancellation requested... waiting for background workers to safely halt.';
      }
      showToast(`Cancellation requested for job [${jobId}]`, 'info');

      const res = await fetch(`/api/harden/cancel/${jobId}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to cancel hardening job');
      }

      const cancelData = await res.json();
      if (cancelData.status === 'already_terminal') {
        showToast(`Job is already in terminal state: ${cancelData.current_status}`, 'info');
        if (dom.btnCancelHardening) dom.btnCancelHardening.classList.add('hidden');
      }
    } catch (err) {
      if (dom.btnCancelHardening) {
        dom.btnCancelHardening.disabled = false;
        dom.btnCancelHardening.innerHTML = '<span class="icon">🛑</span> Cancel Hardening';
      }
      showToast(`Cancellation error: ${err.message}`, 'error');
    }
  }

  async function startHardeningPipeline() {
    if (!state.activeTarget.sourceCode) {
      showToast('No active target code loaded. Please select or ingest a target first.', 'warning');
      return;
    }

    try {
      dom.btnRunHardening.disabled = true;
      dom.btnRunHardening.innerHTML = '<span class="icon">⏳</span> Hardening Pipeline Active...';

      if (dom.btnCancelHardening) {
        dom.btnCancelHardening.classList.remove('hidden');
        dom.btnCancelHardening.disabled = false;
        dom.btnCancelHardening.innerHTML = '<span class="icon">🛑</span> Cancel Hardening';
      }

      // Reset and display progress box
      dom.hardeningProgressBox.classList.remove('hidden');
      dom.hardeningVerdictBanner.classList.add('hidden');
      dom.hardeningProgressBar.style.width = '10%';
      dom.hardeningPercentText.textContent = '10%';
      dom.hardeningStatusText.textContent = 'Orchestrating agents, baseline synthesis, and sandbox spawning...';

      // Clear previous outputs
      resetHardeningKPIs();

      const payload = {
        target_file_path: state.activeTarget.filePath,
        target_source_code: state.activeTarget.sourceCode,
        max_iterations: state.settings.maxIterations,
        target_mutation_score: state.settings.targetMutationScore,
        model_name: state.settings.modelName,
        engine_mode: state.settings.engineMode,
        target_lines: state.gitDiff.enabled && state.gitDiff.modifiedLines.length > 0 ? state.gitDiff.modifiedLines : null,
      };

      const res = await fetch('/api/harden/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to start hardening pipeline');
      }

      const jobData = await res.json();
      state.hardening.jobId = jobData.job_id;
      state.hardening.status = 'RUNNING';

      if (dom.btnCancelHardening) {
        dom.btnCancelHardening.disabled = false;
      }

      showToast(`Started autonomous hardening job [${jobData.job_id}]`, 'info');

      // Begin Polling
      pollHardeningJob(jobData.job_id);
    } catch (err) {
      dom.btnRunHardening.disabled = false;
      dom.btnRunHardening.innerHTML = '<span class="icon">⚡</span> Run TestForge Autonomous Hardening';
      if (dom.btnCancelHardening) {
        dom.btnCancelHardening.classList.add('hidden');
      }
      dom.hardeningProgressBox.classList.add('hidden');
      showToast(`Hardening Error: ${err.message}`, 'error');
    }
  }

  function resetHardeningKPIs() {
    dom.kpiBaseGen.textContent = '0';
    dom.kpiBaseExec.textContent = '0';
    dom.kpiBasePass.textContent = '0';
    dom.kpiBaseFail.textContent = '0';
    dom.kpiBaseVerdict.textContent = '⚪ PENDING';

    dom.kpiLinesCov.textContent = '0 / 0';
    dom.kpiCovPct.textContent = '0.0%';
    dom.kpiMutGen.textContent = '0';
    dom.kpiMutExec.textContent = '0';
    dom.kpiMutKill.textContent = '0';
    dom.kpiMutSurv.textContent = '0';
    dom.kpiMutErr.textContent = '0';

    dom.kpiMutScore.textContent = '0.0%';
    dom.kpiCyclesDone.textContent = '0';
    dom.kpiFinalStatus.textContent = 'RUNNING';

    dom.historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Running multi-agent reflection loops...</td></tr>';
    dom.mutantsTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Executing AST mutants across sandbox workers...</td></tr>';
    dom.diffCodeDisplay.textContent = '// Unified AST diffs will appear here once execution completes.';
  }

  function pollHardeningJob(jobId) {
    if (state.hardening.pollTimer) clearInterval(state.hardening.pollTimer);

    let progressSim = 15;

    state.hardening.pollTimer = setInterval(async () => {
      try {
        const res = await fetch(`/api/harden/status/${jobId}`);
        if (!res.ok) return;

        const job = await res.json();

        if (job.status === 'RUNNING') {
          // Increment simulated progress while job runs
          progressSim = Math.min(progressSim + 12, 90);
          dom.hardeningProgressBar.style.width = `${progressSim}%`;
          dom.hardeningPercentText.textContent = `${progressSim}%`;
          dom.hardeningStatusText.textContent = `Autonomous Multi-Agent reflection loop running (Core Sandbox: ${progressSim}%)...`;
        } else if (job.status === 'CANCELLING') {
          state.hardening.status = 'CANCELLING';
          if (dom.btnCancelHardening) {
            dom.btnCancelHardening.disabled = true;
            dom.btnCancelHardening.innerHTML = '<span class="icon">⏳</span> Cancelling...';
          }
          dom.hardeningStatusText.textContent = 'Cancellation in progress (safely halting sub-processes and cleaning up)...';
        } else if (job.status === 'CANCELLED') {
          clearInterval(state.hardening.pollTimer);
          state.hardening.status = 'CANCELLED';
          if (dom.btnCancelHardening) {
            dom.btnCancelHardening.classList.add('hidden');
            dom.btnCancelHardening.disabled = false;
            dom.btnCancelHardening.innerHTML = '<span class="icon">🛑</span> Cancel Hardening';
          }
          dom.btnRunHardening.disabled = false;
          dom.btnRunHardening.innerHTML = '<span class="icon">⚡</span> Run TestForge Autonomous Hardening';
          dom.hardeningProgressBox.classList.add('hidden');

          dom.hardeningVerdictBanner.classList.remove('hidden');
          dom.hardeningVerdictBanner.className = 'verdict-banner cancelled';
          dom.hardeningVerdictBanner.innerHTML = `
            <div class="verdict-content">
              <h3>🛑 Hardening Cancelled</h3>
              <p>
                Hardening job [<strong>${escapeHtml(jobId)}</strong>] was gracefully cancelled.
                All workers halted in <strong>${job.duration_seconds || 0}s</strong>.
                ${job.final_state ? 'Partial test generation and mutation data were preserved below.' : ''}
              </p>
            </div>
          `;
          showToast(`Hardening job [${jobId}] was cancelled`, 'info');

          if (job.final_state) {
            renderHardeningResults(job, 'CANCELLED');
          }
        } else if (job.status === 'TIMED_OUT') {
          clearInterval(state.hardening.pollTimer);
          state.hardening.status = 'TIMED_OUT';
          if (dom.btnCancelHardening) {
            dom.btnCancelHardening.classList.add('hidden');
            dom.btnCancelHardening.disabled = false;
          }
          dom.btnRunHardening.disabled = false;
          dom.btnRunHardening.innerHTML = '<span class="icon">⚡</span> Run TestForge Autonomous Hardening';
          dom.hardeningProgressBox.classList.add('hidden');

          dom.hardeningVerdictBanner.classList.remove('hidden');
          dom.hardeningVerdictBanner.className = 'verdict-banner timed-out';
          dom.hardeningVerdictBanner.innerHTML = `
            <div class="verdict-content">
              <h3>⏱️ Hardening Timed Out</h3>
              <p>
                Hardening job [<strong>${escapeHtml(jobId)}</strong>] exceeded maximum timeout threshold (${job.timeout_seconds || 300}s).
                Subprocesses were terminated and partial results were retained.
              </p>
            </div>
          `;
          showToast(`Hardening job [${jobId}] timed out`, 'warning');

          if (job.final_state) {
            renderHardeningResults(job, 'TIMED_OUT');
          }
        } else if (job.status === 'COMPLETED') {
          clearInterval(state.hardening.pollTimer);
          if (dom.btnCancelHardening) {
            dom.btnCancelHardening.classList.add('hidden');
          }
          dom.hardeningProgressBar.style.width = '100%';
          dom.hardeningPercentText.textContent = '100%';
          dom.hardeningStatusText.textContent = 'Hardening completed successfully across all AST mutations!';

          renderHardeningResults(job);
        } else if (job.status === 'FAILED') {
          clearInterval(state.hardening.pollTimer);
          if (dom.btnCancelHardening) {
            dom.btnCancelHardening.classList.add('hidden');
          }
          dom.hardeningProgressBox.classList.add('hidden');
          dom.btnRunHardening.disabled = false;
          dom.btnRunHardening.innerHTML = '<span class="icon">⚡</span> Run TestForge Autonomous Hardening';

          dom.hardeningVerdictBanner.classList.remove('hidden');
          dom.hardeningVerdictBanner.className = 'verdict-banner failed';
          dom.hardeningVerdictBanner.innerHTML = `
            <h3>❌ Hardening Pipeline Failed</h3>
            <p>${escapeHtml(job.error || 'Unknown orchestration error')}</p>
          `;
          showToast(`Pipeline execution failed: ${job.error}`, 'error');
        }
      } catch (err) {
        console.warn('Job polling error:', err);
      }
    }, 1200);
  }

  function renderHardeningResults(job, statusOverride = null) {
    if (!statusOverride) {
      state.hardening.status = 'COMPLETED';
    }
    dom.btnRunHardening.disabled = false;
    dom.btnRunHardening.innerHTML = '<span class="icon">⚡</span> Run TestForge Autonomous Hardening';

    const finalState = job.final_state || {};
    state.hardening.finalState = finalState;
    state.hardening.testHardenedCode = job.test_hardened_code || '';

    // Immediately hydrate Wiretap and Telemetry traces (TF-DEF-002 fix)
    fetchWiretap();
    fetchTelemetry();

    // ROW 1: Baseline Execution
    const baseline = finalState.baseline_run || {};
    dom.kpiBaseGen.textContent = baseline.tests_generated || (finalState.test_suite ? finalState.test_suite.length : 0);
    dom.kpiBaseExec.textContent = baseline.tests_executed || 0;
    dom.kpiBasePass.textContent = baseline.tests_passed || 0;
    dom.kpiBaseFail.textContent = baseline.tests_failed || 0;
    const basePassed = baseline.tests_failed === 0 && baseline.tests_passed > 0;
    dom.kpiBaseVerdict.textContent = basePassed ? '🟢 ALL PASSED' : (baseline.tests_failed > 0 ? '🔴 HAS FAILURES' : '⚪ NONE');

    // ROW 2: Mutation & Coverage
    const lastIter = finalState.iteration_history && finalState.iteration_history.length > 0
      ? finalState.iteration_history[finalState.iteration_history.length - 1]
      : null;

    const totalLines = state.activeTarget.lineCount || 1;
    const covPct = lastIter ? (lastIter.line_coverage || 0) : (finalState.baseline_coverage || 0);
    const linesCovered = Math.round((covPct / 100) * totalLines);

    dom.kpiLinesCov.textContent = `${linesCovered} / ${totalLines}`;
    dom.kpiCovPct.textContent = `${covPct.toFixed(1)}%`;

    const mutGen = finalState.mutants ? finalState.mutants.length : 0;
    const mutKill = lastIter ? lastIter.mutants_killed : 0;
    const mutSurv = lastIter ? lastIter.mutants_survived : 0;

    dom.kpiMutGen.textContent = mutGen;
    dom.kpiMutExec.textContent = mutGen;
    dom.kpiMutKill.textContent = mutKill;
    dom.kpiMutSurv.textContent = mutSurv;
    dom.kpiMutErr.textContent = '0';

    // ROW 3: Final Status
    const finalScore = finalState.mutation_score != null ? finalState.mutation_score : (lastIter ? lastIter.mutation_score : 0);
    dom.kpiMutScore.textContent = `${finalScore.toFixed(1)}%`;
    dom.kpiCyclesDone.textContent = `${finalState.current_iteration || (finalState.iteration_history ? finalState.iteration_history.length : 1)} / ${state.settings.maxIterations}`;
    dom.kpiFinalStatus.textContent = statusOverride || finalState.hardening_status || 'HARDENED';

    if (!statusOverride) {
      // Hardening Verdict Banner
      dom.hardeningVerdictBanner.classList.remove('hidden');
      const isSuccess = finalScore >= state.settings.targetMutationScore || finalState.hardening_status === 'TARGET_ACHIEVED';
      dom.hardeningVerdictBanner.className = `verdict-banner ${isSuccess ? 'success' : 'warning'}`;
      dom.hardeningVerdictBanner.innerHTML = `
        <div class="verdict-content">
          <h3>${isSuccess ? '🏆 Autonomous Hardening Verified!' : '⚠️ Hardening Completed (Threshold Not Fully Reached)'}</h3>
          <p>
            Final Verified Mutation Score: <strong>${finalScore.toFixed(1)}%</strong> (Target: ${state.settings.targetMutationScore}%). 
            Completed in <strong>${job.duration_seconds || 0}s</strong> using provider <strong>${escapeHtml(job.active_provider || state.settings.modelName)}</strong>.
          </p>
        </div>
      `;
    }

    // Render History Table
    renderHistoryTable(finalState.iteration_history || []);

    // Render Mutants Table
    state.hardening.mutants = finalState.mutants || [];
    renderMutantsTable(state.hardening.mutants);

    // Hardened Suite Code View
    if (job.test_hardened_code) {
      dom.hardenedSuiteCode.textContent = job.test_hardened_code;
    } else {
      fetchHardenedSuiteCode();
    }

    showToast(`Hardening complete! Mutation Score: ${finalScore.toFixed(1)}%`, 'success');
  }

  function renderHistoryTable(iterations) {
    if (!iterations || iterations.length === 0) {
      dom.historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No iteration telemetry recorded.</td></tr>';
      return;
    }

    dom.historyTableBody.innerHTML = '';
    iterations.forEach(it => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong class="text-cyan">Cycle ${it.iteration}</strong></td>
        <td>${it.total_mutants}</td>
        <td><span class="text-green font-semibold">${it.mutants_killed}</span></td>
        <td><span class="text-red font-semibold">${it.mutants_survived}</span></td>
        <td><span class="badge ${it.mutation_score >= 80 ? 'badge-green' : 'badge-amber'}">${it.mutation_score.toFixed(1)}%</span></td>
        <td>${(it.line_coverage || 0).toFixed(1)}%</td>
        <td>${it.duration_seconds ? `${it.duration_seconds.toFixed(2)}s` : '-'}</td>
      `;
      dom.historyTableBody.appendChild(tr);
    });
  }

  function renderMutantsTable(mutants) {
    const filter = state.hardening.filter;
    const filtered = mutants.filter(m => {
      if (filter === 'KILLED') return m.status === 'KILLED';
      if (filter === 'SURVIVED') return m.status === 'SURVIVED';
      if (filter === 'EQUIVALENT') return m.status === 'EQUIVALENT' || m.equivalence_status === 'EQUIVALENT';
      return true;
    });

    // Counts
    dom.cntAllMut.textContent = mutants.length;
    dom.cntKillMut.textContent = mutants.filter(m => m.status === 'KILLED').length;
    dom.cntSurvMut.textContent = mutants.filter(m => m.status === 'SURVIVED').length;
    if (dom.cntEquivMut) {
      dom.cntEquivMut.textContent = mutants.filter(m => m.status === 'EQUIVALENT' || m.equivalence_status === 'EQUIVALENT').length;
    }

    if (filtered.length === 0) {
      dom.mutantsTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No mutants matching filter (${filter}).</td></tr>`;
      return;
    }

    dom.mutantsTableBody.innerHTML = '';
    filtered.forEach((m, idx) => {
      const tr = document.createElement('tr');
      tr.className = `clickable-row mutant-row ${state.hardening.selectedMutant === m ? 'selected' : ''}`;

      const st = (m.status || (m.killed ? 'KILLED' : 'SURVIVED')).toUpperCase();
      let badgeHtml = '';
      if (st === 'KILLED') badgeHtml = '<span class="badge badge-green">🟢 KILLED</span>';
      else if (st === 'EQUIVALENT') badgeHtml = '<span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid #3b82f6;">🔵 EQUIV</span>';
      else if (st === 'POTENTIALLY_EQUIVALENT') badgeHtml = '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid #f59e0b;">🟡 POTENTIAL</span>';
      else if (st === 'TIMEOUT') badgeHtml = '<span class="badge" style="background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid #f97316;">🟠 TIMEOUT</span>';
      else if (st === 'INVALID') badgeHtml = '<span class="badge" style="background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid #94a3b8;">⚪ INVALID</span>';
      else if (st === 'ERROR') badgeHtml = '<span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #d8b4fe; border: 1px solid #a855f7;">🟣 ERROR</span>';
      else badgeHtml = '<span class="badge badge-red">🔴 SURVIVED</span>';

      tr.innerHTML = `
        <td><code>${m.mutant_id ? m.mutant_id.substring(0, 16) : `M${idx + 1}`}</code></td>
        <td><span class="tag-type">${escapeHtml(m.mutation_type || 'AST_MOD')}</span></td>
        <td>Line ${m.line_number || '-'}</td>
        <td>${badgeHtml}</td>
        <td>${m.exec_duration_ms || m.execution_time_ms ? `${m.exec_duration_ms || m.execution_time_ms}ms` : '-'}</td>
      `;

      tr.addEventListener('click', () => {
        document.querySelectorAll('#mutants-table-body tr').forEach(r => r.classList.remove('selected'));
        tr.classList.add('selected');
        state.hardening.selectedMutant = m;
        inspectMutantDiff(m);
      });

      dom.mutantsTableBody.appendChild(tr);
    });

    // Auto inspect first mutant
    if (filtered.length > 0 && !state.hardening.selectedMutant) {
      state.hardening.selectedMutant = filtered[0];
      inspectMutantDiff(filtered[0]);
    }
  }

  // Filter Buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.hardening.filter = btn.getAttribute('data-filter');
      renderMutantsTable(state.hardening.mutants);
    });
  });

  function inspectMutantDiff(mutant) {
    if (!mutant) return;

    dom.diffSelectedMutantTitle.textContent = `AST Diff: ${mutant.mutant_id || 'Mutant'} (${mutant.mutation_type || 'AST_MOD'}) at line ${mutant.line_number || '-'}`;
    const st = (mutant.status || 'SURVIVED').toUpperCase();
    if (st === 'KILLED') {
      dom.diffStatusBadge.textContent = '🟢 KILLED BY ASSERTION';
      dom.diffStatusBadge.className = 'badge badge-green';
      dom.diffStatusBadge.style.cssText = '';
    } else if (st === 'EQUIVALENT') {
      dom.diffStatusBadge.textContent = '🔵 VERIFIED EQUIVALENT';
      dom.diffStatusBadge.className = 'badge';
      dom.diffStatusBadge.style.cssText = 'background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid #3b82f6;';
    } else if (st === 'POTENTIALLY_EQUIVALENT') {
      dom.diffStatusBadge.textContent = '🟡 POTENTIALLY EQUIVALENT';
      dom.diffStatusBadge.className = 'badge';
      dom.diffStatusBadge.style.cssText = 'background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid #f59e0b;';
    } else if (st === 'TIMEOUT') {
      dom.diffStatusBadge.textContent = '🟠 TIMEOUT (INFINITE LOOP)';
      dom.diffStatusBadge.className = 'badge';
      dom.diffStatusBadge.style.cssText = 'background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid #f97316;';
    } else if (st === 'INVALID') {
      dom.diffStatusBadge.textContent = '⚪ INVALID AST SYNTAX';
      dom.diffStatusBadge.className = 'badge';
      dom.diffStatusBadge.style.cssText = 'background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid #94a3b8;';
    } else {
      dom.diffStatusBadge.textContent = '🔴 SURVIVED (CRITIQUE REQUIRED)';
      dom.diffStatusBadge.className = 'badge badge-red';
      dom.diffStatusBadge.style.cssText = '';
    }

    let diffContent = '';
    const rawDiff = mutant.diff || mutant.unified_diff;
    if (rawDiff) {
      diffContent = colorizeDiff(rawDiff);
    } else if (mutant.original_line && mutant.mutated_line) {
      const syntheticDiff = `--- Original (Line ${mutant.line_number})\n+++ Mutated\n- ${mutant.original_line}\n+ ${mutant.mutated_line}`;
      diffContent = colorizeDiff(syntheticDiff);
    } else {
      diffContent = `<pre class="diff-pre">Mutant details:\nType: ${escapeHtml(mutant.mutation_type || 'AST_MOD')}\nLine: ${mutant.line_number}\nStatus: ${escapeHtml(mutant.status)}</pre>`;
    }

    if (mutant.equivalence_method || mutant.equivalence_reason || mutant.original_expression) {
      const eqMetaBox = `
        <div style="margin-bottom: 0.8rem; padding: 0.6rem; background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; font-size: 0.8rem;">
          <div style="font-weight: 600; color: #60a5fa; margin-bottom: 0.3rem;">⚖️ Equivalence Analysis (Milestone 2)</div>
          <div><strong>Status:</strong> ${escapeHtml(mutant.equivalence_status || mutant.status || 'UNKNOWN')}</div>
          <div><strong>Method:</strong> ${escapeHtml(mutant.equivalence_method || 'STATIC')} (${escapeHtml(mutant.equivalence_confidence || 'MEDIUM')} Confidence)</div>
          <div><strong>Reason:</strong> ${escapeHtml(mutant.equivalence_reason || 'N/A')}</div>
          ${mutant.original_expression ? `<div><strong>Original Expr:</strong> <code>${escapeHtml(mutant.original_expression)}</code></div>` : ''}
          ${mutant.mutated_expression ? `<div><strong>Mutated Expr:</strong> <code>${escapeHtml(mutant.mutated_expression)}</code></div>` : ''}
          <div><strong>Executed:</strong> ${mutant.is_executed ? 'Yes' : 'No (Statically Inferred)'}</div>
        </div>
      `;
      dom.diffCodeDisplay.innerHTML = eqMetaBox + diffContent;
    } else {
      dom.diffCodeDisplay.innerHTML = diffContent;
    }
  }

  function colorizeDiff(diffText) {
    const lines = diffText.split('\n');
    return lines.map(line => {
      const escaped = escapeHtml(line);
      if (line.startsWith('+') && !line.startsWith('+++')) {
        return `<span class="diff-add">${escaped}</span>`;
      }
      if (line.startsWith('-') && !line.startsWith('---')) {
        return `<span class="diff-remove">${escaped}</span>`;
      }
      if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) {
        return `<span class="diff-header-line">${escaped}</span>`;
      }
      return escaped;
    }).join('\n');
  }

  async function fetchHardenedSuiteCode() {
    try {
      const res = await fetch('/api/hardened-code');
      const data = await res.json();
      if (data.exists && data.code) {
        dom.hardenedSuiteCode.textContent = data.code;
        state.hardening.testHardenedCode = data.code;
      }
    } catch (err) {
      console.warn('Failed to read hardened suite:', err);
    }
  }

  if (dom.btnCopyHardenedSuite) {
    dom.btnCopyHardenedSuite.addEventListener('click', () => {
      copyTextToClipboard(dom.hardenedSuiteCode.textContent, dom.btnCopyHardenedSuite, '📋 Copy Suite');
    });
  }

  if (dom.btnDownloadHardenedSuite) {
    dom.btnDownloadHardenedSuite.addEventListener('click', () => {
      const code = dom.hardenedSuiteCode.textContent;
      if (!code) return;

      const blob = new Blob([code], { type: 'text/x-python' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'test_hardened.py';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('Downloaded test_hardened.py!', 'success');
    });
  }

  // =========================================================================
  // Live Wiretap & WebSocket Streaming Hub (Milestone 3)
  // =========================================================================
  if (dom.btnRefreshWiretap) {
    dom.btnRefreshWiretap.addEventListener('click', fetchWiretap);
  }

  function initWebSocketEventStream() {
    if (state.ws.socket && (state.ws.socket.readyState === WebSocket.OPEN || state.ws.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/events`;
      const socket = new WebSocket(wsUrl);
      state.ws.socket = socket;

      if (dom.wiretapWsStatusBadge) {
        dom.wiretapWsStatusBadge.textContent = '⚡ Connecting...';
        dom.wiretapWsStatusBadge.className = 'badge badge-amber';
      }

      socket.onopen = () => {
        state.ws.isConnected = true;
        state.ws.reconnectAttempts = 0;
        if (state.ws.reconnectTimer) {
          clearTimeout(state.ws.reconnectTimer);
          state.ws.reconnectTimer = null;
        }
        if (state.ws.pollingInterval) {
          clearInterval(state.ws.pollingInterval);
          state.ws.pollingInterval = null;
        }
        if (dom.wiretapWsStatusBadge) {
          dom.wiretapWsStatusBadge.textContent = '⚡ Live Streaming';
          dom.wiretapWsStatusBadge.className = 'badge badge-green';
        }
      };

      socket.onmessage = (event) => {
        try {
          const ev = JSON.parse(event.data);
          if (!ev || ev.event_type === 'HUB_CONNECTED' || ev.event_type === 'PONG') {
            return;
          }
          if (ev.event_id && state.ws.seenEventIds.has(ev.event_id)) {
            return;
          }
          if (ev.event_id) {
            state.ws.seenEventIds.add(ev.event_id);
            if (state.ws.seenEventIds.size > 500) {
              const iter = state.ws.seenEventIds.values();
              state.ws.seenEventIds.delete(iter.next().value);
            }
          }
          appendLiveWiretapEvent(ev);
        } catch (parseErr) {
          console.warn('[WS Parse Error]', parseErr);
        }
      };

      socket.onerror = () => {
        state.ws.isConnected = false;
      };

      socket.onclose = () => {
        state.ws.isConnected = false;
        state.ws.socket = null;
        handleWebSocketDisconnect();
      };
    } catch (err) {
      console.warn('[WS Connect Error]', err);
      handleWebSocketDisconnect();
    }
  }

  function handleWebSocketDisconnect() {
    if (state.ws.reconnectAttempts < state.ws.maxReconnectAttempts) {
      state.ws.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(1.5, state.ws.reconnectAttempts), 8000);
      if (dom.wiretapWsStatusBadge) {
        dom.wiretapWsStatusBadge.textContent = `🔌 Reconnecting (${state.ws.reconnectAttempts}/${state.ws.maxReconnectAttempts})...`;
        dom.wiretapWsStatusBadge.className = 'badge badge-amber';
      }
      state.ws.reconnectTimer = setTimeout(initWebSocketEventStream, delay);
    } else {
      // Reconnect limit reached; fallback to polling
      if (dom.wiretapWsStatusBadge) {
        dom.wiretapWsStatusBadge.textContent = '🔄 Polling Fallback';
        dom.wiretapWsStatusBadge.className = 'badge badge-cyan';
      }
      if (!state.ws.pollingInterval) {
        state.ws.pollingInterval = setInterval(fetchWiretap, 3000);
      }
    }
  }

  function disconnectWebSocket() {
    if (state.ws.reconnectTimer) {
      clearTimeout(state.ws.reconnectTimer);
      state.ws.reconnectTimer = null;
    }
    state.ws.reconnectAttempts = state.ws.maxReconnectAttempts;
    if (state.ws.socket) {
      state.ws.socket.close();
      state.ws.socket = null;
    }
    state.ws.isConnected = false;
    handleWebSocketDisconnect();
  }

  function buildWiretapCardElement(ev) {
    const card = document.createElement('div');
    const etype = ev.event_type || ev._kind || 'EVENT';
    const d = ev.payload || ev.data || {};
    const timeStr = ev.timestamp ? new Date(ev.timestamp * 1000).toLocaleTimeString() : '';

    if (etype === 'AGENT_HANDOFF') {
      card.className = 'wiretap-step-card step-handoff';
      const fromAg = d.from_agent || ev.emitter || 'SourceAgent';
      const toAg = d.to_agent || 'TargetAgent';
      const summary = d.summary || 'State payload transfer';
      const iter = d.iteration != null ? `Loop ${d.iteration}` : 'Lifecycle';

      card.innerHTML = `
        <div class="step-header">
          <div class="step-agents">
            <span class="agent-badge agent-from">${escapeHtml(fromAg)}</span>
            <span class="handoff-arrow">➔</span>
            <span class="agent-badge agent-to">${escapeHtml(toAg)}</span>
          </div>
          <div class="step-meta">
            <span class="badge badge-cyan">${iter}</span>
            <span class="step-time">${timeStr}</span>
          </div>
        </div>
        <div class="step-body">
          <p class="step-summary">${escapeHtml(summary)}</p>
          ${d.payload || d.details ? `
            <details class="payload-details">
              <summary>Inspect Contract Payload (${Object.keys(d.payload || d.details || {}).length} keys)</summary>
              <pre class="json-code">${escapeHtml(JSON.stringify(d.payload || d.details, null, 2))}</pre>
            </details>
          ` : ''}
        </div>
      `;
    } else if (etype === 'ADK_TOOL_CALL' || etype === 'TOOL_START' || etype === 'TOOL_COMPLETE') {
      card.className = 'wiretap-step-card step-adk';
      const agent = d.agent || ev.emitter || 'ADK Engine';
      const tool = d.tool_name || 'Tool';
      const summary = d.summary || (etype === 'TOOL_COMPLETE' ? `Tool ${tool} completed in ${d.duration_ms || 0}ms` : `Invoked tool ${tool}`);

      card.innerHTML = `
        <div class="step-header">
          <div class="step-agents">
            <span class="agent-badge agent-tool">🛠️ ${escapeHtml(agent)} &bull; ${escapeHtml(tool)}</span>
          </div>
          <div class="step-meta">
            <span class="badge badge-amber">${etype}</span>
            <span class="step-time">${timeStr}</span>
          </div>
        </div>
        <div class="step-body">
          <p class="step-summary">${escapeHtml(summary)}</p>
          ${d.args || d.result || d.arguments ? `
            <details class="payload-details">
              <summary>Inspect Parameters & Output</summary>
              <pre class="json-code">${escapeHtml(JSON.stringify(d.args || d.result || d.arguments, null, 2))}</pre>
            </details>
          ` : ''}
        </div>
      `;
    } else if (etype === 'STATE_CHANGE') {
      card.className = 'wiretap-step-card step-state';
      const comp = d.component || ev.emitter || 'System';
      const fromSt = d.from_state || 'IDLE';
      const toSt = d.to_state || 'ACTIVE';
      const iter = d.iteration != null ? `Loop ${d.iteration}` : 'System';

      card.innerHTML = `
        <div class="step-header">
          <div class="step-agents">
            <span class="agent-badge agent-tool">🔄 ${escapeHtml(comp)}</span>
            <span class="handoff-arrow">➔</span>
            <span class="agent-badge agent-to">${escapeHtml(toSt)}</span>
          </div>
          <div class="step-meta">
            <span class="badge badge-green">${iter}</span>
            <span class="step-time">${timeStr}</span>
          </div>
        </div>
        <div class="step-body">
          <p class="step-summary">State transition from <strong>${escapeHtml(fromSt)}</strong> to <strong>${escapeHtml(toSt)}</strong></p>
        </div>
      `;
    } else {
      card.className = 'wiretap-step-card step-tool';
      const emitter = ev.emitter || 'TestForge';
      card.innerHTML = `
        <div class="step-header">
          <div class="step-agents">
            <span class="agent-badge agent-tool">⚡ ${escapeHtml(emitter)}</span>
          </div>
          <div class="step-meta">
            <span class="badge badge-cyan">${escapeHtml(etype)}</span>
            <span class="step-time">${timeStr}</span>
          </div>
        </div>
        <div class="step-body">
          <p class="step-summary">${escapeHtml(d.summary || d.message || `Event ${etype}`)}</p>
          ${Object.keys(d).length > 0 ? `
            <details class="payload-details">
              <summary>Inspect Event Payload</summary>
              <pre class="json-code">${escapeHtml(JSON.stringify(d, null, 2))}</pre>
            </details>
          ` : ''}
        </div>
      `;
    }

    return card;
  }

  function appendLiveWiretapEvent(ev) {
    if (!dom.wiretapTimelineContainer) return;

    // Remove empty callout if present
    const callout = dom.wiretapTimelineContainer.querySelector('.info-callout');
    if (callout) {
      callout.remove();
    }

    const card = buildWiretapCardElement(ev);
    card.classList.add('anim-fade-in');
    dom.wiretapTimelineContainer.appendChild(card);

    // Update KPI counters
    const etype = ev.event_type || '';
    if (etype === 'AGENT_HANDOFF') {
      const cur = parseInt(dom.wiretapKpiHandoffs?.textContent || '0', 10);
      if (dom.wiretapKpiHandoffs) dom.wiretapKpiHandoffs.textContent = cur + 1;
    } else if (etype.startsWith('TOOL_') || etype === 'ADK_TOOL_CALL') {
      const cur = parseInt(dom.wiretapKpiAdk?.textContent || '0', 10);
      if (dom.wiretapKpiAdk) dom.wiretapKpiAdk.textContent = cur + 1;
    }

    // Scroll to bottom smoothly
    dom.wiretapTimelineContainer.scrollTop = dom.wiretapTimelineContainer.scrollHeight;
  }

  async function fetchWiretap() {
    try {
      dom.btnRefreshWiretap.disabled = true;
      dom.btnRefreshWiretap.innerHTML = '🔄 Fetching...';

      const res = await fetch('/api/wiretap');
      if (!res.ok) throw new Error('Wiretap fetch failed');
      const data = await res.json();

      dom.wiretapKpiHandoffs.textContent = data.total_handoffs || 0;
      dom.wiretapKpiAgents.textContent = (data.participating_agents || []).length;
      dom.wiretapKpiAdk.textContent = data.total_adk_calls || 0;

      const loops = new Set();
      (data.handoffs || []).forEach(h => {
        if (h.data && h.data.iteration != null) loops.add(h.data.iteration);
      });
      dom.wiretapKpiLoops.textContent = loops.size || 1;

      renderWiretapTimeline(data.handoffs || [], data.adk_calls || []);
    } catch (err) {
      showToast(`Wiretap fetch error: ${err.message}`, 'error');
    } finally {
      dom.btnRefreshWiretap.disabled = false;
      dom.btnRefreshWiretap.innerHTML = '🔄 Refresh Wiretap';
    }
  }

  function renderWiretapTimeline(handoffs, adkCalls) {
    if (!dom.wiretapTimelineContainer) return;

    if (handoffs.length === 0 && adkCalls.length === 0) {
      if (dom.wiretapTimelineContainer.children.length === 0) {
        dom.wiretapTimelineContainer.innerHTML = `
          <div class="info-callout">
            No agent handoffs or ADK tool deliberations logged yet. Run a hardening pipeline to capture live agent interactions!
          </div>
        `;
      }
      return;
    }

    const allEvents = [
      ...handoffs.map(h => ({ ...h, _kind: 'HANDOFF' })),
      ...adkCalls.map(a => ({ ...a, _kind: 'ADK' })),
    ].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

    // Clear existing only if refreshing full list
    dom.wiretapTimelineContainer.innerHTML = '';
    allEvents.forEach((ev) => {
      const card = buildWiretapCardElement(ev);
      dom.wiretapTimelineContainer.appendChild(card);
      const evId = ev.event_id || (ev.data && ev.data.event_id);
      if (evId) state.ws.seenEventIds.add(evId);
    });
  }

  // =========================================================================
  // Telemetry & Observability Trace
  // =========================================================================
  if (dom.btnRefreshTelemetry) {
    dom.btnRefreshTelemetry.addEventListener('click', fetchTelemetry);
  }

  async function fetchTelemetry() {
    try {
      dom.btnRefreshTelemetry.disabled = true;
      dom.btnRefreshTelemetry.innerHTML = '🔄 Fetching...';

      const res = await fetch('/api/telemetry');
      if (!res.ok) throw new Error('Telemetry fetch failed');
      const data = await res.json();

      dom.telemKpiEvents.textContent = data.total_logged_events || 0;
      dom.telemKpiTokens.textContent = (data.total_tokens_used || 0).toLocaleString();

      renderTelemetryTable(data.recent_llm_calls || []);
    } catch (err) {
      showToast(`Telemetry fetch error: ${err.message}`, 'error');
    } finally {
      dom.btnRefreshTelemetry.disabled = false;
      dom.btnRefreshTelemetry.innerHTML = '🔄 Refresh Telemetry';
    }
  }

  function renderTelemetryTable(calls) {
    if (!dom.telemetryTableBody) return;

    if (calls.length === 0) {
      dom.telemetryTableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No LLM inference calls logged yet.</td></tr>';
      return;
    }

    dom.telemetryTableBody.innerHTML = '';
    calls.forEach(c => {
      const d = c.data || {};
      const tr = document.createElement('tr');

      const isAstValid = d.ast_valid !== false;
      const latencyStr = d.latency_ms ? `${d.latency_ms}ms` : (d.latency ? `${(d.latency * 1000).toFixed(0)}ms` : '-');

      tr.innerHTML = `
        <td><strong class="text-primary">${escapeHtml(d.agent || 'Agent')}</strong></td>
        <td><code>${escapeHtml(d.model || d.provider || state.settings.modelName)}</code></td>
        <td>Cycle ${d.iteration != null ? d.iteration : '-'}</td>
        <td>${latencyStr}</td>
        <td>${d.prompt_tokens || 0}</td>
        <td>${d.completion_tokens || 0}</td>
        <td><strong>${d.total_tokens || 0}</strong></td>
        <td><span class="badge ${isAstValid ? 'badge-green' : 'badge-red'}">${isAstValid ? 'VALID' : 'INVALID'}</span></td>
      `;
      dom.telemetryTableBody.appendChild(tr);
    });
  }

  // =========================================================================
  // Benchmark & Ablation Study Controller
  // =========================================================================
  if (dom.btnRefreshBenchmark) {
    dom.btnRefreshBenchmark.addEventListener('click', fetchBenchmarkResults);
  }

  if (dom.btnRunBenchmark) {
    dom.btnRunBenchmark.addEventListener('click', runBenchmarkWorkflow);
  }

  async function fetchBenchmarkResults() {
    try {
      if (dom.btnRefreshBenchmark) {
        dom.btnRefreshBenchmark.disabled = true;
        dom.btnRefreshBenchmark.innerHTML = '🔄 Fetching...';
      }

      const res = await fetch('/api/benchmark/results');
      if (!res.ok) throw new Error('Benchmark results fetch failed');
      const data = await res.json();

      if (data.exists && data.report) {
        renderBenchmarkReport(data.report);
      } else {
        if (dom.benchmarkSummaryTableBody) {
          dom.benchmarkSummaryTableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No benchmark records found. Click "Run Benchmark" to execute!</td></tr>';
        }
      }
    } catch (err) {
      showToast(`Benchmark fetch error: ${err.message}`, 'error');
    } finally {
      if (dom.btnRefreshBenchmark) {
        dom.btnRefreshBenchmark.disabled = false;
        dom.btnRefreshBenchmark.innerHTML = '🔄 Refresh Results';
      }
    }
  }

  function renderBenchmarkReport(report) {
    if (!report) return;

    // 1. Render scenario summary table
    if (dom.benchmarkSummaryTableBody) {
      const summaries = report.scenario_summaries || {};
      const keys = Object.keys(summaries);
      const runs = report.runs || [];

      if (keys.length > 0) {
        dom.benchmarkSummaryTableBody.innerHTML = '';
        keys.forEach(scName => {
          const s = summaries[scName];
          const tr = document.createElement('tr');
          const isReflection = scName.includes('reflection');
          const isZeroShot = scName.includes('zeroshot');
          const badgeClass = isReflection ? 'badge-cyan' : (isZeroShot ? 'badge-purple' : 'badge-emerald');

          tr.innerHTML = `
            <td><strong class="text-primary">${escapeHtml(s.scenario || scName)}</strong></td>
            <td>${s.runs_completed || 1} / ${report.repetitions || 1}</td>
            <td><strong>${(s.mean_duration_sec || s.duration_sec || 0).toFixed(2)}s</strong></td>
            <td>±${(s.stddev_duration_sec || 0).toFixed(2)}s</td>
            <td><span class="badge ${badgeClass}">${(s.mean_mutation_score || s.mutation_score || 0).toFixed(1)}%</span></td>
            <td>${(s.mean_line_coverage || s.line_coverage || 0).toFixed(1)}%</td>
            <td>${(s.total_tokens_consumed || s.tokens || 0).toLocaleString()}</td>
            <td><strong class="text-amber">$${(s.estimated_total_cost_usd || 0).toFixed(5)}</strong></td>
          `;
          dom.benchmarkSummaryTableBody.appendChild(tr);
        });
      } else if (runs.length > 0) {
        dom.benchmarkSummaryTableBody.innerHTML = '';
        runs.forEach(r => {
          const scName = r.run_type || r.scenario || 'run';
          const tr = document.createElement('tr');
          const isReflection = scName.includes('reflection');
          const isZeroShot = scName.includes('zeroshot');
          const badgeClass = isReflection ? 'badge-cyan' : (isZeroShot ? 'badge-purple' : 'badge-emerald');

          const mutScore = r.mutation_score_pct != null ? r.mutation_score_pct : (r.metrics && r.metrics.calculated ? r.metrics.calculated.mutation_score_pct : 0);
          const lineCov = r.line_coverage_pct != null ? r.line_coverage_pct : (r.metrics && r.metrics.calculated ? r.metrics.calculated.line_coverage_pct : 0);
          const duration = r.latency_seconds != null ? r.latency_seconds : (r.metrics && r.metrics.measured ? r.metrics.measured.duration_seconds : 0);
          const tokens = r.tokens_used != null ? r.tokens_used : (r.metrics && r.metrics.measured ? r.metrics.measured.total_tokens : 0);

          tr.innerHTML = `
            <td><strong class="text-primary">${escapeHtml(scName)}</strong></td>
            <td>1 / 1</td>
            <td><strong>${Number(duration).toFixed(2)}s</strong></td>
            <td>±0.00s</td>
            <td><span class="badge ${badgeClass}">${Number(mutScore).toFixed(1)}%</span></td>
            <td>${Number(lineCov).toFixed(1)}%</td>
            <td>${Number(tokens).toLocaleString()}</td>
            <td><strong class="text-amber">$${((tokens / 1000) * 0.00015).toFixed(5)}</strong></td>
          `;
          dom.benchmarkSummaryTableBody.appendChild(tr);
        });
      } else {
        dom.benchmarkSummaryTableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No benchmark records found. Click "Run Benchmark" to execute!</td></tr>';
      }
    }

    // 2. Populate Metric Categorization details
    const allRuns = report.runs || [];
    if (allRuns.length > 0) {
      const lastRun = allRuns[allRuns.length - 1];
      const m = lastRun.metrics || {};

      if (dom.benchMeasuredDetails) {
        dom.benchMeasuredDetails.textContent = JSON.stringify(m.measured || {}, null, 2);
      }
      if (dom.benchCalculatedDetails) {
        dom.benchCalculatedDetails.textContent = JSON.stringify(m.calculated || {}, null, 2);
      }
      if (dom.benchEstimatedDetails) {
        dom.benchEstimatedDetails.textContent = JSON.stringify(m.estimated || {}, null, 2);
      }
    }

    // 3. Populate Markdown preview (Formatted & Raw)
    if (dom.benchMarkdownPreview) {
      fetch('/api/benchmark/markdown')
        .then(r => r.text())
        .then(text => {
          let cleanMd = text;
          if (cleanMd.includes('<pre>') && cleanMd.includes('</pre>')) {
            const temp = document.createElement('div');
            temp.innerHTML = cleanMd;
            cleanMd = temp.textContent || cleanMd;
          }
          dom.benchMarkdownPreview.textContent = cleanMd;
          if (dom.benchRenderedMarkdownView) {
            dom.benchRenderedMarkdownView.innerHTML = renderMarkdownReport(cleanMd);
          }
        })
        .catch(() => {
          dom.benchMarkdownPreview.textContent = JSON.stringify(report, null, 2);
          if (dom.benchRenderedMarkdownView) {
            dom.benchRenderedMarkdownView.innerHTML = '<p class="text-muted">Error loading benchmark report preview.</p>';
          }
        });
    }
  }

  function renderMarkdownReport(md) {
    if (!md || md.trim().startsWith('Run a benchmark')) {
      return '<p class="text-muted" style="font-size: 0.85rem; margin: 0;">Run a benchmark to preview the generated statistical report.</p>';
    }
    const lines = md.split('\n');
    let html = '';
    let inTable = false;
    let tableRows = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      if (line.startsWith('# ')) {
        html += `<h4 class="md-heading" style="color: #f8fafc; font-size: 1rem; margin-bottom: 0.5rem;">${escapeHtml(line.substring(2))}</h4>`;
      } else if (line.startsWith('## ')) {
        html += `<h5 class="md-subheading" style="margin-top: 1rem; margin-bottom: 0.5rem; color: var(--accent-cyan); font-size: 0.88rem;">${escapeHtml(line.substring(3))}</h5>`;
      } else if (line.startsWith('- **Target File:**') || line.startsWith('- **Timestamp:**') || line.startsWith('- **Repetitions') || line.startsWith('- **Hardware')) {
        const parts = line.split(':');
        const label = parts[0].replace(/^- \*\*/, '').replace(/\*\*$/, '');
        const val = parts.slice(1).join(':').trim();
        html += `<div style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.2rem;"><strong style="color: #cbd5e1;">${escapeHtml(label)}:</strong> ${escapeHtml(val)}</div>`;
      } else if (line.startsWith('|') && line.endsWith('|')) {
        if (line.includes('---')) continue;
        const cells = line.split('|').filter((_, idx, arr) => idx > 0 && idx < arr.length - 1).map(c => c.trim());
        if (!inTable) {
          inTable = true;
          tableRows = [];
          tableRows.push(`<thead><tr>${cells.map(c => `<th style="padding: 6px 10px; font-size: 0.74rem; text-align: left; background: rgba(30,41,59,0.9); color: #93c5fd; border-bottom: 1px solid rgba(255,255,255,0.1);">${escapeHtml(c)}</th>`).join('')}</tr></thead><tbody>`);
        } else {
          tableRows.push(`<tr>${cells.map(c => `<td style="padding: 6px 10px; font-size: 0.76rem; border-top: 1px solid rgba(255,255,255,0.05); color: #e2e8f0;">${escapeHtml(c)}</td>`).join('')}</tr>`);
        }
      } else if (inTable && !line.startsWith('|')) {
        inTable = false;
        html += `<div style="overflow-x:auto; margin: 0.75rem 0; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px;"><table class="table" style="width:100%; border-collapse: collapse;">${tableRows.join('')}</tbody></table></div>`;
      } else if (line.startsWith('>')) {
        if (!line.includes('[!NOTE]')) {
          html += `<div class="info-callout" style="margin-top: 0.5rem; font-size: 0.78rem; padding: 0.5rem 0.75rem; background: rgba(6,182,212,0.08); border-left: 3px solid var(--accent-cyan); border-radius: 4px;">${escapeHtml(line.replace(/^>\s*/, ''))}</div>`;
        }
      }
    }
    if (inTable) {
      html += `<div style="overflow-x:auto; margin: 0.75rem 0; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px;"><table class="table" style="width:100%; border-collapse: collapse;">${tableRows.join('')}</tbody></table></div>`;
    }
    return html;
  }

  // Benchmark Markdown toggle listeners
  if (dom.btnBenchMdRendered && dom.btnBenchMdRaw) {
    dom.btnBenchMdRendered.addEventListener('click', () => {
      dom.btnBenchMdRendered.classList.add('active');
      dom.btnBenchMdRendered.classList.remove('btn-outline');
      dom.btnBenchMdRaw.classList.remove('active');
      dom.btnBenchMdRaw.classList.add('btn-outline');
      if (dom.benchRenderedMarkdownView) dom.benchRenderedMarkdownView.classList.remove('hidden');
      if (dom.benchRawMarkdownContainer) dom.benchRawMarkdownContainer.classList.add('hidden');
    });

    dom.btnBenchMdRaw.addEventListener('click', () => {
      dom.btnBenchMdRaw.classList.add('active');
      dom.btnBenchMdRaw.classList.remove('btn-outline');
      dom.btnBenchMdRendered.classList.remove('active');
      dom.btnBenchMdRendered.classList.add('btn-outline');
      if (dom.benchRenderedMarkdownView) dom.benchRenderedMarkdownView.classList.add('hidden');
      if (dom.benchRawMarkdownContainer) dom.benchRawMarkdownContainer.classList.remove('hidden');
    });
  }

  async function runBenchmarkWorkflow() {
    const scenarios = [];
    if (dom.benchScBaseline && dom.benchScBaseline.checked) scenarios.push('baseline');
    if (dom.benchScZeroshot && dom.benchScZeroshot.checked) scenarios.push('zeroshot');
    if (dom.benchScRefl && dom.benchScRefl.checked) scenarios.push('agentic_reflection');

    if (scenarios.length === 0) {
      showToast('Select at least one scenario to benchmark!', 'warning');
      return;
    }

    const repetitions = parseInt(dom.benchRepetitions ? dom.benchRepetitions.value : '1', 10) || 1;
    const targetFile = dom.benchTargetSelect ? dom.benchTargetSelect.value : 'samples/discount.py';

    try {
      if (dom.btnRunBenchmark) {
        dom.btnRunBenchmark.disabled = true;
        dom.btnRunBenchmark.innerHTML = '⚡ Running Benchmark...';
      }

      if (dom.benchStatusAlert) {
        dom.benchStatusAlert.classList.remove('hidden');
        dom.benchStatusAlert.textContent = `🚀 Benchmark job launched: Evaluating [${scenarios.join(', ')}] on ${targetFile} (${repetitions} reps)...`;
      }

      const payload = {
        target_file_path: targetFile,
        scenarios: scenarios,
        repetitions: repetitions,
        engine_mode: state.settings.engineMode,
        model_name: state.settings.modelName,
      };

      const startRes = await fetch('/api/benchmark/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!startRes.ok) throw new Error(`Benchmark start failed (${startRes.status})`);
      const startData = await startRes.json();
      const jobId = startData.job_id;

      // Poll benchmark job until completion
      let finished = false;
      let attempts = 0;
      const maxAttempts = 120; // Up to 3 minutes

      while (!finished && attempts < maxAttempts) {
        attempts++;
        await new Promise(resolve => setTimeout(resolve, 1500));

        const jobRes = await fetch(`/api/benchmark/job/${jobId}`);
        if (!jobRes.ok) continue;
        const jobData = await jobRes.json();

        if (jobData.status === 'COMPLETED') {
          finished = true;
          if (dom.benchStatusAlert) {
            dom.benchStatusAlert.textContent = `✅ Benchmark completed in ${(attempts * 1.5).toFixed(1)}s!`;
          }
          showToast('Benchmark run completed!', 'success');
          renderBenchmarkReport(jobData.report);
        } else if (jobData.status === 'FAILED') {
          finished = true;
          if (dom.benchStatusAlert) {
            dom.benchStatusAlert.textContent = `❌ Benchmark failed: ${jobData.error || 'Unknown error'}`;
          }
          showToast(`Benchmark failed: ${jobData.error}`, 'error');
        } else {
          if (dom.benchStatusAlert) {
            dom.benchStatusAlert.textContent = `⏳ Running benchmark job (${(attempts * 1.5).toFixed(0)}s elapsed)...`;
          }
        }
      }

      if (!finished) {
        showToast('Benchmark timed out waiting for results.', 'warning');
      }
    } catch (err) {
      showToast(`Error running benchmark: ${err.message}`, 'error');
      if (dom.benchStatusAlert) {
        dom.benchStatusAlert.textContent = `❌ Error: ${err.message}`;
      }
    } finally {
      if (dom.btnRunBenchmark) {
        dom.btnRunBenchmark.disabled = false;
        dom.btnRunBenchmark.innerHTML = '🚀 Run Benchmark';
      }
    }
  }

  // =========================================================================
  // Milestone 1.3: Checkpoint Timeline, Diff Inspector & Recovery Controller
  // =========================================================================

  function getStageClass(stage) {
    if (!stage) return 'ingestion';
    const s = stage.toUpperCase();
    if (s.includes('INGESTION')) return 'ingestion';
    if (s.includes('BASELINE')) return 'baseline';
    if (s.includes('REFLECTION')) return 'reflection';
    if (s.includes('FINALIZED')) return 'finalized';
    if (s.includes('CANCELLED')) return 'cancelled';
    if (s.includes('TIMED_OUT')) return 'timed_out';
    return 'ingestion';
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatTimestamp(ts) {
    if (!ts) return 'Unknown';
    try {
      const d = new Date(ts * 1000);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + d.toLocaleDateString();
    } catch {
      return String(ts);
    }
  }

  async function fetchCheckpoints() {
    if (!dom.checkpointCardsStream) return;
    state.checkpoints.loading = true;

    if (dom.checkpointsLoadingState) dom.checkpointsLoadingState.classList.remove('hidden');
    if (dom.checkpointsEmptyState) dom.checkpointsEmptyState.classList.add('hidden');
    if (dom.checkpointsErrorAlert) dom.checkpointsErrorAlert.classList.add('hidden');

    try {
      const params = new URLSearchParams({ limit: '100', offset: '0' });
      const jobFilterVal = dom.cpJobFilter ? dom.cpJobFilter.value.trim() : '';
      if (jobFilterVal) params.append('job_id', jobFilterVal);

      const res = await fetch(`/api/checkpoints?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();

      let items = Array.isArray(data.checkpoints) ? data.checkpoints : [];

      // Apply client-side stage filter
      const stageFilter = dom.cpStageFilter ? dom.cpStageFilter.value : 'ALL';
      if (stageFilter !== 'ALL') {
        if (stageFilter === 'REFLECTION_ITERATION') {
          items = items.filter(c => c.stage && c.stage.startsWith('REFLECTION_ITERATION'));
        } else {
          items = items.filter(c => c.stage === stageFilter);
        }
      }

      // Apply client-side status filter
      const statusFilter = dom.cpStatusFilter ? dom.cpStatusFilter.value : 'ALL';
      if (statusFilter !== 'ALL') {
        items = items.filter(c => (c.status || '').toUpperCase() === statusFilter);
      }

      // Apply sorting
      const sortOrder = dom.cpSortOrder ? dom.cpSortOrder.value : 'newest';
      items.sort((a, b) => {
        const timeA = a.created_at || 0;
        const timeB = b.created_at || 0;
        return sortOrder === 'newest' ? timeB - timeA : timeA - timeB;
      });

      state.checkpoints.items = items;
      state.checkpoints.totalCount = data.total_count || items.length;

      if (dom.cpCountBadge) dom.cpCountBadge.textContent = String(items.length);
      renderCheckpointTimeline();

    } catch (err) {
      if (dom.checkpointsErrorAlert) {
        dom.checkpointsErrorAlert.textContent = `Failed to load checkpoints: ${err.message}`;
        dom.checkpointsErrorAlert.classList.remove('hidden');
      }
      showToast(`Error fetching checkpoints: ${err.message}`, 'error');
    } finally {
      state.checkpoints.loading = false;
      if (dom.checkpointsLoadingState) dom.checkpointsLoadingState.classList.add('hidden');
    }
  }

  function renderCheckpointTimeline() {
    const container = dom.checkpointCardsStream;
    if (!container) return;
    container.replaceChildren();

    const items = state.checkpoints.items;
    if (items.length === 0) {
      if (dom.checkpointsEmptyState) dom.checkpointsEmptyState.classList.remove('hidden');
      return;
    }
    if (dom.checkpointsEmptyState) dom.checkpointsEmptyState.classList.add('hidden');

    items.forEach(cp => {
      const card = document.createElement('div');
      card.className = 'checkpoint-card';
      card.setAttribute('data-id', cp.checkpoint_id);
      card.setAttribute('data-stage', cp.stage || '');

      if (state.checkpoints.selectedId === cp.checkpoint_id) {
        card.classList.add('active-inspected');
      }
      if (state.checkpoints.diffBaseId === cp.checkpoint_id) {
        card.classList.add('diff-base-selected');
      }
      if (state.checkpoints.diffTargetId === cp.checkpoint_id) {
        card.classList.add('diff-target-selected');
      }

      // Header row
      const headerRow = document.createElement('div');
      headerRow.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;';

      const leftHead = document.createElement('div');
      leftHead.style.cssText = 'display: flex; gap: 0.5rem; align-items: center;';

      const stageBadge = document.createElement('span');
      stageBadge.className = `stage-badge ${getStageClass(cp.stage)}`;
      stageBadge.textContent = cp.stage || 'UNKNOWN';

      const idSpan = document.createElement('code');
      idSpan.style.cssText = 'font-size: 0.78rem; color: #38bdf8; font-weight: 600;';
      idSpan.textContent = cp.checkpoint_id;

      leftHead.appendChild(stageBadge);
      leftHead.appendChild(idSpan);

      const timeSpan = document.createElement('span');
      timeSpan.style.cssText = 'font-size: 0.72rem; color: #94a3b8; font-family: var(--font-mono);';
      timeSpan.textContent = formatTimestamp(cp.created_at);

      headerRow.appendChild(leftHead);
      headerRow.appendChild(timeSpan);
      card.appendChild(headerRow);

      // Meta pills row
      const metaRow = document.createElement('div');
      metaRow.style.cssText = 'display: flex; gap: 0.6rem; flex-wrap: wrap; font-size: 0.75rem; color: #cbd5e1; margin-bottom: 0.6rem;';

      const revPill = document.createElement('span');
      revPill.textContent = `Rev: ${cp.revision ?? 0}`;
      metaRow.appendChild(revPill);

      if (cp.job_id) {
        const jobPill = document.createElement('span');
        jobPill.textContent = `Job: ${cp.job_id}`;
        metaRow.appendChild(jobPill);
      }

      const sizePill = document.createElement('span');
      sizePill.textContent = `Size: ${formatBytes(cp.snapshot_bytes)}`;
      metaRow.appendChild(sizePill);

      const statusPill = document.createElement('span');
      statusPill.style.color = cp.status === 'SUCCESS' ? '#34d399' : (cp.status === 'CANCELLED' ? '#fbbf24' : '#94a3b8');
      statusPill.textContent = `Status: ${cp.status || 'N/A'}`;
      metaRow.appendChild(statusPill);

      card.appendChild(metaRow);

      // Metrics preview if available
      const metrics = cp.metrics_summary || {};
      if (Object.keys(metrics).length > 0) {
        const metricBox = document.createElement('div');
        metricBox.style.cssText = 'background: rgba(0,0,0,0.3); padding: 0.35rem 0.6rem; border-radius: 4px; font-size: 0.72rem; color: #94a3b8; margin-bottom: 0.6rem; display: flex; gap: 0.8rem;';

        if (metrics.final_mutation_score !== undefined) {
          const mScore = document.createElement('span');
          mScore.textContent = `Mutation Score: ${metrics.final_mutation_score}%`;
          metricBox.appendChild(mScore);
        }
        if (metrics.lines_covered !== undefined) {
          const lCov = document.createElement('span');
          lCov.textContent = `Covered: ${metrics.lines_covered}`;
          metricBox.appendChild(lCov);
        }
        if (metrics.current_iteration !== undefined) {
          const iter = document.createElement('span');
          iter.textContent = `Iteration: ${metrics.current_iteration}`;
          metricBox.appendChild(iter);
        }
        card.appendChild(metricBox);
      }

      // Actions row
      const actionsRow = document.createElement('div');
      actionsRow.style.cssText = 'display: flex; gap: 0.4rem; align-items: center; justify-content: flex-end; padding-top: 0.4rem; border-top: 1px solid rgba(255,255,255,0.05);';

      const btnInspect = document.createElement('button');
      btnInspect.type = 'button';
      btnInspect.className = 'btn btn-xs btn-outline btn-cp-inspect';
      btnInspect.textContent = '🔍 Inspect';
      btnInspect.addEventListener('click', (e) => {
        e.stopPropagation();
        inspectCheckpoint(cp.checkpoint_id);
      });

      const btnBase = document.createElement('button');
      btnBase.type = 'button';
      btnBase.className = 'btn btn-xs btn-outline btn-cp-set-base';
      btnBase.textContent = state.checkpoints.diffBaseId === cp.checkpoint_id ? '✓ Base (A)' : 'Set Base (A)';
      btnBase.style.color = '#93c5fd';
      btnBase.addEventListener('click', (e) => {
        e.stopPropagation();
        setDiffBase(cp.checkpoint_id);
      });

      const btnTarget = document.createElement('button');
      btnTarget.type = 'button';
      btnTarget.className = 'btn btn-xs btn-outline btn-cp-set-target';
      btnTarget.textContent = state.checkpoints.diffTargetId === cp.checkpoint_id ? '✓ Target (B)' : 'Set Target (B)';
      btnTarget.style.color = '#86efac';
      btnTarget.addEventListener('click', (e) => {
        e.stopPropagation();
        setDiffTarget(cp.checkpoint_id);
      });

      const btnRestore = document.createElement('button');
      btnRestore.type = 'button';
      btnRestore.className = 'btn btn-xs btn-outline btn-cp-restore';
      btnRestore.textContent = '↩ Restore...';
      btnRestore.style.color = '#fde047';
      btnRestore.addEventListener('click', (e) => {
        e.stopPropagation();
        openRestoreModal(cp.checkpoint_id, cp.stage, cp.revision, cp.created_at);
      });

      actionsRow.appendChild(btnInspect);
      actionsRow.appendChild(btnBase);
      actionsRow.appendChild(btnTarget);
      actionsRow.appendChild(btnRestore);
      card.appendChild(actionsRow);

      // Click card to inspect
      card.addEventListener('click', () => {
        inspectCheckpoint(cp.checkpoint_id);
      });

      container.appendChild(card);
    });
  }

  async function inspectCheckpoint(checkpointId) {
    state.checkpoints.selectedId = checkpointId;
    renderCheckpointTimeline(); // updates card active highlight

    if (dom.cpDetailEmptyPlaceholder) dom.cpDetailEmptyPlaceholder.classList.add('hidden');
    if (dom.cpDetailContent) {
      dom.cpDetailContent.classList.remove('hidden');
      dom.cpDetailContent.replaceChildren();

      const loadingP = document.createElement('p');
      loadingP.className = 'text-muted';
      loadingP.style.cssText = 'padding: 1.5rem; text-align: center;';
      loadingP.textContent = `Loading checkpoint details for ${checkpointId}...`;
      dom.cpDetailContent.appendChild(loadingP);
    }

    // Switch right view to Detail
    switchCheckpointSubtab('detail');

    try {
      const res = await fetch(`/api/checkpoints/${checkpointId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();

      renderCheckpointDetails(data);

      // Also populate Raw JSON view
      if (dom.checkpointRawJsonDisplay) {
        dom.checkpointRawJsonDisplay.textContent = JSON.stringify(data.snapshot || data, null, 2);
      }
      if (dom.rawJsonTitle) {
        dom.rawJsonTitle.textContent = `Snapshot Payload (${checkpointId})`;
      }
    } catch (err) {
      if (dom.cpDetailContent) {
        dom.cpDetailContent.replaceChildren();
        const errDiv = document.createElement('div');
        errDiv.className = 'alert danger';
        errDiv.textContent = `Error inspecting checkpoint: ${err.message}`;
        dom.cpDetailContent.appendChild(errDiv);
      }
      showToast(`Inspect error: ${err.message}`, 'error');
    }
  }

  function renderCheckpointDetails(data) {
    const container = dom.cpDetailContent;
    if (!container) return;
    container.replaceChildren();

    const meta = data.metadata || {};

    // Header Card
    const headerBox = document.createElement('div');
    headerBox.style.cssText = 'background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 1rem;';

    const topRow = document.createElement('div');
    topRow.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;';

    const titleH = document.createElement('h4');
    titleH.style.cssText = 'margin: 0; font-size: 1rem; color: #f8fafc; display: flex; align-items: center; gap: 0.5rem;';
    const stBadge = document.createElement('span');
    stBadge.className = `stage-badge ${getStageClass(meta.stage)}`;
    stBadge.textContent = meta.stage || 'STAGE';
    const idCode = document.createElement('code');
    idCode.style.color = '#38bdf8';
    idCode.textContent = meta.checkpoint_id;
    titleH.appendChild(stBadge);
    titleH.appendChild(idCode);

    const timeP = document.createElement('span');
    timeP.style.cssText = 'font-size: 0.78rem; color: #94a3b8; font-family: var(--font-mono);';
    timeP.textContent = formatTimestamp(meta.created_at);

    topRow.appendChild(titleH);
    topRow.appendChild(timeP);
    headerBox.appendChild(topRow);

    const metaLine = document.createElement('div');
    metaLine.style.cssText = 'font-size: 0.8rem; color: #cbd5e1; display: flex; gap: 1rem; flex-wrap: wrap;';
    metaLine.textContent = `Revision: ${meta.revision ?? 0} | Job: ${meta.job_id || 'None'} | Schema Version: ${meta.schema_version ?? 1}`;
    headerBox.appendChild(metaLine);
    container.appendChild(headerBox);

    // Partition 1: Target Space
    const target = data.target || {};
    const targetCard = document.createElement('div');
    targetCard.className = 'partition-card';
    const targetTitle = document.createElement('div');
    targetTitle.className = 'partition-card-title';
    targetTitle.textContent = '📁 Target Space (AST & Symbols)';
    targetCard.appendChild(targetTitle);

    const targetDetails = document.createElement('div');
    targetDetails.style.cssText = 'font-size: 0.8rem; color: #cbd5e1; line-height: 1.6;';

    const modP = document.createElement('div');
    modP.textContent = `Module: ${target.target_module_path || 'N/A'}`;
    const fileP = document.createElement('div');
    fileP.textContent = `File: ${target.target_file_path || 'N/A'}`;
    const funcsP = document.createElement('div');
    const funcsList = Array.isArray(target.functions) ? target.functions : [];
    funcsP.textContent = `Functions (${funcsList.length}): ${funcsList.join(', ') || 'None'}`;
    const classesP = document.createElement('div');
    const classesList = Array.isArray(target.classes) ? target.classes : [];
    classesP.textContent = `Classes (${classesList.length}): ${classesList.join(', ') || 'None'}`;

    targetDetails.appendChild(modP);
    targetDetails.appendChild(fileP);
    targetDetails.appendChild(funcsP);
    targetDetails.appendChild(classesP);
    targetCard.appendChild(targetDetails);
    container.appendChild(targetCard);

    // Partition 2: Test Suite Space
    const suite = data.suite || {};
    const suiteInfo = data.suite_info || {};
    const suiteCard = document.createElement('div');
    suiteCard.className = 'partition-card';
    const suiteTitle = document.createElement('div');
    suiteTitle.className = 'partition-card-title';
    suiteTitle.textContent = '🧪 Suite Space (Active Tests)';
    suiteCard.appendChild(suiteTitle);

    const suiteDetails = document.createElement('div');
    suiteDetails.style.cssText = 'font-size: 0.8rem; color: #cbd5e1; margin-bottom: 0.5rem;';
    suiteDetails.textContent = `Active Provider: ${suite.active_provider || suiteInfo.active_provider || 'N/A'} | Test Module: ${suite.test_module_path || suiteInfo.test_module_path || 'test_target.py'}`;
    suiteCard.appendChild(suiteDetails);

    const testCode = suite.current_test_code || '';
    if (testCode) {
      const codePre = document.createElement('pre');
      codePre.className = 'code-block';
      codePre.style.cssText = 'max-height: 180px; overflow-y: auto; font-size: 0.75rem;';
      const codeElem = document.createElement('code');
      codeElem.textContent = testCode;
      codePre.appendChild(codeElem);
      suiteCard.appendChild(codePre);
    } else {
      const noCode = document.createElement('p');
      noCode.className = 'text-muted';
      noCode.style.fontSize = '0.78rem';
      noCode.textContent = 'No synthesized test code at this checkpoint stage.';
      suiteCard.appendChild(noCode);
    }
    container.appendChild(suiteCard);

    // Partition 3: Mutant Space
    const mutant = data.mutant || {};
    const mutantSummary = data.mutant_summary || {};
    const mutantCard = document.createElement('div');
    mutantCard.className = 'partition-card';
    const mutantTitle = document.createElement('div');
    mutantTitle.className = 'partition-card-title';
    mutantTitle.textContent = '🧬 Mutant Space (AST Mutations)';
    mutantCard.appendChild(mutantTitle);

    const mutSummaryLine = document.createElement('div');
    mutSummaryLine.style.cssText = 'display: flex; gap: 0.8rem; font-size: 0.8rem; margin-bottom: 0.5rem; flex-wrap: wrap;';
    mutSummaryLine.innerHTML = `
      <span>Generated: <strong>${mutantSummary.generated ?? mutant.mutants_generated ?? 0}</strong></span>
      <span style="color: #34d399;">Killed: <strong>${mutantSummary.killed ?? mutant.mutants_killed ?? 0}</strong></span>
      <span style="color: #f87171;">Survived: <strong>${mutantSummary.survived ?? mutant.mutants_survived ?? 0}</strong></span>
      <span style="color: #60a5fa;">Equivalent: <strong>${mutant.mutants_equivalent ?? 0}</strong></span>
      <span style="color: #fbbf24;">Potentially Eq: <strong>${mutant.mutants_potentially_equivalent ?? 0}</strong></span>
    `;
    mutantCard.appendChild(mutSummaryLine);

    const mutantsList = Array.isArray(mutant.mutants) ? mutant.mutants : [];
    if (mutantsList.length > 0) {
      const mutTable = document.createElement('div');
      mutTable.style.cssText = 'max-height: 160px; overflow-y: auto; background: rgba(0,0,0,0.3); border-radius: 4px; padding: 0.4rem;';
      mutantsList.slice(0, 20).forEach(m => {
        const mRow = document.createElement('div');
        mRow.style.cssText = 'font-size: 0.74rem; font-family: var(--font-mono); padding: 2px 4px; border-bottom: 1px solid rgba(255,255,255,0.04); display: flex; justify-content: space-between;';
        const st = (m.status || (m.killed ? 'KILLED' : 'SURVIVED')).toUpperCase();
        let stColor = '#f87171';
        if (st === 'KILLED') stColor = '#34d399';
        else if (st === 'EQUIVALENT') stColor = '#60a5fa';
        else if (st === 'POTENTIALLY_EQUIVALENT') stColor = '#fbbf24';
        else if (st === 'TIMEOUT') stColor = '#fb923c';
        else if (st === 'INVALID') stColor = '#94a3b8';
        mRow.innerHTML = `<span><code>${escapeHtml(m.mutant_id)}</code> Line ${m.line_number}: ${escapeHtml(m.mutation_type || m.operator || 'MUT')}</span> <span style="color: ${stColor}; font-weight: 600;">${escapeHtml(st)}</span>`;
        mutTable.appendChild(mRow);
      });
      mutantCard.appendChild(mutTable);
    }
    container.appendChild(mutantCard);

    // Partition 4: Metrics Space
    const metrics = data.metrics || {};
    const metricsCard = document.createElement('div');
    metricsCard.className = 'partition-card';
    const metricsTitle = document.createElement('div');
    metricsTitle.className = 'partition-card-title';
    metricsTitle.textContent = '📊 Metrics Space (Hardening Convergence)';
    metricsCard.appendChild(metricsTitle);

    const metricsGrid = document.createElement('div');
    metricsGrid.style.cssText = 'display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; font-size: 0.8rem;';
    const rawScore = metrics.raw_mutation_score ?? metrics.final_mutation_score ?? 0;
    const adjScore = metrics.adjusted_mutation_score ?? rawScore;
    metricsGrid.innerHTML = `
      <div style="background: rgba(0,0,0,0.3); padding: 0.4rem 0.6rem; border-radius: 4px;">
        <span style="color: #94a3b8; font-size: 0.72rem; display: block;">Raw Score / Adj Score</span>
        <strong style="color: #38bdf8; font-size: 0.95rem;">${rawScore}% / <span style="color: #34d399;">${adjScore}%</span></strong>
      </div>
      <div style="background: rgba(0,0,0,0.3); padding: 0.4rem 0.6rem; border-radius: 4px;">
        <span style="color: #94a3b8; font-size: 0.72rem; display: block;">Lines Covered</span>
        <strong style="color: #34d399; font-size: 1rem;">${metrics.lines_covered ?? 0}</strong>
      </div>
      <div style="background: rgba(0,0,0,0.3); padding: 0.4rem 0.6rem; border-radius: 4px;">
        <span style="color: #94a3b8; font-size: 0.72rem; display: block;">Hardening Status</span>
        <strong style="color: #fcd34d; font-size: 0.85rem;">${metrics.final_hardening_status || 'IN_PROGRESS'}</strong>
      </div>
    `;
    metricsCard.appendChild(metricsGrid);
    container.appendChild(metricsCard);

    // Partition 5: Critic Space
    const critic = data.critic || {};
    const criticCard = document.createElement('div');
    criticCard.className = 'partition-card';
    const criticTitle = document.createElement('div');
    criticTitle.className = 'partition-card-title';
    criticTitle.textContent = '🧐 Critic Space (Adversarial Feedback)';
    criticCard.appendChild(criticTitle);

    const criticDetails = document.createElement('div');
    criticDetails.style.cssText = 'font-size: 0.8rem; color: #cbd5e1;';
    const directives = Array.isArray(critic.critic_directives) ? critic.critic_directives : [];
    if (directives.length > 0) {
      const dList = document.createElement('ul');
      dList.style.cssText = 'margin: 0; padding-left: 1.2rem;';
      directives.forEach(d => {
        const li = document.createElement('li');
        li.textContent = d;
        dList.appendChild(li);
      });
      criticDetails.appendChild(dList);
    } else {
      criticDetails.textContent = critic.notes || 'No adversarial directives recorded at this checkpoint.';
    }
    criticCard.appendChild(criticDetails);
    container.appendChild(criticCard);
  }

  function setDiffBase(checkpointId) {
    state.checkpoints.diffBaseId = checkpointId;
    if (dom.labelDiffBase) {
      dom.labelDiffBase.textContent = checkpointId;
      dom.labelDiffBase.classList.remove('text-muted');
      dom.labelDiffBase.style.color = '#93c5fd';
      dom.labelDiffBase.style.fontWeight = '600';
    }
    updateDiffButtonState();
    renderCheckpointTimeline();
    showToast(`Checkpoint ${checkpointId} selected as Base (A)`, 'info');
  }

  function setDiffTarget(checkpointId) {
    state.checkpoints.diffTargetId = checkpointId;
    if (dom.labelDiffTarget) {
      dom.labelDiffTarget.textContent = checkpointId;
      dom.labelDiffTarget.classList.remove('text-muted');
      dom.labelDiffTarget.style.color = '#86efac';
      dom.labelDiffTarget.style.fontWeight = '600';
    }
    updateDiffButtonState();
    renderCheckpointTimeline();
    showToast(`Checkpoint ${checkpointId} selected as Target (B)`, 'info');
  }

  function swapDiffSelection() {
    const temp = state.checkpoints.diffBaseId;
    state.checkpoints.diffBaseId = state.checkpoints.diffTargetId;
    state.checkpoints.diffTargetId = temp;

    if (dom.labelDiffBase) dom.labelDiffBase.textContent = state.checkpoints.diffBaseId || 'None selected';
    if (dom.labelDiffTarget) dom.labelDiffTarget.textContent = state.checkpoints.diffTargetId || 'None selected';

    updateDiffButtonState();
    renderCheckpointTimeline();

    if (state.checkpoints.diffBaseId && state.checkpoints.diffTargetId) {
      runCheckpointsDiff(state.checkpoints.diffBaseId, state.checkpoints.diffTargetId);
    }
  }

  function clearDiffSelection() {
    state.checkpoints.diffBaseId = null;
    state.checkpoints.diffTargetId = null;
    if (dom.labelDiffBase) {
      dom.labelDiffBase.textContent = 'None selected';
      dom.labelDiffBase.classList.add('text-muted');
      dom.labelDiffBase.style.color = '';
    }
    if (dom.labelDiffTarget) {
      dom.labelDiffTarget.textContent = 'None selected';
      dom.labelDiffTarget.classList.add('text-muted');
      dom.labelDiffTarget.style.color = '';
    }
    updateDiffButtonState();
    renderCheckpointTimeline();
  }

  function updateDiffButtonState() {
    const canDiff = !!(state.checkpoints.diffBaseId && state.checkpoints.diffTargetId && state.checkpoints.diffBaseId !== state.checkpoints.diffTargetId);
    if (dom.btnTriggerDiffModal) dom.btnTriggerDiffModal.disabled = !canDiff;
    if (dom.btnSwapDiffSelection) dom.btnSwapDiffSelection.disabled = !canDiff;
  }

  async function runCheckpointsDiff(baseId, targetId) {
    switchCheckpointSubtab('diff');

    if (dom.cpDiffEmptyPlaceholder) dom.cpDiffEmptyPlaceholder.classList.add('hidden');
    if (dom.cpDiffContent) {
      dom.cpDiffContent.classList.remove('hidden');
      dom.cpDiffContent.replaceChildren();

      const loadingP = document.createElement('p');
      loadingP.className = 'text-muted';
      loadingP.style.cssText = 'padding: 2rem; text-align: center;';
      loadingP.textContent = `Computing deterministic semantic diff between ${baseId} and ${targetId}...`;
      dom.cpDiffContent.appendChild(loadingP);
    }

    try {
      const res = await fetch(`/api/checkpoints/diff?base_id=${encodeURIComponent(baseId)}&target_id=${encodeURIComponent(targetId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const diffData = await res.json();
      state.checkpoints.currentDiff = diffData;
      renderDiffResults(diffData);
    } catch (err) {
      if (dom.cpDiffContent) {
        dom.cpDiffContent.replaceChildren();
        const errDiv = document.createElement('div');
        errDiv.className = 'alert danger';
        errDiv.textContent = `Error comparing checkpoints: ${err.message}`;
        dom.cpDiffContent.appendChild(errDiv);
      }
      showToast(`Diff error: ${err.message}`, 'error');
    }
  }

  function renderDiffResults(diffData) {
    const container = dom.cpDiffContent;
    if (!container) return;
    container.replaceChildren();

    const summary = diffData.summary || {};

    // Comparison Header Card
    const headerBox = document.createElement('div');
    headerBox.style.cssText = 'background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 1rem;';

    const titleH = document.createElement('h4');
    titleH.style.cssText = 'margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #f8fafc; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;';

    const leftTitle = document.createElement('div');
    leftTitle.innerHTML = `
      <span>Base: <strong>${diffData.base_stage || 'BASE'}</strong> (<code>${diffData.base_checkpoint_id}</code>)</span>
      <span style="color: #94a3b8; margin: 0 0.4rem;">➔</span>
      <span>Target: <strong>${diffData.target_stage || 'TARGET'}</strong> (<code>${diffData.target_checkpoint_id}</code>)</span>
    `;

    const diffBadge = document.createElement('span');
    diffBadge.className = 'badge';
    diffBadge.style.cssText = 'background: rgba(6, 182, 212, 0.2); color: var(--cyan); border: 1px solid rgba(6, 182, 212, 0.4);';
    diffBadge.textContent = `${summary.total_differences || 0} Differences`;

    titleH.appendChild(leftTitle);
    titleH.appendChild(diffBadge);
    headerBox.appendChild(titleH);

    // Summary Metric Badges
    const badgeRow = document.createElement('div');
    badgeRow.style.cssText = 'display: flex; gap: 0.6rem; flex-wrap: wrap; font-size: 0.78rem;';
    badgeRow.innerHTML = `
      <span class="diff-tag added">+ ${summary.added_count || 0} Added</span>
      <span class="diff-tag removed">- ${summary.removed_count || 0} Removed</span>
      <span class="diff-tag changed">~ ${summary.changed_count || 0} Changed</span>
      <span class="diff-tag missing-vs-null">∅ ${summary.missing_vs_null_count || 0} Missing vs Null</span>
    `;
    headerBox.appendChild(badgeRow);
    container.appendChild(headerBox);

    // Specialized Mutant Deltas Section
    const mutantDelta = diffData.mutant_delta || {};
    const newlyKilled = Array.isArray(mutantDelta.newly_killed) ? mutantDelta.newly_killed : [];
    const newlyGen = Array.isArray(mutantDelta.newly_generated) ? mutantDelta.newly_generated : [];
    const newlySurv = Array.isArray(mutantDelta.newly_survived) ? mutantDelta.newly_survived : [];
    const newlyEquiv = Array.isArray(mutantDelta.newly_equivalent) ? mutantDelta.newly_equivalent : [];
    const newlyPotEquiv = Array.isArray(mutantDelta.newly_potentially_equivalent) ? mutantDelta.newly_potentially_equivalent : [];

    if (newlyKilled.length > 0 || newlyGen.length > 0 || newlySurv.length > 0 || newlyEquiv.length > 0 || newlyPotEquiv.length > 0) {
      const deltaCard = document.createElement('div');
      deltaCard.className = 'partition-card';
      deltaCard.innerHTML = `<div class="partition-card-title">🧬 Mutant State Transitions (Milestone 2)</div>`;

      const deltaBody = document.createElement('div');
      deltaBody.style.cssText = 'display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.78rem;';

      newlyKilled.forEach(m => {
        const row = document.createElement('div');
        row.style.cssText = 'padding: 4px 8px; background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; border-radius: 4px; color: #86efac;';
        row.textContent = `🎯 Newly Killed: ${m.mutant_id} (${m.operator || 'MUT'} at line ${m.line_number})`;
        deltaBody.appendChild(row);
      });

      newlyEquiv.forEach(m => {
        const row = document.createElement('div');
        row.style.cssText = 'padding: 4px 8px; background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; border-radius: 4px; color: #93c5fd;';
        row.textContent = `🔵 Verified Equivalent: ${m.mutant_id} (${m.operator || 'MUT'} at line ${m.line_number}) [${m.equivalence_method || 'STATIC'}: ${m.equivalence_reason || ''}]`;
        deltaBody.appendChild(row);
      });

      newlyPotEquiv.forEach(m => {
        const row = document.createElement('div');
        row.style.cssText = 'padding: 4px 8px; background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; border-radius: 4px; color: #fde68a;';
        row.textContent = `🟡 Potentially Equivalent: ${m.mutant_id} (${m.operator || 'MUT'} at line ${m.line_number}) [${m.equivalence_method || 'HEURISTIC'}: ${m.equivalence_reason || ''}]`;
        deltaBody.appendChild(row);
      });

      newlyGen.forEach(m => {
        const row = document.createElement('div');
        row.style.cssText = 'padding: 4px 8px; background: rgba(56, 189, 248, 0.1); border-left: 3px solid #38bdf8; border-radius: 4px; color: #7dd3fc;';
        row.textContent = `✨ Newly Generated: ${m.mutant_id} (${m.operator || 'MUT'} at line ${m.line_number}) [Status: ${m.status || 'SURVIVED'}]`;
        deltaBody.appendChild(row);
      });

      newlySurv.forEach(m => {
        const row = document.createElement('div');
        row.style.cssText = 'padding: 4px 8px; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 4px; color: #fca5a5;';
        row.textContent = `⚠️ Newly Survived: ${m.mutant_id} (${m.operator || 'MUT'} at line ${m.line_number})`;
        deltaBody.appendChild(row);
      });

      deltaCard.appendChild(deltaBody);
      container.appendChild(deltaCard);
    }

    // Semantic Diff Items List
    const diffsList = Array.isArray(diffData.differences) ? diffData.differences : [];
    if (diffsList.length === 0) {
      const noDiffP = document.createElement('div');
      noDiffP.className = 'alert info';
      noDiffP.textContent = 'Both checkpoints have identical state across all Blackboard partitions.';
      container.appendChild(noDiffP);
      return;
    }

    const itemsContainer = document.createElement('div');
    itemsContainer.style.cssText = 'display: flex; flex-direction: column; gap: 0.6rem; max-height: 500px; overflow-y: auto; padding-right: 4px;';

    diffsList.forEach(diff => {
      const itemRow = document.createElement('div');
      const ct = (diff.change_type || 'CHANGED').toLowerCase().replace('_', '-');
      itemRow.className = `diff-item-row ${ct}`;

      const topItem = document.createElement('div');
      topItem.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;';

      const pathCode = document.createElement('code');
      pathCode.style.cssText = 'font-weight: 600; color: #f1f5f9; font-size: 0.8rem;';
      pathCode.textContent = diff.path;

      const tagSpan = document.createElement('span');
      tagSpan.className = `diff-tag ${ct}`;
      tagSpan.textContent = diff.change_type;

      topItem.appendChild(pathCode);
      topItem.appendChild(tagSpan);
      itemRow.appendChild(topItem);

      if (diff.description) {
        const descP = document.createElement('div');
        descP.style.cssText = 'font-size: 0.74rem; color: #94a3b8; margin-bottom: 0.35rem;';
        descP.textContent = diff.description;
        itemRow.appendChild(descP);
      }

      // Base vs Target Values Box
      if (diff.change_type === 'CHANGED') {
        const valGrid = document.createElement('div');
        valGrid.style.cssText = 'display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;';

        const baseValBox = document.createElement('div');
        baseValBox.className = 'diff-val-box base';
        baseValBox.textContent = `Base: ${JSON.stringify(diff.base_value)}`;

        const targetValBox = document.createElement('div');
        targetValBox.className = 'diff-val-box target';
        targetValBox.textContent = `Target: ${JSON.stringify(diff.target_value)}`;

        valGrid.appendChild(baseValBox);
        valGrid.appendChild(targetValBox);
        itemRow.appendChild(valGrid);
      } else if (diff.change_type === 'ADDED') {
        const addValBox = document.createElement('div');
        addValBox.className = 'diff-val-box target';
        addValBox.textContent = `Value: ${JSON.stringify(diff.target_value)}`;
        itemRow.appendChild(addValBox);
      } else if (diff.change_type === 'REMOVED') {
        const remValBox = document.createElement('div');
        remValBox.className = 'diff-val-box base';
        remValBox.textContent = `Was: ${JSON.stringify(diff.base_value)}`;
        itemRow.appendChild(remValBox);
      } else if (diff.change_type === 'MISSING_VS_NULL') {
        const nullValBox = document.createElement('div');
        nullValBox.style.cssText = 'background: rgba(168, 85, 247, 0.15); padding: 0.35rem 0.6rem; border-radius: 4px; color: #d8b4fe; font-size: 0.74rem;';
        nullValBox.textContent = diff.is_null_in_base ? 'Base: null (explicit) ➔ Target: missing' : 'Base: missing ➔ Target: null (explicit)';
        itemRow.appendChild(nullValBox);
      }

      itemsContainer.appendChild(itemRow);
    });

    container.appendChild(itemsContainer);
  }

  function switchCheckpointSubtab(subtab) {
    if (dom.btnSubtabDetail) dom.btnSubtabDetail.classList.toggle('active', subtab === 'detail');
    if (dom.btnSubtabDiff) dom.btnSubtabDiff.classList.toggle('active', subtab === 'diff');
    if (dom.btnSubtabJson) dom.btnSubtabJson.classList.toggle('active', subtab === 'json');

    if (dom.viewCpDetail) dom.viewCpDetail.classList.toggle('hidden', subtab !== 'detail');
    if (dom.viewCpDiff) dom.viewCpDiff.classList.toggle('hidden', subtab !== 'diff');
    if (dom.viewCpJson) dom.viewCpJson.classList.toggle('hidden', subtab !== 'json');
  }

  function openRestoreModal(checkpointId, stage, rev, ts) {
    state.checkpoints.restoringId = checkpointId;
    if (dom.restoreTargetId) dom.restoreTargetId.textContent = checkpointId;
    if (dom.restoreTargetStage) dom.restoreTargetStage.textContent = stage || 'UNKNOWN';
    if (dom.restoreTargetRev) dom.restoreTargetRev.textContent = String(rev ?? 0);
    if (dom.restoreTargetTime) dom.restoreTargetTime.textContent = formatTimestamp(ts);

    if (dom.restoreModalBackdrop) dom.restoreModalBackdrop.classList.remove('hidden');
  }

  function closeRestoreModal() {
    state.checkpoints.restoringId = null;
    if (dom.restoreModalBackdrop) dom.restoreModalBackdrop.classList.add('hidden');
  }

  async function executeRestore() {
    const cpId = state.checkpoints.restoringId;
    if (!cpId) return;

    if (dom.btnConfirmRestore) {
      dom.btnConfirmRestore.disabled = true;
      dom.btnConfirmRestore.textContent = 'Restoring Snapshot...';
    }

    try {
      const res = await fetch(`/api/checkpoints/${encodeURIComponent(cpId)}/restore`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();

      closeRestoreModal();
      showToast(`Snapshot ${cpId} restored successfully!`, 'success');

      if (dom.checkpointsRestoreAlert) {
        dom.checkpointsRestoreAlert.textContent = `✓ Successfully restored checkpoint ${cpId} (Stage: ${data.stage || 'N/A'}, Revision: ${data.revision ?? 0}). State verified in isolated Blackboard.`;
        dom.checkpointsRestoreAlert.classList.remove('hidden');
      }

      // Refresh checkpoint timeline
      await fetchCheckpoints();

    } catch (err) {
      showToast(`Restoration failed: ${err.message}`, 'error');
      if (dom.checkpointsRestoreAlert) {
        dom.checkpointsRestoreAlert.textContent = `❌ Restoration failed: ${err.message}`;
        dom.checkpointsRestoreAlert.className = 'alert danger';
        dom.checkpointsRestoreAlert.classList.remove('hidden');
      }
    } finally {
      if (dom.btnConfirmRestore) {
        dom.btnConfirmRestore.disabled = false;
        dom.btnConfirmRestore.textContent = 'Confirm & Restore Snapshot';
      }
    }
  }

  // Bind Checkpoint Event Listeners
  if (dom.btnRefreshCheckpoints) {
    dom.btnRefreshCheckpoints.addEventListener('click', () => fetchCheckpoints());
  }

  if (dom.cpStageFilter) {
    dom.cpStageFilter.addEventListener('change', () => fetchCheckpoints());
  }

  if (dom.cpStatusFilter) {
    dom.cpStatusFilter.addEventListener('change', () => fetchCheckpoints());
  }

  if (dom.cpJobFilter) {
    dom.cpJobFilter.addEventListener('input', () => fetchCheckpoints());
  }

  if (dom.cpSortOrder) {
    dom.cpSortOrder.addEventListener('change', () => renderCheckpointTimeline());
  }

  if (dom.btnTriggerDiffModal) {
    dom.btnTriggerDiffModal.addEventListener('click', () => {
      if (state.checkpoints.diffBaseId && state.checkpoints.diffTargetId) {
        runCheckpointsDiff(state.checkpoints.diffBaseId, state.checkpoints.diffTargetId);
      }
    });
  }

  if (dom.btnSwapDiffSelection) {
    dom.btnSwapDiffSelection.addEventListener('click', swapDiffSelection);
  }

  if (dom.btnClearDiffSelection) {
    dom.btnClearDiffSelection.addEventListener('click', clearDiffSelection);
  }

  if (dom.btnSubtabDetail) {
    dom.btnSubtabDetail.addEventListener('click', () => switchCheckpointSubtab('detail'));
  }

  if (dom.btnSubtabDiff) {
    dom.btnSubtabDiff.addEventListener('click', () => switchCheckpointSubtab('diff'));
  }

  if (dom.btnSubtabJson) {
    dom.btnSubtabJson.addEventListener('click', () => switchCheckpointSubtab('json'));
  }

  if (dom.btnCopyCheckpointJson && dom.checkpointRawJsonDisplay) {
    dom.btnCopyCheckpointJson.addEventListener('click', async () => {
      const txt = dom.checkpointRawJsonDisplay.textContent;
      try {
        await navigator.clipboard.writeText(txt);
        showToast('Checkpoint JSON copied to clipboard!', 'success');
      } catch {
        showToast('Clipboard access denied', 'warning');
      }
    });
  }

  if (dom.btnCloseRestoreModal) {
    dom.btnCloseRestoreModal.addEventListener('click', closeRestoreModal);
  }

  if (dom.btnCancelRestore) {
    dom.btnCancelRestore.addEventListener('click', closeRestoreModal);
  }

  if (dom.btnConfirmRestore) {
    dom.btnConfirmRestore.addEventListener('click', executeRestore);
  }

  if (dom.restoreModalBackdrop) {
    dom.restoreModalBackdrop.addEventListener('click', (e) => {
      if (e.target === dom.restoreModalBackdrop) closeRestoreModal();
    });
  }


  // =========================================================================
  // Initial Bootstrapping
  // =========================================================================
  async function init() {
    // 1. Fetch system status
    await fetchSystemStatus();

    // 2. Load samples list
    await loadSampleFilesList();

    // 3. Load default sample (discount.py)
    await loadSampleModule('discount.py');

    // 4. Fetch telemetry & wiretap initial counts
    fetchTelemetry();
    fetchWiretap();

    // 5. Connect Real-Time WebSocket Event Stream (Milestone 3)
    initWebSocketEventStream();

    // 6. Check if hardened suite exists on disk
    fetchHardenedSuiteCode();

    // 7. Expose test helpers for QA automation
    window.__testforge = {
      showToast,
      switchTab,
      updateTargetBanner,
      renderHardeningResults,
      fetchWiretap,
      fetchTelemetry,
      fetchCheckpoints,
      inspectCheckpoint,
      runCheckpointsDiff,
      setDiffBase,
      setDiffTarget,
      openRestoreModal,
      executeRestore,
      openA2aModal,
      closeA2aModal,
      fetchAndRenderA2aCard,
      renderA2aCard,
      copyA2aJson,
      initWebSocketEventStream,
      disconnectWebSocket,
      appendLiveWiretapEvent,
      state,
      dom,
    };
  }

  init();
});
