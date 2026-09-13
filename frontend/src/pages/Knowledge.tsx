import React, { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import {
  BookOpen,
  Search,
  FileText,
  Layers,
  AlertCircle,
  RefreshCw,
  Database,
  CheckCircle2,
  ArrowLeft,
  Clock,
  Sparkles,
  ArrowUpRight,
} from "lucide-react";
import {
  api,
  type KnowledgeDocument,
  type KnowledgeSearchResult,
  type KnowledgeDocumentDetail,
} from "../lib/api";

export const Knowledge: React.FC = () => {
  const { documentId } = useParams<{ documentId?: string }>();

  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [totalChunks, setTotalChunks] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Document Detail State
  const [docDetail, setDocDetail] = useState<KnowledgeDocumentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);

  // Search state
  const [query, setQuery] = useState<string>("");
  const [searching, setSearching] = useState<boolean>(false);
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.knowledgeDocuments();
      setDocuments(res.documents || []);
      setTotalChunks(res.total_chunks || 0);
    } catch (err: any) {
      console.error("Failed to fetch knowledge documents:", err);
      setError(err.message || "Failed to load indexed knowledge documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  // When documentId is present in URL, load full document details
  useEffect(() => {
    if (!documentId) {
      setDocDetail(null);
      return;
    }
    setLoadingDetail(true);
    api
      .knowledgeDocument(documentId)
      .then((detail) => setDocDetail(detail))
      .catch((err) => console.error("Failed to load document:", err))
      .finally(() => setLoadingDetail(false));
  }, [documentId]);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    setSearchError(null);
    try {
      const res = await api.searchKnowledge(query.trim(), 5);
      setSearchResults(res.results || []);
    } catch (err: any) {
      console.error("Knowledge search failed:", err);
      setSearchError(err.message || "Semantic search failed. Ensure Ollama & nomic-embed-text are running.");
    } finally {
      setSearching(false);
    }
  };

  // ── DOCUMENT DETAIL VIEW (/knowledge/:documentId) ─────────────────────────
  if (documentId) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto pb-12 font-sans">
        <Link
          to="/knowledge"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-gray-400 hover:text-cyan-400 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Knowledge Base</span>
        </Link>

        {loadingDetail ? (
          <div className="p-16 text-center text-gray-500 font-mono text-xs">
            Loading document chunks and metadata from vector store...
          </div>
        ) : !docDetail ? (
          <div className="p-16 text-center text-red-400 font-mono text-xs">
            Document '{documentId}' not found in knowledge store.
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header */}
            <div className="p-5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 uppercase font-bold">
                  {docDetail.provider_type || "runbook"}
                </span>
                <span className="text-gray-400 bg-slate-800 px-2 py-0.5 rounded">
                  {docDetail.chunk_count} CHUNKS INDEXED
                </span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> nomic-embed-text (768-dim)
                </span>
              </div>
              <h1 className="text-xl font-bold text-white tracking-tight">{docDetail.title}</h1>
              <p className="text-xs font-mono text-gray-500">ID: {docDetail.document_id}</p>
            </div>

            {/* Chunks / Sections */}
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Indexed Sections ({docDetail.chunks.length})
              </h2>
              {docDetail.chunks.map((chunk, idx) => (
                <div
                  key={chunk.chunk_id || idx}
                  className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 font-mono text-xs"
                >
                  <div className="flex items-center justify-between text-cyan-300 font-bold">
                    <span>§ {chunk.section || `Section ${idx + 1}`}</span>
                    <span className="text-[10px] text-gray-500">{chunk.chunk_id.slice(0, 8)}</span>
                  </div>
                  <p className="text-gray-300 font-sans text-xs leading-relaxed whitespace-pre-line">
                    {chunk.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── KNOWLEDGE LISTING & SEARCH VIEW (/knowledge) ──────────────────────────
  return (
    <div className="space-y-6 max-w-6xl mx-auto font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-white/5 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-cyan-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">Runbook & Incident Knowledge Base</h1>
          </div>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            Operational runbooks, architecture specs & post-mortems indexed with Ollama nomic-embed-text.
          </p>
        </div>
        <button
          onClick={fetchDocuments}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-slate-700 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Sync Knowledge</span>
        </button>
      </div>

      {/* Semantic Search Box */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-cyan-400" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Semantic Vector Search (RAG Engine)
            </h2>
          </div>
          <span className="text-[10px] text-gray-500 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
            Cosine Similarity Retrieval
          </span>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 font-mono">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Query failure type, symptom, or service (e.g., 'CrashLoopBackOff port bind', 'OOMKilled memory pressure')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs bg-slate-950 border border-slate-800 rounded focus:outline-none focus:border-cyan-500 text-white placeholder:text-gray-500"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="px-4 py-2 bg-cyan-600 text-white text-xs font-medium rounded hover:bg-cyan-500 transition disabled:opacity-50 flex items-center gap-1.5"
          >
            {searching ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            <span>Retrieve</span>
          </button>
        </form>

        {searchError && (
          <p className="text-xs text-red-400 font-mono">{searchError}</p>
        )}

        {/* Search Results */}
        {searchResults && (
          <div className="pt-2 border-t border-white/5 space-y-2">
            <span className="text-[10px] font-mono text-gray-400 uppercase">
              Retrieved Chunks ({searchResults.length} matches):
            </span>
            {searchResults.length === 0 ? (
              <p className="text-xs font-mono text-gray-500 py-2">No relevant knowledge chunks found.</p>
            ) : (
              searchResults.map((res, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded bg-slate-950/70 border border-slate-800 space-y-1 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <Link
                      to={`/knowledge/${res.document_id}`}
                      className="text-cyan-300 font-bold hover:underline flex items-center gap-1"
                    >
                      <span>{res.title || res.document_id}</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </Link>
                    <span className="text-emerald-400 text-[10px] bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      Similarity: {(res.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <span className="text-gray-500 text-[10px] block">§ {res.section || "General"}</span>
                  <p className="text-gray-300 font-sans text-xs line-clamp-3 pt-0.5">
                    {res.content}
                  </p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Document Registry Table */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-gray-400 uppercase font-bold tracking-wider text-[10px]">
            Indexed Corpus ({documents.length} Runbooks & Specs &bull; {totalChunks} Total Chunks)
          </span>
          <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5" /> SQLite Persistent Store
          </span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="text-[10px] font-mono text-gray-400 uppercase bg-slate-950/70 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-2.5 font-bold">Document Title</th>
                  <th className="px-4 py-2.5 font-bold">Document ID</th>
                  <th className="px-4 py-2.5 font-bold">Type / Category</th>
                  <th className="px-4 py-2.5 font-bold">Indexed Chunks</th>
                  <th className="px-4 py-2.5 font-bold">State</th>
                  <th className="px-4 py-2.5 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {documents.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-white/[0.02] transition">
                    <td className="px-4 py-2.5 font-sans font-medium text-gray-200">
                      <Link to={`/knowledge/${doc.document_id}`} className="hover:text-cyan-400 hover:underline">
                        {doc.title || doc.document_id}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5 text-gray-400">
                      {doc.document_id}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        {doc.provider_type || "runbook"}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-300">
                      {doc.chunk_count} chunks
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-bold">
                        <CheckCircle2 className="w-3 h-3" /> INDEXED
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <Link
                        to={`/knowledge/${doc.document_id}`}
                        className="px-2.5 py-1 text-[10px] font-sans rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition"
                      >
                        Inspect &bull;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
