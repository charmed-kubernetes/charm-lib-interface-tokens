import logging
from typing import Dict, Optional

from ops import CharmBase, Relation, RelationBrokenEvent
from ops.framework import Object
from pydantic import BaseModel, Json, ValidationError

log = logging.getLogger("ClusterAuthTokenRequirer")


class Data(BaseModel):
    """Represents the data structure for tokens."""

    tokens: Json[Dict[str, str]]


class TokensRequirer(Object):
    """Handles the requirer side of the tokens relation."""

    def __init__(self, charm: CharmBase, endpoint: str = "tokens"):
        super().__init__(charm, f"relation-{endpoint}")
        self.endpoint = endpoint

    def request_token(self, user: str, group: str):
        """Request a token for the given user and group."""
        if self.relation:
            self.relation.data[self.model.unit].update({"user": user, "group": group})

    @property
    def relation(self) -> Optional[Relation]:
        """Retrieve the relation for the given endpoint."""
        return self.model.get_relation(self.endpoint)

    @property
    def _data(self) -> Optional[Data]:
        """Aggregate data from all units in the relation."""
        if not self.relation or not self.relation.units:
            return None

        data = {
            k: v
            for unit in self.relation.units
            for k, v in self.relation.data[unit].items()
        }
        try:
            return Data(**data)
        except ValidationError:
            return None

    @property
    def is_ready(self):
        """Check if the relation data is ready and valid."""
        data = self._data
        if data is None:
            log.exception(f"{self.endpoint} relation data not yet available.")
            return False
        return True

    def evaluate_relation(self, event) -> Optional[str]:
        """Evaluate the state of the relation."""
        no_relation = not self.relation or (
            isinstance(event, RelationBrokenEvent) and event.relation is self.relation
        )
        if not self.is_ready:
            if no_relation:
                return f"Missing required {self.endpoint} relation"
            return f"Waiting for {self.endpoint} relation"
        return None

    def get_token(self, user) -> Optional[str]:
        """Return the token for the given user."""
        if not self.is_ready:
            return None

        return self._data.tokens.get(user)
