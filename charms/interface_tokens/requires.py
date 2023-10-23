import json
import logging
from typing import Optional, Set

from ops import CharmBase, Relation, RelationBrokenEvent
from ops.framework import Object
from ops.model import Unit
from pydantic import ValidationError

from .model import ProvidesModel, RequiresModel

log = logging.getLogger("TokensRequirer")


class TokensRequirer(Object):
    """Handles the requirer side of the tokens relation."""

    def __init__(self, charm: CharmBase, endpoint: str = "tokens"):
        super().__init__(charm, f"relation-{endpoint}")
        self.endpoint = endpoint

    def request_token(self, user: str, group: str):
        """Request a token for the given user and group."""
        log.info(f"Requesting Token for {user} using group: {group}")
        if self.relation:
            try:
                data = RequiresModel(
                    requests=self.relation.data[self.unit].get("requests", "{}")
                )
            except ValidationError:
                log.exception("Error validating relation data.")
            data.requests[user] = group
            self.relation.data[self.unit].update(
                {"requests": json.dumps(data.requests)}
            )

    def evaluate_relation(self, event) -> Optional[str]:
        """Evaluate the state of the relation."""
        no_relation = not self.relation or (
            isinstance(event, RelationBrokenEvent) and event.relation is self.relation
        )
        if not self.is_ready:
            if no_relation:
                return f"Missing required {self.endpoint} relation"
            return f"Waiting for {self.endpoint} relation"
        if self.in_flight_requests:
            which_users = ",".join(sorted(self.in_flight_requests))
            return f"Token request for users {which_users} is not yet fulfilled."
        return None

    def in_flight_requests(self) -> Set[str]:
        """Provides a set of requests which don't yet have a response."""
        if not self.is_ready:
            return set()
        reqs = RequiresModel(
            requests=self.relation.data[self.unit].get("requests", "{}")
        )
        return {user for user in reqs.requests.keys() if not self.get_token(user)}

    def get_token(self, user) -> Optional[str]:
        """Return the token for the given user."""
        return self._data.tokens.get(user) if self.is_ready else None

    @property
    def _data(self) -> Optional[ProvidesModel]:
        """Aggregate data from all units in the relation."""
        if not self.relation or not self.relation.units:
            return None

        data = {
            k: v
            for unit in self.relation.units
            for k, v in self.relation.data[unit].items()
        }
        log.info(f"Data in the relation: {data}")
        try:
            return ProvidesModel(**data)
        except ValidationError:
            log.exception("Token Data not yet available.")
            return None

    @property
    def is_ready(self):
        """Check if the relation data is ready and valid."""
        data = self._data
        if data is None:
            log.exception(f"{self.endpoint} relation data not yet available.")
            return False
        return True

    @property
    def relation(self) -> Optional[Relation]:
        """Retrieve the relation for the given endpoint."""
        return self.model.get_relation(self.endpoint)

    @property
    def unit(self) -> Unit:
        return self.model.unit
