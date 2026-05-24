"""
utils.py
"""

def parse_version(v: str) -> tuple[int, int]:
    """
    Convert a patch string to a comparable (major, minor) tuple.

    Args: 
        v (str): Patch string e.g. "15.14" or "15.14.1.2".

    Returns:
        tuple[int, int]: (major, minor) e.g. (15, 14).
            Returns (0, 0) if the string cannot be parsed.
    """
    parts = v.split(".")
    try:
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return (0, 0)
    
def normalize_version(v: str) -> str:
    """
    Normalize a full gamVersion string to major.minor only.

    Args:
        v (str): Full version string e.g. "15.14.1.2".

    Returns:
        str: Shortened version e.g. "15.14".
    """
    parts = v.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return v