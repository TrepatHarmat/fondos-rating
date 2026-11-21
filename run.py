import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

import validations
from morningstar import fetcher, normalize

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text())
GOLDEN = ROOT / "golden.json"
OUT = ROOT / CFG["output"]


def leer_golden():
    if GOLDEN.exists():
        try:
            return json.loads(GOLDEN.read_text())
        except Exception:
            return {}
    return {}


def hash_fondos(fondos):
    return hashlib.sha256(
        json.dumps(fondos, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def escribir(fondos):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": "Morningstar",
        "fondos": fondos,
    }
    texto = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    fd, tmp = tempfile.mkstemp(dir=OUT.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(texto)
    os.replace(tmp, OUT)


def main():
    try:
        raw = fetcher.collect(CFG)
    except fetcher.FetchError as e:
        print(f"FALLO DE RED: {e}")
        return 3

    fondos = normalize.build(raw)
    golden = leer_golden()

    try:
        validations.check(fondos, golden, CFG)
    except validations.ValidationError as e:
        print(f"FALLO DE VALIDACIÓN: {e}")
        return 2

    if not golden:
        muestra = {f["secId"]: f["rating"] for f in fondos if f.get("rating")}
        GOLDEN.write_text(
            json.dumps(dict(list(muestra.items())[:10]), indent=2) + "\n"
        )
        print("golden.json creado con 10 fondos de referencia")

    nuevo = hash_fondos(fondos)
    if OUT.exists():
        try:
            viejo = hash_fondos(json.loads(OUT.read_text())["fondos"])
        except Exception:
            viejo = None
        if viejo == nuevo:
            print("sin cambios, no se escribe nada")
            return 0

    escribir(fondos)
    print(f"escrito {OUT} con {len(fondos)} fondos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
