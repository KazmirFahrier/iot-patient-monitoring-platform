from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session


def get_context(request: Request):
    return request.app.state.context


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.context.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
