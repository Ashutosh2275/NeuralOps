import time
from typing import Dict

class RateLimitEngine:
    """Redis-backed API rate limiting to protect AI pipelines."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.store: Dict[str, list] = {} # Mocking Redis layer
        
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in self.store:
            self.store[client_ip] = []
            
        # Clean old
        self.store[client_ip] = [ts for ts in self.store[client_ip] if now - ts < self.window_seconds]
        
        if len(self.store[client_ip]) >= self.max_requests:
            return False
            
        self.store[client_ip].append(now)
        return True

rate_limiter = RateLimitEngine()
