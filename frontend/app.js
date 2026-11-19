/**
 * BlogCraft AI — Multi-Agent Technical Blog Studio Frontend
 * Connects to LangGraph FastAPI backend.
 */

(function () {
  'use strict';

  // --- State & Configurations ---
  const DEFAULT_API_URL = window.location.protocol.startsWith('http') 
    ? window.location.origin 
    : 'http://127.0.0.1:8000';

  let apiBaseUrl = localStorage.getItem('bwa_api_url') || DEFAULT_API_URL;
  let currentResult = null;
  let generationTimer = null;
  let timerSeconds = 0;
  let simulatedStepTimeout = null;

  // --- DOM Elements ---
  const elements = {
    // Header & Global
    btnApiStatus: document.getElementById('btnApiStatus'),
    btnOpenSettings: document.getElementById('btnOpenSettings'),
    btnOpenHistory: document.getElementById('btnOpenHistory'),
    btnThemeToggle: document.getElementById('btnThemeToggle'),
    historyCount: document.getElementById('historyCount'),
    
    // Form & Studio Card
    inputCard: document.getElementById('inputCard'),
    generateForm: document.getElementById('generateForm'),
    topicInput: document.getElementById('topicInput'),
    btnClearTopic: document.getElementById('btnClearTopic'),
    asOfInput: document.getElementById('asOfInput'),
    btnDateToday: document.getElementById('btnDateToday'),
    btnGenerate: document.getElementById('btnGenerate'),
    topicChips: document.querySelectorAll('.chip'),
    
    // Progress Pipeline
    progressSection: document.getElementById('progressSection'),
    progressStatusText: document.getElementById('progressStatusText'),
    elapsedTimer: document.getElementById('elapsedTimer'),
    agentTickerMessage: document.getElementById('agentTickerMessage'),
    steps: {
      router: document.getElementById('step-router'),
      research: document.getElementById('step-research'),
      orchestrator: document.getElementById('step-orchestrator'),
      worker: document.getElementById('step-worker'),
      reducer: document.getElementById('step-reducer')
    },

    // Results Dashboard
    resultsSection: document.getElementById('resultsSection'),
    resultModeTag: document.getElementById('resultModeTag'),
    resultTitle: document.getElementById('resultTitle'),
    statWordCount: document.getElementById('statWordCount'),
    statReadingTime: document.getElementById('statReadingTime'),
    statSectionCount: document.getElementById('statSectionCount'),
    statEvidenceCount: document.getElementById('statEvidenceCount'),
    statEvidenceWrapper: document.getElementById('statEvidenceWrapper'),
    renderedContent: document.getElementById('renderedContent'),
    tableOfContents: document.getElementById('tableOfContents'),
    rawMarkdownContent: document.getElementById('rawMarkdownContent'),
    evidenceGrid: document.getElementById('evidenceGrid'),
    queriesBox: document.getElementById('queriesBox'),
    tabBtnEvidence: document.getElementById('tabBtnEvidence'),
    evidenceBadge: document.getElementById('evidenceBadge'),

    // Result Action Buttons
    btnCopyMarkdown: document.getElementById('btnCopyMarkdown'),
    btnDownloadMarkdown: document.getElementById('btnDownloadMarkdown'),
    btnPrintBlog: document.getElementById('btnPrintBlog'),
    btnNewBlog: document.getElementById('btnNewBlog'),
    btnCopyRawMarkdown: document.getElementById('btnCopyRawMarkdown'),

    // Details Tab
    detailMode: document.getElementById('detailMode'),
    detailNeedsResearch: document.getElementById('detailNeedsResearch'),
    detailAsOf: document.getElementById('detailAsOf'),
    detailRecency: document.getElementById('detailRecency'),

    // Modals
    settingsModal: document.getElementById('settingsModal'),
    settingsBackdrop: document.getElementById('settingsBackdrop'),
    btnCloseSettings: document.getElementById('btnCloseSettings'),
    apiUrlInput: document.getElementById('apiUrlInput'),
    btnTestApi: document.getElementById('btnTestApi'),
    testHealthResult: document.getElementById('testHealthResult'),
    btnSaveSettings: document.getElementById('btnSaveSettings'),

    historyModal: document.getElementById('historyModal'),
    historyBackdrop: document.getElementById('historyBackdrop'),
    btnCloseHistory: document.getElementById('btnCloseHistory'),
    historyList: document.getElementById('historyList'),
    btnClearHistory: document.getElementById('btnClearHistory'),

    imageModal: document.getElementById('imageModal'),
    modalBackdrop: document.getElementById('modalBackdrop'),
    btnCloseImageModal: document.getElementById('btnCloseImageModal'),
    modalImage: document.getElementById('modalImage'),
    modalCaption: document.getElementById('modalCaption'),

    toastContainer: document.getElementById('toastContainer')
  };

  // --- Initializer ---
  function init() {
    setupTodayDate();
    setupTheme();
    setupEventListeners();
    updateHistoryBadge();
    checkHealth();

    // Check health periodically every 30 seconds
    setInterval(checkHealth, 30000);
  }

  // --- Date Setup ---
  function setupTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    elements.asOfInput.value = today;
  }

  // --- Theme Management ---
  function setupTheme() {
    const savedTheme = localStorage.getItem('bwa_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
  }

  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('bwa_theme', nextTheme);
    showToast(`Switched to ${nextTheme} theme`, 'info');
  }

  // --- API Health Check ---
  async function checkHealth() {
    updateApiStatus('checking', 'Connecting...');
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const resp = await fetch(`${apiBaseUrl}/health`, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (resp.ok) {
        updateApiStatus('online', 'API Online');
      } else {
        updateApiStatus('offline', `Status: ${resp.status}`);
      }
    } catch (err) {
      updateApiStatus('offline', 'API Offline');
    }
  }

  function updateApiStatus(status, text) {
    elements.btnApiStatus.className = `status-pill status-${status}`;
    elements.btnApiStatus.querySelector('.status-text').textContent = text;
  }

  // --- Event Listeners ---
  function setupEventListeners() {
    // Form submission
    elements.generateForm.addEventListener('submit', handleGenerateSubmit);

    // Ctrl+Enter keyboard shortcut
    elements.topicInput.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        elements.generateForm.requestSubmit();
      }
    });

    // Topic clear button visibility
    elements.topicInput.addEventListener('input', () => {
      elements.btnClearTopic.style.display = elements.topicInput.value ? 'block' : 'none';
    });

    elements.btnClearTopic.addEventListener('click', () => {
      elements.topicInput.value = '';
      elements.btnClearTopic.style.display = 'none';
      elements.topicInput.focus();
    });

    // Topic Suggestion Chips
    elements.topicChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        const topic = chip.getAttribute('data-topic');
        elements.topicInput.value = topic;
        elements.btnClearTopic.style.display = 'block';
        elements.topicInput.focus();
      });
    });

    // Today Button
    elements.btnDateToday.addEventListener('click', setupTodayDate);

    // Theme Toggle
    elements.btnThemeToggle.addEventListener('click', toggleTheme);

    // API Status button opens Settings
    elements.btnApiStatus.addEventListener('click', openSettings);
    elements.btnOpenSettings.addEventListener('click', openSettings);
    elements.btnCloseSettings.addEventListener('click', closeSettings);
    elements.settingsBackdrop.addEventListener('click', closeSettings);
    elements.btnTestApi.addEventListener('click', testApiConnection);
    elements.btnSaveSettings.addEventListener('click', saveSettings);

    // History
    elements.btnOpenHistory.addEventListener('click', openHistory);
    elements.btnCloseHistory.addEventListener('click', closeHistory);
    elements.historyBackdrop.addEventListener('click', closeHistory);
    elements.btnClearHistory.addEventListener('click', clearHistory);

    // Image Modal
    elements.btnCloseImageModal.addEventListener('click', closeImageModal);
    elements.modalBackdrop.addEventListener('click', closeImageModal);

    // Result Actions
    elements.btnCopyMarkdown.addEventListener('click', () => copyMarkdown(currentResult?.markdown));
    elements.btnCopyRawMarkdown.addEventListener('click', () => copyMarkdown(currentResult?.markdown));
    elements.btnDownloadMarkdown.addEventListener('click', downloadMarkdownFile);
    elements.btnPrintBlog.addEventListener('click', () => window.print());
    elements.btnNewBlog.addEventListener('click', () => {
      elements.inputCard.scrollIntoView({ behavior: 'smooth' });
      elements.topicInput.select();
    });

    // Result Tabs
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        switchTab(targetTab);
      });
    });

    // Escape closes modals
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeSettings();
        closeHistory();
        closeImageModal();
      }
    });
  }

  // --- Generation Logic ---
  async function handleGenerateSubmit(e) {
    e.preventDefault();

    const topic = elements.topicInput.value.trim();
    const asOf = elements.asOfInput.value.trim() || new Date().toISOString().split('T')[0];

    if (!topic || topic.length < 3) {
      showToast('Please enter a topic with at least 3 characters', 'error');
      return;
    }

    // Disable generate button
    setGeneratingState(true);
    startProgressStepper();

    try {
      const payload = {
        topic: topic,
        as_of: asOf
      };

      const response = await fetch(`${apiBaseUrl}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        let errDetail = `Server returned ${response.status} ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errDetail = errJson.detail;
        } catch (_) {}
        throw new Error(errDetail);
      }

      const result = await response.json();
      currentResult = result;

      // Finalize stepper
      finishProgressStepper();

      // Render results
      renderResults(result, asOf);

      // Save to localStorage history
      saveToHistory(result, asOf);

      // Scroll to result & celebrate
      setTimeout(() => {
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
        celebrateCompletion();
        showToast('Blog successfully generated!', 'success');
      }, 500);

    } catch (err) {
      console.error('Generation failed:', err);
      showToast(`Error: ${err.message}`, 'error');
      resetProgressStepper();
    } finally {
      setGeneratingState(false);
      stopTimer();
    }
  }

  function setGeneratingState(isGenerating) {
    elements.btnGenerate.disabled = isGenerating;
    if (isGenerating) {
      elements.btnGenerate.classList.add('loading');
      elements.btnGenerate.querySelector('.btn-text').textContent = 'Generating Blog...';
      elements.progressSection.style.display = 'block';
      elements.progressSection.scrollIntoView({ behavior: 'smooth' });
    } else {
      elements.btnGenerate.classList.remove('loading');
      elements.btnGenerate.querySelector('.btn-text').textContent = 'Generate Blog Post';
    }
  }

  // --- Stepper & Progress Simulation ---
  function startProgressStepper() {
    timerSeconds = 0;
    elements.elapsedTimer.textContent = '00:00';
    clearInterval(generationTimer);
    generationTimer = setInterval(() => {
      timerSeconds++;
      const mins = String(Math.floor(timerSeconds / 60)).padStart(2, '0');
      const secs = String(timerSeconds % 60).padStart(2, '0');
      elements.elapsedTimer.textContent = `${mins}:${secs}`;
    }, 1000);

    // Reset all steps
    Object.values(elements.steps).forEach((step) => {
      step.className = 'step-item';
      step.querySelector('.step-status').textContent = 'Waiting';
    });

    // Step 1: Router
    activateStep('router', 'Analyzing topic domain & recency requirements...');
    updateTicker('Invoking RouterNode with gpt-4.1-mini...');

    // Schedule progressive feedback
    clearTimeout(simulatedStepTimeout);
    simulatedStepTimeout = setTimeout(() => {
      completeStep('router');
      activateStep('research', 'Querying Tavily API for fresh evidence...');
      updateTicker('Gathering authoritative references and normalizing publication dates...');

      simulatedStepTimeout = setTimeout(() => {
        completeStep('research');
        activateStep('orchestrator', 'Drafting blog outline & section constraints...');
        updateTicker('OrchestratorNode synthesizing tasks with word count budgets...');

        simulatedStepTimeout = setTimeout(() => {
          completeStep('orchestrator');
          activateStep('worker', 'Dispatching parallel worker agents...');
          updateTicker('Workers drafting sections concurrently via LangGraph Send()...');

          simulatedStepTimeout = setTimeout(() => {
            completeStep('worker');
            activateStep('reducer', 'Merging sections & generating Gemini diagrams...');
            updateTicker('ReducerSubgraph assembling document and placing images...');
          }, 12000);

        }, 7000);

      }, 6000);

    }, 3500);
  }

  function activateStep(stepKey, statusText) {
    const step = elements.steps[stepKey];
    if (step) {
      step.className = 'step-item active';
      step.querySelector('.step-status').textContent = 'In progress...';
    }
    if (statusText) elements.progressStatusText.textContent = statusText;
  }

  function completeStep(stepKey) {
    const step = elements.steps[stepKey];
    if (step) {
      step.className = 'step-item completed';
      step.querySelector('.step-status').textContent = 'Done ✓';
    }
  }

  function finishProgressStepper() {
    clearTimeout(simulatedStepTimeout);
    Object.keys(elements.steps).forEach((k) => completeStep(k));
    elements.progressStatusText.textContent = 'All agents finished successfully!';
    updateTicker('Pipeline complete. Rendering markdown...');
    setTimeout(() => {
      elements.progressSection.style.display = 'none';
    }, 1200);
  }

  function resetProgressStepper() {
    clearTimeout(simulatedStepTimeout);
    elements.progressSection.style.display = 'none';
  }

  function updateTicker(msg) {
    elements.agentTickerMessage.textContent = msg;
  }

  function stopTimer() {
    clearInterval(generationTimer);
  }

  // --- Celebrate Completion ---
  function celebrateCompletion() {
    if (typeof confetti === 'function') {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.7 }
      });
    }
  }

  // --- Rendering Blog Post & Evidence ---
  function renderResults(result, asOf) {
    elements.resultsSection.style.display = 'flex';

    // Meta Header
    const mode = result.mode || 'closed_book';
    elements.resultModeTag.textContent = mode;
    elements.resultModeTag.className = `meta-mode-tag mode-${mode.replace('_', '-')}`;
    
    const title = result.title || elements.topicInput.value;
    elements.resultTitle.textContent = title;

    // Word Count & Stats
    const rawMd = result.markdown || '';
    const words = countWords(rawMd);
    const readingTime = Math.max(1, Math.round(words / 200));

    elements.statWordCount.textContent = `${words.toLocaleString()} words`;
    elements.statReadingTime.textContent = `${readingTime} min read`;

    // Count Sections
    const sectionHeaders = (rawMd.match(/^##\s+.+$/gm) || []);
    elements.statSectionCount.textContent = `${sectionHeaders.length} sections`;

    // Evidence
    const evidenceList = result.evidence || [];
    elements.statEvidenceCount.textContent = `${evidenceList.length} sources`;
    elements.evidenceBadge.textContent = evidenceList.length;

    if (!result.needs_research || evidenceList.length === 0) {
      elements.statEvidenceWrapper.style.opacity = '0.5';
    } else {
      elements.statEvidenceWrapper.style.opacity = '1';
    }

    // Render Markdown
    renderMarkdownContent(rawMd);

    // Build Table of Contents
    buildTableOfContents();

    // Render Evidence Panel
    renderEvidence(result);

    // Raw Markdown View
    elements.rawMarkdownContent.textContent = rawMd;
    if (window.hljs) {
      hljs.highlightElement(elements.rawMarkdownContent);
    }

    // Pipeline Details Tab
    renderDetails(result, asOf);

    // Switch to Rendered tab by default
    switchTab('tab-rendered');
  }

  function renderMarkdownContent(markdown) {
    // Configure marked options
    if (window.marked) {
      marked.setOptions({
        gfm: true,
        breaks: false,
        highlight: function (code, lang) {
          if (window.hljs && lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
          }
          return code;
        }
      });

      // Parse markdown to HTML and sanitize
      let html = marked.parse(markdown);
      if (window.DOMPurify) {
        html = DOMPurify.sanitize(html);
      }

      elements.renderedContent.innerHTML = html;

      // Post-process images to point to API server & lightbox
      remapImagesAndLightbox();

      // Add copy buttons to code blocks
      addCodeCopyButtons();
    }
  }

  function remapImagesAndLightbox() {
    const images = elements.renderedContent.querySelectorAll('img');
    images.forEach((img) => {
      let src = img.getAttribute('src') || '';
      
      // Remap relative path `../images/xyz.png` or `images/xyz.png`
      if (src.includes('../images/')) {
        const filename = src.split('../images/')[1];
        img.src = `${apiBaseUrl}/images/${filename}`;
      } else if (src.startsWith('images/')) {
        const filename = src.split('images/')[1];
        img.src = `${apiBaseUrl}/images/${filename}`;
      }

      // Add click lightbox preview
      img.addEventListener('click', () => {
        openImageModal(img.src, img.alt || img.getAttribute('title') || 'Diagram');
      });
    });
  }

  function addCodeCopyButtons() {
    const preBlocks = elements.renderedContent.querySelectorAll('pre');
    preBlocks.forEach((pre) => {
      // Don't re-add if already exists
      if (pre.querySelector('.btn-copy-code')) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-copy-code';
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>`;
      btn.title = 'Copy snippet';

      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const codeText = pre.querySelector('code')?.innerText || pre.innerText;
        navigator.clipboard.writeText(codeText);
        btn.innerHTML = '✓';
        showToast('Code copied to clipboard', 'info');
        setTimeout(() => {
          btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>`;
        }, 1800);
      });

      pre.style.position = 'relative';
      btn.style.cssText = 'position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); color: #ccc; border-radius: 4px; padding: 4px 7px; cursor: pointer; transition: all 0.2s;';
      pre.appendChild(btn);
    });
  }

  function buildTableOfContents() {
    elements.tableOfContents.innerHTML = '';
    const headings = elements.renderedContent.querySelectorAll('h2');

    if (headings.length === 0) {
      elements.tableOfContents.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">No section headings found.</span>';
      return;
    }

    headings.forEach((h2, index) => {
      const id = h2.id || `section-${index + 1}`;
      h2.id = id;

      const link = document.createElement('a');
      link.href = `#${id}`;
      link.className = 'toc-link';
      link.textContent = h2.textContent.replace(/^#+\s*/, '');

      link.addEventListener('click', (e) => {
        e.preventDefault();
        h2.scrollIntoView({ behavior: 'smooth' });
        document.querySelectorAll('.toc-link').forEach((l) => l.classList.remove('active'));
        link.classList.add('active');
      });

      elements.tableOfContents.appendChild(link);
    });
  }

  function renderEvidence(result) {
    const evidence = result.evidence || [];
    const queries = result.queries || [];

    // Queries Chips
    elements.queriesBox.innerHTML = '';
    if (queries.length > 0) {
      queries.forEach((q) => {
        const chip = document.createElement('span');
        chip.className = 'query-chip';
        chip.textContent = q;
        elements.queriesBox.appendChild(chip);
      });
    } else {
      elements.queriesBox.innerHTML = '<span style="color:var(--text-muted);font-size:0.82rem;">No external search queries were triggered.</span>';
    }

    // Evidence Cards Grid
    elements.evidenceGrid.innerHTML = '';
    if (evidence.length === 0) {
      elements.evidenceGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 32px; text-align: center; color: var(--text-muted);">
          No web evidence collected. Router classified topic as <code>${result.mode}</code>.
        </div>
      `;
      return;
    }

    evidence.forEach((item) => {
      const card = document.createElement('div');
      card.className = 'evidence-card';

      let domain = '';
      try {
        if (item.url) domain = new URL(item.url).hostname.replace('www.', '');
      } catch (_) {
        domain = item.url;
      }

      card.innerHTML = `
        <div class="evidence-card-meta">
          <span class="evidence-domain">${domain}</span>
          <span>${item.published_at || 'Date unspecified'}</span>
        </div>
        <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="evidence-card-title">
          ${item.title || 'Untitled Source'} &nearr;
        </a>
        <p class="evidence-snippet">${item.snippet || 'No text snippet available.'}</p>
      `;

      elements.evidenceGrid.appendChild(card);
    });
  }

  function renderDetails(result, asOf) {
    elements.detailMode.textContent = result.mode || 'N/A';
    elements.detailNeedsResearch.textContent = result.needs_research ? 'Yes' : 'No';
    elements.detailAsOf.textContent = asOf;

    const recencyMap = {
      open_book: '7 days',
      hybrid: '45 days',
      closed_book: '3650 days (Evergreen)'
    };
    elements.detailRecency.textContent = recencyMap[result.mode] || 'N/A';
  }

  // --- Tabs Switcher ---
  function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach((pane) => {
      pane.classList.toggle('active', pane.id === tabId);
    });
  }

  // --- Copy & Download Actions ---
  function copyMarkdown(md) {
    if (!md) {
      showToast('No markdown content to copy', 'error');
      return;
    }
    navigator.clipboard.writeText(md).then(() => {
      showToast('Markdown copied to clipboard!', 'success');
    }).catch(() => {
      showToast('Failed to copy to clipboard', 'error');
    });
  }

  function downloadMarkdownFile() {
    if (!currentResult || !currentResult.markdown) {
      showToast('No content available for download', 'error');
      return;
    }

    const title = currentResult.title || 'blog_post';
    const slug = title
      .toLowerCase()
      .replace(/[^a-z0-9 _-]+/g, '')
      .replace(/\s+/g, '_')
      .replace(/^_+|_+$/g, '');

    const blob = new Blob([currentResult.markdown], { type: 'text/markdown;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${slug || 'blog'}.md`;
    link.click();
    URL.revokeObjectURL(link.href);

    showToast(`Downloaded ${link.download}`, 'success');
  }

  // --- Image Lightbox Modal ---
  function openImageModal(src, caption) {
    elements.modalImage.src = src;
    elements.modalCaption.textContent = caption;
    elements.imageModal.classList.add('open');
  }

  function closeImageModal() {
    elements.imageModal.classList.remove('open');
    elements.modalImage.src = '';
  }

  // --- Settings Modal ---
  function openSettings() {
    elements.apiUrlInput.value = apiBaseUrl;
    elements.testHealthResult.textContent = 'Untested';
    elements.testHealthResult.className = 'health-result-text';
    elements.settingsModal.classList.add('open');
  }

  function closeSettings() {
    elements.settingsModal.classList.remove('open');
  }

  async function testApiConnection() {
    const url = elements.apiUrlInput.value.trim().replace(/\/+$/, '');
    elements.testHealthResult.textContent = 'Testing...';
    elements.testHealthResult.className = 'health-result-text';

    try {
      const resp = await fetch(`${url}/health`);
      if (resp.ok) {
        elements.testHealthResult.textContent = 'Connection OK (200)';
        elements.testHealthResult.className = 'health-result-text success';
      } else {
        elements.testHealthResult.textContent = `Error: ${resp.status}`;
        elements.testHealthResult.className = 'health-result-text error';
      }
    } catch (e) {
      elements.testHealthResult.textContent = 'Failed to connect';
      elements.testHealthResult.className = 'health-result-text error';
    }
  }

  function saveSettings() {
    const newUrl = elements.apiUrlInput.value.trim().replace(/\/+$/, '');
    if (newUrl) {
      apiBaseUrl = newUrl;
      localStorage.setItem('bwa_api_url', apiBaseUrl);
      showToast('Settings saved', 'success');
      checkHealth();
    }
    closeSettings();
  }

  // --- History Management ---
  function getHistory() {
    try {
      return JSON.parse(localStorage.getItem('bwa_history') || '[]');
    } catch (_) {
      return [];
    }
  }

  function saveToHistory(result, asOf) {
    const history = getHistory();
    const entry = {
      id: Date.now(),
      topic: elements.topicInput.value,
      asOf: asOf,
      title: result.title,
      mode: result.mode,
      date: new Date().toLocaleDateString(),
      result: result
    };

    // Prepend and limit to 15 items
    history.unshift(entry);
    if (history.length > 15) history.pop();

    localStorage.setItem('bwa_history', JSON.stringify(history));
    updateHistoryBadge();
  }

  function updateHistoryBadge() {
    const history = getHistory();
    elements.historyCount.textContent = history.length;
  }

  function openHistory() {
    const history = getHistory();
    elements.historyList.innerHTML = '';

    if (history.length === 0) {
      elements.historyList.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);">No saved generations yet.</div>';
    } else {
      history.forEach((item) => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.innerHTML = `
          <div class="history-item-title">${item.title || item.topic}</div>
          <div class="history-item-meta">${item.mode} &bull; ${item.date}</div>
        `;
        div.addEventListener('click', () => {
          currentResult = item.result;
          renderResults(item.result, item.asOf);
          closeHistory();
          elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
          showToast('Loaded post from history', 'info');
        });
        elements.historyList.appendChild(div);
      });
    }

    elements.historyModal.classList.add('open');
  }

  function closeHistory() {
    elements.historyModal.classList.remove('open');
  }

  function clearHistory() {
    localStorage.removeItem('bwa_history');
    updateHistoryBadge();
    elements.historyList.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);">History cleared.</div>';
    showToast('History cleared', 'info');
  }

  // --- Utility Functions ---
  function countWords(str) {
    if (!str) return 0;
    return str.trim().split(/\s+/).filter(Boolean).length;
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✓';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease-out';
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }

  // --- Start App ---
  init();

})();

