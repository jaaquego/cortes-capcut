# -*- coding: utf-8 -*-
"""Acha e foca a janela do EDITOR do CapCut (nao a launcher/shell em branco)."""
import time
import win32api, win32con, win32gui, win32process


def _exe(pid):
    try:
        h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        try:
            return win32process.GetModuleFileNameEx(h, 0)
        finally:
            win32api.CloseHandle(h)
    except Exception:
        return ""


def listar():
    """Lista janelas do processo CapCut: (hwnd, titulo, visivel, area, rect)."""
    out = []
    def cb(hwnd, _):
        if not win32gui.IsWindow(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if "capcut" not in _exe(pid).lower():
            return
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        out.append({
            "hwnd": hwnd,
            "titulo": win32gui.GetWindowText(hwnd),
            "visivel": bool(win32gui.IsWindowVisible(hwnd)),
            "onscreen": l > -10000,
            "area": (r - l) * (b - t),
            "rect": (l, t, r, b),
        })
    win32gui.EnumWindows(cb, None)
    return out


def janela_editor():
    """Escolhe a janela do editor: visivel, on-screen, maior area."""
    cands = [w for w in listar() if w["visivel"] and w["area"] > 100000]
    if not cands:
        cands = listar()
    cands.sort(key=lambda w: (w["onscreen"], w["area"]), reverse=True)
    return cands[0] if cands else None


def _capcut_hwnds():
    s = set()
    def cb(h, _):
        if not win32gui.IsWindow(h):
            return
        _, pid = win32process.GetWindowThreadProcessId(h)
        if "capcut" in _exe(pid).lower():
            s.add(h)
    win32gui.EnumWindows(cb, None)
    return s


def _alt_pulse():
    """Pressiona/solta ALT pra satisfazer a regra de 'input do usuario' do Windows,
    liberando o SetForegroundWindow (foreground lock)."""
    try:
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


def focar(hwnd=None):
    w = janela_editor() if hwnd is None else {"hwnd": hwnd}
    if not w:
        return False
    hwnd = w["hwnd"]

    # desliga o timeout do foreground lock
    try:
        win32gui.SystemParametersInfo(win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 0)
    except Exception:
        pass

    capcuts = _capcut_hwnds()
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    time.sleep(0.15)

    def _traz():
        try:
            # se a janela do topo NAO e' do CapCut, minimiza pra tirar da frente
            fg = win32gui.GetForegroundWindow()
            if fg and fg not in capcuts:
                try: win32gui.ShowWindow(fg, win32con.SW_MINIMIZE)
                except Exception: pass
                time.sleep(0.15)
            th_fg, _ = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
            th_alvo, _ = win32process.GetWindowThreadProcessId(hwnd)
            cur = win32api.GetCurrentThreadId()
            for th in {th_fg, cur}:
                try: win32process.AttachThreadInput(th, th_alvo, True)
                except Exception: pass
            _alt_pulse()
            win32gui.BringWindowToTop(hwnd)
            try: win32gui.SetForegroundWindow(hwnd)
            except Exception: pass
            try: win32gui.SetActiveWindow(hwnd)
            except Exception: pass
            for th in {th_fg, cur}:
                try: win32process.AttachThreadInput(th, th_alvo, False)
                except Exception: pass
        except Exception as e:
            print("focar erro:", e)

    # tenta ate o CapCut ser de fato a janela em primeiro plano
    for _ in range(5):
        _traz()
        time.sleep(0.25)
        if win32gui.GetForegroundWindow() == hwnd:
            time.sleep(0.45)  # deixa repintar
            return True
    time.sleep(0.4)
    return win32gui.GetForegroundWindow() == hwnd


def rect(hwnd):
    return win32gui.GetWindowRect(hwnd)


if __name__ == "__main__":
    for w in listar():
        print(f"hwnd={w['hwnd']} vis={w['visivel']} onscreen={w['onscreen']} "
              f"area={w['area']:>9} rect={w['rect']}  {w['titulo']!r}")
    print("\n-> editor escolhido:", janela_editor())
