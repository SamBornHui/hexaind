from hashlib import sha512
from typing import Any


def hash_obj(object: Any) -> str:
    return sha512(repr(object).encode()).hexdigest()
