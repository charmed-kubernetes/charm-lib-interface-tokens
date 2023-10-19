import json
from dataclasses import dataclass
from typing import List, Optional

from ops import CharmBase, Relation, Unit


@dataclass
class TokenRequest:
    """Represents a request for an authentication token.

    Attributes:
        unit (str): The name of the unit making the request.
        user (str): The user associated with the token request.
        group (str): The group associated with the user.
    """

    relation_id: int
    unit: str
    user: str
    group: str


class TokensProvider:
    """Implements the Provides side of the tokens interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint

    def send_token(self, request: TokenRequest, token: str) -> None:
        """Send the token to the related units."""
        # Aggregate tokens from all relations.
        tokens = {
            k: v
            for relation in self.relations
            for k, v in json.loads(relation.data[self.unit].get("tokens", "{}")).items()
        }

        tokens[request.user] = token
        value = json.dumps(tokens)

        # Update all relations with the new token data.
        for relation in self.relations:
            relation.data[self.unit]["tokens"] = value

    @property
    def token_requests(self) -> List[TokenRequest]:
        """List of token requests based on relations."""
        if not self.relations:
            return []
        return [
            TokenRequest(
                relation_id=relation.id, unit=unit.name, user=user, group=group
            )
            for relation in self.relations
            for unit in relation.units
            if (user := relation.data[unit].get("user"))
            and (group := relation.data[unit].get("group"))
        ]

    @property
    def relations(self) -> Optional[List[Relation]]:
        """List of relations of this endpoint."""
        return self.charm.model.relations.get(self.endpoint)

    @property
    def unit(self) -> Unit:
        """Return the charm unit."""
        return self.charm.unit
