from contextlib import contextmanager
from contextvars import ContextVar


_current_request = ContextVar("audit_current_request", default=None)
_actor_override = ContextVar("audit_actor_override", default=None)
_disabled_depth = ContextVar("audit_disabled_depth", default=0)


def get_current_request():
    return _current_request.get()


def get_actor_override():
    return _actor_override.get()


def is_audit_suspended():
    return _disabled_depth.get() > 0


@contextmanager
def audit_request(request):
    token = _current_request.set(request)
    try:
        yield
    finally:
        _current_request.reset(token)


@contextmanager
def audit_actor(actor):
    token = _actor_override.set(actor)
    try:
        yield
    finally:
        _actor_override.reset(token)


@contextmanager
def suspend_audit():
    token = _disabled_depth.set(_disabled_depth.get() + 1)
    try:
        yield
    finally:
        _disabled_depth.reset(token)
