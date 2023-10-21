from typing import Dict

from pydantic import BaseModel, Json


class RequiresModel(BaseModel):
    requests: Json[Dict[str, str]]


class ProvidesModel(BaseModel):
    tokens: Json[Dict[str, str]]
