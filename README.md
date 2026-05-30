# Exportador Automático CapCut → Cortes por vídeo

Transforma 1 projeto do CapCut (timeline com vários vídeos no padrão `ESTRUTURA X - V Y`)
em N clipes separados, com precisão de frame, já organizados em pastas.

## Por que funciona assim

O CapCut PC não exporta trechos da timeline pela automação (teclas I/O não respondem,
o campo de range no arquivo é ignorado, e o diálogo só exporta a timeline inteira).
Então a estratégia é: **exportar a timeline inteira 1 vez → cortar com o ffmpeg/NVENC**
nos timecodes exatos de cada vídeo (do fim de um rótulo até o início do próximo).
O resultado é idêntico ao corte manual com I/O — o rótulo (~1,8s) fica de fora.

## Uso recomendado: toque zero (`Exportar Automatico.bat`)

1. No CapCut, **abra o projeto** (deixe ele aberto na timeline).
2. Dê 2 cliques em **`Exportar Automatico.bat`**.
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

- `destino.pasta_local` — onde os cortes são salvos. **Atual: `I:\Meu Drive\Cortes CapCut`**
  (pasta do Google Drive → sobe pro Drive sozinho). Dentro dela, cada projeto ganha uma
  **pasta-mãe** com o nome do projeto, e dentro dela `Estrutura N\V M\`. Ex.:
  `Cortes CapCut\Criativos Vídeo Narrado Vistas de Anitá\Estrutura 1\V1\...`
- `vigia.pasta_export_capcut` — pasta que o Vigia observa. **Atual: `C:\Users\compu\CapCut_Export_Temp`**
  (pasta local, fora do OneDrive, pra não subir o arquivão à toa). Exporte a timeline aqui.
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

- `Exportar Automatico.bat` — fluxo toque zero (2 cliques, com o projeto aberto)
- `exportar_auto.py` — orquestra: aciona o export na UI + corta/organiza/sobe
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

## Google Drive (configurado)

O **Google Drive para Desktop** está instalado e montado em `I:\` (`I:\Meu Drive`).
O destino dos cortes aponta para `I:\Meu Drive\Cortes CapCut`, então os clipes sobem
para o Drive automaticamente. Depois é só mover, dentro do Drive, para a pasta do
empreendimento (move interno do Drive, sem re-upload).

Obs: a letra do mount (`I:`) pode mudar se você reorganizar os drives. Se um dia o
destino parar de funcionar, confira a letra atual do Google Drive e atualize
`destino.pasta_local` no `config.json`.
