# NO TOCAR sin motivo. Codex tiene prohibido editarlo.
class ValidationError(RuntimeError):
    pass


def check(rows, golden, cfg):
    if not isinstance(rows, list) or not rows:
        raise ValidationError("lista vacía o formato inesperado")

    n = len(rows)
    if not cfg["min_total"] <= n <= cfg["max_total"]:
        raise ValidationError(f"número de fondos fuera de rango: {n}")

    for campo in ("secId", "rating", "name"):
        if campo not in rows[0]:
            raise ValidationError(f"campo {campo} desaparecido")

    rated = sum(1 for r in rows if r.get("rating"))
    ratio = rated / n
    if ratio < cfg["min_rated_ratio"]:
        raise ValidationError(f"cobertura de rating baja: {ratio:.1%}")

    for r in rows:
        if r.get("rating") is not None and r["rating"] not in (1, 2, 3, 4, 5):
            raise ValidationError(f"rating fuera de rango en {r['secId']}: {r['rating']}")

    isins = [r["isin"] for r in rows if r.get("isin")]
    if len(isins) != len(set(isins)):
        raise ValidationError("ISIN duplicados tras normalizar")

    index = {r["secId"]: r.get("rating") for r in rows}
    cambios = 0
    for secid, esperado in golden.items():
        if secid not in index:
            raise ValidationError(f"golden ausente: {secid}")
        if index[secid] != esperado:
            cambios += 1
    if cambios > cfg.get("max_golden_changes", 2):
        raise ValidationError(f"{cambios} cambios en golden, revisa el endpoint")
