def summarize(values: tuple[bool, ...]) -> dict[str, int | float]:
    count = len(values)
    ok = sum(values)
    error = count - ok
    ratio = 1.0 if count == 0 else ok / count
    return {"count": count, "ok": ok, "error": error, "ratio": ratio}
