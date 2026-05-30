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
sys.stdout.reconfigure(encoding="utf-8")

import auto
import ocr_tela
import exportar
import vigiar
import split


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


def _esperar_novo(pastas, antes, timeout=1200):
    """Espera um .mp4 novo aparecer e estabilizar. Devolve o caminho."""
    t0 = time.time()
    novo = None
    while time.time() - t0 < timeout:
        agora = _snapshot(pastas)
        cands = [p for p in agora if p not in antes]
        if cands:
            novo = max(cands, key=os.path.getmtime)
            break
        time.sleep(2)
    if not novo:
        return None
    # espera parar de crescer (export terminou)
    tam = -1
    while True:
        try:
            t = os.path.getsize(novo)
        except OSError:
            t = -1
        if t == tam and t > 0:
            break
        tam = t
        time.sleep(2)
    return novo


def _confirmar_export(itens):
    """Acha o botao 'Exportar' de CONFIRMAR no dialogo (mesma linha do 'Cancelar')."""
    canc = auto.achar(itens, "cancelar")
    exps = [i for i in itens if "exportar" in i["texto"].lower() and i["conf"] > 0.4]
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
    from PIL import ImageGrab
    import time as _t
    for tent in range(8):
        itens = ocr_tela.ler(im=ImageGrab.grab())
        canc = auto.achar(itens, "cancelar")
        compart = auto.achar(itens, "compartilhar", "tiktok", "youtube")
        if canc and compart:
            print(f"      fechando janela de compartilhar (Cancelar em {canc['cx']},{canc['cy']})")
            auto.pyautogui.moveTo(canc["cx"], canc["cy"], duration=0.2)
            auto.pyautogui.click(canc["cx"], canc["cy"])
            return
        _t.sleep(1.5)
    print("      (janela de compartilhar nao apareceu — seguindo)")


def main():
    cfg = exportar.carregar_config()
    ff = split.achar_ffmpeg()
    pastas = _pastas_export(cfg)
    print("Pastas de export vigiadas:", pastas)

    print("\n[1/5] Procurando o editor (projeto precisa estar aberto)...")
    h, itens = auto.garantir_editor()
    print(f"      editor hwnd={h}")
    antes = _snapshot(pastas)

    if auto.achar(itens, "exportar para"):
        print("[2/5] Dialogo de export ja esta aberto.")
        itens2 = itens
    else:
        topo = min([i for i in itens if "exportar" in i["texto"].lower()], key=lambda i: i["cy"])
        print(f"[2/5] Abrindo dialogo de export (clica Exportar em {topo['cx']},{topo['cy']})...")
        auto.clicar(topo)
        time.sleep(5)
        itens2 = auto.ler()
    if not auto.achar(itens2, "exportar para"):
        auto.salvar("erro_dialogo.png")
        sys.exit("Dialogo de export nao abriu (veja erro_dialogo.png).")
    conf = _confirmar_export(itens2)
    if not conf:
        auto.dump(itens2, "DIALOGO")
        sys.exit("Botao 'Exportar' de confirmar nao localizado.")
    print(f"[3/5] Confirmando export (clica em {conf['cx']},{conf['cy']})... isso vai gerar o arquivo grande.")
    auto.clicar(conf)

    print("[4/5] Exportando no CapCut e aguardando o arquivo (ate 20 min)...")
    novo = _esperar_novo(pastas, antes, timeout=1200)
    if not novo:
        sys.exit("Nao detectei o arquivo exportado. (Export pode ter falhado.)")
    print(f"      arquivo: {novo}  ({os.path.getsize(novo)/1e6:.0f} MB)")

    print("      fechando a janela de compartilhar do CapCut...")
    _fechar_dialogo_pos_export()

    print("[5/5] Cortando, organizando e subindo pro destino...")
    raiz = vigiar.processar(novo, cfg, ff)
    if os.path.exists(novo):
        print(f"\n*** ATENCAO: o arquivo NAO foi cortado e ficou em:\n    {novo}")
        print("    (O projeto exportado pode nao ter as caixas ESTRUTURA-VY,")
        print("     ou havia mais de um projeto aberto e foi pego o errado.")
        print("     Deixe aberto SO o projeto certo e rode de novo.)")
        return
    print("\nPRONTO. ")
    if raiz and os.path.isdir(raiz):
        print(f"Abrindo a pasta dos cortes: {raiz}")
        try:
            os.startfile(raiz)            # abre no Explorer do Windows
        except Exception as e:
            print(f"(nao consegui abrir a pasta: {e})")


if __name__ == "__main__":
    main()
