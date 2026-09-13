import React, { useState, useEffect } from 'react';
import { 
  Wrench, 
  Terminal, 
  Play, 
  ShieldCheck, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Code,
  Layers,
  Search
} from 'lucide-react';
import { api, type ToolMetadata, type ToolCallRecord } from '../lib/api';
import { usePlatform } from '../contexts/PlatformContext';

export const Tools: React.FC = () => {
  const { currentRole } = usePlatform();
  const [tools, setTools] = useState<ToolMetadata[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Execution modal/state
  const [executingTool, setExecutingTool] = useState<ToolMetadata | null>(null);
  const [execArgs, setExecArgs] = useState<string>('{}');
  const [executing, setExecuting] = useState<boolean>(false);
  const [execResult, setExecResult] = useState<ToolCallRecord | null>(null);
  const [execError, setExecError] = useState<string | null>(null);

  const fetchTools = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listTools();
      setTools(res.tools || []);
    } catch (err: any) {
      console.error('Failed to fetch tools registry:', err);
      setError(err.message || 'Failed to retrieve registered investigation tools');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  const categories = ['all', ...Array.from(new Set(tools.map((t) => t.category).filter(Boolean)))];

  const filteredTools = tools.filter((t) => {
    const matchesCategory = selectedCategory === 'all' || t.category === selectedCategory;
    const matchesSearch = 
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleOpenExecute = (tool: ToolMetadata) => {
    setExecutingTool(tool);
    setExecResult(null);
    setExecError(null);
    // Provide sensible default parameters
    const defaultParams: Record<string, any> = {};
    if (tool.required_params && tool.required_params.length > 0) {
      tool.required_params.forEach((param: string) => {
        if (param === 'namespace') defaultParams[param] = 'sentinelops-e2e';
        else if (param === 'pod_name') defaultParams[param] = 'crashloop-workload';
        else if (param === 'limit') defaultParams[param] = 50;
        else if (param === 'query') defaultParams[param] = '{namespace="sentinelops-e2e"}';
        else defaultParams[param] = '';
      });
    } else if (tool.parameters) {
      Object.keys(tool.parameters).forEach((param) => {
        if (param === 'namespace') defaultParams[param] = 'sentinelops-e2e';
      });
    }
    setExecArgs(JSON.stringify(defaultParams, null, 2));
  };

  const handleExecute = async () => {
    if (!executingTool) return;
    setExecuting(true);
    setExecError(null);
    setExecResult(null);
    try {
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(execArgs);
      } catch (e) {
        throw new Error('Invalid JSON arguments format');
      }

      const res = await api.executeTool(executingTool.name, parsedArgs);
      setExecResult(res.call_record);
    } catch (err: any) {
      console.error('Failed to execute tool:', err);
      setExecError(err.message || 'Tool execution encountered an error');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Wrench className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Diagnostic Tool Registry</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Read-only diagnostic capabilities authorized for autonomous agent investigation with zero-trust RBAC enclaves.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded">
            <ShieldCheck className="h-3.5 w-3.5" />
            READ_ONLY ENFORCED
          </span>
          <button
            onClick={fetchTools}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded border border-border bg-card hover:bg-muted text-foreground transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="flex flex-wrap gap-1.5 w-full sm:w-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize ${
                selectedCategory === cat
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : 'bg-card border border-border text-muted-foreground hover:text-foreground'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search tools..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-muted/40 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary text-foreground placeholder:text-muted-foreground"
          />
        </div>
      </div>

      {/* Tools Grid */}
      {loading ? (
        <div className="p-16 text-center text-sm text-muted-foreground flex flex-col items-center gap-3">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span>Discovering authorized diagnostic tools from backend registry...</span>
        </div>
      ) : error ? (
        <div className="p-8 text-center text-sm text-destructive flex flex-col items-center gap-2">
          <AlertCircle className="h-6 w-6" />
          <span>{error}</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool) => (
            <div
              key={tool.name}
              className="bg-card border border-border rounded-lg p-4 shadow-sm hover:border-border/80 transition-colors flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground font-mono">{tool.name}</h3>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-muted border border-border text-muted-foreground uppercase">
                      {tool.category || 'general'}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {tool.timeout_seconds || 15}s
                  </span>
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed">
                  {tool.description}
                </p>

                {tool.required_params && tool.required_params.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase text-muted-foreground">Required Parameters:</span>
                    <div className="flex flex-wrap gap-1">
                      {tool.required_params.map((p: string) => (
                        <span key={p} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-border mt-4 flex items-center justify-between">
                <span className="text-[10px] font-mono text-muted-foreground uppercase flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3 text-emerald-500" />
                  {tool.permission || 'READ_ONLY'}
                </span>
                {currentRole === "viewer" ? (
                  <button
                    disabled
                    data-testid="run-tool-btn"
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded bg-muted/40 text-muted-foreground/40 border border-border/50 cursor-not-allowed"
                    title="Requires Operator or Admin role"
                  >
                    <Play className="h-3 w-3" />
                    Run Tool
                  </button>
                ) : (
                  <button
                    onClick={() => handleOpenExecute(tool)}
                    data-testid="run-tool-btn"
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded bg-muted hover:bg-primary hover:text-primary-foreground text-foreground transition-colors"
                  >
                    <Play className="h-3 w-3" />
                    Run Tool
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Execution Modal */}
      {executingTool && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-lg shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-bold text-foreground font-mono">
                  Execute: {executingTool.name}
                </h3>
              </div>
              <button
                onClick={() => setExecutingTool(null)}
                className="text-muted-foreground hover:text-foreground text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">
                {executingTool.description}
              </p>
              <label className="text-xs font-mono text-foreground block font-semibold">
                Arguments (JSON format):
              </label>
              <textarea
                value={execArgs}
                onChange={(e) => setExecArgs(e.target.value)}
                rows={4}
                className="w-full p-2.5 bg-muted/40 border border-border rounded font-mono text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setExecutingTool(null)}
                className="px-3 py-1.5 text-xs rounded border border-border text-muted-foreground hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={handleExecute}
                disabled={executing}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-primary text-primary-foreground hover:bg-primary/90 flex items-center gap-2 disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5" />
                    Execute in Cluster
                  </>
                )}
              </button>
            </div>

            {/* Execution Result */}
            {execError && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{execError}</span>
              </div>
            )}

            {execResult && (
              <div className="space-y-2 pt-3 border-t border-border">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold font-mono text-foreground flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    Execution Success ({(execResult.latency_ms ?? execResult.duration_ms ?? 0).toFixed(1)}ms)
                  </span>
                  <span className="text-[10px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                    Secrets Redacted
                  </span>
                </div>
                <pre className="p-3 bg-muted/50 border border-border rounded font-mono text-xs text-foreground overflow-x-auto max-h-64 whitespace-pre-wrap">
                  {JSON.stringify(execResult.result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
