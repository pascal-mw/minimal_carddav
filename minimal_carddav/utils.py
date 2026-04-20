import hashlib


def make_uid(source_id: str) -> str:
    return hashlib.sha256(source_id.encode()).hexdigest()[:32]