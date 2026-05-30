# -*- coding: utf-8 -*-
"""Motor de automacao de UI do CapCut.

CapCut abre ~20 janelas (CEF multi-processo); a janela de conteudo real pode ser
minimizada pra fora da tela enquanto um 'shell' em branco fica em primeiro plano.
Por isso a janela certa e' escolhida por CONTEUDO (OCR), nao por area:
restaura/foca cada candidata e fica com a que mostra texto do CapCut.

Captura full-screen (DWM) + RapidOCR + pyautogui. Sem depender de acessibilidade
(a arvore UIA do CapCut e' vazia).
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
import win32gui, win32con, win32api
import pyautogui
import focuswin
import ocr_tela
from PIL import ImageGrab

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

_HWND = None
KW = ("criar projeto", "exportar", "projetos", "inicio", "modelos",
      "duracao", "tamanho", "espacos", "mais ferramentas")


def _hits(itens):
    txt = " ".join(i["texto"].lower() for i in itens if i["conf"] > 0.5)
    return sum(1 for k in KW if k in txt)


def _e_conteudo(itens):
    """Janela de conteudo real do CapCut: ou bate palavras-chave da home,
    ou tem MUITO texto na tela (editor tem dezenas de rotulos)."""
    confs = [i for i in itens if i["conf"] > 0.5]
    return _hits(itens) >= 2 or len(confs) >= 12


def garantir_capcut(verbose=True, preferir=None, evitar=None, exigir=None, excluir=None):
    """Acha, restaura e foca a janela de CONTEUDO do CapCut (verificada por OCR).
    preferir: hwnd a testar primeiro. evitar: hwnd a deixar por ultimo (ex: home antiga).
    exigir: substring que DEVE aparecer no OCR (ex: 'exportar' p/ achar o editor).
    excluir: substring que NAO pode aparecer (ex: 'criar projeto' p/ rejeitar a home).
    Retorna (hwnd, itens_ocr)."""
    global _HWND
    wins = focuswin.listar()
    cands = [w for w in wins if w["area"] > 4000 or w["rect"][0] < -1000]
    cands.sort(key=lambda w: (w["onscreen"], w["area"]), reverse=True)
    ordem = [c["hwnd"] for c in cands]
    for h in (preferir, _HWND):
        if h and h != evitar and win32gui.IsWindow(h) and h in ordem:
            ordem.remove(h); ordem.insert(0, h)
    if evitar in ordem:  # evitar sempre por ultimo (vence a preferencia)
        ordem = [h for h in ordem if h != evitar] + [evitar]
    sw = win32api.GetSystemMetrics(0)
    sh = win32api.GetSystemMetrics(1)
    seen = set()
    for h in ordem:
        if h in seen:
            continue
        seen.add(h)
        try:
            win32gui.ShowWindow(h, win32con.SW_RESTORE)
        except Exception:
            continue
        time.sleep(0.3)
        # se a janela estiver fora da tela, traz pra (0,0) com tamanho que cabe
        l, t, r, b = win32gui.GetWindowRect(h)
        if l >= sw or r <= 0 or t >= sh or b <= 0 or l < -1000:
            ww, hh = min(r - l, sw), min(b - t, sh)
            if ww > 200 and hh > 200:
                try: win32gui.MoveWindow(h, 0, 0, ww, hh, True)
                except Exception: pass
                time.sleep(0.3)
        focuswin.focar(h)
        time.sleep(0.9)
        if win32gui.GetForegroundWindow() != h:
            continue
        itens = ocr_tela.ler(im=ImageGrab.grab())
        ok = _e_conteudo(itens)
        if exigir:
            ok = ok and achar(itens, exigir) is not None
        if excluir:
            ok = ok and achar(itens, excluir) is None
        if verbose:
            print(f"  candidata hwnd={h} rect={win32gui.GetWindowRect(h)} "
                  f"hits={_hits(itens)} textos={len([i for i in itens if i['conf']>0.5])} -> {'OK' if ok else 'skip'}")
        if ok:
            _HWND = h
            return h, itens
    raise RuntimeError("Nao achei a janela de conteudo do CapCut" + (f" com {exigir!r}" if exigir else ""))


def garantir_editor(timeout=30):
    """Acha a janela do EDITOR (tem 'Exportar' e NAO tem 'Criar projeto' = nao e' a home)."""
    t0 = time.time()
    while True:
        try:
            return garantir_capcut(exigir="exportar", excluir="criar projeto")
        except RuntimeError:
            if time.time() - t0 > timeout:
                raise RuntimeError("Editor nao encontrado. Abra o projeto no CapCut (timeline).")
            time.sleep(2)


def _bbox():
    if _HWND is None:
        return None
    l, t, r, b = focuswin.rect(_HWND)
    return (max(0, l), max(0, t), r, b)


def ler():
    return ocr_tela.ler(bbox=_bbox())


def achar(itens, *alvos, contem=True, minconf=0.4):
    al = [a.lower() for a in alvos]
    for it in itens:
        if it["conf"] < minconf:
            continue
        t = it["texto"].lower().strip()
        for a in al:
            if (a in t) if contem else (t == a):
                return it
    return None


def clicar(it, dbl=False, dx=0, dy=0):
    x, y = it["cx"] + dx, it["cy"] + dy
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.doubleClick(x, y) if dbl else pyautogui.click(x, y)
    time.sleep(0.4)


def dump(itens, titulo="", minconf=0.45):
    if titulo:
        print(f"\n=== {titulo} ({len(itens)} textos) ===")
    for it in itens:
        if it["conf"] >= minconf:
            print(f"({it['cx']:>4},{it['cy']:>4}) {it['conf']:.2f} {it['texto']!r}")


def salvar(nome):
    im = ImageGrab.grab(bbox=_bbox())
    im.save(nome)
    im.resize((1280, int(1280 * im.size[1] / im.size[0]))).save(nome.replace(".png", "_small.png"))


if __name__ == "__main__":
    alvo = " ".join(sys.argv[1:]) or "copia"
    h, itens = garantir_capcut()
    print(f"\nJanela de conteudo: hwnd={h}")
    proj = achar(itens, alvo)
    if not proj:
        dump(itens, "HOME")
        print(f"\nProjeto contendo {alvo!r} nao achado.")
        sys.exit(1)
    print(f"Abrindo projeto {proj['texto']!r} @({proj['cx']},{proj['cy']})")
    home = h
    clicar(proj, dbl=True)
    print("Carregando editor...")
    time.sleep(10)
    h2, itens2 = garantir_editor(home)
    print(f"\nJanela do editor: hwnd={h2}")
    dump(itens2, "EDITOR")
    exp = achar(itens2, "exportar", "export")
    print("\n>>> Botao Exportar:", exp)
    salvar("editor.png")
