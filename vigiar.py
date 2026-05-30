# -*- coding: utf-8 -*-
"""
CapCut Exporter - Vigia de pasta
================================
Vigia a pasta onde voce exporta a timeline INTEIRA do CapCut. Quando um novo
.mp4 aparece, identifica o projeto (pelo nome do arquivo), confirma que e a
timeline inteira (pela duracao), corta nos N videos, organiza em Estrutura\\V
e (opcional) apaga o arquivo grande.

Uso:
    py vigiar.py            # fica vigiando (Ctrl+C pra parar)
    py vigiar.py --agora    # processa o .mp4 mais recente da pasta, uma vez
"""
import json
import os
import sys
import time
import unicodedata

import exportar
import segments as seg
import split

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold().strip()


def _mtime_draft(nome):
    """Data de modificacao do draft_content.json do projeto (pra achar o que esta aberto)."""
    dc = os.path.join(seg.BASE, nome, "draft_content.json")
    try:
        return os.path.getmtime(dc)
    except OSError:
        return 0


def achar_projeto(nome_arquivo):
    """Acha o projeto que corresponde ao arquivo exportado.

    O CapCut as vezes TRUNCA o nome ('Reels-Jurere III-Narrado-.mp4'), entao:
    1) tenta match exato; 2) tenta por PREFIXO (nome do projeto comeca com o do
    arquivo, ou vice-versa); entre varios, fica com o draft MAIS RECENTE
    (= o projeto que estava aberto e acabou de exportar)."""
    import re
    base = os.path.splitext(os.path.basename(nome_arquivo))[0]
    base = re.sub(r"\s*\(\d+\)\s*$", "", base)         # tira (1), (2)... do CapCut
    base = re.sub(r"\s*\d+$", "", base)               # tira numero solto no fim
    nb = _norm(base).rstrip(" -_.()")                  # tira pontuacao/traco/parenteses no fim
    nomes = [d.name for d in os.scandir(seg.BASE) if d.is_dir()]
    por_norm = {_norm(n): n for n in nomes}

    # 1) match exato
    if _norm(base) in por_norm:
        return por_norm[_norm(base)]

    # 2) match por prefixo (um e' inicio do outro), desempate pelo draft mais recente
    cands = []
    for n in nomes:
        nn = _norm(n).rstrip(" -_.")
        if nn and (nn.startswith(nb) or nb.startswith(nn)):
            cands.append(n)
    if cands:
        return max(cands, key=_mtime_draft)
    return None


def processar(video, cfg, ff):
    nome = os.path.basename(video)
    proj = achar_projeto(video)
    if not proj:
        print(f"  [ignorado] '{nome}': nao achei projeto com esse nome.")
        return
    try:
        r = seg.extrair(proj)
    except Exception as e:
        print(f"  [ignorado] '{nome}': erro lendo projeto ({e}).")
        return
    if not r["segmentos"]:
        print(f"  [ignorado] '{nome}': projeto sem videos ESTRUTURA-VY.")
        return

    # confirma que e a timeline INTEIRA (duracao bate com a do projeto)
    dur_vid = split.duracao_us(video, ff) or 0
    tol = cfg["vigia"].get("tolerancia_duracao_s", 3) * 1_000_000
    if abs(dur_vid - r["duracao_us"]) > tol:
        print(f"  [ignorado] '{nome}': duracao {dur_vid/1e6:.1f}s != timeline "
              f"{r['duracao_us']/1e6:.1f}s (parece um clipe avulso, nao a timeline inteira).")
        return

    pasta = cfg["destino"]["pasta_local"]
    print(f"  >> {proj}: cortando {len(r['segmentos'])} videos...")
    ok, total, raiz = exportar.gerar_cortes(proj, video, pasta,
                                            cfg.get("nome_arquivo", "{projeto}__{nome}"),
                                            log=lambda m: None)
    print(f"  >> {ok}/{total} clipes em {raiz}")

    if cfg["vigia"].get("deletar_apos_cortar"):
        try:
            os.remove(video)
            print(f"  >> arquivo grande apagado: {nome}")
        except OSError as e:
            print(f"  >> nao consegui apagar {nome}: {e}")
    return raiz


def _mp4s(pasta):
    try:
        return {e.path: e.stat().st_size for e in os.scandir(pasta)
                if e.is_file() and e.name.lower().endswith(".mp4")}
    except FileNotFoundError:
        return {}


def main():
    cfg = exportar.carregar_config()
    pasta = cfg["vigia"]["pasta_export_capcut"]
    ff = split.achar_ffmpeg()
    os.makedirs(pasta, exist_ok=True)

    if "--agora" in sys.argv:
        atuais = _mp4s(pasta)
        if not atuais:
            sys.exit("Nenhum .mp4 na pasta vigiada.")
        recente = max(atuais, key=os.path.getmtime)
        print(f"Processando o mais recente: {os.path.basename(recente)}")
        processar(recente, cfg, ff)
        return

    print(f"Vigiando: {pasta}")
    print(f"Destino:  {cfg['destino']['pasta_local']}")
    print("Exporte a timeline inteira do CapCut aqui. (Ctrl+C pra parar)\n")
    vistos = _mp4s(pasta)  # ignora o que ja existe
    while True:
        time.sleep(3)
        agora = _mp4s(pasta)
        novos = [p for p in agora if p not in vistos]
        for p in novos:
            # espera o arquivo parar de crescer (export terminou)
            tam = -1
            while agora.get(p) != tam:
                tam = agora[p]
                time.sleep(2)
                agora = _mp4s(pasta)
            print(f"[novo] {os.path.basename(p)}")
            processar(p, cfg, ff)
        vistos = _mp4s(pasta)


if __name__ == "__main__":
    main()
