"""Paper-fund operations. Reads halalquant facts and Research/sleeves rules."""

from .live_rules import live_rules
from .session import SessionResult, run_session

__all__ = ["SessionResult", "live_rules", "run_session"]
