import math
import random
import time

from curl_cffi import requests as creq

INSTANCES = ["klr5zyak8x", "9vehuxllxs"]

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://lt.morningstar.com/1c6qh1t6k9/fundscreener/results.aspx?LanguageId=es-ES",
    "Origin": "https://lt.morningstar.com",
}


class FetchError(RuntimeError):
    pass


def _session():
    s = creq.Session(impersonate="chrome")
    s.headers.update(HEADERS)
    return s


def _page(session, instance, params, attempts=6):
    url = f"https://lt.morningstar.com/api/rest.svc/{instance}/security/screener"
    last = None
    for i in range(attempts):
        r = session.get(url, params=params, timeout=(5, 25))
        last = r.status_code
        if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
            return r.json()
        if r.status_code in (400, 404):
            raise FetchError(f"{r.status_code}: {r.text[:200]}")
        time.sleep(min(60, 2 ** i) + random.uniform(0, 1.5))
    raise FetchError(f"reintentos agotados, último estado {last}")


def collect(cfg, log=print):
    base = {
        "outputType": "json",
        "version": 1,
        "languageId": cfg["language"],
        "currencyId": cfg["currency"],
        "universeIds": cfg["universe"],
        "securityDataPoints": "|".join(cfg["data_points"]),
        "sortOrder": "SecId asc",
        "filters": cfg["filters"],
        "pageSize": cfg["page_size"],
    }

    rows, total, pages = [], None, None
    instance = INSTANCES[0]
    session = _session()

    for p in range(1, cfg["max_pages"] + 1):
        params = dict(base, page=p)
        try:
            data = _page(session, instance, params)
        except FetchError:
            instance = INSTANCES[1] if instance == INSTANCES[0] else INSTANCES[0]
            session = _session()
            data = _page(session, instance, params)

        if total is None:
            total = int(data.get("total", 0))
            if total <= 0:
                raise FetchError("el endpoint devuelve total=0")
            pages = max(1, math.ceil(total / cfg["page_size"]))
            log(f"total={total} páginas={pages}")

        rows.extend(data.get("rows") or [])
        if p >= pages:
            break
        time.sleep(random.uniform(*cfg["sleep_between_pages"]))

    return rows
