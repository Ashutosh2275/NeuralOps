"""Security and enterprise hardening modules for SentinelOps AI."""

from sentinelops.security.hardening import (
    RateLimiter,
    WebSocketRateLimiter,
    RequestValidator,
    DataEncryption,
    SecurityAuditLog,
    rate_limiter,
    ws_rate_limiter,
    security_audit_log,
    get_client_id,
)
from sentinelops.security.auth import (
    Role,
    User,
    get_current_user,
    require_role,
    require_viewer,
    require_operator,
    require_admin,
    register_api_key,
)
from sentinelops.security.approval import (
    RiskLevel,
    ApprovalStatus,
    ExecutionStatus,
    ProposedAction,
    ApprovalManager,
    get_approval_manager,
)
from sentinelops.security.sanitizer import (
    PromptSanitizer,
    SanitizationResult,
    get_prompt_sanitizer,
)
from sentinelops.security.redactor import (
    SecretRedactor,
    get_secret_redactor,
)
from sentinelops.security.audit import (
    AuditEvent,
    AuditTrail,
    get_audit_trail,
)
from sentinelops.security.retention import (
    RetentionPolicy,
    CleanupReport,
    RetentionManager,
    get_retention_manager,
)

__all__ = [
    # Hardening
    "RateLimiter",
    "WebSocketRateLimiter",
    "RequestValidator",
    "DataEncryption",
    "SecurityAuditLog",
    "rate_limiter",
    "ws_rate_limiter",
    "security_audit_log",
    "get_client_id",
    # Auth & RBAC
    "Role",
    "User",
    "get_current_user",
    "require_role",
    "require_viewer",
    "require_operator",
    "require_admin",
    "register_api_key",
    # Human Approval
    "RiskLevel",
    "ApprovalStatus",
    "ExecutionStatus",
    "ProposedAction",
    "ApprovalManager",
    "get_approval_manager",
    # Sanitization
    "PromptSanitizer",
    "SanitizationResult",
    "get_prompt_sanitizer",
    # Redaction
    "SecretRedactor",
    "get_secret_redactor",
    # Audit Trail
    "AuditEvent",
    "AuditTrail",
    "get_audit_trail",
    # Retention
    "RetentionPolicy",
    "CleanupReport",
    "RetentionManager",
    "get_retention_manager",
]
