import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Filter, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  RefreshCw,
  Eye,
  Key,
  Database,
  ChevronDown,
  ChevronRight,
  UserCheck
} from 'lucide-react';
import { api, type AuditEvent } from '../lib/api';

export const Audit: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter & Search
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchAuditEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.auditEvents(100);
      setEvents(res.events || []);
      setTotal(res.count || (res.events ? res.events.length : 0));
    } catch (err: any) {
      console.error('Failed to fetch audit trail:', err);
      setError(err.message || 'Failed to query persistent audit trail');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
  }, []);

  const filteredEvents = events.filter((e) => {
    const matchesStatus = statusFilter === 'all' || e.execution_status === statusFilter;
    const matchesSearch = 
      (e.actor && e.actor.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (e.action && e.action.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (e.event_id && e.event_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (e.investigation_id && e.investigation_id.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Security & Governance Audit Trail</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Immutable, zero-trust audit records capturing autonomous tool executions, AI investigations, and operator access.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 bg-muted border border-border text-foreground rounded">
            <Key className="h-3.5 w-3.5 text-primary" />
            SECRET REDACTION ACTIVE
          </span>
          <button
            onClick={fetchAuditEvents}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded border border-border bg-card hover:bg-muted text-foreground transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="flex gap-2">
          {['all', 'success', 'failed', 'denied'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize ${
                statusFilter === status
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : 'bg-card border border-border text-muted-foreground hover:text-foreground'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by actor, action, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-muted/40 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary text-foreground placeholder:text-muted-foreground"
          />
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
        <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Immutable Event Records</h3>
            <span className="text-xs font-mono bg-muted px-2 py-0.5 rounded text-muted-foreground">
              {filteredEvents.length} events
            </span>
          </div>
        </div>

        {loading ? (
          <div className="p-16 text-center text-sm text-muted-foreground flex flex-col items-center gap-3">
            <RefreshCw className="h-6 w-6 animate-spin text-primary" />
            <span>Reading persistent audit records from disk...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-destructive flex flex-col items-center gap-2">
            <AlertCircle className="h-6 w-6" />
            <span>{error}</span>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-12 text-center text-sm text-muted-foreground">
            No audit records match the selected filter.
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filteredEvents.map((e) => {
              const isExpanded = expandedId === e.event_id;
              return (
                <div key={e.event_id} className="hover:bg-muted/30 transition-colors">
                  <div 
                    onClick={() => toggleExpand(e.event_id)}
                    className="p-4 flex items-center justify-between cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="text-muted-foreground">
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-semibold text-foreground">
                            {e.action || 'investigation_action'}
                          </span>
                          <span className={`text-[10px] font-mono px-2 py-0.2 rounded ${
                            e.execution_status === 'success'
                              ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                              : e.execution_status === 'denied'
                              ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                              : 'bg-destructive/10 text-destructive border border-destructive/20'
                          }`}>
                            {e.execution_status || 'recorded'}
                          </span>
                          {e.role && (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-muted border border-border text-muted-foreground">
                              Role: {e.role}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
                          <span className="flex items-center gap-1">
                            <UserCheck className="h-3 w-3" />
                            Actor: {e.actor}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(e.timestamp).toLocaleTimeString()}
                          </span>
                          {e.duration_ms !== undefined && e.duration_ms > 0 && (
                            <>
                              <span>•</span>
                              <span>{e.duration_ms.toFixed(1)}ms</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="text-right font-mono text-xs text-muted-foreground">
                      <div className="truncate max-w-[180px]">{e.event_id.slice(0, 16)}...</div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="px-12 pb-4 pt-1 border-t border-border/50 bg-muted/20 space-y-3">
                      {e.investigation_id && (
                        <div className="text-xs font-mono">
                          <span className="text-muted-foreground">Investigation ID: </span>
                          <span className="text-primary font-semibold">{e.investigation_id}</span>
                        </div>
                      )}

                      {e.selected_tools && e.selected_tools.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-mono uppercase text-muted-foreground">Tools Executed:</span>
                          <div className="flex flex-wrap gap-1.5">
                            {e.selected_tools.map((t) => (
                              <span key={t} className="text-xs font-mono px-2 py-0.5 rounded bg-muted border border-border text-foreground">
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {e.evidence_sources && e.evidence_sources.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-mono uppercase text-muted-foreground">Evidence Sources:</span>
                          <div className="flex flex-wrap gap-1.5">
                            {e.evidence_sources.map((s) => (
                              <span key={s} className="text-xs font-mono px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {e.final_rca && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-mono uppercase text-muted-foreground">Deterministic RCA:</span>
                          <div className="p-3 bg-card border border-border rounded text-xs font-mono text-foreground whitespace-pre-wrap">
                            {e.final_rca}
                          </div>
                        </div>
                      )}

                      {e.sanitized_arguments && Object.keys(e.sanitized_arguments).length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-mono uppercase text-muted-foreground">Sanitized Arguments:</span>
                          <pre className="p-2.5 bg-card border border-border rounded text-[11px] font-mono text-foreground overflow-x-auto">
                            {JSON.stringify(e.sanitized_arguments, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
