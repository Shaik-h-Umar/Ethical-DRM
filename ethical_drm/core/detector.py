try:
    from .hashing import hash_video
except ImportError:
    from core.hashing import hash_video


PHASH_MAX_DISTANCE = 10


def _hamming_distance_hex(hash_a: str, hash_b: str) -> int | None:
    """Return bit Hamming distance for two hex pHash strings, else None."""
    if not hash_a or not hash_b or len(hash_a) != len(hash_b):
        return None

    try:
        value_a = int(hash_a, 16)
        value_b = int(hash_b, 16)
    except ValueError:
        return None

    return (value_a ^ value_b).bit_count()


def get_video_hashes(video_path: str, sample_every_n: int = 30) -> list:
    """Backward-compatible alias used by existing app code."""
    _ = sample_every_n
    return hash_video(video_path)


def detect_leak(leaked_video_path: str, database: list) -> tuple[str | None, float]:
    """
    Identify which user a leaked video likely belongs to.

    Args:
        leaked_video_path: Path to leaked video file
        database: List of records:
            [
              {"user_id": "user123", "hashes": ["...", "..."]},
              ...
            ]

    Returns:
        Tuple of:
        - matched user_id (or None)
        - confidence percentage (0.0 to 100.0)
    """
    leaked_hashes = hash_video(leaked_video_path)
    leaked_set = set(leaked_hashes)

    if not leaked_set:
        return None, 0.0

    best_user = None
    best_count = 0

    for record in database:
        user_id = record.get("user_id")
        stored_hashes = record.get("hashes", [])
        stored_set = set(stored_hashes)

        # Fast path for exact matches.
        exact_count = len(leaked_set.intersection(stored_set))
        match_count = exact_count

        # Fuzzy path for re-encoded uploads (hosting platforms often transcode).
        if match_count < len(leaked_set):
            for leaked_hash in leaked_set:
                if leaked_hash in stored_set:
                    continue

                for stored_hash in stored_set:
                    distance = _hamming_distance_hex(leaked_hash, stored_hash)
                    if distance is not None and distance <= PHASH_MAX_DISTANCE:
                        match_count += 1
                        break

        if match_count > best_count:
            best_count = match_count
            best_user = user_id

    confidence = (best_count / len(leaked_set)) * 100 if leaked_set else 0.0

    if best_user:
        return best_user, confidence

    return None, 0.0