from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CustomerProfile:
    customer_id: str
    email: str
    tags: List[str] = field(default_factory=list)
    is_active: bool = True

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag.strip().lower())
