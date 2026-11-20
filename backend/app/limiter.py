from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared in-memory rate limiter keyed by client remote IP
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
