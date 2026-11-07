from datetime import datetime, timezone
from typing import Optional

def format_iso_timestamp(dt: Optional[datetime] = None) -> str:
    target = dt or datetime.now(timezone.utc)
    return target.isoformat()
