def to_minutes(hhmm: str) -> int:
    """Turn '09:30' into 570 (minutes since midnight)."""
    try:
        hours, minutes = hhmm.split(":")
        hours = int(hours)
        minutes = int(minutes)
    except (ValueError, AttributeError):
        raise ValueError(f"'{hhmm}' is not a time. Use 24-hour HH:MM, e.g. 09:30.") from None
    if not (0 <= hours <=23 and 0 <= minutes <=59):
        raise ValueError(f"'{hhmm}' is not a real time. Hours go 00-23 and minutes 00-59.")
    return hours * 60 + minutes

def to_hhmm(minutes: int) -> str:
    """Turn 570 back into '09:30'."""
    hours, mins = divmod(minutes, 60)
    return f"{hours:02d}:{mins:02d}"
