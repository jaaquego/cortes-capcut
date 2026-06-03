# -*- coding: utf-8 -*-
"""
Corta o video exportado (timeline inteira) em clipes por segmento, via ffmpeg.
Corte com re-encode = precisao de frame (qualidade alta, visualmente sem perda).
"""
import os
import subprocess
import glob

HERE = os.path.dirname(os.path.abspath(__file__))

# roda o ffmpeg SEM abrir janela de console (senao pisca uma a cada corte)
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def _run(cmd, **kw):
    return subprocess.run(cmd, creationflags=_NO_WINDOW, **kw)


def achar_ffmpeg():
    """Acha o ffmpeg.exe que vem com o CapCut (versao mais recente)."""
    apps = os.path.join(os.environ["LOCALAPPDATA"], "CapCut", "Apps")
    cands = glob.glob(os.path.join(apps, "*", "ffmpeg.exe"))
    if cands:
        return sorted(cands)[-1]  # maior versao
    return "ffmpeg"  # tenta o PATH


def duracao_us(video, ffmpeg=None):
    """Retorna a duracao do video em microssegundos (via ffmpeg)."""
    ffmpeg = ffmpeg or achar_ffmpeg()
    r = _run([ffmpeg, "-hide_banner", "-i", video], capture_output=True, text=True)
    import re as _re
    m = _re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if not m:
        return None
    s = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return int(s * 1_000_000)


def _tc(us):
    """microssegundos -> 'HH:MM:SS.mmm' pro ffmpeg."""
    s = us / 1_000_000
    h = int(s // 3600); s -= h * 3600
    m = int(s // 60); s -= m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def cortar(video_in, start_us, dur_us, saida, ffmpeg=None, cq=20):
    """Corta [start, start+dur] com re-encode via NVENC (precisao de frame, qualidade alta)."""
    ffmpeg = ffmpeg or achar_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-ss", _tc(start_us),
        "-i", video_in,
        "-t", _tc(dur_us),
        "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", str(cq), "-b:v", "0",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        saida,
    ]
    r = _run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou:\n{r.stderr[-800:]}")
    return saida


# ------------------------- autoteste -------------------------
if __name__ == "__main__":
    ff = achar_ffmpeg()
    print("ffmpeg:", ff)
    tmp = os.path.join(HERE, "_selftest")
    os.makedirs(tmp, exist_ok=True)
    base = os.path.join(tmp, "fonte.mp4")
    # gera 20s de testsrc com timecode + audio
    subprocess.run([ff, "-y", "-f", "lavfi", "-i", "testsrc=duration=20:size=320x240:rate=30",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
                    "-c:v", "h264_nvenc", "-pix_fmt", "yuv420p", "-c:a", "aac", base],
                   capture_output=True)
    # corta [3.0s, 8.0s) -> deve dar 5.0s
    out = os.path.join(tmp, "corte.mp4")
    cortar(base, 3_000_000, 5_000_000, out, ff)
    # mede duracao do corte
    probe = subprocess.run([ff, "-i", out], capture_output=True, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", probe.stderr)
    if m:
        dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        print(f"duracao do corte: {dur:.2f}s (esperado ~5.00s)")
    print("autoteste OK" if m else "falhou")
