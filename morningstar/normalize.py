def build(rows):
    out = {}
    for r in rows:
        secid = r.get("SecId")
        if not secid:
            continue
        out[secid] = {
            "secId": secid,
            "isin": r.get("ISIN"),
            "name": r.get("LegalName"),
            "category": r.get("CategoryName"),
            "rating": r.get("StarRatingM255"),
            "risk": r.get("MorningstarRiskM255"),
            "currency": r.get("PriceCurrency"),
        }
    return [out[k] for k in sorted(out)]
