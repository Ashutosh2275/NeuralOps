"""
Centralized Secret Management and Redaction Engine for SentinelOps AI.
Redacts API keys, credentials, tokens, connection strings, and private keys
across tool outputs, evidence objects, audit logs, API responses, and RCA reasoning.
"""
from __future__ import annotations

import re
from typing import Any


class SecretRedactor:
    """Detects and redacts sensitive credentials from strings, dicts, lists, and tool records."""

    SECRET_PATTERNS = [
        # AWS Access Key ID
        (r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_AWS_KEY]"),
        # JWT Token
        (r"\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b", "[REDACTED_JWT_TOKEN]"),
        # Bearer token
        (r"(?i)\bBearer\s+[A-Za-z0-9_\-\.]{15,}\b", "Bearer [REDACTED_BEARER_TOKEN]"),
        # Database connection strings with embedded passwords
        (r"(?i)\b(postgres(?:ql)?|mysql|redis|mongodb)://([^:\s]+):([^@\s]+)@([^\s/:]+)", r"\1://\2:[REDACTED_DB_PASSWORD]@\4"),
        # Private keys (RSA, EC, Generic)
        (r"-----BEGIN\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY-----", "[REDACTED_PRIVATE_KEY]"),
        # OpenAI / Anthropic / Generic sk- keys
        (r"\b(sk-[a-zA-Z0-9]{20,})\b", "[REDACTED_API_KEY]"),
        # Password key-value pairs in config/logs/JSON
        (r'(?i)(["\']?(?:password|passwd|secret|access_key|auth_token|client_secret)["\']?\s*[:=]\s*["\'])([^"\'\s]{4,})(["\'])', r'\1[REDACTED_SECRET]\3'),
        # Generic Slack / Github / AWS tokens
        (r"\bghp_[A-Za-z0-9]{36}\b", "[REDACTED_GITHUB_TOKEN]"),
        (r"\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}\b", "[REDACTED_SLACK_TOKEN]"),
    ]

    def __init__(self) -> None:
        self._compiled_patterns = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.SECRET_PATTERNS
        ]

    def redact_text(self, text: str) -> str:
        """Redact known secret patterns from a string."""
        if not text or not isinstance(text, str):
            return text
        result = text
        for pattern, replacement in self._compiled_patterns:
            result = pattern.sub(replacement, result)
        return result

    def redact_data(self, data: Any) -> Any:
        """
        Recursively redact sensitive data from nested structures (dict, list, tuple, set, str).
        """
        if isinstance(data, str):
            return self.redact_text(data)
        elif isinstance(data, dict):
            redacted_dict = {}
            for k, v in data.items():
                k_lower = str(k).lower()
                # If key name itself indicates sensitive value, redact directly
                if any(sec in k_lower for sec in ("password", "secret", "token", "auth", "credential", "private_key")):
                    redacted_dict[k] = "[REDACTED_SECRET]"
                else:
                    redacted_dict[k] = self.redact_data(v)
            return redacted_dict
        elif isinstance(data, list):
            return [self.redact_data(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self.redact_data(item) for item in data)
        elif isinstance(data, set):
            return {self.redact_data(item) for item in data}
        return data

    def scan_for_secrets(self, text: str) -> list[str]:
        """Audit text and return names of any secret types matched."""
        if not text or not isinstance(text, str):
            return []
        found = []
        for pattern, replacement in self._compiled_patterns:
            if pattern.search(text):
                found.append(replacement.strip("[]"))
        return found


# Global singleton
_redactor: SecretRedactor | None = None


def get_secret_redactor() -> SecretRedactor:
    global _redactor
    if _redactor is None:
        _redactor = SecretRedactor()
    return _redactor
