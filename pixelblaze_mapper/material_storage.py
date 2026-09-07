"""Material storage boundary: durable JSON values, session-only Python caches.

TD OP.storeStartupValue supplies the value serialized to a toe/tox and loaded
at startup, without replacing the live value. Never pickle shader adapters or
state classes: importlib.reload can invalidate their Python class identity.
"""
import json


def state_document(value):
    """Accept an old store regardless of class identity; emit detached primitives."""
    if value is None:
        return None
    if not isinstance(value, dict):
        converter = getattr(value, 'to_dict', None)
        if not callable(converter):
            raise TypeError('material state must be a document or a convertible store')
        value = converter()
    document = json.loads(json.dumps(value, allow_nan=False))
    if not isinstance(document, dict) or not isinstance(document.get('materials'), dict):
        raise ValueError('material state requires a materials object')
    return document


def runtime_cache(owner, key):
    """Retain session cache identity, but replace it with None when saving.

    A non-TD host without startup-value support gets a module-local cache;
    remove any old unsafe entry instead of silently making it persistent.
    """
    register = getattr(owner, 'storeStartupValue', None)
    if not callable(register):
        storage = getattr(owner, 'storage', None)
        if isinstance(storage, dict):
            storage.pop(key, None)
        return {}
    register(key, None)
    cache = owner.fetch(key, None)
    if not isinstance(cache, dict):
        cache = {}
        owner.store(key, cache)
    return cache
