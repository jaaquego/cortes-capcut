# Exportador Automático CapCut → Cortes por vídeo

Transforma 1 projeto do CapCut (timeline com vários vídeos no padrão `ESTRUTURA X - V Y`)
em N clipes separados, com precisão de frame, já organizados em pastas.

> 👉 **Equipe:** veja o guia completo em **[INSTRUCOES.md](INSTRUCOES.md)** (instalar, montar a
> timeline, regras de uso). Resumo de instalação abaixo.

## 📥 Instalação (passo a passo para a equipe)

**Pré-requisitos na sua máquina:**
- Windows 10/11
- **CapCut Desktop** instalado
- (Opcional) **Google Drive para Desktop**, se quiser salvar os cortes direto no Drive
  — mas **não é obrigatório**: dá pra salvar em qualquer pasta (Área de Trabalho, Vídeos, etc.)

**Instalar:**
1. Baixe o projeto (botão verde **Code → Download ZIP** no GitHub) e **descompacte**
   numa pasta fixa (ex.: `Documentos\Cortes CapCut`). Não rode de dentro do .zip.
2. Dê **2 cliques em `Instalar.bat`**.
   - Se aparecer "Python instalado, rode de novo", feche e dê 2 cliques no `Instalar.bat` outra vez.
   - O instalador baixa as bibliotecas e cria o atalho **"Cortes CapCut"** na Área de Trabalho.
3. Abra o **CapCut** no projeto que quer exportar e dê 2 cliques no atalho **"Cortes CapCut"**.
4. Na **1ª vez**, o programa pergunta **onde salvar os cortes**: Área de Trabalho,
   pasta Vídeos, escolher uma pasta, ou colar um caminho (pode ser Google Drive **ou
   qualquer pasta** — não precisa de Drive). Dá pra mudar depois no link **"alterar"**.
   Depois é só clicar **▶ Começar**.

**Como usar no dia a dia:** abra **só** o projeto desejado no CapCut → atalho → **Começar**.
Não mexa no mouse durante os ~15s de cliques; o resto roda enquanto você trabalha.

> O CapCut pode estar em Português **ou** Inglês (o programa entende os dois).

## Por que funciona assim

O CapCut PC não exporta trechos da timeline pela automação (teclas I/O não respondem,
o campo de range no arquivo é ignorado, e o diálogo só exporta a timeline inteira).
Então a estratégia é: **exportar a timeline inteira 1 vez → cortar com o ffmpeg/NVENC**
nos timecodes exatos de cada vídeo (do fim de um rótulo até o início do próximo).
O resultado é idêntico ao corte manual com I/O — o rótulo (~1,8s) fica de fora.

## Uso recomendado: o app (`exportador_gui.py`)

Há um atalho **"Exportar Cortes CapCut"** na Área de Trabalho (ícone próprio) que
abre um **app pequeno e moderno** (`exportador_gui.py`, via `pythonw`, sem console).

1. No CapCut, **abra o projeto** (deixe ele aberto na timeline; feche os outros).
2. Abra o app pelo atalho e clique em **▶ Começar**.
3. O app mostra o passo a passo (spinner animado) e, no fim, um **link clicável**
   pra pasta dos cortes. Durante os ~15s de cliques, não mexa no mouse;
   no resto (gerar/cortar), use o PC normalmente.

Versão "console" (debug): `Exportar Automatico.bat` ou `py exportar_auto.py`.
Recriar o atalho: gere o ícone com `py gerar_icone.py` e aponte um atalho do
`pythonw.exe` pra `exportador_gui.py` (ver histórico do WScript.Shell).
3. O programa faz tudo sozinho:
   - acha a janela do editor do CapCut (lê a tela com OCR),
   - clica **Exportar** e **confirma** (o CapCut exporta a timeline inteira),
   - espera o `.mp4` ficar pronto,
   - identifica qual projeto está aberto (pelo prefixo do nome + draft mais recente),
   - corta os N vídeos, organiza em `Estrutura N\VM\` e sobe pro Drive,
   - apaga o arquivo grande.

Seu único toque é **abrir o projeto**. O resto é automático — você não exporta nada.

### Como a automação de UI funciona (e por que é assim)
O CapCut abre ~20 janelas internas e não expõe acessibilidade, então:
- a tela é lida com **OCR** (`rapidocr`), localizando botões/textos por escrito;
- a janela certa é escolhida por **conteúdo** (a que tem "Exportar" e não é a home),
  trazendo-a pra frente e pra dentro da tela mesmo quando o CapCut a joga pra fora;
- o arquivo exportado vai pra pasta padrão do CapCut (Downloads) e é detectado lá.

Requisito: rode com a tela livre (a automação traz o CapCut pra frente e minimiza
a janela que estiver na frente). Resolução testada: 2560×1600.

## Alternativa: o Vigia (você exporta, ele corta)

Se preferir exportar manualmente: 2 cliques em **`Iniciar Vigia.bat`**, exporte a
timeline inteira pra pasta vigiada (`config.json` → `vigia.pasta_export_capcut`), e o
Vigia identifica, corta, organiza e apaga sozinho.

## Uso manual (sem o Vigia)

```powershell
cd $env:USERPROFILE\Claude\capcut-exporter
py scan.py                              # lista projetos com vídeos a exportar
py scan.py "<projeto>"                  # mostra os trechos de um projeto
py exportar.py "<projeto>" --video "C:\...\timeline_inteira.mp4"
py vigiar.py --agora                    # processa o .mp4 mais recente da pasta vigiada
```

## Configuração (`config.json`)

- `destino.pasta_local` — onde os cortes são salvos. Vem **vazio**; o app pergunta na 1ª vez
  (Área de Trabalho, Vídeos, escolher pasta ou colar caminho — Drive **ou** qualquer pasta).
  Dá pra trocar no link **"alterar"** do app. Dentro dela, cada projeto ganha uma
  **pasta-mãe** com o nome do projeto **sem o formato**, e dentro dela `Estrutura N\V M\`.
- **Reels + Feed na mesma pasta:** os projetos `Reels-...` e `Feed-...` (mesmo vídeo em
  9:16 e 4:5) caem na **mesma pasta-mãe** (o prefixo `Reels/Feed` é removido do nome da
  pasta) e se diferenciam pelo **nome do arquivo** (que mantém `Reels`/`Feed` na frente).
  Ex.: `Cortes CapCut\Narrado Vistas de Anitá III E1 V\Estrutura 1\V1\`
  contém `Reels Narrado... E1-V1.mp4` **e** `Feed Narrado... E1-V1.mp4`.
  Formatos reconhecidos como prefixo: `reels, feed, stories, story, carrossel`.
- `vigia.pasta_export_capcut` — pasta que o Vigia observa (opcional; vazio = usa a pasta
  Downloads). Só importa pra alternativa manual (o Vigia).
- `vigia.deletar_apos_cortar` — apaga o arquivo grande depois de cortar (true/false).
- `vigia.tolerancia_duracao_s` — margem pra confirmar que o vídeo é a timeline inteira.
- `nome_arquivo` — padrão do nome. Variáveis: `{projeto}` (nome limpo do projeto),
  `{nome}` (ex: `E1-V1`). Atual: `{projeto} {nome}` →
  `Criativos Vídeo Narrado Vistas de Anitá E1-V1.mp4`.

## Requisito no projeto do CapCut

Cada vídeo precisa de uma caixa de texto separadora no padrão **`ESTRUTURA X ... V Y`**
no início (serve de marcador; não entra no corte). O número da estrutura e da versão
podem estar em vários formatos (`ESTRUTURA 1 ... V3`, `Estrutura1 V3`, etc.).

## Arquivos

- `exportador_gui.py` — **o app** (janela com botão, spinner, passos e link da pasta)
- `Exportar Automatico.bat` — versão console (debug) do mesmo fluxo
- `exportar_auto.py` — orquestra: `executar(cb)` aciona o export na UI + corta/organiza/sobe
- `gerar_icone.py` / `icon.ico` — ícone do atalho
- `auto.py` — motor de UI (acha/foca a janela certa do CapCut, OCR, clique)
- `ocr_tela.py` — captura a tela + OCR (rapidocr)
- `focuswin.py` — traz a janela do CapCut pra frente (vence o foreground lock)
- `Iniciar Vigia.bat` — inicia o Vigia com 2 cliques (alternativa manual)
- `vigiar.py` — vigia a pasta e dispara o corte automático
- `scan.py` — detecção: lista projetos e trechos
- `segments.py` — extrai os timecodes de cada vídeo
- `split.py` — corta via ffmpeg/NVENC (motor)
- `exportar.py` — núcleo de corte + uso manual por linha de comando
- `config.json` — configurações

## Onde salvar (Drive é opcional)

Você escolhe a pasta de destino no app (1ª vez ou no link **"alterar"**): Área de
Trabalho, pasta Vídeos, escolher uma pasta, ou colar um caminho. **Não precisa de
Google Drive.** Se quiser que os cortes subam pro Drive automaticamente, basta escolher
uma pasta que esteja dentro do **Google Drive para Desktop** (ex.: `G:\Meu Drive\...`).
