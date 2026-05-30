# -*- coding: utf-8 -*-
"""
Extrai os segmentos (videos) de um projeto CapCut a partir das caixas de texto
separadoras no padrao "ESTRUTURA X - V Y".

Cada segmento vira: {nome, estrutura, versao, start_us, end_us, duration_us}.
O fim de um segmento = inicio do proximo separador (o ultimo vai ate o fim do projeto).
"""
import json
import os
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.join(os.environ["LOCALAPPDATA"], "CapCut", "User Data",
                    "Projects", "com.lveditor.draft")

# Os projetos rotulam o separador de duas formas:
#  - por extenso:  "ESTRUTURA 1 ... V3" / "ESTRUTURA1-V3"
#  - forma curta:  "E1 - V1" / "E1-V1" / "E 1 - V 1" / "E1 V1"
RE_FULL = re.compile(r"estrutura\s*0*(\d+).*?\bv\s*0*(\d+)", re.IGNORECASE | re.DOTALL)
# forma curta: ANCORADA no inicio do texto da caixa, com o V colado num numero,
# pra nao casar por engano com frases comuns.
RE_CURTA = re.compile(r"^\s*e\s*0*(\d+)\s*[-–—]?\s*v\s*0*(\d+)\b", re.IGNORECASE)


def match_rotulo(txt):
    """Devolve (estrutura, versao) se o texto for um rotulo separador, senao None."""
    if not txt:
        return None
    m = RE_FULL.search(txt)
    if m:
        return int(m.group(1)), int(m.group(2))
    flat = re.sub(r"\s+", " ", txt).strip()
    m = RE_CURTA.match(flat)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _plain(content):
    try:
        return json.loads(content).get("text", "")
    except Exception:
        return str(content or "")


def _load(proj):
    path = os.path.join(BASE, proj, "draft_content.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def extrair(proj):
    d = _load(proj)
    proj_dur = int(d.get("duration", 0))
    texts = {t["id"]: _plain(t.get("content", "")) for t in d.get("materials", {}).get("texts", [])}

    seps = []
    for tr in d.get("tracks", []):
        if tr.get("type") != "text":
            continue
        for s in tr.get("segments", []):
            txt = texts.get(s.get("material_id"), "")
            mr = match_rotulo(txt)
            if not mr:
                continue
            tt = s.get("target_timerange", {})
            seps.append({
                "estrutura": mr[0],
                "versao": mr[1],
                "txt_start": int(tt.get("start", 0)),
                "txt_dur": int(tt.get("duration", 0)),
            })

    # ordena por posicao na timeline
    seps.sort(key=lambda x: x["txt_start"])

    segs = []
    for i, sp in enumerate(seps):
        prox = seps[i + 1]["txt_start"] if i + 1 < len(seps) else proj_dur
        # criterio da Mariane: IN = fim do rotulo atual; OUT = inicio do proximo rotulo.
        # assim o rotulo (~1.8s) fica de fora do corte final.
        start = sp["txt_start"] + sp["txt_dur"]
        end = prox
        segs.append({
            "nome": f"E{sp['estrutura']}-V{sp['versao']}",
            "estrutura": sp["estrutura"],
            "versao": sp["versao"],
            "start_us": start,
            "end_us": end,
            "duration_us": end - start,
            "rotulo_start_us": sp["txt_start"],
            "rotulo_dur_us": sp["txt_dur"],
        })
    return {"projeto": proj, "duracao_us": proj_dur, "segmentos": segs}


def _fmt(us):
    s = us / 1_000_000
    m, s = divmod(s, 60)
    return f"{int(m)}:{s:05.2f}"


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "Reels-Jurerê III-Narrado-E1-V"
    r = extrair(proj)
    print(f"Projeto: {r['projeto']}  (duracao {_fmt(r['duracao_us'])})")
    print(f"{len(r['segmentos'])} segmento(s):\n")
    print(f"  {'nome':<18} {'inicio':>8} {'fim':>8} {'duracao':>8}  {'txt_dur':>8}")
    for s in r["segmentos"]:
        print(f"  {s['nome']:<18} {_fmt(s['start_us']):>8} {_fmt(s['end_us']):>8} "
              f"{_fmt(s['duration_us']):>8}  {_fmt(s['txt_dur_us']):>8}")
