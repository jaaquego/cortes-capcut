# -*- coding: utf-8 -*-
"""
Exportador AUTOMATICO do CapCut (toque zero).
==============================================
Pre-requisito: o projeto JA ABERTO no editor do CapCut (na timeline).

O programa:
  1. acha a janela do editor (a que tem 'Exportar' e nao e' a home),
  2. clica 'Exportar' -> abre o dialogo,
  3. clica 'Exportar' (confirmar) -> o CapCut exporta a timeline inteira,
  4. espera o .mp4 aparecer e parar de crescer,
  5. identifica o projeto, corta nos N videos, organiza em Estrutura\\V,
     sobe pro destino (Drive) e apaga o arquivo grande.

Uso:  py exportar_auto.py        (com o projeto aberto no CapCut)
"""
import os, sys, time
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import auto
import ocr_tela
import exportar
import vigiar
import split

# Rotulos dos passos (sem as palavras que o OCR procura no CapCut:
# 'exportar', 'cancelar', etc. — pra interface nao confundir a automacao).
PASSOS = [
    "Localizar o projeto aberto",
    "Gerar o vídeo no CapCut",
    "Aguardar a renderização",
    "Cortar e organizar no Drive",
]


def _pastas_export(cfg):
    """Pastas onde o CapCut pode largar o .mp4 (Downloads + a temporaria do config)."""
    ps = []
    dl = os.path.join(os.path.expanduser("~"), "Downloads")
    ps.append(dl)
    t = cfg.get("vigia", {}).get("pasta_export_capcut")
    if t and t not in ps:
        ps.append(t)
    return [p for p in ps if os.path.isdir(p)]


def _snapshot(pastas):
    s = {}
    for p in pastas:
        s.update(vigiar._mp4s(p))
    return s


def _esperar_e_fechar(pastas, antes, timeout=1800):
    """Espera o .mp4 ficar pronto e, NO INSTANTE que o export termina, fecha o
    aviso de compartilhar (Esc + Cancelar). Devolve o caminho do .mp4."""
    t0 = time.time()
    novo = None
    # 1) espera o arquivo aparecer (poll rapido)
    while time.time() - t0 < timeout:
        cands = [p for p in _snapshot(pastas) if p not in antes]
        if cands:
            novo = max(cands, key=os.path.getmtime)
            break
        time.sleep(0.5)
    if not novo:
        return None
    # 2) detecta o fim do render: tamanho parado por ~1s (poll rapido)
    tam, estavel = -1, 0
    while time.time() - t0 < timeout:
        try:
            t = os.path.getsize(novo)
        except OSError:
            t = -1
        if t > 0 and t == tam:
            estavel += 1
            if estavel >= 3:
                break
        else:
            estavel = 0
        tam = t
        time.sleep(0.35)
    # 3) acabou AGORA -> fecha o aviso de compartilhar instantaneamente
    try:
        auto.pyautogui.press("esc")
    except Exception:
        pass
    # 4) garantia: se o aviso ainda estiver la', clica Cancelar
    try:
        itens = ocr_tela.ler(im=auto._grab())
        canc = auto.achar(itens, "cancelar", "cancel")
        if canc and auto.achar(itens, "compartilhar", "share", "tiktok", "youtube", "salvo", "saved"):
            auto.clicar(canc)
    except Exception:
        pass
    return novo


def _confirmar_export(itens):
    """Acha o botao de CONFIRMAR (Exportar/Export) no dialogo, na linha do Cancelar/Cancel."""
    canc = auto.achar(itens, "cancelar", "cancel")
    exps = [i for i in itens if "export" in i["texto"].lower() and i["conf"] > 0.4]
    if canc:
        perto = [i for i in exps if abs(i["cy"] - canc["cy"]) < 40 and i["cx"] < canc["cx"]]
        if perto:
            return max(perto, key=lambda i: i["cx"])  # o mais a' direita antes do Cancelar
    # senao, o 'exportar' mais embaixo (maior y)
    return max(exps, key=lambda i: i["cy"]) if exps else None


def _fechar_dialogo_pos_export():
    """Depois do export o CapCut abre uma janela de 'compartilhar' (TikTok/YouTube)
    e fica tocando o video. Fecha clicando em 'Cancelar'.
    Logo apos o export esse pop-up ja esta em primeiro plano, entao lemos a tela
    COMO ESTA (sem ficar alternando janelas, o que esconderia o pop-up)."""
    import time as _t
    for tent in range(8):
        itens = ocr_tela.ler(im=auto._grab())
        canc = auto.achar(itens, "cancelar")
        compart = auto.achar(itens, "compartilhar", "tiktok", "youtube")
        if canc and compart:
            print(f"      fechando janela de compartilhar (Cancelar em {canc['cx']},{canc['cy']})")
            auto.pyautogui.moveTo(canc["cx"], canc["cy"], duration=0.2)
            auto.pyautogui.click(canc["cx"], canc["cy"])
            return
        _t.sleep(1.5)
    print("      (janela de compartilhar nao apareceu — seguindo)")


def _contar_clipes(raiz):
    n = 0
    if raiz and os.path.isdir(raiz):
        for _, _, fs in os.walk(raiz):
            n += sum(1 for f in fs if f.lower().endswith(".mp4"))
    return n


def executar(cb=None, abrir=False):
    """Roda o fluxo toque-zero. cb(passo_idx, detalhe) e' chamado a cada passo
    (passo_idx 0..3, ver PASSOS). Retorna (pasta_dos_cortes, n_clipes).
    Em erro, levanta RuntimeError com mensagem amigavel."""
    def _cb(i, d=""):
        if cb:
            try: cb(i, d)
            except Exception: pass

    cfg = exportar.carregar_config()
    ff = split.achar_ffmpeg()
    pastas = _pastas_export(cfg)

    # 1) localizar o projeto/editor
    _cb(0, "procurando o projeto aberto…")
    h, itens = auto.garantir_editor()
    antes = _snapshot(pastas)

    # 2) abrir o diálogo e confirmar
    _cb(1, "abrindo o diálogo no CapCut…")
    if auto.achar(itens, "exportar para", "export to"):
        itens2 = itens
    else:
        topo = min([i for i in itens if "export" in i["texto"].lower()],
                   key=lambda i: i["cy"])
        auto.clicar(topo)
        time.sleep(3)
        # a janela troca de id ao abrir o diálogo; usa a janela em 1º plano (o CapCut)
        try:
            auto._HWND = auto.win32gui.GetForegroundWindow()
        except Exception:
            auto._HWND = None
        itens2 = auto.ler()
    if not auto.achar(itens2, "exportar para", "export to"):
        raise RuntimeError("Não consegui abrir a janela de geração do vídeo no CapCut.")
    conf = _confirmar_export(itens2)
    if not conf:
        raise RuntimeError("Não encontrei o botão de confirmar no CapCut.")
    _cb(1, "confirmando…")
    auto.clicar(conf)

    # 3) aguardar o arquivo e fechar o aviso de compartilhar NA HORA
    _cb(2, "o CapCut está gerando o vídeo — isso pode levar alguns minutos…")
    novo = _esperar_e_fechar(pastas, antes, timeout=1800)
    if not novo:
        raise RuntimeError("Não detectei o vídeo gerado (a geração pode ter falhado).")

    # 4) cortar e organizar
    _cb(3, "cortando os vídeos e organizando no Drive…")
    raiz = vigiar.processar(novo, cfg, ff)
    if os.path.exists(novo):
        raise RuntimeError("O projeto aberto não tem as caixas ESTRUTURA-VY "
                           "(ou havia mais de um projeto aberto). "
                           "Deixe aberto só o projeto certo e tente de novo.")
    n = _contar_clipes(raiz)
    # limpa a tela: minimiza as janelas do CapCut no fim
    try: auto.focuswin.minimizar_capcuts()
    except Exception: pass
    if abrir and raiz and os.path.isdir(raiz):
        try: os.startfile(raiz)
        except Exception: pass
    return raiz, n


def main():
    def log(i, d):
        print(f"[{i+1}/4] {PASSOS[i]}: {d}")
    try:
        raiz, n = executar(cb=log, abrir=True)
        print(f"\nPRONTO — {n} clipes em {raiz}")
    except Exception as e:
        print(f"\nERRO: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
