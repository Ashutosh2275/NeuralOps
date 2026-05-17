import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import DependencyGraph from "../components/topology/DependencyGraph";
import type { TopologyGraph } from "../lib/api";

interface ReplayBranch {
  branch_id: string;
  frame_index: number;
  alternate_remediation: string;
  divergence_reason: string;
  potential_outcome: string;
  confidence: number;
}

interface AIReasoning {
  frame_index: number;
  root_cause: string;
  confidence: number;
  evidence: string[];
  reasoning_chain: string[];
}

interface RemediationOverlay {
  frame_index: number;
  action: string;
  severity: string;
  impact_estimate: string;
  status: "proposed" | "executing" | "completed" | "rolled_back";
}

interface EnhancedReplayFrame {
  frame_id?: string;
  frame_index?: number;
  timestamp?: string;
  event_count?: number;
  events?: unknown[];
  topology_state?: TopologyGraph;
  ai_reasoning?: AIReasoning;
  remediation_overlays?: RemediationOverlay[];
  alternative_branches?: ReplayBranch[];
}

export const CinematicReplay: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [frames, setFrames] = useState<EnhancedReplayFrame[]>([]);
  const [timeline, setTimeline] = useState<unknown[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showReasoningOverlay, setShowReasoningOverlay] = useState(true);
  const [showRemediationOverlay, setShowRemediationOverlay] = useState(true);
  const [showBranches, setShowBranches] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<ReplayBranch | null>(null);
  const playbackIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (id) {
      api.replay(id).then((r) => {
        setFrames((r.frames as EnhancedReplayFrame[]) || []);
        setTimeline(r.timeline || []);
      }).catch(() => {
        setFrames([]);
        setTimeline([]);
      });
    }
  }, [id]);

  // Enhanced playback with variable speed
  useEffect(() => {
    if (playbackIntervalRef.current) clearInterval(playbackIntervalRef.current);

    if (!playing || frames.length === 0) return;

    const baseDuration = 1200;
    const adjustedDuration = baseDuration / playbackSpeed;

    playbackIntervalRef.current = setInterval(() => {
      setFrameIdx((prevIdx) => {
        const nextIdx = prevIdx + 1;
        if (nextIdx >= frames.length) {
          setPlaying(false);
          return prevIdx;
        }
        return nextIdx;
      });
    }, adjustedDuration);

    return () => {
      if (playbackIntervalRef.current) clearInterval(playbackIntervalRef.current);
    };
  }, [playing, frames.length, playbackSpeed]);

  const current = frames[frameIdx];
  const topo = current?.topology_state;
  const aiReasoning = current?.ai_reasoning;
  const remediationActions = current?.remediation_overlays || [];
  const branches = current?.alternative_branches || [];

  const handleRewind = () => {
    setFrameIdx(0);
    setPlaying(false);
  };

  const handlePrevFrame = () => {
    setFrameIdx((idx) => Math.max(0, idx - 1));
    setPlaying(false);
  };

  const handleNextFrame = () => {
    setFrameIdx((idx) => Math.min(frames.length - 1, idx + 1));
    setPlaying(false);
  };

  const handleBranchExploration = (branch: ReplayBranch) => {
    setSelectedBranch(branch);
    setFrameIdx(branch.frame_index);
    setShowBranches(true);
  };

  const handleExitBranch = () => {
    setSelectedBranch(null);
    setShowBranches(false);
  };

  return (
    <div className="cinematic-replay p-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 min-h-screen">
      <style>{`
        .cinematic-replay {
          font-family: "JetBrains Mono", monospace;
        }

        .replay-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          padding: 16px;
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 8px;
        }

        .replay-title {
          font-size: 24px;
          font-weight: bold;
          color: #60a5fa;
          margin: 0;
        }

        .replay-frame-counter {
          font-size: 12px;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .replay-controls {
          display: flex;
          gap: 8px;
          align-items: center;
          margin-bottom: 16px;
          padding: 12px;
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.1);
          border-radius: 8px;
        }

        .control-button {
          padding: 8px 12px;
          background: rgba(59, 130, 246, 0.2);
          border: 1px solid rgba(59, 130, 246, 0.5);
          color: #60a5fa;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 600;
          transition: all 0.2s;
        }

        .control-button:hover {
          background: rgba(59, 130, 246, 0.3);
          border-color: rgba(59, 130, 246, 0.8);
        }

        .control-button.active {
          background: rgba(59, 130, 246, 0.5);
          border-color: rgba(59, 130, 246, 1);
        }

        .timeline-scrubber {
          flex: 1;
          height: 6px;
          background: rgba(100, 116, 139, 0.3);
          border-radius: 3px;
          cursor: pointer;
          position: relative;
        }

        .timeline-scrubber input {
          width: 100%;
          height: 100%;
          cursor: pointer;
          -webkit-appearance: none;
          appearance: none;
          background: transparent;
          padding: 0;
        }

        .timeline-scrubber input::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 12px;
          height: 12px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
        }

        .timeline-scrubber input::-moz-range-thumb {
          width: 12px;
          height: 12px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
        }

        .playback-speed-control {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .playback-speed-control label {
          font-size: 11px;
          color: #94a3b8;
          text-transform: uppercase;
        }

        .playback-speed-control select {
          padding: 6px;
          background: rgba(30, 41, 59, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.2);
          color: #94a3b8;
          border-radius: 4px;
          font-size: 11px;
          cursor: pointer;
        }

        .replay-display {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-bottom: 16px;
        }

        .panel {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.1);
          border-radius: 8px;
          padding: 16px;
          min-height: 300px;
          display: flex;
          flex-direction: column;
        }

        .panel-title {
          font-size: 12px;
          color: #60a5fa;
          text-transform: uppercase;
          font-weight: 600;
          margin-bottom: 12px;
          letter-spacing: 1px;
        }

        .events-list {
          flex: 1;
          overflow-y: auto;
          space-y: 8px;
        }

        .event-item {
          padding: 8px;
          background: rgba(30, 41, 59, 0.5);
          border-left: 2px solid #3b82f6;
          border-radius: 2px;
          font-size: 11px;
          color: #cbd5e1;
          margin-bottom: 4px;
          white-space: pre-wrap;
          word-break: break-word;
        }

        .reasoning-overlay {
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 6px;
          padding: 12px;
          margin-bottom: 12px;
        }

        .reasoning-label {
          font-size: 11px;
          color: #60a5fa;
          text-transform: uppercase;
          font-weight: 600;
          margin-bottom: 6px;
        }

        .reasoning-content {
          font-size: 12px;
          color: #cbd5e1;
          line-height: 1.4;
        }

        .confidence-score {
          display: inline-block;
          padding: 2px 8px;
          background: rgba(59, 130, 246, 0.2);
          border-radius: 3px;
          font-size: 11px;
          color: #60a5fa;
          margin-top: 6px;
        }

        .remediation-action {
          background: rgba(34, 197, 94, 0.1);
          border: 1px solid rgba(34, 197, 94, 0.3);
          border-radius: 6px;
          padding: 10px;
          margin-bottom: 10px;
          font-size: 11px;
        }

        .action-status {
          display: inline-block;
          padding: 2px 6px;
          border-radius: 2px;
          font-size: 10px;
          font-weight: 600;
          margin-top: 4px;
        }

        .action-status.proposed {
          background: rgba(59, 130, 246, 0.3);
          color: #60a5fa;
        }

        .action-status.executing {
          background: rgba(251, 146, 60, 0.3);
          color: #fb923c;
          animation: pulse 2s infinite;
        }

        .action-status.completed {
          background: rgba(34, 197, 94, 0.3);
          color: #22c55e;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }

        .branch-explorer {
          background: rgba(139, 92, 246, 0.05);
          border: 1px solid rgba(139, 92, 246, 0.3);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
        }

        .branch-item {
          padding: 10px;
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(139, 92, 246, 0.2);
          border-radius: 4px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .branch-item:hover {
          background: rgba(139, 92, 246, 0.15);
          border-color: rgba(139, 92, 246, 0.5);
        }

        .branch-item.selected {
          background: rgba(139, 92, 246, 0.25);
          border-color: rgba(139, 92, 246, 0.8);
        }

        .timeline-full {
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.1);
          border-radius: 8px;
          padding: 16px;
        }

        .timeline-events {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 8px;
          max-height: 200px;
          overflow-y: auto;
        }

        .timeline-marker {
          padding: 8px;
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 4px;
          font-size: 10px;
          color: #94a3b8;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
        }

        .timeline-marker:hover {
          border-color: rgba(59, 130, 246, 0.5);
          background: rgba(59, 130, 246, 0.1);
        }
      `}</style>

      {/* Header */}
      <div className="replay-header">
        <div>
          <h1 className="replay-title">🎬 Cinematic Incident Replay</h1>
          <p className="replay-frame-counter">Incident {id}</p>
        </div>
        <div className="text-right">
          <div className="replay-frame-counter">
            Frame {frameIdx + 1} / {frames.length}
          </div>
          {current?.timestamp && (
            <div className="text-sm text-blue-400 mt-2">{current.timestamp}</div>
          )}
        </div>
      </div>

      {/* Playback Controls */}
      <div className="replay-controls">
        <button className="control-button" onClick={handleRewind} title="Rewind to start">
          ⏮ Rewind
        </button>
        <button className="control-button" onClick={handlePrevFrame} title="Previous frame">
          ⏪ Prev
        </button>
        <button
          className={`control-button ${playing ? "active" : ""}`}
          onClick={() => setPlaying(!playing)}
          title="Play/Pause"
        >
          {playing ? "⏸ Pause" : "▶ Play"}
        </button>
        <button className="control-button" onClick={handleNextFrame} title="Next frame">
          ⏩ Next
        </button>

        {/* Timeline Scrubber */}
        <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
          <div className="timeline-scrubber">
            <input
              type="range"
              min={0}
              max={Math.max(frames.length - 1, 0)}
              value={frameIdx}
              onChange={(e) => {
                setFrameIdx(Number(e.target.value));
                setPlaying(false);
              }}
            />
          </div>
        </div>

        {/* Speed Control */}
        <div className="playback-speed-control">
          <label>Speed:</label>
          <select value={playbackSpeed} onChange={(e) => setPlaybackSpeed(Number(e.target.value))}>
            <option value={0.5}>0.5×</option>
            <option value={1}>1×</option>
            <option value={1.5}>1.5×</option>
            <option value={2}>2×</option>
          </select>
        </div>

        {/* Overlay Toggles */}
        <button
          className={`control-button ${showReasoningOverlay ? "active" : ""}`}
          onClick={() => setShowReasoningOverlay(!showReasoningOverlay)}
          title="Toggle AI reasoning overlay"
        >
          🤖 AI
        </button>
        <button
          className={`control-button ${showRemediationOverlay ? "active" : ""}`}
          onClick={() => setShowRemediationOverlay(!showRemediationOverlay)}
          title="Toggle remediation overlay"
        >
          ⚙️ Fix
        </button>
        <button
          className={`control-button ${showBranches ? "active" : ""}`}
          onClick={() => setShowBranches(!showBranches)}
          title="Toggle branch exploration"
        >
          🔀 Branch
        </button>
      </div>

      {/* Main Display */}
      <div className="replay-display">
        {/* Events Panel */}
        <div className="panel">
          <div className="panel-title">📡 Events ({current?.event_count || 0})</div>
          <div className="events-list">
            {(current?.events ?? []).map((e: unknown, i: number) => (
              <div key={i} className="event-item">
                {typeof e === "string" ? e : JSON.stringify(e, null, 2)}
              </div>
            ))}
            {(!current?.events || current.events.length === 0) && (
              <div style={{ color: "#64748b", fontSize: "11px" }}>No events at this frame</div>
            )}
          </div>
        </div>

        {/* Topology Panel */}
        <div className="panel">
          <div className="panel-title">🗺️ Topology State</div>
          {topo && topo.nodes ? (
            <DependencyGraph graph={topo as TopologyGraph} width={400} height={280} />
          ) : (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b" }}>
              Topology state at frame {frameIdx + 1}
            </div>
          )}
        </div>
      </div>

      {/* AI Reasoning Overlay */}
      {showReasoningOverlay && aiReasoning && (
        <div className="panel" style={{ marginBottom: "16px" }}>
          <div className="panel-title">🤖 AI Reasoning</div>
          <div className="reasoning-overlay">
            <div className="reasoning-label">Root Cause Analysis</div>
            <div className="reasoning-content">{aiReasoning.root_cause}</div>
            <div className="confidence-score">Confidence: {(aiReasoning.confidence * 100).toFixed(0)}%</div>
          </div>

          {aiReasoning.reasoning_chain && aiReasoning.reasoning_chain.length > 0 && (
            <div style={{ marginTop: "12px" }}>
              <div className="reasoning-label">Evidence Chain</div>
              {aiReasoning.reasoning_chain.map((reason, idx) => (
                <div key={idx} className="reasoning-content" style={{ marginBottom: "8px", paddingLeft: "8px", borderLeft: "2px solid #3b82f6" }}>
                  {idx + 1}. {reason}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Remediation Overlay */}
      {showRemediationOverlay && remediationActions.length > 0 && (
        <div className="panel" style={{ marginBottom: "16px" }}>
          <div className="panel-title">⚙️ Remediation Actions</div>
          {remediationActions.map((action, idx) => (
            <div key={idx} className="remediation-action">
              <div style={{ fontWeight: 600, color: "#22c55e" }}>{action.action}</div>
              <div style={{ color: "#cbd5e1", marginTop: "4px", fontSize: "10px" }}>
                Severity: <span style={{ color: action.severity === "critical" ? "#ef4444" : "#fb923c" }}>{action.severity}</span>
              </div>
              <div style={{ color: "#cbd5e1", marginTop: "4px", fontSize: "10px" }}>
                Impact: {action.impact_estimate}
              </div>
              <div className={`action-status ${action.status}`}>{action.status.toUpperCase()}</div>
            </div>
          ))}
        </div>
      )}

      {/* Branch Explorer */}
      {showBranches && branches.length > 0 && (
        <div className="branch-explorer">
          <div className="panel-title">🔀 Alternative Branches</div>
          <div style={{ marginBottom: "12px", fontSize: "11px", color: "#94a3b8" }}>
            {branches.length} alternative remediation paths discovered
          </div>
          {branches.map((branch, idx) => (
            <div
              key={idx}
              className={`branch-item ${selectedBranch?.branch_id === branch.branch_id ? "selected" : ""}`}
              onClick={() => handleBranchExploration(branch)}
            >
              <div style={{ fontWeight: 600, color: "#a78bfa" }}>Path {idx + 1}: {branch.alternate_remediation}</div>
              <div style={{ fontSize: "10px", color: "#cbd5e1", marginTop: "4px" }}>
                Divergence: {branch.divergence_reason}
              </div>
              <div style={{ fontSize: "10px", color: "#cbd5e1", marginTop: "2px" }}>
                Outcome: {branch.potential_outcome}
              </div>
              <div style={{ fontSize: "10px", marginTop: "4px" }}>
                <span style={{ color: "#60a5fa" }}>Confidence: {(branch.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
          {selectedBranch && (
            <button
              className="control-button"
              onClick={handleExitBranch}
              style={{ marginTop: "12px", width: "100%" }}
            >
              ✕ Exit Branch
            </button>
          )}
        </div>
      )}

      {/* Full Timeline */}
      <div className="timeline-full">
        <div className="panel-title">📅 Full Timeline ({timeline.length} events)</div>
        <div className="timeline-events">
          {(timeline as { timestamp?: string; event_type?: string; title?: string }[]).map((t, i) => (
            <div
              key={i}
              className="timeline-marker"
              onClick={() => setFrameIdx(i)}
              title={`${t.timestamp} — ${t.event_type}`}
            >
              <div>{i + 1}</div>
              <div style={{ fontSize: "9px", marginTop: "4px" }}>{t.event_type}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CinematicReplay;
