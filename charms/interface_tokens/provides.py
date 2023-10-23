import json
import logging
from dataclasses import dataclass
from typing import Dict, List

from ops import CharmBase, Relation, Unit
from pydantic import ValidationError

from .model import ProvidesModel, RequiresModel

log = logging.getLogger("TokensProvider")


@dataclass
class Request:
    """Represents a request for an authentication token.

    Attributes:
        unit (str): The name of the unit making the request.
        relation_id (int): The ID of the relation associated with the request.
        request (Dict[str,str]): Mapping of the token requests consisting of user:group.
    """

    unit: str
    relation_id: int
    requests: Dict[str, str]


class TokensProvider:
    """Implements the Provides side of the tokens interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint

    def send_token(self, request: Request, tokens: Dict[str, str]) -> None:
        """Send the token to the related units."""
        for relation in self.relations:
            if relation.id == request.relation_id:
                existing_tokens = json.loads(
                    relation.data[self.unit].get("tokens", "{}")
                )
                existing_tokens.update(tokens)
                relation.data[self.unit]["tokens"] = json.dumps(existing_tokens)

    def remove_stale_tokens(self) -> None:
        """Remove tokens that are no longer in the requests."""

        current_requests = {
            req.relation_id: req.requests for req in self.token_requests
        }

        for relation in self.relations:
            try:
                data = ProvidesModel(
                    tokens=relation.data[self.unit].get("tokens", "{}")
                )
                exisiting_tokens = data.tokens
                required_tokens = current_requests.get(relation.id, {})

                tokens_to_remove = set(exisiting_tokens) - set(required_tokens)
                for token in tokens_to_remove:
                    exisiting_tokens.pop(token, None)

                relation.data[self.unit]["tokens"] = json.dumps(exisiting_tokens)
            except ValidationError:
                log.exception(f"Failed to validate data from relation {relation.id}")

    @property
    def token_requests(self) -> List[Request]:
        """List of token requests based on relations."""
        requests = []
        for relation in self.relations:
            for unit in relation.units:
                data = relation.data[unit].get("requests", "{}")
                parsed_data = RequiresModel(requests=data)
                requests.append(
                    Request(
                        unit=unit.name,
                        relation_id=relation.id,
                        requests=parsed_data.requests,
                    )
                )
        return requests

    @property
    def relations(self) -> List[Relation]:
        """List of relations of this endpoint."""
        return self.charm.model.relations.get(self.endpoint) or []

    @property
    def unit(self) -> Unit:
        """Return the charm unit."""
        return self.charm.unit
