# -*- coding: utf-8 -*-
"""
CapCut Exporter - Orquestrador / nucleo de corte
=================================================
Pega o video da TIMELINE INTEIRA (exportado do CapCut) e corta em N clipes,
um por video do padrao ESTRUTURA-VY, organizando em Estrutura N\\VM\\.

Uso CLI:
    py exportar.py "<projeto>" --video "C:\\...\\timeline_inteira.mp4"
"""
import argparse
import glob
import json
import os
import re
import sys

import segments as seg
import split

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config.json")
CONFIG_EXEMPLO = os.path.join(HERE, "config.exemplo.json")


def carregar_config():
    # 1a vez (ou apos baixar do GitHub): cria o config.json a partir do modelo
    if not os.path.isfile(CONFIG) and os.path.isfile(CONFIG_EXEMPLO):
        import shutil
        shutil.copyfile(CONFIG_EXEMPLO, CONFIG)
    with open(CONFIG, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    # portabilidade: expande variaveis (%USERPROFILE% etc.) e aplica defaults
    cfg.setdefault("destino", {})
    cfg.setdefault("vigia", {})
    d = cfg["destino"].get("pasta_local") or ""
    cfg["destino"]["pasta_local"] = os.path.expandvars(os.path.expanduser(d)) if d else ""
    t = cfg["vigia"].get("pasta_export_capcut") or ""
    if t:
        t = os.path.expandvars(os.path.expanduser(t))
    cfg["vigia"]["pasta_export_capcut"] = t
    cfg["vigia"].setdefault("deletar_apos_cortar", True)
    cfg["vigia"].setdefault("tolerancia_duracao_s", 3)
    cfg.setdefault("nome_arquivo", "{projeto} {nome}")
    return cfg


def salvar_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)


def slug(s):
    return re.sub(r"[^\w\-]+", "-", s, flags=re.UNICODE).strip("-")


# Formatos (prefixo no nome do projeto) que NAO entram na pasta-mae:
# Reels (9:16) e Feed (4:5) sao o MESMO video -> mesma pasta, formato so' no arquivo.
FORMATOS = ("reels", "feed", "stories", "story", "carrossel")


def _limpar(s):
    """Limpa pra usar em nome de pasta/arquivo: tira ilegais, tracos viram espaco."""
    s = re.sub(r'[\\/:*?"<>|]+', " ", s)
    s = re.sub(r"[-–—]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s


def _sem_formato(projeto):
    """Remove o prefixo de formato (Reels/Feed/...) do inicio do nome do projeto."""
    pat = r"^(" + "|".join(FORMATOS) + r")\b[\s\-–—_]*"
    m = re.match(pat, projeto, re.IGNORECASE)
    return projeto[m.end():] if m else projeto


def nome_arquivo_projeto(projeto):
    """Nome COMPLETO limpo do projeto (mantem Reels/Feed na frente) -> nome do arquivo.
    Ex.: 'Feed-Narrado-Vistas de Anita III-E1-V' -> 'Feed Narrado Vistas de Anita III E1 V'."""
    return _limpar(projeto) or "Projeto"


def nome_pasta_projeto(projeto):
    """Nome da PASTA-mae, SEM o formato (Reels/Feed) -> os dois formatos caem na MESMA pasta.
    Ex.: 'Reels-Narrado-Vistas...' e 'Feed-Narrado-Vistas...' -> 'Narrado Vistas...'."""
    return _limpar(_sem_formato(projeto)) or "Projeto"


def pasta_saida_projeto(pasta, projeto):
    """Pasta-mae onde vao as Estruturas: <destino>/<Projeto sem formato>/."""
    return os.path.join(pasta, nome_pasta_projeto(projeto))


def achar_video_recente():
    cands = []
    for pasta in (os.path.join(os.environ["USERPROFILE"], "Downloads"),
                  os.path.join(os.environ["USERPROFILE"], "Desktop")):
        cands += glob.glob(os.path.join(pasta, "*.mp4"))
    return max(cands, key=os.path.getmtime) if cands else None


def gerar_cortes(projeto, video, pasta, modelo="{projeto}__{nome}", dry=False, log=print):
    """Corta o video inteiro nos N trechos do projeto, dentro de uma pasta-mae
    com o nome do projeto. Retorna (ok, total, raiz) — raiz = pasta-mae do projeto."""
    r = seg.extrair(projeto)
    if not r["segmentos"]:
        raise ValueError(f"Projeto '{projeto}' sem videos no padrao ESTRUTURA-VY.")
    raiz = pasta_saida_projeto(pasta, projeto)   # <destino>/<Nome do Projeto>/
    os.makedirs(raiz, exist_ok=True)
    ff = split.achar_ffmpeg()
    ok = 0
    for s in r["segmentos"]:
        subpasta = os.path.join(raiz, f"Estrutura {s['estrutura']}", f"V{s['versao']}")
        os.makedirs(subpasta, exist_ok=True)
        nome = modelo.format(projeto=nome_arquivo_projeto(projeto), nome=s["nome"])
        saida = os.path.join(subpasta, nome + ".mp4")
        if os.path.exists(saida):
            saida = os.path.join(subpasta, nome + "_2.mp4")
        rel = os.path.relpath(saida, raiz)
        log(f"  {s['nome']:<10} {seg._fmt(s['start_us'])} (+{seg._fmt(s['duration_us'])}) -> {rel}")
        if dry:
            continue
        try:
            split.cortar(video, s["start_us"], s["duration_us"], saida, ff)
            ok += 1
        except Exception as e:
            log(f"     [FALHOU] {e}")
    return ok, len(r["segmentos"]), raiz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("--video")
    ap.add_argument("--pasta")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = carregar_config()
    pasta = args.pasta or cfg["destino"].get("pasta_local") or ""
    if not pasta:
        sys.exit("Defina destino.pasta_local no config.json ou use --pasta.")

    video = args.video or achar_video_recente()
    if not args.dry_run and (not video or not os.path.isfile(video)):
        sys.exit("Video da timeline nao encontrado. Use --video.")

    print(f"Projeto:  {args.projeto}")
    print(f"Video:    {video}")
    print(f"Destino:  {pasta}\n")
    ok, total, raiz = gerar_cortes(args.projeto, video, pasta,
                                   cfg.get("nome_arquivo", "{projeto}__{nome}"),
                                   dry=args.dry_run)
    if not args.dry_run:
        print(f"\n=== {ok}/{total} clipes gerados em {raiz} ===")


if __name__ == "__main__":
    main()
