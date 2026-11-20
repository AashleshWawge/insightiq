import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  Database,
  FileSpreadsheet,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  Eye,
  Server,
  DollarSign,
  ShoppingCart,
  Package,
  Users,
  TrendingUp,
  BarChart3,
  Calendar,
  MapPin,
  Award,
  Sparkles,
  Send,
  Code2,
  Copy,
  Check,
  ShieldCheck,
  HelpCircle,
  Play,
  Table as TableIcon,
  Download,
  History,
  RotateCcw,
  PieChart as PieIcon,
  MessageSquare,
  Terminal,
  ArrowRight,
  Search,
  Columns,
  ArrowUpDown,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const getSessionId = () => {
  try {
    let sid = localStorage.getItem('insightiq_session_id');
    if (!sid) {
      sid = 'sess_' + (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2) + Date.now().toString(36));
      localStorage.setItem('insightiq_session_id', sid);
    }
    return sid;
  } catch {
    return 'default_session';
  }
};

const apiFetch = (url, options = {}) => {
  const headers = new Headers(options.headers || {});
  headers.set('X-Session-ID', getSessionId());
  return fetch(url, { ...options, headers });
};

const COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

const EXAMPLE_QUESTIONS = [
  'Show the top five products by revenue',
  'What is our total revenue?',
  'What is the monthly revenue trend?',
  'Show revenue breakdown by city',
  'Which category has the highest units sold?',
  'What is the average order value?',
];

const SCHEMA_COLUMNS = [
  { name: 'order_id', type: 'text', desc: 'Order ID' },
  { name: 'order_date', type: 'date', desc: 'Order date' },
  { name: 'customer_name', type: 'text', desc: 'Customer name' },
  { name: 'city', type: 'text', desc: 'City' },
  { name: 'product_name', type: 'text', desc: 'Product name' },
  { name: 'category', type: 'text', desc: 'Category' },
  { name: 'quantity', type: 'integer', desc: 'Quantity' },
  { name: 'unit_price', type: 'numeric', desc: 'Unit price (₹)' },
];

export default function App() {
  // Navigation: 'analytics' | 'ask-ai' | 'data' | 'history'
  const [activeTab, setActiveTab] = useState('analytics');

  // Interactive table and keyboard controls
  const questionInputRef = useRef(null);
  const [showSchemaDrawer, setShowSchemaDrawer] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  // System Health States
  const [backendStatus, setBackendStatus] = useState({ loading: true, online: false });
  const [dbStatus, setDbStatus] = useState({ loading: true, connected: false, latency: null });

  // Datasets State
  const [datasets, setDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);

  // Dashboard Analytics States
  const [summary, setSummary] = useState(null);
  const [monthlyData, setMonthlyData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [cityData, setCityData] = useState([]);
  const [topProducts, setTopProducts] = useState([]);

  // Preview States
  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Upload States
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);

  // Ask AI States (Phase 5, 6, 7, 8)
  const [question, setQuestion] = useState('Show the top five products by revenue');
  const [generating, setGenerating] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState(null);
  const [copiedSql, setCopiedSql] = useState(false);

  // Execution & Results States
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);

  // Phase 8: AI Explanation & Dynamic Chart States
  const [aiResultExplanation, setAiResultExplanation] = useState(null);
  const [explainingResult, setExplainingResult] = useState(false);
  const [dynamicChartType, setDynamicChartType] = useState(null);

  // Phase 9: Query History States
  const [historyItems, setHistoryItems] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // 1. Health Checks
  const fetchHealth = async () => {
    try {
      const res = await apiFetch(`${API_BASE}/health`);
      setBackendStatus({ loading: false, online: res.ok });
    } catch {
      setBackendStatus({ loading: false, online: false });
    }

    try {
      const res = await apiFetch(`${API_BASE}/health/database`);
      if (res.ok) {
        const data = await res.json();
        setDbStatus({ loading: false, connected: true, latency: data.latency_ms });
      } else {
        setDbStatus({ loading: false, connected: false, latency: null });
      }
    } catch {
      setDbStatus({ loading: false, connected: false, latency: null });
    }
  };

  // 2. Fetch Datasets
  const fetchDatasets = async () => {
    setLoadingDatasets(true);
    try {
      const res = await apiFetch(`${API_BASE}/datasets`);
      if (!res.ok) throw new Error('Failed to load datasets');
      const data = await res.json();
      setDatasets(data);
      if (data.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDatasets(false);
    }
  };

  // 3. Fetch Dashboard Analytics
  const fetchDashboardData = async (datasetId) => {
    if (!datasetId) return;
    try {
      const [sumRes, monRes, catRes, citRes, topRes] = await Promise.all([
        apiFetch(`${API_BASE}/dashboard/${datasetId}/summary`),
        apiFetch(`${API_BASE}/dashboard/${datasetId}/monthly-revenue`),
        apiFetch(`${API_BASE}/dashboard/${datasetId}/category-revenue`),
        apiFetch(`${API_BASE}/dashboard/${datasetId}/city-revenue`),
        apiFetch(`${API_BASE}/dashboard/${datasetId}/top-products?limit=5`),
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (monRes.ok) setMonthlyData(await monRes.json());
      if (catRes.ok) setCategoryData(await catRes.json());
      if (citRes.ok) setCityData(await citRes.json());
      if (topRes.ok) setTopProducts(await topRes.json());
    } catch (err) {
      console.error('Error fetching dashboard analytics:', err);
    }
  };

  // 4. Fetch Dataset Preview
  const fetchPreview = async (datasetId) => {
    if (!datasetId) return;
    setLoadingPreview(true);
    try {
      const res = await apiFetch(`${API_BASE}/datasets/${datasetId}/preview?limit=10`);
      if (res.ok) setPreviewData(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPreview(false);
    }
  };

  // 5. Fetch Query History (Phase 9)
  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const url = selectedDatasetId
        ? `${API_BASE}/query-history?dataset_id=${selectedDatasetId}`
        : `${API_BASE}/query-history`;
      const res = await apiFetch(url);
      if (res.ok) {
        setHistoryItems(await res.json());
      }
    } catch (err) {
      console.error('Failed to load query history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  // 6. Generate SQL (Phase 5)
  const handleGenerateSQL = async (e) => {
    e?.preventDefault();
    if (!selectedDatasetId || !question.trim()) return;

    setGenerating(true);
    setQueryError(null);
    setQueryResult(null);
    setExecutionResult(null);
    setExecutionError(null);
    setAiResultExplanation(null);
    setDynamicChartType(null);
    setCopiedSql(false);

    try {
      const res = await apiFetch(`${API_BASE}/ai/generate-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          question: question.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to generate query');
      setQueryResult(data);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  // 7. Safe SQL Execution (Phase 6) & AI Explanation (Phase 8)
  const handleExecuteSQL = async (customSql = null, customQuestion = null) => {
    const targetSql = customSql || queryResult?.sql;
    const targetQuestion = customQuestion || question;
    if (!selectedDatasetId || !targetSql) return;

    setExecuting(true);
    setExecutionError(null);
    setExecutionResult(null);
    setAiResultExplanation(null);
    setDynamicChartType(null);

    try {
      const res = await apiFetch(`${API_BASE}/ai/execute-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          sql: targetSql,
          question: targetQuestion,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Query execution failed');
      setExecutionResult(data);

      // Refresh history
      fetchHistory();

      // Trigger Phase 8: AI Result Explanation & Chart Recommendation
      if (data.rows && data.rows.length > 0) {
        requestAIExplanation(targetQuestion, data.columns, data.rows, data.row_count);
      }
    } catch (err) {
      setExecutionError(err.message);
    } finally {
      setExecuting(false);
    }
  };

  // Phase 8: Request Plain-English AI Explanation
  const requestAIExplanation = async (userQuestion, cols, rows, totalCount) => {
    setExplainingResult(true);
    try {
      const res = await apiFetch(`${API_BASE}/ai/explain-results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userQuestion,
          columns: cols,
          sample_rows: rows.slice(0, 5),
          total_row_count: totalCount,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setAiResultExplanation(data.explanation);
        setDynamicChartType(data.recommended_chart);
      }
    } catch (err) {
      console.error('Failed to get AI result explanation:', err);
    } finally {
      setExplainingResult(false);
    }
  };

  // 8. Client-side CSV export
  const exportCurrentTableToCSV = () => {
    if (!executionResult || !executionResult.rows.length) return;
    const headers = executionResult.columns.join(',');
    const csvRows = executionResult.rows.map((row) =>
      executionResult.columns.map((col) => `"${row[col] !== undefined ? row[col] : ''}"`).join(',')
    );
    const csvContent = [headers, ...csvRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `insightiq_query_results_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // 9. Copy SQL helper
  const handleCopySQL = () => {
    if (queryResult?.sql) {
      navigator.clipboard.writeText(queryResult.sql);
      setCopiedSql(true);
      setTimeout(() => setCopiedSql(false), 2000);
    }
  };

  // 10. Handle Upload
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const res = await apiFetch(`${API_BASE}/datasets/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      setUploadResult(data);
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';

      await fetchDatasets();
      setSelectedDatasetId(data.dataset_id);
      setActiveTab('analytics');
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // 11. Delete Dataset
  const handleDelete = async (datasetId) => {
    if (!window.confirm('Are you sure you want to delete this dataset? All its records and query history will be removed.')) return;
    try {
      const res = await apiFetch(`${API_BASE}/datasets/${datasetId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      const updated = datasets.filter((d) => d.id !== datasetId);
      setDatasets(updated);
      if (selectedDatasetId === datasetId) {
        const nextId = updated.length > 0 ? updated[0].id : null;
        setSelectedDatasetId(nextId);
      }
    } catch (err) {
      alert(`Error deleting dataset: ${err.message}`);
    }
  };

  // 12. Delete History Item
  const handleDeleteHistory = async (historyId) => {
    try {
      const res = await apiFetch(`${API_BASE}/query-history/${historyId}`, { method: 'DELETE' });
      if (res.ok) {
        setHistoryItems((prev) => prev.filter((h) => h.id !== historyId));
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      fetchDashboardData(selectedDatasetId);
      fetchPreview(selectedDatasetId);
      fetchHistory();
      setQueryResult(null);
      setExecutionResult(null);
      setAiResultExplanation(null);
      setDynamicChartType(null);
    }
  }, [selectedDatasetId]);

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  // Sorting helper for results table
  const handleSort = (columnKey) => {
    setSortConfig((prev) => {
      if (prev.key === columnKey) {
        return {
          key: columnKey,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        };
      }
      return { key: columnKey, direction: 'asc' };
    });
  };

  const getSortedRows = (rows) => {
    if (!rows || !sortConfig.key) return rows || [];
    return [...rows].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }
      return sortConfig.direction === 'asc'
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  };

  // Quick cell filter helper
  const handleCellClick = (col, val) => {
    if (val === null || val === undefined) return;
    const cleanVal = String(val).trim();
    if (!cleanVal || cleanVal === '-' || cleanVal === '—') return;
    setQuestion(`Show records where ${col} is '${cleanVal}'`);
    questionInputRef.current?.focus();
  };

  // Global Keyboard Shortcuts (/ to focus, Cmd/Ctrl+Enter to run, Esc to blur)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
        e.preventDefault();
        setActiveTab('ask-ai');
        setTimeout(() => questionInputRef.current?.focus(), 50);
        return;
      }

      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        if (queryResult?.sql && !executing) {
          handleExecuteSQL();
        } else if (question.trim() && !generating) {
          handleGenerateSQL();
        }
        return;
      }

      if (e.key === 'Escape' && document.activeElement === questionInputRef.current) {
        questionInputRef.current.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [question, generating, executing, queryResult]);

  // Helper for rendering dynamic Recharts chart in Phase 8
  const renderDynamicChart = () => {
    if (!executionResult || !executionResult.rows || executionResult.rows.length === 0) return null;
    const cols = executionResult.columns;
    if (cols.length < 2) return null;

    const labelKey = cols[0];
    const valueKey = cols[1];

    if (dynamicChartType === 'line') {
      return (
        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={executionResult.rows} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey={labelKey} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px' }}
              />
              <Line type="monotone" dataKey={valueKey} stroke="#4f46e5" strokeWidth={3} dot={{ fill: '#4f46e5', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Default to Bar Chart
    return (
      <div className="h-64 w-full pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={executionResult.rows} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey={labelKey} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px' }}
            />
            <Bar dataKey={valueKey} radius={[6, 6, 0, 0]}>
              {executionResult.rows.map((_, index) => (
                <Cell key={`bar-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="flex items-center gap-2 sm:gap-2.5">
              <div className="w-7 h-7 sm:w-8 sm:h-8 bg-slate-900 rounded-lg flex items-center justify-center text-white font-bold text-xs sm:text-sm tracking-tight shadow-sm">
                IQ
              </div>
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="font-semibold text-slate-900 tracking-tight text-sm sm:text-base">InsightIQ</span>
                <span className="text-[10px] sm:text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  v1.0
                </span>
              </div>
            </div>

            {/* Navigation Tabs (Desktop) */}
            <nav className="hidden md:flex items-center space-x-1 pl-6 border-l border-slate-200">
              <button
                onClick={() => setActiveTab('analytics')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'analytics'
                    ? 'bg-slate-900 text-white font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Analytics</span>
              </button>
              <button
                onClick={() => setActiveTab('ask-ai')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'ask-ai'
                    ? 'bg-slate-900 text-white font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Terminal className="w-3.5 h-3.5" />
                <span>Query</span>
              </button>
              <button
                onClick={() => setActiveTab('data')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'data'
                    ? 'bg-slate-900 text-white font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>Datasets</span>
              </button>
              <button
                onClick={() => { setActiveTab('history'); fetchHistory(); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'history'
                    ? 'bg-slate-900 text-white font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <History className="w-3.5 h-3.5" />
                <span>History</span>
              </button>
            </nav>
          </div>

          {/* Right Controls: Dataset Selector */}
          <div className="flex items-center gap-2 sm:gap-3">
            {datasets.length > 0 && (
              <div className="flex items-center gap-1.5 sm:gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2 sm:px-2.5 py-1 max-w-[160px] sm:max-w-[220px] md:max-w-xs">
                <Layers className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <select
                  value={selectedDatasetId || ''}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="bg-transparent text-[11px] sm:text-xs font-medium text-slate-700 outline-none cursor-pointer truncate w-full"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} {d.is_demo ? '(Demo)' : ''} ({d.row_count} rows)
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-5 sm:py-8 pb-24 md:pb-8">
        
        {/* TAB 1: ASK AI (PHASES 5, 6, 7, 8) */}
        {activeTab === 'ask-ai' && (
          <div className="max-w-4xl mx-auto space-y-6">
            {!selectedDataset ? (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center max-w-lg mx-auto shadow-sm">
                <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-slate-900 mb-1">No Dataset Selected</h3>
                <p className="text-xs text-slate-500 mb-6">
                  Select an imported dataset or upload a sales CSV to begin querying.
                </p>
                <button
                  onClick={() => setActiveTab('data')}
                  className="py-2 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg shadow-sm transition cursor-pointer"
                >
                  Upload CSV
                </button>
              </div>
            ) : (
              <>
                {/* Header Card */}
                <div className="bg-white rounded-xl p-4 sm:p-6 border border-slate-200 shadow-sm space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h2 className="text-sm sm:text-base font-semibold text-slate-900 tracking-tight">Query data</h2>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Ask questions in plain English to generate SQL, view charts, and inspect tables.
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        type="button"
                        onClick={() => setShowSchemaDrawer(!showSchemaDrawer)}
                        className={`px-2.5 py-1 text-xs rounded-md border flex items-center gap-1.5 transition cursor-pointer ${
                          showSchemaDrawer
                            ? 'bg-slate-900 text-white border-slate-900 font-medium'
                            : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                        }`}
                        title="Toggle database schema"
                      >
                        <Columns className="w-3.5 h-3.5" />
                        <span>Schema ({SCHEMA_COLUMNS.length})</span>
                      </button>

                      <span className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-mono border border-slate-200 max-w-[150px] sm:max-w-none truncate">
                        {selectedDataset.name}
                      </span>
                    </div>
                  </div>

                  {/* Schema Drawer */}
                  {showSchemaDrawer && (
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-500">
                        <span className="font-medium">Columns in sales table (click any column to append):</span>
                        <span className="text-[10px] font-mono">PostgreSQL</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {SCHEMA_COLUMNS.map((col) => (
                          <button
                            key={col.name}
                            type="button"
                            onClick={() => {
                              setQuestion((prev) => (prev ? `${prev} ${col.name}` : col.name));
                              questionInputRef.current?.focus();
                            }}
                            className="text-xs font-mono px-2 py-1 rounded bg-white hover:bg-slate-200 border border-slate-200 text-slate-700 flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
                            title={`Insert ${col.name} (${col.type})`}
                          >
                            <span className="font-semibold text-slate-900">{col.name}</span>
                            <span className="text-[10px] text-slate-400 font-sans">({col.type})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Question Input Form */}
                  <form onSubmit={handleGenerateSQL} className="space-y-3 pt-1">
                    <div className="relative flex items-center">
                      <input
                        ref={questionInputRef}
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="e.g. Which product generated highest revenue?"
                        className="w-full text-xs sm:text-sm pl-3 sm:pl-4 pr-24 sm:pr-36 py-2.5 sm:py-3 border border-slate-200 rounded-lg outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-400 shadow-sm transition"
                      />
                      <div className="absolute right-20 text-[10px] font-mono bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded border border-slate-200 pointer-events-none hidden sm:block">
                        /
                      </div>
                      <button
                        type="submit"
                        disabled={generating || !question.trim()}
                        className={`absolute right-1 top-1 bottom-1 sm:right-1.5 sm:top-1.5 sm:bottom-1.5 px-3 sm:px-3.5 rounded-md text-xs font-medium flex items-center gap-1 sm:gap-1.5 transition ${
                          generating || !question.trim()
                            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                            : 'bg-slate-900 hover:bg-slate-800 text-white shadow-sm cursor-pointer'
                        }`}
                      >
                        {generating ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span className="hidden sm:inline">Generating...</span>
                          </>
                        ) : (
                          <>
                            <ArrowRight className="w-3.5 h-3.5" />
                            <span className="hidden sm:inline">Generate SQL</span>
                            <span className="sm:hidden font-medium">Generate</span>
                            <span className="text-[10px] opacity-60 font-mono hidden md:inline">⌘↵</span>
                          </>
                        )}
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[11px] font-medium text-slate-400 mr-1">
                        Suggestions:
                      </span>
                      {EXAMPLE_QUESTIONS.map((q, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setQuestion(q)}
                          className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </form>
                </div>

                {/* Skeleton Loader during generation */}
                {generating && (
                  <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-3 animate-pulse shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="h-4 bg-slate-200 rounded w-1/4" />
                      <div className="h-4 bg-slate-100 rounded w-16" />
                    </div>
                    <div className="h-24 bg-slate-900/10 rounded-lg" />
                    <div className="h-3 bg-slate-200 rounded w-2/3" />
                  </div>
                )}

                {/* Generation Error Alert */}
                {queryError && (
                  <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                    <div className="text-xs space-y-1">
                      <p className="font-semibold text-rose-900">Generation Failed</p>
                      <p className="font-mono">{queryError}</p>
                    </div>
                  </div>
                )}

                {/* Generated SQL Preview Card */}
                {queryResult && (
                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-0">
                    <div className="p-3 sm:p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2 bg-slate-50/70">
                      <div className="flex items-center gap-2">
                        <Code2 className="w-4 h-4 text-slate-700" />
                        <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Generated SQL</h3>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {queryResult.latency_ms} ms
                        </span>
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        {queryResult.chart_type && (
                          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 capitalize">
                            {queryResult.chart_type} view
                          </span>
                        )}
                        {queryResult.can_answer && (
                          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            Valid
                          </span>
                        )}
                      </div>
                    </div>

                    {queryResult.sql ? (
                      <div className="relative bg-slate-900 text-slate-100 p-4 font-mono text-xs overflow-x-auto">
                        <button
                          onClick={handleCopySQL}
                          className="absolute right-3 top-3 p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1 text-[11px] cursor-pointer"
                          title="Copy SQL"
                        >
                          {copiedSql ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                        <pre className="pr-16 leading-relaxed whitespace-pre-wrap">{queryResult.sql}</pre>
                      </div>
                    ) : (
                      <div className="p-5 bg-amber-50/70 border-b border-amber-200 text-amber-900 text-xs">
                        <p className="font-semibold mb-1">Cannot Answer from Available Schema</p>
                        <p className="text-amber-800">{queryResult.explanation}</p>
                      </div>
                    )}

                    {queryResult.sql && (
                      <div className="p-4 space-y-3">
                        <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                          {queryResult.explanation}
                        </p>

                        {/* Approval Action Banner */}
                        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div>
                            <p className="font-medium text-slate-900 text-xs">Read-only execution</p>
                            <p className="text-slate-500 text-[11px]">
                              AST validated. 5-second statement timeout.
                            </p>
                          </div>

                          <button
                            onClick={() => handleExecuteSQL()}
                            disabled={executing}
                            className={`px-4 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition shadow-sm w-full sm:w-auto ${
                              executing
                                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                                : 'bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white cursor-pointer'
                            }`}
                          >
                            {executing ? (
                              <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                <span>Running...</span>
                              </>
                            ) : (
                              <>
                                <Play className="w-3.5 h-3.5 fill-current" />
                                <span>Run Query</span>
                                <span className="text-[10px] opacity-60 font-mono hidden md:inline">⌘↵</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Skeleton Loader during execution */}
                {executing && (
                  <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-4 animate-pulse shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="h-4 bg-slate-200 rounded w-1/3" />
                      <div className="h-4 bg-slate-100 rounded w-20" />
                    </div>
                    <div className="space-y-2 pt-1">
                      <div className="h-8 bg-slate-100 rounded" />
                      <div className="h-8 bg-slate-50 rounded" />
                      <div className="h-8 bg-slate-100 rounded" />
                      <div className="h-8 bg-slate-50 rounded" />
                    </div>
                  </div>
                )}

                {/* Execution Error Alert */}
                {executionError && (
                  <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                    <div className="text-xs space-y-1">
                      <p className="font-semibold text-rose-900">Execution Blocked</p>
                      <p className="font-mono">{executionError}</p>
                    </div>
                  </div>
                )}

                {/* Execution Results */}
                {executionResult && !executing && (
                  <div className="space-y-6">
                    {/* Summary / Analysis Card */}
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-slate-900" />
                          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                            Analysis
                          </h4>
                        </div>
                        {dynamicChartType && (
                          <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 capitalize">
                            {dynamicChartType} view
                          </span>
                        )}
                      </div>

                      {explainingResult ? (
                        <div className="flex items-center gap-2 text-xs text-slate-500 py-1">
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Summarizing results...</span>
                        </div>
                      ) : (
                        <p className="text-sm text-slate-800 leading-relaxed font-normal">
                          {aiResultExplanation || `Returned ${executionResult.row_count} matching records.`}
                        </p>
                      )}
                    </div>

                    {/* Dynamic Chart */}
                    {dynamicChartType && dynamicChartType !== 'table' && executionResult.rows.length > 0 && (
                      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Visualization</h3>
                          <span className="text-[11px] text-slate-400 capitalize">
                            {dynamicChartType} chart
                          </span>
                        </div>
                        {renderDynamicChart()}
                      </div>
                    )}

                    {/* Query Results Table */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-0">
                      <div className="p-3 sm:p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 bg-slate-50/70">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Results</h3>
                          <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono border border-slate-200">
                            {executionResult.row_count} rows ({executionResult.execution_time_ms} ms)
                          </span>
                          <span className="text-[10px] text-slate-400 hidden sm:inline">
                            (click headers to sort)
                          </span>
                        </div>

                        <button
                          onClick={exportCurrentTableToCSV}
                          className="py-1 px-2.5 rounded-md text-xs font-medium bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 flex items-center justify-center gap-1.5 transition shadow-sm cursor-pointer self-start sm:self-auto"
                        >
                          <Download className="w-3.5 h-3.5 text-slate-500" />
                          <span>Export CSV</span>
                        </button>
                      </div>

                      {executionResult.rows.length === 0 ? (
                        <div className="p-8 text-center text-xs text-slate-400">
                          Query executed successfully, but returned 0 matching rows.
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                              <tr>
                                {executionResult.columns.map((col, idx) => (
                                  <th
                                    key={idx}
                                    onClick={() => handleSort(col)}
                                    className="py-2.5 px-4 capitalize select-none cursor-pointer hover:bg-slate-100 transition"
                                    title="Click to sort"
                                  >
                                    <div className="flex items-center gap-1.5">
                                      <span>{col.replace(/_/g, ' ')}</span>
                                      {sortConfig.key === col ? (
                                        sortConfig.direction === 'asc' ? (
                                          <ChevronUp className="w-3.5 h-3.5 text-slate-900" />
                                        ) : (
                                          <ChevronDown className="w-3.5 h-3.5 text-slate-900" />
                                        )
                                      ) : (
                                        <ArrowUpDown className="w-3 h-3 text-slate-300 hover:text-slate-500" />
                                      )}
                                    </div>
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
                              {getSortedRows(executionResult.rows).map((row, rIdx) => (
                                <tr key={rIdx} className="hover:bg-slate-50/80 transition">
                                  {executionResult.columns.map((col, cIdx) => {
                                    const val = row[col];
                                    const isNumeric = typeof val === 'number';
                                    const isCurrency = col.toLowerCase().includes('revenue') || col.toLowerCase().includes('price');
                                    return (
                                      <td
                                        key={cIdx}
                                        onClick={() => handleCellClick(col, val)}
                                        className="py-2.5 px-4 cursor-pointer hover:bg-slate-100/90 hover:text-slate-950 transition"
                                        title={`Click to filter by ${col}='${val}'`}
                                      >
                                        {val === null || val === undefined
                                          ? '-'
                                          : isCurrency
                                          ? `₹${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                                          : isNumeric
                                          ? Number(val).toLocaleString()
                                          : String(val)}
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 2: ANALYTICS DASHBOARD */}
        {activeTab === 'analytics' && (
          <div className="space-y-8">
            {!selectedDataset ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto shadow-sm">
                <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-slate-900 mb-1">No Dataset Selected</h3>
                <p className="text-xs text-slate-500 mb-6">
                  Upload a sales CSV to view metrics and charts.
                </p>
                <button
                  onClick={() => setActiveTab('data')}
                  className="py-2 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg shadow-sm transition cursor-pointer"
                >
                  Upload CSV
                </button>
              </div>
            ) : (
              <>
                <div>
                  <h1 className="text-xl font-semibold text-slate-900 tracking-tight">
                    {selectedDataset.name}
                  </h1>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {selectedDataset.row_count.toLocaleString()} transactions from {selectedDataset.original_filename}
                  </p>
                </div>

                {summary && (
                  <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                    <div className="bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                      <div className="flex items-center justify-between text-slate-500 mb-1.5">
                        <span className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-slate-500">Revenue</span>
                        <DollarSign className="w-4 h-4 text-slate-400" />
                      </div>
                      <div>
                        <div className="text-base sm:text-xl font-semibold text-slate-900 tabular-nums">
                          ₹{summary.total_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <span className="text-[10px] sm:text-[11px] text-slate-400">Gross sales</span>
                      </div>
                    </div>

                    <div className="bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                      <div className="flex items-center justify-between text-slate-500 mb-1.5">
                        <span className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-slate-500">Orders</span>
                        <ShoppingCart className="w-4 h-4 text-slate-400" />
                      </div>
                      <div>
                        <div className="text-base sm:text-xl font-semibold text-slate-900 tabular-nums">
                          {summary.total_orders.toLocaleString()}
                        </div>
                        <span className="text-[10px] sm:text-[11px] text-slate-400">Completed</span>
                      </div>
                    </div>

                    <div className="bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                      <div className="flex items-center justify-between text-slate-500 mb-1.5">
                        <span className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-slate-500">Units Sold</span>
                        <Package className="w-4 h-4 text-slate-400" />
                      </div>
                      <div>
                        <div className="text-base sm:text-xl font-semibold text-slate-900 tabular-nums">
                          {summary.total_units_sold.toLocaleString()}
                        </div>
                        <span className="text-[10px] sm:text-[11px] text-slate-400">Items</span>
                      </div>
                    </div>

                    <div className="bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                      <div className="flex items-center justify-between text-slate-500 mb-1.5">
                        <span className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-slate-500">Customers</span>
                        <Users className="w-4 h-4 text-slate-400" />
                      </div>
                      <div>
                        <div className="text-base sm:text-xl font-semibold text-slate-900 tabular-nums">
                          {summary.unique_customers.toLocaleString()}
                        </div>
                        <span className="text-[10px] sm:text-[11px] text-slate-400">Unique</span>
                      </div>
                    </div>

                    <div className="bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between col-span-2 sm:col-span-1">
                      <div className="flex items-center justify-between text-slate-500 mb-1.5">
                        <span className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-slate-500">Avg Order</span>
                        <TrendingUp className="w-4 h-4 text-slate-400" />
                      </div>
                      <div>
                        <div className="text-base sm:text-xl font-semibold text-slate-900 tabular-nums">
                          ₹{summary.average_order_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <span className="text-[10px] sm:text-[11px] text-slate-400">Per order</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Monthly Revenue</h3>
                      <span className="text-[11px] text-slate-400">₹ in thousands</span>
                    </div>

                    <div className="h-64 w-full pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={monthlyData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                          <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                          <YAxis
                            tick={{ fontSize: 11, fill: '#64748b' }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                          />
                          <Tooltip
                            formatter={(value) => [`₹${Number(value).toLocaleString()}`, 'Revenue']}
                            labelFormatter={(label) => `Month: ${label}`}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px' }}
                          />
                          <Line
                            type="monotone"
                            dataKey="revenue"
                            stroke="#4f46e5"
                            strokeWidth={3}
                            dot={{ fill: '#4f46e5', strokeWidth: 2, r: 4 }}
                            activeDot={{ r: 6 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Category Revenue</h3>
                      <span className="text-[11px] text-slate-400">By segment</span>
                    </div>

                    <div className="h-64 w-full pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={categoryData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                          <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                          <YAxis
                            tick={{ fontSize: 11, fill: '#64748b' }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                          />
                          <Tooltip
                            formatter={(value) => [`₹${Number(value).toLocaleString()}`, 'Revenue']}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '12px' }}
                          />
                          <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                            {categoryData.map((_, index) => (
                              <Cell key={`cat-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">City Revenue</h3>
                      <span className="text-[11px] text-slate-400">By location</span>
                    </div>

                    <div className="h-64 w-full pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={cityData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                          <XAxis dataKey="city" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                          <YAxis
                            tick={{ fontSize: 11, fill: '#64748b' }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                          />
                          <Tooltip
                            formatter={(value) => [`₹${Number(value).toLocaleString()}`, 'Revenue']}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '12px' }}
                          />
                          <Bar dataKey="revenue" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Top 5 Products</h3>
                      <span className="text-[11px] text-slate-400">By revenue</span>
                    </div>

                    <div className="h-64 w-full pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={topProducts}
                          layout="vertical"
                          margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                          <XAxis
                            type="number"
                            tick={{ fontSize: 11, fill: '#64748b' }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                          />
                          <YAxis
                            type="category"
                            dataKey="product_name"
                            tick={{ fontSize: 10, fill: '#334155' }}
                            width={110}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip
                            formatter={(value) => [`₹${Number(value).toLocaleString()}`, 'Revenue']}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '12px' }}
                          />
                          <Bar dataKey="revenue" fill="#10b981" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* TAB 3: QUERY HISTORY (PHASE 9) */}
        {activeTab === 'history' && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-slate-900 tracking-tight">Query history</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Past queries with execution status, row counts, and CSV exports.
                  </p>
                </div>

                <button
                  onClick={fetchHistory}
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
                  title="Refresh history"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              {loadingHistory && historyItems.length === 0 ? (
                <p className="text-xs text-slate-400 py-12 text-center">Loading history...</p>
              ) : historyItems.length === 0 ? (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No queries run yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {historyItems.map((item) => (
                    <div
                      key={item.id}
                      className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-slate-50 transition space-y-2.5"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2.5 sm:gap-4">
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-slate-900">{item.question}</p>
                          <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                            <span>{new Date(item.created_at).toLocaleString()}</span>
                            <span>•</span>
                            <span className="text-slate-700 font-medium">{item.row_count} rows</span>
                            <span>•</span>
                            <span className="capitalize">{item.status}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0 self-start sm:self-auto">
                          {/* Re-run button */}
                          <button
                            onClick={() => {
                              setQuestion(item.question);
                              setActiveTab('ask-ai');
                              handleExecuteSQL(item.generated_sql, item.question);
                            }}
                            className="py-1 px-2.5 rounded-md text-[11px] font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition flex items-center gap-1 cursor-pointer"
                            title="Re-run query"
                          >
                            <RotateCcw className="w-3 h-3" />
                            <span>Re-run</span>
                          </button>

                          {/* Export CSV button */}
                          <a
                            href={`${API_BASE}/query-history/${item.id}/export`}
                            className="py-1 px-2.5 rounded-md text-[11px] font-medium bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 transition flex items-center gap-1 cursor-pointer"
                            title="Download CSV"
                          >
                            <Download className="w-3 h-3 text-slate-500" />
                            <span>CSV</span>
                          </a>

                          {/* Delete button */}
                          <button
                            onClick={() => handleDeleteHistory(item.id)}
                            className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition cursor-pointer"
                            title="Delete record"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {item.generated_sql && (
                        <div className="bg-slate-900 text-slate-200 p-2.5 rounded-lg text-[11px] font-mono overflow-x-auto">
                          <code>{item.generated_sql}</code>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: DATA MANAGEMENT */}
        {activeTab === 'data' && (
          <div className="space-y-8">
            <section className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <Upload className="w-4 h-4 text-slate-700" />
                <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Upload sales CSV</h2>
              </div>

              <form onSubmit={handleUpload} className="space-y-4">
                <div className="border border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-6 text-center transition bg-slate-50/50">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    id="csv-file-input"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setUploadFile(e.target.files[0]);
                        setUploadError(null);
                      }
                    }}
                  />
                  <label htmlFor="csv-file-input" className="cursor-pointer flex flex-col items-center">
                    <FileSpreadsheet className="w-8 h-8 text-slate-400 mb-2" />
                    <span className="text-sm font-medium text-slate-800">
                      {uploadFile ? uploadFile.name : 'Drop a CSV file here, or click to browse'}
                    </span>
                    <span className="text-xs text-slate-400 mt-1">
                      Columns: order_id, order_date, customer_name, city, product_name, category, quantity, unit_price
                    </span>
                    {uploadFile && (
                      <span className="text-xs font-mono text-slate-600 mt-2 bg-slate-100 px-2 py-0.5 rounded">
                        {(uploadFile.size / 1024).toFixed(1)} KB
                      </span>
                    )}
                  </label>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <p className="text-[11px] sm:text-xs text-slate-400">
                    Sample file: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 font-mono">sample_data/sales_sample.csv</code>
                  </p>
                  <button
                    type="submit"
                    disabled={!uploadFile || uploading}
                    className={`py-2 px-4 rounded-lg text-xs font-medium transition flex items-center justify-center gap-1.5 w-full sm:w-auto ${
                      !uploadFile || uploading
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : 'bg-slate-900 hover:bg-slate-800 text-white shadow-sm cursor-pointer'
                    }`}
                  >
                    {uploading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Ingesting...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-3.5 h-3.5" />
                        <span>Upload CSV</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              {uploadResult && (
                <div className="mt-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                  <div className="text-xs space-y-1">
                    <p className="font-semibold text-emerald-900">
                      Imported '{uploadResult.filename}'
                    </p>
                    <p>
                      Total: <span className="font-mono font-medium">{uploadResult.total_rows}</span> | 
                      Imported: <span className="font-mono font-medium text-emerald-700">{uploadResult.imported_rows}</span> | 
                      Rejected: <span className="font-mono font-medium">{uploadResult.rejected_rows}</span>
                    </p>
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                  <div className="text-xs space-y-1">
                    <p className="font-semibold text-rose-900">Upload failed</p>
                    <p className="font-mono">{uploadError}</p>
                  </div>
                </div>
              )}
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">Imported datasets</h3>
                  <span className="text-[11px] px-2 py-0.5 bg-slate-100 rounded font-mono text-slate-600 border border-slate-200">
                    {datasets.length}
                  </span>
                </div>

                {loadingDatasets && datasets.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">Loading datasets...</p>
                ) : datasets.length === 0 ? (
                  <div className="text-center py-8 text-slate-400 text-xs">
                    No datasets uploaded yet.
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {datasets.map((d) => (
                      <li
                        key={d.id}
                        onClick={() => setSelectedDatasetId(d.id)}
                        className={`p-3 rounded-lg border text-xs cursor-pointer transition flex items-center justify-between ${
                          selectedDatasetId === d.id
                            ? 'border-slate-900 bg-slate-50 font-medium'
                            : 'border-slate-200 bg-white hover:bg-slate-50'
                        }`}
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-slate-900">{d.name}</p>
                            {d.is_demo && (
                              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Demo
                              </span>
                            )}
                          </div>
                          <p className="text-slate-400 text-[11px] font-mono">
                            {d.row_count} rows • {new Date(d.created_at).toLocaleDateString()}
                          </p>
                        </div>

                        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                          {!d.is_demo && (
                            <button
                              onClick={() => handleDelete(d.id)}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition cursor-pointer"
                              title="Delete dataset"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="lg:col-span-2 bg-white rounded-xl p-5 border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
                    Dataset preview {previewData ? `(${previewData.filename})` : ''}
                  </h3>
                  {previewData && (
                    <span className="text-xs text-slate-400">
                      Showing {previewData.preview_count} of {previewData.total_rows} rows
                    </span>
                  )}
                </div>

                {loadingPreview ? (
                  <p className="text-xs text-slate-400 py-12 text-center">Loading preview...</p>
                ) : !previewData || previewData.rows.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 text-xs">
                    Select a dataset to preview records.
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                        <tr>
                          <th className="py-2.5 px-3">Order ID</th>
                          <th className="py-2.5 px-3">Date</th>
                          <th className="py-2.5 px-3">Customer</th>
                          <th className="py-2.5 px-3">City</th>
                          <th className="py-2.5 px-3">Product</th>
                          <th className="py-2.5 px-3">Category</th>
                          <th className="py-2.5 px-3 text-right">Qty</th>
                          <th className="py-2.5 px-3 text-right">Price</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
                        {previewData.rows.map((r) => (
                          <tr key={r.id} className="hover:bg-slate-50/70 transition">
                            <td className="py-2 px-3 font-semibold text-slate-900">{r.order_id}</td>
                            <td className="py-2 px-3">{r.order_date}</td>
                            <td className="py-2 px-3 font-sans font-medium text-slate-800">{r.customer_name}</td>
                            <td className="py-2 px-3">{r.city}</td>
                            <td className="py-2 px-3 font-sans text-slate-800">{r.product_name}</td>
                            <td className="py-2 px-3">
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700">
                                {r.category}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-right font-semibold">{r.quantity}</td>
                            <td className="py-2 px-3 text-right font-semibold">₹{Number(r.unit_price).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white/95 backdrop-blur-md border-t border-slate-200 px-3 py-1.5 flex items-center justify-around shadow-lg">
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg text-[10px] font-medium transition cursor-pointer ${
            activeTab === 'analytics'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Analytics</span>
        </button>
        <button
          onClick={() => setActiveTab('ask-ai')}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg text-[10px] font-medium transition cursor-pointer ${
            activeTab === 'ask-ai'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>Query</span>
        </button>
        <button
          onClick={() => setActiveTab('data')}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg text-[10px] font-medium transition cursor-pointer ${
            activeTab === 'data'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Datasets</span>
        </button>
        <button
          onClick={() => { setActiveTab('history'); fetchHistory(); }}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg text-[10px] font-medium transition cursor-pointer ${
            activeTab === 'history'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          <History className="w-4 h-4" />
          <span>History</span>
        </button>
      </nav>
    </div>
  );
}
