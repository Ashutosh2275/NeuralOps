from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "SentinelOps AI"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_log_format: Literal["json", "console"] = "json"
    app_secret_key: str = Field(default="dev-secret-change-in-production", min_length=16)
    app_cors_origins: str = "http://localhost:5173"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "sentinelops"
    postgres_password: str = "sentinelops"
    postgres_db: str = "sentinelops"
    database_url: str | None = None

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0
    redis_password: str = ""
    redis_url: str | None = None

    # Redis Streams (legacy + ingestion)
    stream_events_raw: str = "so:events:raw"
    stream_events_enriched: str = "so:events:enriched"
    stream_metrics: str = "so:metrics"
    stream_correlation: str = "so:correlation"
    stream_incidents: str = "so:incidents"
    stream_ai_tasks: str = "so:ai:tasks"
    stream_ai_results: str = "so:ai:results"
    stream_topology: str = "so:topology"
    stream_replay: str = "so:replay"
    stream_metrics_events: str = "metrics.events"
    stream_topology_events: str = "topology.events"
    stream_anomaly_events: str = "anomaly.events"
    stream_incident_events: str = "incident.events"
    stream_rca_events: str = "rca.events"
    stream_dead_letter: str = "dlq.events"
    consumer_group_collector: str = "sentinelops-collector"
    consumer_group_correlation: str = "sentinelops-correlation"
    consumer_group_ai: str = "sentinelops-ai"
    consumer_group_replay: str = "sentinelops-replay"
    consumer_group_dlq: str = "sentinelops-dlq"
    stream_max_len: int = 100_000
    stream_retry_max_attempts: int = 3
    stream_retry_backoff_seconds: int = 2
    ingestion_correlation_window_seconds: int = 120
    loki_query_limit: int = 500
    prometheus_poll_interval_seconds: int = 15

    # Kubernetes
    k8s_in_cluster: bool = False
    k8s_kubeconfig: str | None = None
    k8s_namespace: str = "default"
    k8s_watch_timeout_seconds: int = 300
    k8s_collect_interval_seconds: int = 15

    # Prometheus / Loki
    prometheus_url: str = "http://localhost:9090"
    prometheus_query_timeout_seconds: int = 30
    loki_url: str = "http://localhost:3100"
    loki_query_timeout_seconds: int = 30

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_fallback_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: int = 120
    ollama_max_tokens: int = 2048
    ai_agent_concurrency: int = 3

    # Feature flags
    feature_nlp_assistant: bool = True
    feature_replay_engine: bool = True
    feature_ai_agents: bool = True
    feature_dependency_graph: bool = True
    feature_anomaly_detection: bool = True

    # Anomaly thresholds
    anomaly_cpu_threshold_percent: float = 85.0
    anomaly_memory_threshold_percent: float = 90.0
    anomaly_restart_burst_count: int = 3
    anomaly_restart_window_seconds: int = 300
    anomaly_zscore_threshold: float = 2.5

    # Replay
    replay_buffer_hours: int = 24
    replay_snapshot_interval_seconds: int = 60
    replay_max_events_per_incident: int = 50_000

    # WebSocket
    ws_heartbeat_interval_seconds: int = 30
    ws_max_connections: int = 500

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return self.async_database_url.replace("+asyncpg", "")

    @property
    def effective_redis_url(self) -> str:
        if self.redis_url:
            return self.redis_url
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def all_stream_names(self) -> list[str]:
        return self.all_ingestion_streams + [
            self.stream_events_enriched,
            self.stream_correlation,
            self.stream_ai_tasks,
            self.stream_ai_results,
            self.stream_replay,
        ]

    @property
    def all_ingestion_streams(self) -> list[str]:
        return [
            self.stream_events_raw,
            self.stream_metrics_events,
            self.stream_topology_events,
            self.stream_anomaly_events,
            self.stream_incident_events,
            self.stream_rca_events,
            self.stream_dead_letter,
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
