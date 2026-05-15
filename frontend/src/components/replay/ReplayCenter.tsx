import React, { useEffect, useState } from "react";
import { Play, Pause, RotateCcw, FastForward } from "lucide-react";
import "../../../styles/replay.css";

interface ReplayFrame {
  timestamp: number;
  incident_state: any;
  topology_state: any;
  metrics: any;
}

interface ReplaySession {
  incident_id: string;
  frames: ReplayFrame[];
  duration_seconds: number;
  timeline: any[];
}

const ReplayCenterComponent: React.FC<{ incidentId?: string }> = ({ incidentId }) => {
  const [replay, setReplay] = useState<ReplaySession | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReplay = async () => {
      if (!incidentId) return;

      try {
        const response = await fetch(`/api/incidents/${incidentId}/replay`);
        if (response.ok) {
          const data = await response.json();
          setReplay(data);
          setLoading(false);
        }
      } catch (error) {
        console.error("Failed to fetch replay:", error);
        setLoading(false);
      }
    };

    fetchReplay();
  }, [incidentId]);

  useEffect(() => {
    if (!isPlaying || !replay) return;

    const frameDelay = (1000 / (replay.frames.length / replay.duration_seconds)) / speed;
    const timer = setTimeout(() => {
      if (currentFrame < replay.frames.length - 1) {
        setCurrentFrame(currentFrame + 1);
      } else {
        setIsPlaying(false);
      }
    }, frameDelay);

    return () => clearTimeout(timer);
  }, [isPlaying, currentFrame, replay, speed]);

  if (loading || !replay) {
    return (
      <div className="replay-container">
        <div className="replay-loading">Loading replay...</div>
      </div>
    );
  }

  const currentFrameData = replay.frames[currentFrame];
  const progress = (currentFrame / replay.frames.length) * 100;

  return (
    <div className="replay-container">
      <div className="replay-header">
        <h2>🎬 Incident Replay Center</h2>
        <span className="replay-time">
          {currentFrame} / {replay.frames.length} frames
        </span>
      </div>

      <div className="replay-viewer">
        <div className="replay-main">
          {currentFrameData && (
            <div className="frame-content">
              <div className="frame-header">
                <h3>Frame: {currentFrame}</h3>
                <span className="frame-timestamp">{new Date(currentFrameData.timestamp * 1000).toLocaleTimeString()}</span>
              </div>

              <div className="frame-grid">
                <div className="frame-section">
                  <h4>🔴 Incident State</h4>
                  <div className="frame-data">
                    <pre>{JSON.stringify(currentFrameData.incident_state, null, 2)}</pre>
                  </div>
                </div>

                <div className="frame-section">
                  <h4>📊 Metrics</h4>
                  <div className="frame-metrics">
                    {Object.entries(currentFrameData.metrics || {}).map(([key, value]: [string, any]) => (
                      <div key={key} className="metric-row">
                        <span className="metric-key">{key}:</span>
                        <span className="metric-value">{typeof value === "number" ? value.toFixed(2) : String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="replay-timeline">
          <div className="timeline-events">
            {replay.timeline.map((event, idx) => (
              <div key={idx} className="timeline-item" onClick={() => setCurrentFrame(idx * Math.floor(replay.frames.length / replay.timeline.length))}>
                <div className="timeline-dot" style={{ background: getEventColor(event.type) }} />
                <span className="timeline-label">{event.title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="replay-controls">
        <div className="controls-left">
          <button
            className="control-btn"
            onClick={() => setCurrentFrame(0)}
            title="Restart"
          >
            <RotateCcw size={16} />
          </button>
          <button
            className="control-btn play-btn"
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <button
            className="control-btn"
            onClick={() => setSpeed(Math.min(speed + 0.5, 4))}
            title="Speed up"
          >
            <FastForward size={16} />
          </button>
        </div>

        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
            onClick={(e) => {
              const rect = e.currentTarget.parentElement?.getBoundingClientRect();
              if (rect) {
                const percent = (e.clientX - rect.left) / rect.width;
                setCurrentFrame(Math.floor(percent * replay.frames.length));
              }
            }}
          />
          <input
            type="range"
            min="0"
            max={replay.frames.length - 1}
            value={currentFrame}
            onChange={(e) => setCurrentFrame(parseInt(e.target.value))}
            className="progress-slider"
          />
        </div>

        <div className="controls-right">
          <span className="speed-display">Speed: {speed.toFixed(1)}x</span>
        </div>
      </div>
    </div>
  );
};

function getEventColor(type: string): string {
  switch (type) {
    case "incident_created":
      return "#ff4444";
    case "degradation":
      return "#ff9900";
    case "remediation":
      return "#4CAF50";
    case "resolved":
      return "#44ff44";
    default:
      return "#9999ff";
  }
}

export default ReplayCenterComponent;
