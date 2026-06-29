from datetime import datetime, timezone

def format_bytes(size: int) -> str:
    if size is None:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size)

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {units[i]}"

def format_expiry(expiry_ms: int) -> str:
    if not expiry_ms:
        return "∞ (без срока)"

    dt = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")

def format_remaining(expiry_ms: int) -> str:
    if not expiry_ms:
        return "∞"

    now = datetime.now(timezone.utc)
    expiry = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)

    delta = expiry - now

    if delta.total_seconds() <= 0:
        return "❌ истекла"

    days = delta.days
    hours = delta.seconds // 3600

    return f"{days} дн. {hours} ч."

def format_cost(cost, disc):
    return cost * ((100 - disc) / 100)