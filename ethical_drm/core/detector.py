try:
    from .hashing import hash_video
except ImportError:
    from core.hashing import hash_video


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
        print("No hashes generated from leaked video.")
        return None, 0.0

    best_user = None
    best_count = 0

    for record in database:
        user_id = record.get("user_id")
        stored_hashes = record.get("hashes", [])

        match_count = len(leaked_set.intersection(set(stored_hashes)))
        print(f"[DEBUG] user_id={user_id}, matches={match_count}")

        if match_count > best_count:
            best_count = match_count
            best_user = user_id

    confidence = (best_count / len(leaked_set)) * 100 if leaked_set else 0.0

    if best_user:
        print(
            f"[INFO] Leak matched: user_id={best_user}, "
            f"match_count={best_count}, confidence={confidence:.2f}%"
        )
        return best_user, confidence

    print("[INFO] No matching user found above threshold.")
    return None, 0.0