# 📹 Cortes do CapCut — guia da equipe

Programa que pega **um projeto do CapCut** (com vários vídeos numa timeline só) e
**exporta, corta e organiza tudo em pastas automaticamente**. Você só abre o projeto
e clica em **Começar**.

---

## ✅ Pré-requisitos (na sua máquina)

- **Windows** 10/11
- **CapCut Desktop** instalado (pode estar em Português **ou** Inglês)
- **Conta no GitHub** (gratuita) pra baixar — peça ao responsável pra te liberar o acesso
- **Google Drive para Desktop** é **opcional** — dá pra salvar em **qualquer pasta**
  (Área de Trabalho, Vídeos, etc.)

---

## 1️⃣ Instalar (só uma vez)

1. Acesse o repositório: **https://github.com/jaaquego/cortes-capcut**
2. Botão verde **`Code` → `Download ZIP`**
3. **Descompacte** numa pasta fixa (ex.: `Documentos`). ⚠️ Não rode de dentro do `.zip`.
4. Dê **2 cliques em `Instalar.bat`**.
   - Se aparecer *"Python instalado, rode de novo"*, feche e dê 2 cliques no `Instalar.bat` outra vez.
   - Ele baixa as bibliotecas e cria o atalho **"Cortes CapCut"** na Área de Trabalho.

---

## 2️⃣ Como montar a timeline no CapCut (parte mais importante!)

O programa identifica cada vídeo por uma **caixa de texto** que funciona como **etiqueta**:

- Coloque todos os vídeos/variações **em sequência** numa timeline só.
- **No começo de cada vídeo**, adicione uma **caixa de texto** com a etiqueta no padrão:
  - `ESTRUTURA 1 - V1`, `ESTRUTURA 1 - V2`, `ESTRUTURA 2 - V1`… **ou** a forma curta
  - `E1 - V1`, `E1 - V2`, `E2 - V1`…
- Cada etiqueta marca onde **começa** um vídeo. O programa corta de **uma etiqueta até a próxima**.
- A etiqueta **não aparece** no vídeo final (ela é só o marcador — o corte começa logo depois dela).
- O último vídeo vai da etiqueta dele até o **fim** da timeline.

Na prática, a timeline fica assim:

```
[E1-V1] vídeo…  [E1-V2] vídeo…  [E1-V3] vídeo…  [E2-V1] vídeo…  …
```

### 🎬 Reels e Feed (9:16 e 4:5)

Se o mesmo vídeo tem as duas versões, crie **dois projetos** com o **mesmo nome**, mudando
só o começo: `Reels-…` e `Feed-…`. Os cortes dos dois caem **na mesma pasta**, com
"Reels"/"Feed" na frente do nome do arquivo.

---

## 3️⃣ Como usar no dia a dia

1. Abra no CapCut **só o projeto** que quer exportar (feche os outros).
2. Dê 2 cliques no atalho **"Cortes CapCut"** → botão **▶ Começar**.
3. Na **1ª vez**, escolha **onde salvar**: Área de Trabalho, Pasta Vídeos, escolher uma
   pasta, ou colar um caminho (Drive **ou** qualquer pasta). Dá pra mudar depois no link **"alterar"**.

---

## ⚠️ Regras importantes enquanto o programa trabalha

- **Não mexa no mouse nem no teclado** nos ~15 segundos em que ele clica sozinho no CapCut
  (abrir exportar → confirmar → fechar aviso). Depois disso pode usar o PC normal enquanto
  ele renderiza e corta.
- Deixe **só um projeto aberto** no CapCut (se tiver vários, ele pode pegar o errado).
- Não feche o CapCut nem a janelinha do programa durante o processo.
- A janelinha do programa fica **fixa no canto inferior direito** mostrando o progresso.

---

## 📁 O que ele entrega

No fim, abre sozinho a pasta com os cortes organizados:

```
<Nome do Projeto>/
├── Estrutura 1/  V1  V2  V3  V4  V5
├── Estrutura 2/  V1  V2  V3  V4  V5
└── Estrutura 3/  …
```

Cada `V` tem o(s) arquivo(s) do vídeo (e, se você fez Reels + Feed, os dois lado a lado).

---

Dúvidas? Fale com o responsável pela ferramenta. 🙌
