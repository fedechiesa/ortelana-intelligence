import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import DomainError

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    name: str
    role: str


def authenticate(
    request: Request, credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
):
    token = credential.credentials if credential else ""
    cfg = request.app.state.settings
    for expected, actor in [
        (cfg.operator_token, Actor("local-operator", "operator")),
        (cfg.supervisor_token, Actor("local-supervisor", "supervisor")),
        (cfg.automation_token, Actor("n8n-automation", "automation")),
    ]:
        if secrets.compare_digest(token, expected):
            return actor
    raise DomainError(401, "A valid local bearer token is required")


def supervisor(actor: Annotated[Actor, Depends(authenticate)]):
    if actor.role != "supervisor":
        raise DomainError(403, "Supervisor role required")
    return actor
