import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import DependencyGraph from "../components/topology/DependencyGraph";
import type { TopologyGraph } from "../lib/api";

export default function Replay() {
  const { id } = useParams<{ id: string }>();
  const [frames, setFrames] = useState<
    { frame_id?: string; frame_index?: number; timestamp?: string; event_count?: number; events?: unknown[]; topology_state?: TopologyGraph }[]
  >([]);
  const [timeline, setTimeline] = useState<unknown[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (id) {
      api.replay(id).then((r) => {
        setFrames((r.frames as typeof frames) || []);
        setTimeline(r.timeline || []);
      }).catch(() => {
        setFrames([]);
        setTimeline([]);
      });
    }
  }, [id]);

  useEffect(() => {
    if (!playing || frames.length === 0) return;
    const t = setInterval(() => setFrameIdx((i) => (i + 1) % frames.length), 1200);
    return () => clearInterval(t);
  }, [playing, frames.length]);

  const current = frames[frameIdx];
  const topo = current?.topology_state;

  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl font-bold">Incident Replay</h2>
      <p className="text-gray-500 text-sm">Incident {id}</p>

      <div className="flex gap-2 items-center">
        <button onClick={() => setPlaying(!playing)} className="bg-sentinel-700 px-4 py-2 rounded text-sm">
          {playing ? "Pause" : "Play"}
        </button>
        <input
          type="range"
          min={0}
          max={Math.max(frames.length - 1, 0)}
          value={frameIdx}
          onChange={(e) => setFrameIdx(Number(e.target.value))}
          className="flex-1"
        />
        <span className="text-sm text-gray-400">
          Frame {frameIdx + 1} / {frames.length}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4 min-h-[280px]">
          {current ? (
            <>
              <p className="text-sentinel-accent text-sm">{current.timestamp}</p>
              <p className="text-gray-400 text-sm">{current.event_count} events</p>
              <ul className="mt-4 space-y-1 max-h-48 overflow-y-auto">
                {(current.events ?? []).map((e: unknown, i: number) => (
                  <li key={i} className="text-xs font-mono text-gray-500">{JSON.stringify(e)}</li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-gray-500">No replay frames. Process an incident via workers first.</p>
          )}
        </div>
        <div>
          {topo && topo.nodes ? (
            <DependencyGraph graph={topo as TopologyGraph} width={400} height={280} />
          ) : (
            <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-8 text-center text-gray-500 h-[280px] flex items-center justify-center">
              Topology state at frame {frameIdx + 1}
            </div>
          )}
        </div>
      </div>

      <div className="bg-sentinel-900 border border-sentinel-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-2">Full Timeline ({timeline.length} events)</h3>
        <ul className="max-h-40 overflow-y-auto text-xs space-y-1">
          {(timeline as { timestamp?: string; event_type?: string; title?: string }[]).map((t, i) => (
            <li key={i} className="text-gray-500">{t.timestamp} — {t.event_type}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
