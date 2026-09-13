"""
Kubernetes Pod Log Forwarder to Loki.
Continuously reads real container logs from Kubernetes pods and forwards them to Loki.
Ensures true live workload-to-Loki integration without synthetic manual log generation.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)

TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\s+(.*)$")


class PodLogShipper:
    """Streams real pod logs from Kubernetes into Loki."""

    def __init__(
        self,
        namespace: str = "sentinelops-e2e",
        loki_url: Optional[str] = None,
        poll_interval: float = 3.0,
    ) -> None:
        self.namespace = namespace
        self.settings = get_settings()
        self.loki_url = (loki_url or self.settings.loki_url).rstrip("/")
        self.poll_interval = poll_interval
        self._seen_lines: set[str] = set()
        self._core_api: Any = None

    async def _init_k8s(self) -> bool:
        if self._core_api is not None:
            return True
        try:
            from kubernetes_asyncio import client, config

            if self.settings.k8s_in_cluster:
                config.load_incluster_config()
            elif self.settings.k8s_kubeconfig:
                await config.load_kube_config(config_file=self.settings.k8s_kubeconfig)
            else:
                await config.load_kube_config()
            self._core_api = client.CoreV1Api()
            return True
        except Exception as e:
            log.warning("k8s_client_init_failed", error=str(e))
            return False

    async def ship_once(self) -> int:
        """Polls all pods in namespace and ships new log lines to Loki. Returns number of shipped lines."""
        if not await self._init_k8s():
            return 0

        total_shipped = 0
        streams_to_push = []

        try:
            pod_list = await self._core_api.list_namespaced_pod(self.namespace)
            now_ns = int(time.time() * 1e9)

            for pod in pod_list.items:
                pod_name = pod.metadata.name
                app_name = (
                    pod.metadata.labels.get("app")
                    or pod.metadata.labels.get("k8s-app")
                    or pod_name.split("-")[0]
                )

                try:
                    raw_logs = await self._core_api.read_namespaced_pod_log(
                        name=pod_name,
                        namespace=self.namespace,
                        tail_lines=50,
                        timestamps=True,
                    )
                except Exception:
                    continue

                if not raw_logs:
                    continue

                lines = raw_logs.strip().splitlines()
                pod_values = []

                for idx, line in enumerate(lines):
                    line_hash = hashlib.sha256(f"{pod_name}:{line}".encode()).hexdigest()
                    if line_hash in self._seen_lines:
                        continue
                    self._seen_lines.add(line_hash)

                    m = TIMESTAMP_RE.match(line)
                    if m:
                        ts_str, content = m.group(1), m.group(2)
                        try:
                            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            ts_ns = str(int(dt.timestamp() * 1e9))
                        except Exception:
                            ts_ns = str(now_ns + idx)
                    else:
                        content = line
                        ts_ns = str(now_ns + idx)

                    log_age_s = time.time() - (int(ts_ns) / 1e9)
                    if log_age_s > 7200 or log_age_s < -60:
                        ts_ns = str(int(time.time() * 1e9) + idx)

                    pod_values.append([ts_ns, content])

                if pod_values:
                    pod_values.sort(key=lambda v: int(v[0]))
                    streams_to_push.append({
                        "stream": {
                            "namespace": self.namespace,
                            "pod": pod_name,
                            "app": app_name,
                            "service": app_name,
                            "job": "kubernetes-pods",
                        },
                        "values": pod_values,
                    })
                    total_shipped += len(pod_values)

            if len(self._seen_lines) > 10000:
                self._seen_lines = set(list(self._seen_lines)[-5000:])

            if streams_to_push:
                payload = {"streams": streams_to_push}
                push_url = f"{self.loki_url}/loki/api/v1/push"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(push_url, json=payload)
                    if resp.status_code == 204:
                        log.info(
                            "pod_logs_shipped_to_loki",
                            lines=total_shipped,
                            pods=len(streams_to_push),
                            namespace=self.namespace,
                        )
                    else:
                        log.warning(
                            "loki_push_failed",
                            status=resp.status_code,
                            body=resp.text,
                        )

        except Exception as e:
            log.warning("pod_log_shipper_error", error=str(e))

        return total_shipped

    async def run_forever(self) -> None:
        """Continuously ships pod logs until cancelled."""
        log.info("pod_log_shipper_started", namespace=self.namespace, loki_url=self.loki_url)
        while True:
            try:
                await self.ship_once()
            except Exception as e:
                log.error("pod_log_shipper_loop_error", error=str(e))
            await asyncio.sleep(self.poll_interval)


if __name__ == "__main__":
    shipper = PodLogShipper()
    asyncio.run(shipper.run_forever())
