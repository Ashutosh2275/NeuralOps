"""
Prompt Injection Defense and External Data Sanitization for SentinelOps AI.
Treats all logs, telemetry, Kubernetes metadata, and external documents as UNTRUSTED DATA.
Prevents data from overriding LLM directives or hijacking execution boundaries.
"""
from __future__ import annotations

import html
import re
from typing import NamedTuple


class SanitizationResult(NamedTuple):
    sanitized_text: str
    injections_detected: list[str]
    is_safe: bool


class PromptSanitizer:
    """Multi-layer prompt injection detection and external telemetry boundary defense."""

    PROMPT_INJECTION_PATTERNS = [
        (r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|directives|rules)", "ignore_instructions"),
        (r"(reveal|show|display|print|dump)\s+(the\s+)?(system\s+)?prompt", "reveal_prompt"),
        (r"(print|echo|expose|dump|leak)\s+(environment|env\s+vars|config|secrets)", "leak_env"),
        (r"(use|grant|assume|escalate)\s+(administrator|admin|root|superuser)\s+(privileges|role)", "escalate_privilege"),
        (r"(run|execute|call)\s+(kubectl\s+(delete|edit|apply|drain)|rm\s+-rf|drop\s+table)", "dangerous_command"),
        (r"(disable|bypass|turn\s+off|override)\s+(safety|guardrails|security|restrictions)", "disable_safety"),
        (r"(return|give\s+me|expose)\s+(database|db)\s+(credentials|password|conn\s+string)", "leak_db_creds"),
        (r"(call|spawn|open)\s+(shell|bash|powershell|cmd|sh|terminal)", "call_shell"),
        (r"<\s*/?\s*(system|assistant|instruction|prompt|context)\s*>", "delimiter_injection"),
    ]

    def __init__(self, max_length: int = 50_000) -> None:
        self.max_length = max_length
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), name)
            for p, name in self.PROMPT_INJECTION_PATTERNS
        ]

    def analyze(self, text: str) -> list[str]:
        """Check for prompt injection signatures."""
        if not text:
            return []
        detected = []
        for pattern, name in self._compiled_patterns:
            if pattern.search(text):
                detected.append(name)
        return detected

    def sanitize(self, text: str, placeholder: str = "[NEUTRALIZED_INJECTION_ATTEMPT]") -> SanitizationResult:
        """
        Sanitize untrusted external text.
        Neutralizes detected injection attempts and truncates oversized payloads.
        """
        if not text:
            return SanitizationResult(sanitized_text="", injections_detected=[], is_safe=True)

        # Truncate if exceeds bounds
        clipped = text[: self.max_length]
        detected: list[str] = []

        sanitized = clipped
        for pattern, name in self._compiled_patterns:
            if pattern.search(sanitized):
                detected.append(name)
                sanitized = pattern.sub(placeholder, sanitized)

        # Escape XML-like tags to prevent delimiter confusion
        sanitized = sanitized.replace("<|im_start|>", "").replace("<|im_end|>", "")
        sanitized = sanitized.replace("[INST]", "").replace("[/INST]", "")

        return SanitizationResult(
            sanitized_text=sanitized,
            injections_detected=detected,
            is_safe=len(detected) == 0,
        )

    def wrap_untrusted(self, content: str, source_label: str = "operational_telemetry") -> str:
        """
        Wrap external content with explicit boundary tags so LLM treats it as raw data,
        not as operational commands.
        """
        result = self.sanitize(content)
        clean_text = result.sanitized_text
        return (
            f"<UNTRUSTED_EXTERNAL_DATA source=\"{source_label}\">\n"
            f"{clean_text}\n"
            f"</UNTRUSTED_EXTERNAL_DATA>"
        )


# Global singleton
_sanitizer: PromptSanitizer | None = None


def get_prompt_sanitizer() -> PromptSanitizer:
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = PromptSanitizer()
    return _sanitizer
