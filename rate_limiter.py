"""
Lihtne IP-põhine päringulimiit.
"""
import time
from collections import defaultdict

import config


class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)  # ip -> [timestamps]

    def is_allowed(self, ip):
        """Kontrolli kas IP tohib päringut teha."""
        now = time.time()
        timestamps = self.requests[ip]

        # Eemalda vanad kirjed (üle 1 tunni)
        self.requests[ip] = [t for t in timestamps if now - t < 3600]
        timestamps = self.requests[ip]

        # Kontrolli minutilimiiti
        recent_minute = sum(1 for t in timestamps if now - t < 60)
        if recent_minute >= config.MAX_REQUESTS_PER_MINUTE:
            return False, "Liiga palju päringuid. Palun oodake minut."

        # Kontrolli tunnilimiiti
        if len(timestamps) >= config.MAX_REQUESTS_PER_HOUR:
            return False, "Tunnilimiit täis. Palun proovige hiljem."

        # Luba
        self.requests[ip].append(now)
        return True, ""

    def cleanup(self):
        """Eemalda vanad IP-d."""
        now = time.time()
        expired = [ip for ip, times in self.requests.items()
                   if not times or now - max(times) > 7200]
        for ip in expired:
            del self.requests[ip]
