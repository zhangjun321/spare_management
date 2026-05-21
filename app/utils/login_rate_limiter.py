# -*- coding: utf-8 -*-
"""
登录速率限制器（内存实现）

提供 IP 级别的登录尝试频率限制。
无需 Redis 依赖，适用于单机部署场景。

用法：
    from app.utils.login_rate_limiter import LoginRateLimiter
    limiter = LoginRateLimiter(max_attempts=10, window_seconds=60)
    if not limiter.is_allowed(ip):
        raise RateLimitError('登录尝试过于频繁，请稍后再试')
"""

import time
import threading


class LoginRateLimiter:
    """登录频率限制器（线程安全）"""

    def __init__(self, max_attempts: int = 10, window_seconds: int = 60):
        """
        Args:
            max_attempts: 时间窗口内最大尝试次数
            window_seconds: 时间窗口（秒）
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict = {}  # ip -> [(timestamp, ...)]
        self._lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        """检查指定 IP 是否允许登录尝试"""
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                self._attempts[ip] = []

            # 清理过期记录
            self._attempts[ip] = [
                t for t in self._attempts[ip]
                if now - t < self.window_seconds
            ]

            if len(self._attempts[ip]) >= self.max_attempts:
                return False

            self._attempts[ip].append(now)
            return True

    def reset(self, ip: str) -> None:
        """重置指定 IP 的计数（登录成功后调用）"""
        with self._lock:
            self._attempts.pop(ip, None)

    def remaining(self, ip: str) -> int:
        """返回指定 IP 剩余尝试次数"""
        now = time.time()
        with self._lock:
            if ip not in self._attempts:
                return self.max_attempts
            active = [t for t in self._attempts[ip] if now - t < self.window_seconds]
            return max(0, self.max_attempts - len(active))

    def cleanup(self) -> None:
        """清理所有过期记录（可定期调用）"""
        now = time.time()
        with self._lock:
            stale_ips = [
                ip for ip, attempts in self._attempts.items()
                if not any(now - t < self.window_seconds for t in attempts)
            ]
            for ip in stale_ips:
                del self._attempts[ip]


# 默认全局实例（IP 每分钟最多 10 次）
default_limiter = LoginRateLimiter(max_attempts=10, window_seconds=60)
