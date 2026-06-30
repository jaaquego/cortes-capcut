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
    "Cortar e organizar nas pastas",
]
PASSOS_CORTE = [
    "Identificar o projeto",
    "Cortar e organizar nas pastas",
]


class App:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.active = None
        self.angle = 0
        self.running = False
        self.result_folder = None
        self._pausar_pin = False   # pausa a fixacao no canto (ex.: enquanto um popup esta aberto)
        self.modo = "completo"     # "completo" (exporta+corta) ou "corte" (so' corta)
        self._video_corte = None

        root.title("Cortes CapCut")
        root.configure(bg=BG)
        root.resizable(False, False)
        try:
            root.attributes("-alpha", 0.0)   # nasce invisivel; so' aparece ja' posicionada
        except Exception:
            pass
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
        self._center(440, 684)
        self._tick()
        self.root.update_idletasks()
        self._reposicionar()                   # ja' posiciona ANTES de aparecer
        self.root.after(80, self._mostrar)     # revela ja' no lugar (sem pulo)
        self.root.after(120, self._poll)

    def _mostrar(self):
        self._reposicionar()
        try:
            self.root.attributes("-alpha", 1.0)   # agora aparece, ja' no canto
        except Exception:
            pass
        self.root.after(1000, self._pin_loop)

    def _pin_loop(self):
        # re-fixa o app no canto inferior direito sempre (mesmo se a escala da
        # tela mudar ou algo tentar mover) -> nunca cobre os botoes do CapCut.
        # Pausado enquanto um popup (ex.: escolher pasta) esta aberto, senao o app
        # re-sobe por cima e esconde o popup.
        if not self._pausar_pin:
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
        tk.Label(tw, text="gera, corta e organiza em pastas — sozinho",
                 bg=BG, fg=SUB, font=self.f_sub).pack(anchor="w")

        # dica
        tip = tk.Frame(self.root, bg=CARD)
        tip.pack(fill="x", padx=22, pady=(8, 6))
        tk.Label(tip, text="①  Abra no CapCut só o projeto desejado\n"
                            "②  Não use o mouse enquanto eu trabalho",
                 bg=CARD, fg=SUB, font=self.f_small, justify="left").pack(anchor="w", padx=12, pady=8)

        # pasta de destino (onde salva) + botao alterar
        dest = tk.Frame(self.root, bg=BG)
        dest.pack(fill="x", padx=24, pady=(2, 2))
        alt = tk.Label(dest, text="alterar", bg=BG, fg=LINK, font=self.f_link, cursor="hand2")
        alt.pack(side="right")
        alt.bind("<Button-1>", lambda e: self._alterar_destino())
        self.dest_lb = tk.Label(dest, text="", bg=BG, fg=SUB, font=self.f_small,
                                anchor="w", justify="left", wraplength=320)
        self.dest_lb.pack(side="left")
        self._atualizar_destino_label()

        # passos (montados dinamicamente conforme o modo)
        self.card = tk.Frame(self.root, bg=CARD)
        self.card.pack(fill="x", padx=22, pady=6)
        self.steps = []
        self._montar_passos(PASSOS)

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

        # botao principal (exportar + cortar)
        self.btn = tk.Frame(self.root, bg=ACCENT, cursor="hand2")
        self.btn.pack(fill="x", padx=22, pady=(10, 4))
        self.btn_lb = tk.Label(self.btn, text="▶   Começar", bg=ACCENT, fg="#06121A", font=self.f_btn)
        self.btn_lb.pack(pady=11)

        # botao secundario (so' cortar um video ja' exportado)
        self.btn2 = tk.Frame(self.root, bg=CARD2, cursor="hand2")
        self.btn2.pack(fill="x", padx=22, pady=(0, 18))
        self.btn2_lb = tk.Label(self.btn2, text="✂   Só cortar (já exportei)",
                                bg=CARD2, fg=TXT, font=self.f_small)
        self.btn2_lb.pack(pady=8)
        for w in (self.btn2, self.btn2_lb):
            w.bind("<Button-1>", lambda e: self.start_corte())
            w.bind("<Enter>", lambda e: (self.btn2.config(bg="#2C3146"), self.btn2_lb.config(bg="#2C3146")))
            w.bind("<Leave>", lambda e: (self.btn2.config(bg=CARD2), self.btn2_lb.config(bg=CARD2)))

        self._btn_enable(True)

    def _montar_passos(self, lista):
        """(Re)constroi as linhas de passos conforme a lista dada."""
        for w in self.card.winfo_children():
            w.destroy()
        self.steps = []
        for i, nome in enumerate(lista):
            row = tk.Frame(self.card, bg=CARD)
            row.pack(fill="x", padx=12, pady=(10 if i == 0 else 6, 6 if i < len(lista)-1 else 12))
            cv = tk.Canvas(row, width=24, height=24, bg=CARD, highlightthickness=0)
            cv.pack(side="left")
            lb = tk.Label(row, text=nome, bg=CARD, fg=SUB, font=self.f_step)
            lb.pack(side="left", padx=10)
            self.steps.append({"canvas": cv, "label": lb, "state": "idle"})
            self._draw_step(i)

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
            # botao secundario "Só cortar"
            self.btn2.config(bg=CARD2); self.btn2_lb.config(bg=CARD2, fg=TXT)
            for w in (self.btn2, self.btn2_lb):
                w.bind("<Button-1>", lambda e: self.start_corte())
                w.bind("<Enter>", lambda e: (self.btn2.config(bg="#2C3146"), self.btn2_lb.config(bg="#2C3146")))
                w.bind("<Leave>", lambda e: (self.btn2.config(bg=CARD2), self.btn2_lb.config(bg=CARD2)))
        else:
            self.btn.config(bg=CARD2); self.btn_lb.config(bg=CARD2, fg=SUB)
            self.btn2_lb.config(fg=SUB)
            for w in (self.btn, self.btn_lb, self.btn2, self.btn2_lb):
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

    # ---------- pasta de destino ----------
    def _pasta_conhecida(self, qual):
        """Caminho da Area de Trabalho / Videos (lida com OneDrive e PT/EN)."""
        h = os.path.expanduser("~")
        cands = {
            "Desktop": [os.path.join(h, "Desktop"),
                        os.path.join(h, "OneDrive", "Desktop"),
                        os.path.join(h, "OneDrive", "Área de Trabalho")],
            "Videos":  [os.path.join(h, "Videos"), os.path.join(h, "Vídeos"),
                        os.path.join(h, "OneDrive", "Videos"),
                        os.path.join(h, "OneDrive", "Vídeos")],
        }.get(qual, [])
        for c in cands:
            if os.path.isdir(c):
                return c
        return cands[0] if cands else h

    def _atualizar_destino_label(self):
        try:
            import exportar
            d = exportar.carregar_config()["destino"]["pasta_local"]
        except Exception:
            d = ""
        if d:
            txt = d if len(d) <= 46 else "…" + d[-44:]
            self.dest_lb.config(text="💾  Salva em:  " + txt)
        else:
            self.dest_lb.config(text="💾  Salva em:  (escolher na 1ª vez)")

    def _escolher_destino(self):
        """Menu: Area de Trabalho / Videos / Escolher pasta / Colar caminho. Devolve o path."""
        import tkinter as tk
        from tkinter import filedialog, simpledialog
        sub = "Cortes CapCut"
        esc = {"p": None}
        self._pausar_pin = True                       # nao deixa o app re-subir por cima
        try: self.root.attributes("-topmost", False)
        except Exception: pass
        win = tk.Toplevel(self.root)
        win.title("Onde salvar os cortes?")
        win.configure(bg=CARD); win.resizable(False, False)
        win.attributes("-topmost", True)
        tk.Label(win, text="Onde salvar os cortes?", bg=CARD, fg=TXT, font=self.f_step).pack(padx=22, pady=(16, 2))
        tk.Label(win, text="Pode ser qualquer pasta (não precisa de Drive).",
                 bg=CARD, fg=SUB, font=self.f_small).pack(padx=22, pady=(0, 10))

        def fechar(p):
            esc["p"] = p; win.destroy()

        def desk():  fechar(os.path.join(self._pasta_conhecida("Desktop"), sub))
        def vids():  fechar(os.path.join(self._pasta_conhecida("Videos"), sub))
        def pick():
            win.attributes("-topmost", False)
            p = filedialog.askdirectory(title="Escolha a pasta", parent=win)
            if p: fechar(p)
            else: win.attributes("-topmost", True)
        def paste():
            win.attributes("-topmost", False)
            p = simpledialog.askstring("Colar caminho", "Cole o caminho da pasta:", parent=win)
            if p: fechar(p.strip().strip('"'))
            else: win.attributes("-topmost", True)

        for txt, cmd in [("🖥   Área de Trabalho", desk), ("🎬   Pasta Vídeos", vids),
                         ("📁   Escolher uma pasta…", pick), ("📋   Colar um caminho…", paste)]:
            b = tk.Frame(win, bg=ACCENT, cursor="hand2")
            b.pack(fill="x", padx=22, pady=4)
            l = tk.Label(b, text=txt, bg=ACCENT, fg="#06121A", font=self.f_small)
            l.pack(pady=9, padx=10, anchor="w")
            for wdg in (b, l):
                wdg.bind("<Button-1>", lambda e, c=cmd: c())
                wdg.bind("<Enter>", lambda e, fr=b, la=l: (fr.config(bg=ACCENT2), la.config(bg=ACCENT2)))
                wdg.bind("<Leave>", lambda e, fr=b, la=l: (fr.config(bg=ACCENT), la.config(bg=ACCENT)))
        canc = tk.Label(win, text="cancelar", bg=CARD, fg=SUB, font=self.f_small, cursor="hand2")
        canc.pack(pady=(6, 10))
        canc.bind("<Button-1>", lambda e: fechar(None))
        win.update_idletasks()
        # centraliza o popup sobre o app
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        win.geometry(f"+{max(0, rx-40)}+{max(0, ry-40)}")
        win.grab_set()
        self.root.wait_window(win)
        self._pausar_pin = False
        try: self.root.attributes("-topmost", True)
        except Exception: pass
        return esc["p"]

    def _definir_destino(self):
        """Abre o menu, cria a pasta e salva no config. Devolve True se definiu."""
        import exportar
        pasta = self._escolher_destino()
        try: self.root.attributes("-topmost", True)
        except Exception: pass
        if not pasta:
            return False
        try:
            os.makedirs(pasta, exist_ok=True)
        except Exception:
            from tkinter import messagebox
            messagebox.showwarning("Pasta inválida", f"Não consegui usar:\n{pasta}", parent=self.root)
            return False
        cfg = exportar.carregar_config()
        cfg["destino"]["pasta_local"] = pasta
        exportar.salvar_config(cfg)
        self._atualizar_destino_label()
        return True

    def _alterar_destino(self):
        if self.running:
            return
        self._definir_destino()

    # ---------- execucao ----------
    def _garantir_destino(self):
        """Na 1a vez (ou se a pasta sumiu), pede a pasta de destino e salva."""
        import exportar
        d = exportar.carregar_config()["destino"]["pasta_local"]
        if d and os.path.isdir(d):
            return True
        return self._definir_destino()

    def _iniciar(self, modo, passos):
        """Prepara a UI e dispara o worker no modo dado."""
        self.modo = modo
        self.running = True
        self.result_folder = None
        self.result.pack_forget()
        self._montar_passos(passos)
        self.active = None
        self.detail.config(text="Iniciando…", fg=SUB)
        self._btn_enable(False, "Trabalhando…")
        threading.Thread(target=self._worker, daemon=True).start()

    def start(self):
        """Modo completo: exporta no CapCut + corta + organiza."""
        if self.running:
            return
        if not self._garantir_destino():
            return
        self._iniciar("completo", PASSOS)

    def start_corte(self):
        """Modo só cortar: pega um vídeo JÁ exportado e só corta/organiza."""
        if self.running:
            return
        if not self._garantir_destino():
            return
        # escolhe o vídeo já exportado
        from tkinter import filedialog
        self._pausar_pin = True
        try: self.root.attributes("-topmost", False)
        except Exception: pass
        import os as _os
        video = filedialog.askopenfilename(
            title="Escolha o vídeo já exportado (a timeline inteira)",
            initialdir=_os.path.join(_os.path.expanduser("~"), "Downloads"),
            filetypes=[("Vídeos", "*.mp4 *.mov *.mkv"), ("Todos", "*.*")],
            parent=self.root)
        self._pausar_pin = False
        try: self.root.attributes("-topmost", True)
        except Exception: pass
        if not video:
            return
        self._video_corte = video
        self._iniciar("corte", PASSOS_CORTE)

    def _worker(self):
        def cb(i, d=""):
            self.q.put(("step", i, d))
        try:
            if self.modo == "corte":
                import exportar_auto
                raiz, n = exportar_auto.executar_corte(self._video_corte, cb=cb, abrir=False)
            elif DEMO:
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
        self.res_title.config(text=f"✓  {n} clipes prontos")
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
