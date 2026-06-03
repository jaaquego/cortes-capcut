# -*- coding: utf-8 -*-
"""
Exportador de Cortes (CapCut) - interface grafica.
Janela pequena e moderna: abre e ESPERA voce clicar pra comecar.
Mostra o passo a passo com spinner animado e, no fim, um link clicavel
pra pasta dos cortes.

Uso:
    pythonw exportador_gui.py          (sem console)
    py exportador_gui.py --demo        (simula, pra ver o visual)
"""
import os
import sys
import queue
import threading

# pythonw nao tem stdout/stderr -> evita erro em prints de modulos importados
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# DPI-aware: faz tudo (posicao, captura de tela, cliques) usar pixels FISICOS
# consistentes (senao a escala 125%/100% bagunça posicao e cliques).
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import tkinter as tk
from tkinter import font as tkfont

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon.ico")
DEMO = "--demo" in sys.argv

# --- paleta (escura, moderna) ---
BG      = "#13151F"
CARD    = "#1C1F2E"
CARD2   = "#232739"
TXT     = "#EAECF5"
SUB     = "#8B92AB"
ACCENT  = "#37B6E9"   # azul
ACCENT2 = "#19C7B6"   # teal
OK      = "#46D6A0"
ERR     = "#FF6B7A"
LINK    = "#5BC6F2"

PASSOS = [
    "Localizar o projeto aberto",
    "Gerar o vídeo no CapCut",
    "Aguardar a renderização",
    "Cortar e organizar no Drive",
]


class App:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.active = None
        self.angle = 0
        self.running = False
        self.result_folder = None

        root.title("Cortes CapCut")
        root.configure(bg=BG)
        root.resizable(False, False)
        try:
            root.iconbitmap(ICON)
        except Exception:
            pass

        self.f_title = tkfont.Font(family="Segoe UI Semibold", size=16)
        self.f_sub   = tkfont.Font(family="Segoe UI", size=9)
        self.f_step  = tkfont.Font(family="Segoe UI", size=10)
        self.f_small = tkfont.Font(family="Segoe UI", size=9)
        self.f_btn   = tkfont.Font(family="Segoe UI Semibold", size=11)
        self.f_link  = tkfont.Font(family="Segoe UI", size=9, underline=True)

        self._build()
        self._center(440, 580)
        self._tick()
        self.root.after(300, self._pin_loop)   # mantem fixo no canto inf. direito
        self.root.after(120, self._poll)

    def _pin_loop(self):
        # re-fixa o app no canto inferior direito sempre (mesmo se a escala da
        # tela mudar ou algo tentar mover) -> nunca cobre os botoes do CapCut
        self._reposicionar()
        self.root.after(1000, self._pin_loop)
        if not DEMO:
            self._preload_ocr()   # carrega o modelo de OCR em segundo plano
        if DEMO:
            self.root.after(900, self.start)

    def _preload_ocr(self):
        def _load():
            try:
                import ocr_tela
                ocr_tela._ocr()   # forca o carregamento do modelo agora
            except Exception:
                pass
        threading.Thread(target=_load, daemon=True).start()

    # ---------- layout ----------
    def _build(self):
        # cabecalho
        head = tk.Frame(self.root, bg=BG)
        head.pack(fill="x", padx=22, pady=(22, 8))
        self.logo_img = self._load_logo(54)
        if self.logo_img:
            tk.Label(head, image=self.logo_img, bg=BG).pack(side="left")
        tw = tk.Frame(head, bg=BG)
        tw.pack(side="left", padx=12)
        tk.Label(tw, text="Cortes CapCut", bg=BG, fg=TXT, font=self.f_title).pack(anchor="w")
        tk.Label(tw, text="gera, corta e organiza no Drive — sozinho",
                 bg=BG, fg=SUB, font=self.f_sub).pack(anchor="w")

        # dica
        tip = tk.Frame(self.root, bg=CARD)
        tip.pack(fill="x", padx=22, pady=(8, 6))
        tk.Label(tip, text="①  Abra no CapCut só o projeto desejado\n"
                            "②  Não use o mouse enquanto eu trabalho",
                 bg=CARD, fg=SUB, font=self.f_small, justify="left").pack(anchor="w", padx=12, pady=8)

        # passos
        self.card = tk.Frame(self.root, bg=CARD)
        self.card.pack(fill="x", padx=22, pady=6)
        self.steps = []
        for i, nome in enumerate(PASSOS):
            row = tk.Frame(self.card, bg=CARD)
            row.pack(fill="x", padx=12, pady=(10 if i == 0 else 6, 6 if i < len(PASSOS)-1 else 12))
            cv = tk.Canvas(row, width=24, height=24, bg=CARD, highlightthickness=0)
            cv.pack(side="left")
            lb = tk.Label(row, text=nome, bg=CARD, fg=SUB, font=self.f_step)
            lb.pack(side="left", padx=10)
            self.steps.append({"canvas": cv, "label": lb, "state": "idle"})
            self._draw_step(i)

        # detalhe (status atual)
        self.detail = tk.Label(self.root, text="Pronto pra começar.",
                               bg=BG, fg=SUB, font=self.f_small, wraplength=396, justify="left")
        self.detail.pack(fill="x", padx=24, pady=(4, 4))

        # resultado (link), escondido no inicio
        self.result = tk.Frame(self.root, bg=BG)
        self.res_title = tk.Label(self.result, text="", bg=BG, fg=OK, font=self.f_step)
        self.res_title.pack(anchor="w")
        self.link = tk.Label(self.result, text="", bg=BG, fg=LINK, font=self.f_link, cursor="hand2")
        self.link.pack(anchor="w", pady=(2, 0))
        self.link.bind("<Button-1>", lambda e: self._abrir_pasta())

        # botao
        self.btn = tk.Frame(self.root, bg=ACCENT, cursor="hand2")
        self.btn.pack(fill="x", padx=22, pady=(10, 20))
        self.btn_lb = tk.Label(self.btn, text="▶   Começar", bg=ACCENT, fg="#06121A", font=self.f_btn)
        self.btn_lb.pack(pady=11)
        self._btn_enable(True)

    def _reposicionar(self):
        """Forca a janela pro canto inferior direito + topmost (via win32, confiavel)."""
        try:
            import win32gui, win32api, win32con
            h = win32gui.FindWindow(None, "Cortes CapCut")
            if not h:
                return
            sw = win32api.GetSystemMetrics(0)
            sh = win32api.GetSystemMetrics(1)
            l, t, r, b = win32gui.GetWindowRect(h)
            ww, hh = r - l, b - t
            x = max(0, sw - ww - 18)
            y = max(0, sh - hh - 55)
            win32gui.SetWindowPos(h, win32con.HWND_TOPMOST, x, y, 0, 0, win32con.SWP_NOSIZE)
        except Exception:
            pass

    def _load_logo(self, size):
        try:
            from PIL import Image, ImageTk
            im = Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def _center(self, w, h):
        self.root.update_idletasks()
        try:
            import win32api
            sw = win32api.GetSystemMetrics(0)
            sh = win32api.GetSystemMetrics(1)
        except Exception:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        # canto inferior direito (longe dos botoes que clico no CapCut)
        x = max(0, sw - w - 20)
        y = max(0, sh - h - 60)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.attributes("-topmost", True)   # sempre visivel por cima

    # ---------- botao ----------
    def _btn_enable(self, on, texto=None):
        if texto:
            self.btn_lb.config(text=texto)
        if on:
            self.btn.config(bg=ACCENT); self.btn_lb.config(bg=ACCENT, fg="#06121A")
            self.btn.bind("<Button-1>", lambda e: self.start())
            self.btn_lb.bind("<Button-1>", lambda e: self.start())
            self.btn.bind("<Enter>", lambda e: (self.btn.config(bg=ACCENT2), self.btn_lb.config(bg=ACCENT2)))
            self.btn.bind("<Leave>", lambda e: (self.btn.config(bg=ACCENT), self.btn_lb.config(bg=ACCENT)))
        else:
            self.btn.config(bg=CARD2); self.btn_lb.config(bg=CARD2, fg=SUB)
            for w in (self.btn, self.btn_lb):
                w.unbind("<Button-1>"); w.unbind("<Enter>"); w.unbind("<Leave>")

    # ---------- desenho dos passos ----------
    def _draw_step(self, i):
        cv = self.steps[i]["canvas"]
        st = self.steps[i]["state"]
        cv.delete("all")
        cx, cy, r = 12, 12, 8
        if st == "idle":
            cv.create_oval(cx-r, cy-r, cx+r, cy+r, outline=SUB, width=2)
            self.steps[i]["label"].config(fg=SUB)
        elif st == "running":
            ext = 270
            cv.create_arc(cx-r, cy-r, cx+r, cy+r, start=self.angle, extent=ext,
                          style="arc", outline=ACCENT, width=3)
            self.steps[i]["label"].config(fg=TXT)
        elif st == "done":
            cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill=OK, outline=OK)
            cv.create_line(cx-4, cy, cx-1, cy+4, fill="#06121A", width=2)
            cv.create_line(cx-1, cy+4, cx+5, cy-4, fill="#06121A", width=2)
            self.steps[i]["label"].config(fg=TXT)
        elif st == "error":
            cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill=ERR, outline=ERR)
            cv.create_line(cx-3, cy-3, cx+3, cy+3, fill="white", width=2)
            cv.create_line(cx+3, cy-3, cx-3, cy+3, fill="white", width=2)
            self.steps[i]["label"].config(fg=TXT)

    def _tick(self):
        self.angle = (self.angle - 12) % 360
        if self.active is not None:
            self._draw_step(self.active)
        self.root.after(70, self._tick)

    def _set_state(self, i, state):
        self.steps[i]["state"] = state
        self._draw_step(i)

    # ---------- execucao ----------
    def start(self):
        if self.running:
            return
        self.running = True
        self.result_folder = None
        self.result.pack_forget()
        for i in range(len(self.steps)):
            self._set_state(i, "idle")
        self.active = None
        self.detail.config(text="Iniciando…", fg=SUB)
        self._btn_enable(False, "Trabalhando…")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        def cb(i, d=""):
            self.q.put(("step", i, d))
        try:
            if DEMO:
                raiz, n = self._demo(cb)
            else:
                import exportar_auto
                raiz, n = exportar_auto.executar(cb=cb, abrir=False)
            self.q.put(("done", raiz, n))
        except Exception as e:
            self.q.put(("error", str(e)))

    def _demo(self, cb):
        import time
        msgs = ["procurando o projeto…", "gerando o vídeo…",
                "renderizando (pode demorar)…", "cortando e organizando…"]
        for i in range(4):
            cb(i, msgs[i])
            time.sleep(1.6)
        dest = "I:\\Meu Drive\\Cortes CapCut\\Criativos Vídeo Narrado Vistas de Anitá"
        return dest, 10

    def _poll(self):
        try:
            while True:
                ev = self.q.get_nowait()
                if ev[0] == "step":
                    _, i, d = ev
                    for k in range(i):
                        if self.steps[k]["state"] != "done":
                            self._set_state(k, "done")
                    self._set_state(i, "running")
                    self.active = i
                    self.detail.config(text=d, fg=SUB)
                elif ev[0] == "done":
                    _, raiz, n = ev
                    for k in range(len(self.steps)):
                        self._set_state(k, "done")
                    self.active = None
                    self.running = False
                    self.detail.config(text="", fg=SUB)
                    self._mostrar_resultado(raiz, n)
                    self._btn_enable(True, "↻   Fazer outro")
                    self._raise()
                elif ev[0] == "error":
                    _, msg = ev
                    if self.active is not None:
                        self._set_state(self.active, "error")
                    self.active = None
                    self.running = False
                    self.detail.config(text="⚠  " + msg, fg=ERR)
                    self._btn_enable(True, "▶   Tentar de novo")
                    self._raise()
        except queue.Empty:
            pass
        self.root.after(120, self._poll)

    def _mostrar_resultado(self, raiz, n):
        self.result_folder = raiz
        self.res_title.config(text=f"✓  {n} clipes prontos no Drive")
        nome = os.path.basename(raiz.rstrip("\\/")) if raiz else ""
        self.link.config(text=f"📂  Abrir pasta:  {nome}")
        self.result.pack(fill="x", padx=24, pady=(2, 2), before=self.btn)

    def _abrir_pasta(self):
        if self.result_folder and os.path.isdir(self.result_folder):
            try:
                os.startfile(self.result_folder)
            except Exception:
                pass

    def _raise(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)   # mantem sempre por cima
        except Exception:
            pass


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
