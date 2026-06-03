# -*- coding: utf-8 -*-
"""OCR da tela: localiza textos da UI do CapCut e devolve coordenadas de clique.
Usa RapidOCR (onnx, offline). Captura full-screen (DWM) -> funciona com a UI GPU do CapCut.
"""
import sys, time
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # pixels fisicos consistentes
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass
import numpy as np
from PIL import ImageGrab

_engine = None


def _ocr():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def capturar(bbox=None):
    im = ImageGrab.grab(bbox=bbox) if bbox else ImageGrab.grab()
    return im


def ler(bbox=None, im=None):
    """Roda OCR. Devolve lista de dicts: {texto, cx, cy, x0,y0,x1,y1, conf}.
    Coords ja em tela absoluta (soma offset do bbox)."""
    if im is None:
        im = capturar(bbox)
    ox, oy = (bbox[0], bbox[1]) if bbox else (0, 0)
    arr = np.array(im)[:, :, ::-1]  # RGB->BGR
    res, _ = _ocr()(arr)
    out = []
    if not res:
        return out
    for box, txt, conf in res:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        out.append({
            "texto": txt,
            "cx": int(ox + (x0 + x1) / 2),
            "cy": int(oy + (y0 + y1) / 2),
            "x0": int(ox + x0), "y0": int(oy + y0),
            "x1": int(ox + x1), "y1": int(oy + y1),
            "conf": float(conf),
        })
    return out


def achar(itens, *alvos, contem=True):
    """Acha o primeiro item cujo texto bate com algum alvo (case-insensitive)."""
    al = [a.lower() for a in alvos]
    for it in itens:
        t = it["texto"].lower().strip()
        for a in al:
            if (a in t) if contem else (t == a):
                return it
    return None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import focuswin
    w = focuswin.janela_editor()
    if w:
        focuswin.focar(w["hwnd"])
        time.sleep(1.0)
    t0 = time.time()
    itens = ler()
    print(f"OCR: {len(itens)} textos em {time.time()-t0:.1f}s\n")
    alvo = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    for it in itens:
        flag = ""
        if alvo and alvo.lower() in it["texto"].lower():
            flag = "   <<<<<"
        if it["conf"] > 0.5:
            print(f"({it['cx']:>4},{it['cy']:>4}) {it['conf']:.2f} {it['texto']!r}{flag}")
