# -*- coding: utf-8 -*-
"""
CapCut Exporter - Deteccao
==========================
Varre os projetos do CapCut e identifica quais contem videos no padrao
"ESTRUTURA X - V Y" (caixas de texto separadoras) - ou seja, os projetos
que tem variacoes a exportar.

Uso:
    py scan.py                 # lista projetos COM segmentos (candidatos a exportar)
    py scan.py "<projeto>"     # detalha os segmentos de UM projeto
    py scan.py --json "<proj>" # idem, em JSON (consumido pelo exportador)
"""
import json
import os
import sys
from datetime import datetime, timezone

import segments as seg

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = seg.BASE
MANIFEST = os.path.join(BASE, "root_meta_info.json")


def _modificados():
    """nome do projeto -> (timestamp_us, datetime) a partir do manifesto."""
    out = {}
    if os.path.isfile(MANIFEST):
        with open(MANIFEST, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for d in data.get("all_draft_store", []):
            if d.get("draft_is_invisible"):
                continue
            ts = d.get("tm_draft_modified") or 0
            out[d.get("draft_name", "")] = ts
    return out


def _human(ts_us):
    if not ts_us:
        return "?"
    try:
        dt = datetime.fromtimestamp(ts_us / 1_000_000, tz=timezone.utc).astimezone()
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, OSError):
        return "?"


def varrer():
    """Retorna lista de projetos com segmentos: [{nome, qtd, modificado_us}]."""
    mods = _modificados()
    achados = []
    for entry in os.scandir(BASE):
        if not entry.is_dir():
            continue
        try:
            r = seg.extrair(entry.name)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            continue
        if r["segmentos"]:
            achados.append({
                "nome": entry.name,
                "qtd": len(r["segmentos"]),
                "modificado_us": mods.get(entry.name, 0),
            })
    achados.sort(key=lambda x: x["modificado_us"], reverse=True)
    return achados


def detalhar(proj):
    r = seg.extrair(proj)
    print(f"\nProjeto: {r['projeto']}  (duracao {seg._fmt(r['duracao_us'])})")
    print(f"{len(r['segmentos'])} video(s) a exportar:\n")
    nomes = {}
    for s in r["segmentos"]:
        nomes[s["nome"]] = nomes.get(s["nome"], 0) + 1
        dup = "  << NOME DUPLICADO" if nomes[s["nome"]] > 1 else ""
        print(f"  {s['nome']:<18} {seg._fmt(s['start_us']):>8} -> {seg._fmt(s['end_us']):>8}"
              f"  ({seg._fmt(s['duration_us'])}){dup}")


def main():
    args = sys.argv[1:]
    if "--json" in args:
        args.remove("--json")
        proj = args[0] if args else None
        print(json.dumps(seg.extrair(proj), ensure_ascii=False, indent=2))
        return
    if args:
        detalhar(args[0])
        return

    achados = varrer()
    print(f"\n{len(achados)} projeto(s) com videos no padrao ESTRUTURA-VY "
          f"(mais recentes primeiro):\n")
    for a in achados:
        print(f"  {_human(a['modificado_us']):>16}  {a['qtd']:>2} vid  {a['nome']}")
    print("\nDetalhar um projeto:  py scan.py \"<nome do projeto>\"")


if __name__ == "__main__":
    main()
