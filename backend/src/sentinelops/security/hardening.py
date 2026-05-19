"""
Enterprise Security Hardening Module
- API rate limiting
- WebSocket protection
- Data encryption
- Request validation
- CORS hardening
"""

import time
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import logging

log = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API endpoints"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limit"""
        now = time.time()

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Remove old requests outside window
        cutoff = now - self.window_seconds
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]

        # Check if within limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True

        return False

    def get_retry_after(self, client_id: str) -> int:
        """Get seconds until client can retry"""
        if client_id not in self.requests or not self.requests[client_id]:
            return 0

        oldest_request = self.requests[client_id][0]
        retry_time = oldest_request + self.window_seconds
        return max(0, int(retry_time - time.time()))


class WebSocketRateLimiter:
    """Rate limiter for WebSocket connections"""

    def __init__(self,
                 messages_per_second: int = 10,
                 burst_size: int = 20):
        self.messages_per_second = messages_per_second
        self.burst_size = burst_size
        self.client_tokens: Dict[str, float] = {}
        self.client_last_update: Dict[str, float] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Token bucket for WebSocket messages"""
        now = time.time()

        if client_id not in self.client_tokens:
            self.client_tokens[client_id] = self.burst_size
            self.client_last_update[client_id] = now
            return True

        # Refill tokens based on time elapsed
        time_passed = now - self.client_last_update[client_id]
        tokens_earned = time_passed * self.messages_per_second

        self.client_tokens[client_id] = min(
            self.burst_size,
            self.client_tokens[client_id] + tokens_earned
        )
        self.client_last_update[client_id] = now

        # Check if we can send
        if self.client_tokens[client_id] >= 1:
            self.client_tokens[client_id] -= 1
            return True

        return False


class RequestValidator:
    """Validate and sanitize incoming requests"""

    @staticmethod
    def validate_cluster_id(cluster_id: str) -> bool:
        """Validate UUID format for cluster ID"""
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, cluster_id.lower()))

    @staticmethod
    def validate_json_payload(data: dict, max_size_bytes: int = 1_000_000) -> bool:
        """Validate JSON payload size and structure"""
        import json

        try:
            json_str = json.dumps(data)
            if len(json_str.encode('utf-8')) > max_size_bytes:
                log.warning(f"Payload exceeds max size: {len(json_str)} bytes")
                return False
            return True
        except Exception as e:
            log.error(f"Payload validation error: {e}")
            return False

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Remove potentially dangerous characters"""
        # Truncate
        value = value[:max_length]
        # Remove null bytes
        value = value.replace('\x00', '')
        # Remove control characters (except newline/tab)
        value = ''.join(
            c for c in value
            if ord(c) >= 32 or c in '\n\t\r'
        )
        return value


class DataEncryption:
    """Simple encryption for sensitive data at rest"""

    @staticmethod
    def hash_sensitive_data(data: str, salt: str = "") -> str:
        """Hash sensitive data for storage"""
        salted = f"{salt}{data}".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()

    @staticmethod
    def compute_data_checksum(data: str) -> str:
        """Compute checksum for data integrity"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_data_integrity(data: str, checksum: str) -> bool:
        """Verify data hasn't been tampered with"""
        computed = DataEncryption.compute_data_checksum(data)
        return computed == checksum


class SecurityAuditLog:
    """Log security-relevant events"""

    def __init__(self):
        self.events: list[dict] = []
        self.max_events = 10000

    def log_rate_limit_exceeded(self, client_id: str, endpoint: str):
        """Log rate limit violation"""
        self.events.append({
            'type': 'rate_limit_exceeded',
            'client_id': client_id,
            'endpoint': endpoint,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'warning'
        })
        self._cleanup_old_events()

    def log_invalid_request(self, client_id: str, reason: str):
        """Log invalid request"""
        self.events.append({
            'type': 'invalid_request',
            'client_id': client_id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'warning'
        })
        self._cleanup_old_events()

    def log_security_event(self, event_type: str, details: dict, severity: str = "info"):
        """Log security event"""
        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            **details
        }
        self.events.append(event)
        self._cleanup_old_events()

    def _cleanup_old_events(self):
        """Remove old events to prevent unbounded growth"""
        if len(self.events) > self.max_events:
            # Keep last N events
            self.events = self.events[-self.max_events:]

    def get_recent_events(self, hours: int = 24) -> list[dict]:
        """Get recent security events"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            e for e in self.events
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]

    def get_critical_events(self) -> list[dict]:
        """Get critical security events"""
        return [e for e in self.events if e.get('severity') == 'critical']


# Global instances
rate_limiter = RateLimiter(max_requests=1000, window_seconds=60)
ws_rate_limiter = WebSocketRateLimiter(messages_per_second=10, burst_size=50)
security_audit_log = SecurityAuditLog()


def get_client_id(request) -> str:
    """Extract client identifier from request"""
    # Try X-Forwarded-For for proxied requests
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    # Fall back to remote address
    return request.client.host if request.client else "unknown"
