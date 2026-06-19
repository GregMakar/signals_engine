from typing import Literal, TypeAlias, Any


HitScope: TypeAlias = Literal["direct", "related", "context"]
RoutingDecision: TypeAlias = Literal[
    "ignore",
    "store_only",
    "manual_review",
    "alert",
]