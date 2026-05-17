import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import AdvancedTopologyVisualization from "../components/topology/AdvancedTopologyVisualization";
import type { TopologyGraph } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, SkipBack, SkipForward, FastForward, Clock, Cpu, GitBranch, Terminal, ShieldAlert } from "lucide-react";

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

  return (
    <div className="h-full flex flex-col gap-6">
      <header className="flex justify-between items-end">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/30 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.2)]">
            <Clock size={24} className="text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-display font-bold text-white tracking-tight uppercase" style={{ textShadow: '0 0 10px rgba(168,85,247,0.5)' }}>
              Cinematic Replay
            </h1>
            <p className="text-sm text-purple-400/70 font-sans tracking-widest uppercase mt-1">
              Time-Series Incident Reconstruction
            </p>
          </div>
        </div>
        <div className="glass-panel px-6 py-2 rounded-lg flex gap-8 border-purple-500/30 text-right">
           <div>
              <div className="text-[10px] text-gray-500 font-display uppercase tracking-widest">Frame Record</div>
              <div className="text-xl font-bold font-sans text-white">{frameIdx + 1} <span className="text-gray-500 text-sm">/ {frames.length || 1}</span></div>
           </div>
           {current?.timestamp && (
              <div>
                 <div className="text-[10px] text-gray-500 font-display uppercase tracking-widest">Temporal Index</div>
                 <div className="text-lg font-mono text-purple-400">{current.timestamp}</div>
              </div>
           )}
        </div>
      </header>

      {/* Main Cinematic Grid */}
      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* Left Side: Topology & Reasoning */}
        <div className="col-span-8 flex flex-col gap-6">
           <motion.div 
             initial={{ opacity: 0, scale: 0.98 }}
             animate={{ opacity: 1, scale: 1 }}
             className="glass-panel rounded-xl flex-1 relative overflow-hidden border border-purple-500/30 shadow-[0_0_20px_rgba(168,85,247,0.1)]"
           >
              <div className="absolute top-4 left-4 z-10 flex gap-2">
                 <div className="glass-panel px-3 py-1.5 rounded-lg border border-purple-500/50 flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                    </span>
                    <span className="text-[10px] text-purple-400 font-display uppercase tracking-widest">Temporal Hologram</span>
                 </div>
              </div>
              
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(168,85,247,0.05)_0%,transparent_70%)] pointer-events-none" />
              
              {topo && topo.nodes ? (
                <AdvancedTopologyVisualization graph={topo} showPressure={true} showHealth={true} showEdgeWeights={false} animateUpdates={false} />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-purple-500/50 font-mono text-sm uppercase tracking-widest">
                  Awaiting Telemetry Data...
                </div>
              )}
           </motion.div>

           <AnimatePresence mode="popLayout">
              {showReasoningOverlay && aiReasoning && (
                 <motion.div 
                   initial={{ opacity: 0, y: 20 }}
                   animate={{ opacity: 1, y: 0 }}
                   exit={{ opacity: 0, scale: 0.95 }}
                   className="glass-panel rounded-xl p-5 border border-sentinel-accent/30 bg-sentinel-900/90 glow-border-accent"
                 >
                    <div className="flex justify-between items-start mb-4">
                       <div className="flex items-center gap-2">
                          <Cpu size={16} className="text-sentinel-accent" />
                          <h3 className="text-xs font-display text-sentinel-accent uppercase tracking-widest">AI Root Cause Synthesis</h3>
                       </div>
                       <span className="text-xs font-mono text-sentinel-accent px-2 py-0.5 bg-sentinel-accent/20 rounded">
                          CONF {Math.round(aiReasoning.confidence * 100)}%
                       </span>
                    </div>
                    
                    <p className="text-lg font-sans text-white mb-4 leading-relaxed">
                       {aiReasoning.root_cause}
                    </p>
                    
                    <div className="space-y-2">
                       {aiReasoning.reasoning_chain?.map((reason, i) => (
                          <motion.div 
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                            key={i} 
                            className="flex gap-3 text-sm text-gray-300 font-sans"
                          >
                             <span className="text-sentinel-accent opacity-50 font-mono text-xs mt-0.5">{(i+1).toString().padStart(2, '0')}</span>
                             <span>{reason}</span>
                          </motion.div>
                       ))}
                    </div>
                 </motion.div>
              )}
           </AnimatePresence>
        </div>

        {/* Right Side: Remediation & Events */}
        <div className="col-span-4 flex flex-col gap-6 h-full">
           <AnimatePresence>
              {showRemediationOverlay && remediationActions.length > 0 && (
                 <motion.div 
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   className="glass-panel border-orange-500/30 rounded-xl p-5 shadow-[0_0_15px_rgba(249,115,22,0.1)]"
                 >
                    <div className="flex items-center gap-2 mb-4">
                       <ShieldAlert size={16} className="text-orange-400" />
                       <h3 className="text-xs font-display text-orange-400 uppercase tracking-widest">Autonomous Remediation</h3>
                    </div>
                    
                    <div className="space-y-3">
                       {remediationActions.map((action, i) => (
                          <div key={i} className="bg-black/40 border border-orange-500/20 rounded-lg p-3">
                             <div className="text-sm text-white font-sans font-medium mb-2">{action.action}</div>
                             <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-widest">
                                <span className={action.severity === 'critical' ? 'text-red-400' : 'text-orange-400'}>{action.severity}</span>
                                <span className={`px-2 py-0.5 rounded ${action.status === 'executing' ? 'bg-orange-500/20 text-orange-400 animate-pulse' : action.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-gray-700/50 text-gray-400'}`}>
                                   {action.status}
                                </span>
                             </div>
                          </div>
                       ))}
                    </div>
                 </motion.div>
              )}
           </AnimatePresence>

           <div className="glass-panel border-gray-700/50 rounded-xl p-5 flex-1 flex flex-col overflow-hidden">
              <div className="flex items-center gap-2 mb-4">
                 <Terminal size={16} className="text-gray-400" />
                 <h3 className="text-xs font-display text-gray-400 uppercase tracking-widest">Event Telemetry</h3>
              </div>
              
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-2">
                 {(current?.events ?? []).map((e: any, i) => (
                    <motion.div 
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      key={i} 
                      className="text-[10px] font-mono text-gray-400 bg-black/30 p-2 rounded border-l-2 border-gray-700 break-words"
                    >
                       {typeof e === 'string' ? e : JSON.stringify(e)}
                    </motion.div>
                 ))}
                 {(!current?.events || current.events.length === 0) && (
                    <div className="text-center text-gray-600 text-xs font-mono py-8">NO EVENTS RECORDED</div>
                 )}
              </div>
           </div>
        </div>
      </div>

      {/* Control Bar */}
      <div className="glass-panel rounded-xl p-4 flex flex-col gap-4">
         <div className="flex items-center gap-4">
            <span className="text-[10px] font-mono text-gray-500 w-12 text-right">START</span>
            <div className="flex-1 relative h-10 group flex items-center">
               <div className="absolute inset-x-0 h-1 bg-gray-700/50 rounded-full" />
               <input
                 type="range"
                 min={0}
                 max={Math.max(frames.length - 1, 0)}
                 value={frameIdx}
                 onChange={(e) => {
                   setFrameIdx(Number(e.target.value));
                   setPlaying(false);
                 }}
                 className="absolute inset-0 w-full opacity-0 cursor-pointer z-10"
               />
               <motion.div 
                 className="absolute h-2 bg-purple-500 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.8)] pointer-events-none"
                 style={{ width: `${(frameIdx / Math.max(frames.length - 1, 1)) * 100}%` }}
               />
               <motion.div 
                 className="absolute w-4 h-4 bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,1)] pointer-events-none -ml-2"
                 style={{ left: `${(frameIdx / Math.max(frames.length - 1, 1)) * 100}%` }}
               />
            </div>
            <span className="text-[10px] font-mono text-gray-500 w-12">END</span>
         </div>

         <div className="flex justify-between items-center px-4">
            <div className="flex gap-2">
               {[0.5, 1, 1.5, 2].map(speed => (
                  <button
                    key={speed}
                    onClick={() => setPlaybackSpeed(speed)}
                    className={`px-3 py-1 text-[10px] font-mono rounded ${playbackSpeed === speed ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50' : 'text-gray-500 hover:text-gray-300'}`}
                  >
                     {speed}x
                  </button>
               ))}
            </div>

            <div className="flex gap-4">
               <button onClick={() => { setFrameIdx(0); setPlaying(false); }} className="p-2 text-gray-400 hover:text-white transition-colors">
                  <SkipBack size={20} />
               </button>
               <button onClick={() => { setFrameIdx(i => Math.max(0, i - 1)); setPlaying(false); }} className="p-2 text-gray-400 hover:text-white transition-colors">
                  <FastForward size={20} className="rotate-180" />
               </button>
               <button 
                 onClick={() => setPlaying(!playing)} 
                 className="w-12 h-12 bg-purple-500 text-white rounded-full flex items-center justify-center hover:bg-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.4)] transition-all"
               >
                  {playing ? <Pause size={24} /> : <Play size={24} className="ml-1" />}
               </button>
               <button onClick={() => { setFrameIdx(i => Math.min(frames.length - 1, i + 1)); setPlaying(false); }} className="p-2 text-gray-400 hover:text-white transition-colors">
                  <FastForward size={20} />
               </button>
               <button onClick={() => { setFrameIdx(frames.length - 1); setPlaying(false); }} className="p-2 text-gray-400 hover:text-white transition-colors">
                  <SkipForward size={20} />
               </button>
            </div>

            <div className="flex gap-2">
               <button 
                  onClick={() => setShowReasoningOverlay(!showReasoningOverlay)}
                  className={`px-3 py-1.5 text-[10px] font-mono rounded uppercase tracking-widest flex items-center gap-2 ${showReasoningOverlay ? 'bg-sentinel-accent/20 text-sentinel-accent border border-sentinel-accent/50' : 'text-gray-500 hover:text-gray-300'}`}
               >
                  <Cpu size={12} /> AI Trace
               </button>
               <button 
                  onClick={() => setShowRemediationOverlay(!showRemediationOverlay)}
                  className={`px-3 py-1.5 text-[10px] font-mono rounded uppercase tracking-widest flex items-center gap-2 ${showRemediationOverlay ? 'bg-orange-500/20 text-orange-400 border border-orange-500/50' : 'text-gray-500 hover:text-gray-300'}`}
               >
                  <ShieldAlert size={12} /> Actions
               </button>
               <button 
                  onClick={() => setShowBranches(!showBranches)}
                  className={`px-3 py-1.5 text-[10px] font-mono rounded uppercase tracking-widest flex items-center gap-2 ${showBranches ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50' : 'text-gray-500 hover:text-gray-300'}`}
               >
                  <GitBranch size={12} /> Branches
               </button>
            </div>
         </div>
      </div>
    </div>
  );
};

export default CinematicReplay;
