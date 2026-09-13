import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  Server, 
  ShieldCheck, 
  Database, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Terminal,
  Activity,
  Layers,
  Key,
  Lock,
  Trash2,
} from 'lucide-react';
import { api, type SystemInfo, type HealthResponse } from '../lib/api';
import { usePlatform } from '../contexts/PlatformContext';

export const SystemSettings: React.FC = () => {
  const { currentRole, currentUser } = usePlatform();
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [testingDiagnostics, setTestingDiagnostics] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Retention cleanup state
  const [retentionDryRun, setRetentionDryRun] = useState<boolean>(true);
  const [cleaningRetention, setCleaningRetention] = useState<boolean>(false);
  const [retentionResult, setRetentionResult] = useState<any>(null);
  const [retentionError, setRetentionError] = useState<string | null>(null);

  const fetchSystemData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [infoRes, healthRes] = await Promise.all([
        api.systemInfo(),
        api.health(),
      ]);
      setSystemInfo(infoRes);
      setHealth(healthRes);
    } catch (err: any) {
      console.error('Failed to load system settings:', err);
      setError(err.message || 'Failed to retrieve platform configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemData();
  }, []);

  const runDiagnostics = async () => {
    setTestingDiagnostics(true);
    try {
      const healthRes = await api.health();
      setHealth(healthRes);
    } catch (err: any) {
      console.error('Diagnostics check failed:', err);
    } finally {
      setTestingDiagnostics(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <SettingsIcon className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Platform Configuration & System Health</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Real environment configuration, AI runtime models, cluster endpoints, and zero-trust security parameters.
          </p>
        </div>
        <button
          onClick={runDiagnostics}
          disabled={testingDiagnostics}
          className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-sm"
        >
          <Activity className={`h-3.5 w-3.5 ${testingDiagnostics ? 'animate-spin' : ''}`} />
          Run Live Diagnostics
        </button>
      </div>

      {loading ? (
        <div className="p-16 text-center text-sm text-muted-foreground flex flex-col items-center gap-3">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span>Retrieving system settings from backend...</span>
        </div>
      ) : error ? (
        <div className="p-8 text-center text-sm text-destructive flex flex-col items-center gap-2">
          <AlertCircle className="h-6 w-6" />
          <span>{error}</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Subsystem Health Status Grid */}
          <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" />
                Live Subsystem Health Probes ({health?.status || 'UNKNOWN'})
              </h2>
              <span className="text-[11px] font-mono text-muted-foreground">
                Checked: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3">
              {health && Object.entries(health.dependencies || {}).map(([name, dep]: [string, any]) => {
                const statusStr = typeof dep === 'string' ? dep : dep?.status || 'unknown';
                const isHealthy = statusStr === 'healthy';
                const latency = typeof dep === 'object' && dep?.latency_ms !== undefined ? `${dep.latency_ms.toFixed(1)}ms` : 'active';
                return (
                  <div key={name} className="p-3 bg-muted/30 border border-border rounded-md text-center space-y-1">
                    <div className="text-[10px] font-mono uppercase text-muted-foreground truncate">{name}</div>
                    <div className="flex items-center justify-center gap-1">
                      <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-destructive'}`} />
                      <span className="text-xs font-bold font-mono uppercase text-foreground">{statusStr}</span>
                    </div>
                    <div className="text-[10px] font-mono text-muted-foreground">{latency}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* AI Engine Configuration */}
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <Cpu className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">AI Engine & Local LLM Runtime</h3>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Provider:</span>
                  <span className="font-semibold text-foreground">{systemInfo?.ai_engine?.provider || 'Ollama (Local)'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">LLM Model:</span>
                  <span className="font-semibold text-primary">{systemInfo?.ai_engine?.llm_model || 'llama3.2'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Embedding Model:</span>
                  <span className="font-semibold text-primary">{systemInfo?.ai_engine?.embedding_model || 'nomic-embed-text'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Embedding Dimension:</span>
                  <span className="text-foreground">768-dim (dense vectors)</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Context Window:</span>
                  <span className="text-foreground">{systemInfo?.ai_engine?.context_length || 4096} tokens</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-muted-foreground">Hardware Acceleration:</span>
                  <span className="text-emerald-500 font-semibold">{systemInfo?.ai_engine?.gpu_acceleration || 'CUDA (RTX 3050 Ti Laptop GPU)'}</span>
                </div>
              </div>
            </div>

            {/* Infrastructure Endpoints */}
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <Server className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">Connected Infrastructure</h3>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Kubernetes Cluster:</span>
                  <span className="text-foreground truncate max-w-[240px]" title={systemInfo?.infrastructure?.kubernetes_endpoint}>
                    {systemInfo?.infrastructure?.kubernetes_endpoint || 'k3s v1.31.5'}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Target Namespace:</span>
                  <span className="text-foreground">{systemInfo?.platform?.namespace || 'sentinelops-e2e'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Prometheus Endpoint:</span>
                  <span className="text-foreground">{systemInfo?.infrastructure?.prometheus_url || 'http://127.0.0.1:9090'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Loki Log Engine:</span>
                  <span className="text-foreground">{systemInfo?.infrastructure?.loki_url || 'http://127.0.0.1:3100'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Redis Streams:</span>
                  <span className="text-foreground">{systemInfo?.infrastructure?.redis_host || '127.0.0.1:6380'}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-muted-foreground">PostgreSQL DB:</span>
                  <span className="text-foreground">{systemInfo?.infrastructure?.postgres_host || '127.0.0.1:5433 (sentinelops_dev)'}</span>
                </div>
              </div>
            </div>

            {/* Zero-Trust Security & RBAC Governance */}
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <ShieldCheck className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">Zero-Trust Security & Governance</h3>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded border border-border">
                  <div>
                    <div className="text-xs font-semibold text-foreground">Zero-Trust Tool Enclave</div>
                    <div className="text-[11px] text-muted-foreground">Restricts all agent tool calls to strict READ_ONLY whitelist</div>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-semibold">
                    ACTIVE
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded border border-border">
                  <div>
                    <div className="text-xs font-semibold text-foreground">Automatic Secret Redactor</div>
                    <div className="text-[11px] text-muted-foreground">Strips JWTs, API tokens, passwords, and private keys from prompts & logs</div>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-semibold">
                    ACTIVE
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded border border-border">
                  <div>
                    <div className="text-xs font-semibold text-foreground">Human-in-the-Loop Remediation</div>
                    <div className="text-[11px] text-muted-foreground">Requires operator confirmation before executing corrective actions</div>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20 font-semibold">
                    REQUIRED
                  </span>
                </div>
              </div>
            </div>

            {/* Platform Runtime Information */}
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <Terminal className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">Platform Runtime Details</h3>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Platform Name:</span>
                  <span className="text-foreground font-semibold">SentinelOps AI Enterprise</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Release Version:</span>
                  <span className="text-foreground">{systemInfo?.platform?.version || '1.0.0-prod'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Environment:</span>
                  <span className="text-foreground capitalize">{systemInfo?.platform?.environment || 'production'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Operator Session:</span>
                  <span className="text-primary font-semibold font-mono">
                    {currentUser ? `${currentUser.username} (${currentUser.user_id})` : 'operator (usr-op)'}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Active Role:</span>
                  <span className={`font-semibold uppercase ${
                    currentRole === 'admin' ? 'text-amber-400' : currentRole === 'operator' ? 'text-emerald-400' : 'text-sky-400'
                  }`}>
                    {currentRole} {currentRole === 'admin' ? '(Full Governance)' : currentRole === 'operator' ? '(Actions & Tools)' : '(Read Only)'}
                  </span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-muted-foreground">Audit Retention:</span>
                  <span className="text-foreground">90 days (persistent disk logging)</span>
                </div>
              </div>
            </div>

            {/* Admin Data Retention Policy Governance Panel */}
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4 md:col-span-2">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Trash2 className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-foreground">Data Retention & Purge Policy Management</h3>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                  currentRole === 'admin'
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-muted text-muted-foreground border border-border'
                }`}>
                  {currentRole === 'admin' ? 'Admin Authorized' : 'Admin Role Required'}
                </span>
              </div>

              <p className="text-xs text-muted-foreground">
                Enforce platform data retention limits across historical investigations and persistent audit logs.
                Viewer and Operator roles are restricted from executing purges.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-1">
                <label className="flex items-center gap-2 text-xs font-mono text-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={retentionDryRun}
                    onChange={(e) => setRetentionDryRun(e.target.checked)}
                    className="rounded border-border text-primary focus:ring-primary h-4 w-4 bg-muted"
                  />
                  <span>Dry Run (Simulate purge without deleting records)</span>
                </label>

                {currentRole === 'admin' ? (
                  <button
                    onClick={async () => {
                      setCleaningRetention(true);
                      setRetentionError(null);
                      try {
                        const res = await api.retentionCleanup(retentionDryRun);
                        setRetentionResult(res);
                      } catch (err: any) {
                        setRetentionError(err.message || 'Failed to execute retention policy');
                      } finally {
                        setCleaningRetention(false);
                      }
                    }}
                    disabled={cleaningRetention}
                    data-testid="execute-retention-btn"
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-amber-600 hover:bg-amber-500 text-white transition disabled:opacity-50 font-mono shadow-sm"
                  >
                    <Trash2 className={`h-3.5 w-3.5 ${cleaningRetention ? 'animate-spin' : ''}`} />
                    <span>{cleaningRetention ? 'Executing...' : retentionDryRun ? 'Execute Retention (Dry Run)' : 'Execute Live Purge'}</span>
                  </button>
                ) : (
                  <div className="relative group">
                    <button
                      disabled
                      data-testid="execute-retention-btn"
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-slate-800 text-gray-500 border border-slate-700 cursor-not-allowed opacity-70 font-mono"
                      title="Requires Admin role to execute retention policy"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      <span>Execute Retention (Admin Only)</span>
                    </button>
                    <span className="hidden group-hover:block absolute left-0 top-full mt-1.5 z-30 px-2 py-1 text-[10px] font-mono bg-slate-900 border border-slate-700 text-amber-300 rounded shadow whitespace-nowrap">
                      Requires Admin role to execute retention cleanup
                    </span>
                  </div>
                )}
              </div>

              {retentionError && (
                <div className="p-3 rounded bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{retentionError}</span>
                </div>
              )}

              {retentionResult && (
                <div className="p-3 rounded bg-muted/40 border border-border text-xs font-mono space-y-2 mt-2">
                  <div className="flex items-center justify-between font-bold text-foreground">
                    <span>Execution Report (Dry Run: {String(retentionResult.dry_run)})</span>
                    <span className="text-emerald-400">Success</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <div className="p-2 bg-card rounded border border-border">
                      <div className="text-muted-foreground text-[10px] uppercase">Investigations</div>
                      <div className="text-foreground mt-0.5">
                        Scanned: {retentionResult.investigations?.scanned || 0} | Expired: {retentionResult.investigations?.expired || 0} | Deleted: {retentionResult.investigations?.deleted || 0}
                      </div>
                    </div>
                    <div className="p-2 bg-card rounded border border-border">
                      <div className="text-muted-foreground text-[10px] uppercase">Audit Trail</div>
                      <div className="text-foreground mt-0.5">
                        Scanned: {retentionResult.audit_trail?.scanned || 0} | Expired: {retentionResult.audit_trail?.expired || 0} | Deleted: {retentionResult.audit_trail?.deleted || 0}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
