import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Editor } from 'ketcher-react';
import { StandaloneStructServiceProvider } from 'ketcher-standalone';

// Import Ketcher styles
import 'ketcher-react/dist/index.css';
import './App.css';

// Initialize TanStack query client and Ketcher standalone provider
const queryClient = new QueryClient();
const structServiceProvider = new StandaloneStructServiceProvider();

interface ReagentItem {
  cas: string;
  name: string;
  location: string;
  supplier: string;
  svg: string;
  similarity?: number;
}

interface SearchResponse {
  count: number;
  items: ReagentItem[];
}

interface SearchHistoryItem {
  id: string;
  mode: 'substructure' | 'exact' | 'similarity';
  molfile: string;
  svg: string;
  createdAt: number;
}

const HISTORY_STORAGE_KEY = 'reagent-search-history';

// Backend API configuration
const apiHost = import.meta.env.VITE_HOST || 'http://localhost:8000';
const api = axios.create({
  baseURL: apiHost,
});

function ReagentSearchPortal() {
  const [searchMode, setSearchMode] = useState<'substructure' | 'exact' | 'similarity'>('substructure');
  const [limit, setLimit] = useState<number>(20);
  const [ketcher, setKetcher] = useState<any>(null);
  
  // Feedback states
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  
  // Results cache
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [history, setHistory] = useState<SearchHistoryItem[]>(() => {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
  }, [history]);

  // Initialize Ketcher global instance
  const onKetcherInit = (ketcherInstance: any) => {
    setKetcher(ketcherInstance);
    (window as any).ketcher = ketcherInstance;
  };

  // Intercept global paste events to easily load SMILES/SMARTS from clipboard directly into Ketcher
  useEffect(() => {
    const handleGlobalPaste = async (e: ClipboardEvent) => {
      // Do not intercept if user is typing in standard text inputs
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA')) {
        return;
      }

      const pastedText = e.clipboardData?.getData('text');
      if (pastedText && ketcher) {
        const trimmed = pastedText.trim();
        // Skip handling if it looks like empty json or brackets (sometimes clipboard contains random JSON)
        if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
          return;
        }
        
        try {
          // Attempt to load the SMILES/SMARTS string into the editor
          await ketcher.setMolecule(trimmed);
          setErrorMessage(null);
          showNotification('info', `Imported structure from clipboard: "${trimmed.substring(0, 30)}${trimmed.length > 30 ? '...' : ''}"`);
        } catch (err: any) {
          console.error("Clipboard paste import failed:", err);
          // Don't interrupt standard clipboard actions if it's not a valid smiles, 
          // but if the user intended to paste, show a subtle warning.
        }
      }
    };

    window.addEventListener('paste', handleGlobalPaste);
    return () => {
      window.removeEventListener('paste', handleGlobalPaste);
    };
  }, [ketcher]);

  // Helper for notification toasts
  const showNotification = (type: 'success' | 'error' | 'info', text: string) => {
    setNotification({ type, text });
    if (type !== 'error') {
      setTimeout(() => setNotification(null), 4000);
    }
  };

  // Search Mutation
  const searchMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      if (!ketcher) {
        throw new Error("Structure editor is loading. Please try again in a moment.");
      }

      let queryStr = "";
      try {
        if (searchMode === 'substructure') {
          queryStr = await ketcher.getSmarts();
        } else {
          queryStr = await ketcher.getSmiles();
        }
      } catch (err: any) {
        throw new Error("Unable to extract structure from editor. Please draw a molecule first.");
      }

      // Check if anything is actually drawn
      if (!queryStr || queryStr.trim() === "" || queryStr === "{}" || queryStr === "[]") {
        throw new Error("The structure editor is empty. Please draw or paste a chemical structure to search.");
      }

      const molfile = await ketcher.getMolfile();
      let svg = '';
      try {
        const ket = await ketcher.getKet();
        const svgBlob = await ketcher.generateImage(ket, { outputFormat: 'svg' });
        svg = await svgBlob.text();
      } catch {
        // SVG preview is optional; the molfile remains the source for restore.
      }

      // API requests based on search mode
      if (searchMode === 'substructure') {
        console.log("DEBUG: Sending Molfile for substructure search:", molfile);
        const res = await api.post<SearchResponse>('/search/substructure', { molfile });
        return { data: res.data, historyItem: { mode: searchMode, molfile, svg } };
      } else if (searchMode === 'exact') {
        const res = await api.post<SearchResponse>('/search/exact', { smiles: queryStr });
        return { data: res.data, historyItem: { mode: searchMode, molfile, svg } };
      } else {
        const res = await api.post<SearchResponse>('/search/similarity', { smiles: queryStr, limit });
        return { data: res.data, historyItem: { mode: searchMode, molfile, svg } };
      }
    },
    onSuccess: (response) => {
      const data = response.data;
      setResults(data);
      const item = { ...response.historyItem, id: crypto.randomUUID(), createdAt: Date.now() };
      setHistory((current) => [item, ...current.filter((entry) => !(entry.mode === item.mode && entry.molfile === item.molfile))].slice(0, 20));
      if (data.count === 0) {
        showNotification('info', 'No matching reagents found in the database.');
      } else {
        showNotification('success', `Search completed. Found ${data.count} matches.`);
      }
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : err.message || "An error occurred during search.";
      setErrorMessage(msg);
      setResults(null);
    }
  });

  const restoreHistory = async (item: SearchHistoryItem) => {
    if (!ketcher) return;
    try {
      await ketcher.setMolecule(item.molfile);
      setSearchMode(item.mode);
      setErrorMessage(null);
      showNotification('info', '履歴の構造式をエディタに復元しました。');
    } catch {
      showNotification('error', '履歴の構造式を復元できませんでした。');
    }
  };

  // Database Reload Mutation
  const reloadMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/reload');
      return res.data;
    },
    onSuccess: (data: any) => {
      showNotification('success', data.message || "Library reloaded from CSV successfully.");
      // Clear previous search results upon library reload to prevent mismatching
      setResults(null);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : err.message || "Failed to reload library.";
      showNotification('error', `Reload failed: ${msg}`);
    }
  });

  const handleCopyCas = async (cas: string, index: number) => {
    try {
      // Clipboard API is unavailable on non-secure contexts (for example HTTP).
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(cas);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = cas;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const copied = document.execCommand('copy');
        document.body.removeChild(textarea);
        if (!copied) throw new Error('Clipboard copy failed');
      }

      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 1500);
    } catch (error) {
      console.error('CAS copy failed:', error);
      showNotification('error', 'CAS番号をコピーできませんでした。');
    }
  };

  return (
    <div className={`app-shell ${isHistoryOpen ? '' : 'history-collapsed'}`}>
      <aside className="history-sidebar">
        <div className="history-sidebar-header">
          <div>
            <span className="history-kicker">LOCAL STORAGE</span>
            <h2>検索履歴</h2>
          </div>
          <button className="history-toggle" onClick={() => setIsHistoryOpen(false)} aria-label="履歴を閉じる">‹</button>
        </div>
        {history.length === 0 ? (
          <p className="history-empty">検索を実行すると、<br />構造式がここに保存されます。</p>
        ) : (
          <div className="history-list">
            {history.map((item, index) => (
              <button className="history-item" key={item.id} onClick={() => restoreHistory(item)} title="クリックしてエディタに復元">
                <span className="history-number">{String(index + 1).padStart(2, '0')}</span>
                <span className="history-structure">
                  {item.svg ? (
                    <img src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(item.svg)}`} alt="構造式" />
                  ) : (
                    <span className="history-no-preview">構造式</span>
                  )}
                </span>
                <span className="history-mode">{item.mode === 'substructure' ? '部分構造' : item.mode === 'exact' ? '完全一致' : '類似検索'}</span>
              </button>
            ))}
          </div>
        )}
        <p className="history-limit">最大20件 · 新しい順</p>
      </aside>
      {!isHistoryOpen && <button className="history-open" onClick={() => setIsHistoryOpen(true)} aria-label="履歴を開く">›<span>履歴</span></button>}
      <div className="app-container">
      {/* Toast Notification */}
      {notification && (
        <div className={`notification-toast ${notification.type} animate-slide-in`}>
          <div className="toast-content">
            <span className="toast-icon">
              {notification.type === 'success' && '✅'}
              {notification.type === 'error' && '❌'}
              {notification.type === 'info' && 'ℹ️'}
            </span>
            <p className="toast-text">{notification.text}</p>
          </div>
          <button className="toast-close" onClick={() => setNotification(null)}>&times;</button>
        </div>
      )}

      {/* Hero Header */}
      <header className="app-header">
        <div className="header-meta">
          <span className="lab-badge">BIOTECH RESEARCH PORTAL</span>
          <h1>試薬検索システム</h1>
        </div>
        <div className="header-actions">
          <button 
            className={`btn btn-secondary reload-btn ${reloadMutation.isPending ? 'loading' : ''}`}
            onClick={() => reloadMutation.mutate()}
            disabled={reloadMutation.isPending}
            title="Reload compound library from CSV"
          >
            <svg className="icon-refresh" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
            </svg>
            <span>{reloadMutation.isPending ? 'Reloading...' : 'Reload CSV'}</span>
          </button>
        </div>
      </header>

      <main className="app-main">
        {/* Ketcher drawing board */}
        <section className="editor-card card">
          <div className="card-header">
            <div className="header-left">
              <span className="step-num">1</span>
              <h2>分子構造を描画</h2>
            </div>
          </div>
          <div className="ketcher-wrapper">
            <Editor
              staticResourcesUrl=""
              structServiceProvider={structServiceProvider}
              onInit={onKetcherInit}
            />
          </div>
        </section>

        {/* Search configurations */}
        <section className="config-card card">
          <div className="card-header">
            <div className="header-left">
              <span className="step-num">2</span>
              <h2>検索設定と実行</h2>
            </div>
          </div>
          
          <div className="search-tabs">
            <button 
              className={`search-tab-btn ${searchMode === 'substructure' ? 'active' : ''}`}
              onClick={() => setSearchMode('substructure')}
            >
              <div className="tab-icon-wrapper">🎯</div>
              <div className="tab-text-wrapper">
                <h3>部分構造検索</h3>
                <p>SMARTS matching</p>
              </div>
            </button>

            <button 
              className={`search-tab-btn ${searchMode === 'exact' ? 'active' : ''}`}
              onClick={() => setSearchMode('exact')}
            >
              <div className="tab-icon-wrapper">🔒</div>
              <div className="tab-text-wrapper">
                <h3>完全一致検索</h3>
                <p>Canonical SMILES</p>
              </div>
            </button>

            <button 
              className={`search-tab-btn ${searchMode === 'similarity' ? 'active' : ''}`}
              onClick={() => setSearchMode('similarity')}
            >
              <div className="tab-icon-wrapper">📊</div>
              <div className="tab-text-wrapper">
                <h3>類似検索</h3>
                <p>Tanimoto similarity</p>
              </div>
            </button>
          </div>

          <div className="form-container">
            {searchMode === 'similarity' && (
              <div className="form-group similarity-form animate-fade-in">
                <div className="form-label-row">
                  <label htmlFor="limit-range">類似試薬の最大取得件数</label>
                  <span className="range-indicator">{limit} 件</span>
                </div>
                <div className="range-control">
                  <span className="range-bound-lbl">5</span>
                  <input
                    id="limit-range"
                    type="range"
                    min="5"
                    max="100"
                    step="5"
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                  />
                  <span className="range-bound-lbl">100</span>
                </div>
              </div>
            )}

            <button 
              className={`btn btn-primary search-btn ${searchMutation.isPending ? 'loading' : ''}`}
              onClick={() => searchMutation.mutate()}
              disabled={searchMutation.isPending}
            >
              {searchMutation.isPending ? (
                <>
                  <span className="spinner"></span>
                  Searching...
                </>
              ) : (
                '検索を実行'
              )}
            </button>
          </div>
        </section>

        {/* Error Feedback */}
        {errorMessage && (
          <div className="error-alert animate-shake">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <h4>化学構造式または検索条件のエラー</h4>
              <p>{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Search results */}
        <section className="results-container">
          <div className="results-heading-row">
            <h2>3. 検索結果</h2>
            {results && (
              <span className="results-count">
                検索結果: <strong>{results.count}</strong> 件
              </span>
            )}
          </div>

          {searchMutation.isPending ? (
            <div className="results-loading-grid">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="card result-skeleton">
                  <div className="skeleton-media"></div>
                  <div className="skeleton-line full"></div>
                  <div className="skeleton-line medium"></div>
                  <div className="skeleton-line short"></div>
                </div>
              ))}
            </div>
          ) : results === null ? (
            <div className="empty-panel card">
              <span className="empty-icon">🧪</span>
              <h3>検索が未実行です</h3>
              <p>1. 上部エディタで構造式を描画してください。<br />2. 検索モードを選択し、「検索を実行」ボタンをクリックしてください。</p>
            </div>
          ) : results.items.length === 0 ? (
            <div className="empty-panel card animate-fade-in">
              <span className="empty-icon">🔍</span>
              <h3>該当する試薬が見つかりませんでした</h3>
              <p>描画した構造を確認するか、部分構造検索などの異なる検索モードをお試しください。</p>
            </div>
          ) : (
            <div className="results-grid animate-fade-in">
              {results.items.map((item, index) => (
                <article key={item.cas + '-' + index} className="card result-card">
                  {item.similarity !== undefined && item.similarity !== null && (
                    <div className="similarity-tag">
                      <span className="sim-lbl">Similarity</span>
                      <span className="sim-pct">{Math.round(item.similarity * 1000) / 10}%</span>
                    </div>
                  )}

                  <div className="svg-container">
                    <div 
                      className="svg-renderer" 
                      dangerouslySetInnerHTML={{ __html: item.svg }} 
                    />
                  </div>

                  <div className="card-info">
                    <h3 className="reagent-name" title={item.name}>{item.name}</h3>
                    
                    <div className="metadata-table">
                      <div className="meta-row">
                        <span className="meta-label">CAS</span>
                        <span 
                          className={`meta-value cas-number ${copiedIndex === index ? 'copied' : ''}`}
                          onClick={() => handleCopyCas(item.cas, index)}
                          title="クリックしてCAS番号をコピー"
                        >
                          {item.cas}
                          <span className="tooltip-text">
                            {copiedIndex === index ? 'コピー完了' : 'クリックでコピー'}
                          </span>
                        </span>
                      </div>

                      <div className="meta-row">
                        <span className="meta-label">保管棚</span>
                        <span className="meta-value shelf-badge">{item.location}</span>
                      </div>

                      <div className="meta-row">
                        <span className="meta-label">メーカー</span>
                        <span className="meta-value supplier-text">{item.supplier}</span>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="app-footer">
        <p>🔬 Chemical Reagent Search Engine &copy; 2026. Powered by RDKit SubstructLibrary.</p>
      </footer>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ReagentSearchPortal />
    </QueryClientProvider>
  );
}
