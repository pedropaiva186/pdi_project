# Etapa 2 — Especificação de implementação do Frontend

> Documento de tarefa para o agente responsável pelo frontend. Complementa (não substitui) [FRONTEND.md](FRONTEND.md), [API.md](API.md) e [PROCESSOS.md](PROCESSOS.md). Em caso de conflito, **este documento prevalece** sobre FRONTEND.md nos pontos que ele detalha; para o contrato HTTP, **API.md prevalece**.

## 0. Regras do trabalho

- **Escopo de escrita:** apenas a pasta `frontend/`. **Não** altere `shared/`, `docs/`, `backend/`, `run.py` nem arquivos da raiz. Se achar um problema no catálogo ou na especificação, **pare e reporte** ao líder em vez de contornar.
- **Não faça commits.** O líder cuida do versionamento.
- **Dependências de runtime:** somente `react` e `react-dom` (18.x). DevDependencies: `vite`, `@vitejs/plugin-react`, ESLint padrão do template Vite. Nenhuma biblioteca de UI, gráfico, estado, roteamento, ícones ou CSS-in-JS. Ícones: SVG inline ou caracteres Unicode.
- **JavaScript puro** (`.jsx`/`.js`), sem TypeScript. Componentes funcionais com hooks.
- **Idioma:** todo texto visível em português do Brasil; identificadores em inglês.
- Ambiente local: Node 26 / npm 11 (o projeto deve funcionar com Node ≥ 20).

## 1. Setup

```
frontend/
├── index.html                 # <html lang="pt-BR">, <title>Processador de Imagens — PDI</title>
├── package.json               # name "pdi-frontend", "private": true, "type": "module"
├── vite.config.js
├── eslint.config.js
├── .env.example               # VITE_USE_MOCK=false
├── .gitignore                 # node_modules/, dist/
├── README.md                  # como rodar (dev, mock, build)
└── src/ …                     # ver §3
```

Scripts do `package.json`: `dev` (`vite`), `build` (`vite build`), `preview` (`vite preview`), `lint` (`eslint .`).

### `vite.config.js`

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@shared': path.resolve(__dirname, '../shared') } },
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
    fs: { allow: [path.resolve(__dirname, '..')] },
  },
  build: { outDir: 'dist', emptyOutDir: true },
})
```

- O mock importa o catálogo com `import catalog from '@shared/processes.json'`.
- `base` fica no padrão (`/`): o FastAPI serve o build na raiz.

## 2. Camada de API — `src/api/`

### 2.1 `errors.js`

```js
export class ApiError extends Error {
  constructor(status, code, message, details = {}) { super(message); this.name = 'ApiError'; Object.assign(this, { status, code, details }) }
}
```

### 2.2 `client.js` (API real)

Base: `const BASE = '/api'`.

| Função | Requisição | Retorno |
|---|---|---|
| `getProcesses()` | `GET /api/processes` | JSON do catálogo (com `implemented`) |
| `inspectImage(file)` | `POST /api/images/inspect`, `FormData` com `file` | `{ mode, width, height, source_mode, filename }` |
| `runProcess(processId, file, params)` | `POST /api/process/${encodeURIComponent(id)}`, `FormData` com `file` e `params = JSON.stringify(params)` | resposta de sucesso de API.md |

- Não defina `Content-Type` manualmente no `FormData`.
- Função interna `request(url, options)`:
  - `fetch` rejeitou (rede/servidor fora) → `throw new ApiError(0, 'network_error', 'Não foi possível conectar ao servidor. Verifique se o backend está rodando.')`.
  - `!response.ok` → tenta `await response.json()`; se tiver `error.code`, lança `ApiError(status, error.code, error.message, error.details)`; senão lança `ApiError(status, 'http_error', \`Erro inesperado do servidor (HTTP ${status}).\`)`.
  - Sucesso → `response.json()`.

### 2.3 `mock.js` (sem backend)

Mesma interface. Comportamento:

- **`getProcesses()`**: espera 150 ms; devolve um clone profundo de `@shared/processes.json` com `implemented: true` em todos, **exceto `sobel` com `implemented: false`** (para exercitar o selo).
- **`inspectImage(file)`**: rejeita com `ApiError(400, 'invalid_image', 'O arquivo não é um PNG válido.')` se `file.type !== 'image/png'` e o nome não terminar em `.png`. Decodifica com `createImageBitmap` → `OffscreenCanvas`/`<canvas>` → `getImageData`. `mode = 'gray'` se R = G = B em todos os pixels, senão `'rgb'`. `source_mode`: `'L'` ou `'RGB'`. Erro de decodificação → `invalid_image`.
- **`runProcess(processId, file, params)`**:
  1. espera 400 ms;
  2. processo inexistente → `ApiError(404, 'process_not_found', …)`;
  3. reinspeciona o arquivo; se `mode` não estiver em `process.modes` → `ApiError(422, 'unsupported_mode', 'Este processo não está disponível para imagens …')`;
  4. `sobel` → `ApiError(501, 'not_implemented', 'O processo "Gradiente de Sobel" ainda não foi implementado.')`;
  5. monta a resposta **exatamente** no formato de API.md (`process_id`, `params`, `input`, `outputs`, `histograms`, `metrics`, `elapsed_ms`). `params` = os parâmetros recebidos completados com os defaults dos parâmetros visíveis;
  6. saída padrão: `main` `result` "Resultado (simulado)", com a imagem de entrada como data URL PNG (`canvas.toDataURL('image/png')`);
  7. casos especiais:
     - `rgb_split`: 3 saídas `main` `r`/`g`/`b` ("Canal R", "Canal G", "Canal B"), cada uma uma imagem cinza com o valor do canal (R=G=B=canal);
     - `hsv_split`: 3 saídas `main` `h`/`s`/`v` ("Canal H", "Canal S", "Canal V"); conversão RGB→HSV em JS só no mock, com H escalado para 0–255;
     - `histogram_equalization`: saída `main` `equalized` "Imagem equalizada" (cópia da entrada) e histogramas `before` "Histograma original" e `after` "Histograma equalizado" (256 contagens do canal R; no mock `after` pode ser igual a `before`);
     - `laplacian_sharpen`: `main` `result` "Imagem realçada" + `aux` `laplacian` "Laplaciano ajustado" (cópia da entrada);
  8. `metrics`: `[{ label: 'Tempo de processamento', value: <ms reais medidos com performance.now()>, unit: 'ms' }]`; `elapsed_ms` igual.
  9. `outputs[].mode/width/height` preenchidos (canais RGB/HSV → `'gray'`).

### 2.4 `index.js`

```js
import * as real from './client.js'
import * as mock from './mock.js'
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
export const api = USE_MOCK ? mock : real
export { ApiError } from './errors.js'
```

Com o mock ativo, mostre um selo discreto "Modo simulado" na barra superior.

## 3. Estrutura de `src/`

```
src/
├── main.jsx
├── App.jsx
├── App.module.css
├── api/            errors.js, client.js, mock.js, index.js
├── state/          appReducer.js, actions.js (constantes dos tipos)
├── hooks/
│   ├── useCatalog.js        # carrega o catálogo e expõe retry
│   ├── useImageLoader.js    # openFile(file, { asOriginal })
│   ├── useProcessRunner.js  # run(); descarta respostas obsoletas
│   └── useKeyboardShortcuts.js
├── components/
│   ├── FileMenu/            FileMenu.jsx, SaveMenu.jsx, FileMenu.module.css
│   ├── ProcessSidebar/      ProcessSidebar.jsx, ProcessItem.jsx, *.module.css
│   ├── ImagePanel/          ImagePanel.jsx, *.module.css
│   ├── InputPanel/          InputPanel.jsx (ImagePanel + dropzone + botão abrir)
│   ├── OutputPanel/         OutputPanel.jsx (ImagePanel + abas)
│   ├── ParamsPanel/         ParamsPanel.jsx, ParamField.jsx, Toggle.jsx, SegmentedControl.jsx, *.module.css
│   ├── AccessoryPanel/      AccessoryPanel.jsx, MetricsTable.jsx, *.module.css
│   ├── HistogramChart/      HistogramChart.jsx, *.module.css
│   ├── ImageModal/          ImageModal.jsx, *.module.css
│   ├── Toast/               ToastContainer.jsx, *.module.css
│   ├── Spinner/             Spinner.jsx
│   └── CatalogError/        CatalogError.jsx (tela cheia com "Tentar novamente")
├── utils/
│   ├── params.js
│   ├── download.js
│   ├── dataUrl.js
│   ├── format.js            # modeLabel, dims, nomes de arquivo, formatação numérica
│   └── messages.js          # mensagens de erro amigáveis por código
└── styles/
    ├── tokens.css
    └── global.css           # reset, body, foco visível, scrollbar
```

CSS: **CSS Modules** (`*.module.css`) por componente + `tokens.css`/`global.css` globais.

## 4. Estado — `state/appReducer.js`

Estado inicial:

```js
{
  catalog: null,                 // { version, categories, processes }
  catalogStatus: 'loading',      // 'loading' | 'ready' | 'error'
  catalogError: null,            // string
  input: null,                   // ImageRef
  original: null,                // ImageRef
  selectedProcessId: null,
  paramsByProcess: {},           // { [processId]: { [paramId]: value } }
  result: null,                  // resposta de runProcess + { inputName }
  activeOutputId: null,
  status: 'idle',                // 'idle' | 'inspecting' | 'processing'
  requestId: 0,                  // incrementa a cada processamento iniciado
  toasts: [],                    // { id, kind: 'error'|'success'|'info', message }
}
```

`ImageRef = { file: File, url: string /* object URL ou data URL */, name: string /* sem extensão */, filename: string, mode: 'gray'|'rgb', width, height, sourceMode }`

Ações (constantes em `actions.js`):

| Ação | Payload | Efeito |
|---|---|---|
| `CATALOG_LOADING` | — | `catalogStatus='loading'` |
| `CATALOG_LOADED` | `catalog` | guarda; `catalogStatus='ready'`; inicializa `paramsByProcess[id]` com os defaults de cada processo |
| `CATALOG_ERROR` | `message` | `catalogStatus='error'` |
| `INSPECT_START` | — | `status='inspecting'` |
| `IMAGE_LOADED` | `image, asOriginal` | `input=image`; se `asOriginal`, `original=image`; `result=null`, `activeOutputId=null`; `status='idle'`; se o processo selecionado não aceitar `image.mode`, `selectedProcessId=null` |
| `INSPECT_ERROR` | — | `status='idle'` (a mensagem vai por `PUSH_TOAST`) |
| `SELECT_PROCESS` | `id` | só se habilitado para o modo atual |
| `SET_PARAM` | `processId, paramId, value` | atualiza o valor (já normalizado) |
| `RESET_PARAMS` | `processId` | volta aos defaults |
| `PROCESS_START` | — | `status='processing'`; `requestId+1` |
| `PROCESS_SUCCESS` | `requestId, result` | ignora se `requestId` não for o atual; `result`; `activeOutputId` = id da primeira saída `main`; `status='idle'` |
| `PROCESS_ERROR` | `requestId` | ignora se obsoleto; `status='idle'` |
| `SET_ACTIVE_OUTPUT` | `id` | — |
| `RESTORE_ORIGINAL` | — | `input=original`; `result=null`; `activeOutputId=null`; revalida a seleção pelo modo |
| `PUSH_TOAST` / `DISMISS_TOAST` | `toast` / `id` | — |

Regras:
- **Respostas obsoletas:** se `IMAGE_LOADED` ou `RESTORE_ORIGINAL` acontecer durante um processamento, incremente `requestId` e volte `status` para `'idle'`, para que a resposta antiga seja descartada.
- **Object URLs:** revogue (`URL.revokeObjectURL`) os URLs de `ImageRef` que deixarem de ser referenciados por `input` ou `original` (faça isso num `useEffect` no `App`, nunca dentro do reducer).
- `paramsByProcess` persiste ao trocar de processo ou de imagem (não reseta).

## 5. Utilitários

### 5.1 `utils/params.js` (funções puras, exportadas e cobertas por comentários JSDoc)

- `getDefaults(process) → object` com todos os parâmetros.
- `isVisible(param, values) → boolean`: sem `visible_if` → `true`; senão `values[visible_if.param] === visible_if.equals`.
- `visibleParams(process, values) → object` com só os parâmetros visíveis (é isso que vai para a API).
- `normalizeValue(param, raw) → value`:
  - `int`: `Math.round(Number(raw))`; `NaN` → default; clamp `[min, max]`; se `odd` e o valor for par → `v + 1` se `v + 1 <= max`, senão `v - 1`.
  - `float`: `Number(raw)`; `NaN` → default; clamp; arredonda para o número de casas decimais de `step`.
  - `bool`: `Boolean(raw)`.
  - `select`: se não estiver em `options`, usa o default.
- `checkConstraints(process, values) → string[]` com as mensagens violadas. Só a regra `less_equal`; avalia apenas quando os dois parâmetros estão visíveis. Regra desconhecida é ignorada com `console.warn`.
- `decimalsOf(step) → number` (ex.: `0.01 → 2`, `1 → 0`).

### 5.2 `utils/format.js`

- `modeLabel(mode)`: `gray → 'Cinza 8 bits'`, `rgb → 'RGB 24 bits'`.
- `dims(w, h)`: `'512 × 384'`.
- `outputFilename(inputName, processId, outputId)`: `${inputName}_${processId}_${outputId}.png`.
- `stripExtension(filename)`.
- `formatNumber(value)`: inteiros sem casas decimais; floats com até 2 casas, separador decimal **vírgula** (`toLocaleString('pt-BR')`).

### 5.3 `utils/dataUrl.js`

- `dataUrlToBlob(dataUrl) → Blob` (decodifica base64 com `atob`).
- `dataUrlToFile(dataUrl, filename) → File` (`type: 'image/png'`).

### 5.4 `utils/download.js`

- `downloadDataUrl(dataUrl, filename)`: cria um `<a download>`, clica e remove.

### 5.5 `utils/messages.js`

`friendlyMessage(error)`, com prioridade sobre `error.message` nestes códigos:

| `code` | Mensagem |
|---|---|
| `not_implemented` | "Processo ainda não implementado no backend." |
| `network_error` | (usa a mensagem do `ApiError`) |
| `unsupported_mode` | "Este processo não está disponível para o tipo da imagem atual." |
| outros | `error.message` (vem em português do backend); se vazio, "Ocorreu um erro inesperado." |

Para `processing_error` e `invalid_output`, mostre também `error.message` completo (ajuda a depurar os handlers do grupo) num toast de duração maior (10 s).

## 6. Componentes — comportamento detalhado

### 6.1 `App.jsx` — layout

CSS Grid:

```
grid-template-columns: 240px 1fr;
grid-template-rows: 56px 1fr;
grid-template-areas: "top top" "side main";
height: 100vh;
```

- `main` tem rolagem vertical própria e, dentro, uma grade: linha 1 = `InputPanel` | `OutputPanel` (50/50, altura `min(55vh, 560px)`), linha 2 = `ParamsPanel`, linha 3 = `AccessoryPanel`. Espaçamento `var(--space-4)`.
- `< 1024px`: entrada e saída empilhadas. A barra lateral continua visível (pode encolher para 200 px).
- Se `catalogStatus === 'loading'`, mostre um spinner central; se `'error'`, mostre `CatalogError` com "Tentar novamente", que chama `retry()` de `useCatalog`.

### 6.2 `FileMenu`

À esquerda, botões na ordem:

1. **Abrir PNG** — `<input type="file" accept="image/png,.png" hidden>`, acionado pelo botão. Atalho `Ctrl/Cmd+O`.
2. **Salvar resultado** — botão dividido (`SaveMenu`): clique principal baixa a saída `main` ativa; a seta ▾ abre um menu com **todas** as saídas (`main` e `aux`), mostrando `label` e o papel ("principal"/"acessória"). Fecha com `Esc` ou clique fora. Desabilitado sem `result`. Atalho `Ctrl/Cmd+S` (com `preventDefault`). Após salvar, mostre o toast de sucesso "Imagem salva: {arquivo}".
3. **Usar como entrada** — desabilitado sem `result`. Converte a saída `main` ativa com `dataUrlToFile(img, outputFilename(...))` e chama `openFile(file, { asOriginal: false })`; o `name` da nova entrada é o nome do arquivo sem extensão.
4. **Restaurar original** — desabilitado se `!original || input === original`.

À direita: `filename · Cinza 8 bits · 512 × 384` (ou "Nenhuma imagem carregada") e o selo "Modo simulado" quando `USE_MOCK`.

### 6.3 `ProcessSidebar`

- Título "Processos". Categorias na ordem de `catalog.categories`, cada uma num cabeçalho recolhível (botão com `aria-expanded`), **todas abertas** por padrão.
- Itens na ordem do catálogo. Estados:
  - **habilitado:** clicável; destaque quando selecionado (`aria-current="true"`, barra de cor de destaque à esquerda);
  - **desabilitado** (sem imagem, ou `!process.modes.includes(input.mode)`): opacidade 0,45, `cursor: not-allowed`, `aria-disabled="true"`, sem seleção. Tooltip (`title`): sem imagem → "Abra uma imagem"; só `gray` → "Disponível apenas para imagens em escala de cinza"; só `rgb` → "Disponível apenas para imagens coloridas (RGB)".
  - `implemented === false` → selo pequeno "não implementado" ao lado do nome (não desabilita).
- O item é um `<button>`, para funcionar com o teclado.

### 6.4 `ImagePanel` (genérico)

Props: `title`, `src`, `alt`, `badge` (texto), `emptyContent` (nó), `loading` (bool), `onImageClick`, `headerExtra` (nó, ex.: abas).

- Cabeçalho com o título à esquerda e o selo à direita (`Cinza 8 bits · 512 × 384`).
- Corpo com fundo xadrez discreto (CSS `conic-gradient`), imagem com `object-fit: contain`, `max-width/height: 100%`, `image-rendering: auto`. Clicar abre o modal (cursor `zoom-in`).
- `loading` → sobreposição semitransparente com spinner e "Processando…".

### 6.5 `InputPanel`

- `ImagePanel` com o título "Imagem de entrada".
- **Arrastar e soltar** em todo o painel: em `dragenter`/`dragover`, destaca a borda tracejada com a cor de destaque ("Solte o PNG aqui"); em `drop`, pega o primeiro arquivo.
- Estado vazio: ícone, "Arraste um PNG aqui ou" + botão "Abrir PNG".
- Validação antes de chamar a API: se não for PNG (MIME `image/png` ou extensão `.png`), mostre o toast "Selecione um arquivo PNG." e não chame a API.
- `status === 'inspecting'` → `loading`.

### 6.6 `OutputPanel`

- Título "Imagem de saída". Com mais de uma saída `main`, mostra abas (`role="tablist"`, botões `role="tab"`, `aria-selected`) com o `label` de cada uma; troca com clique e com as setas ←/→.
- Selo: modo e dimensões da saída ativa.
- Estado vazio: "Selecione um processo e clique em Aplicar para ver o resultado."
- `status === 'processing'` → `loading` (mantém o resultado anterior por baixo, se houver).

### 6.7 `ParamsPanel`

- Sem processo selecionado: "Selecione um processo na barra lateral."
- Cabeçalho: nome do processo, `description` abaixo em texto secundário, selo "não implementado" se for o caso. À direita: **Restaurar padrões** (secundário) e **Aplicar ▶** (primário, mostra o atalho `Ctrl+Enter`/`⌘+Enter` conforme a plataforma).
- **Aplicar** desabilitado se: não houver imagem, o processo estiver desabilitado para o modo, `status !== 'idle'` ou houver constraints violadas.
- Processo sem parâmetros: "Este processo não possui parâmetros."
- Campos em grade responsiva (`repeat(auto-fill, minmax(280px, 1fr))`), só os visíveis (`isVisible`).
- Mensagens de constraint violada abaixo dos campos, em vermelho, com `role="alert"`.

### 6.8 `ParamField`

Rótulo + ⓘ (se houver `help`: botão com `title` e `aria-label` contendo o texto da ajuda; mostra um popover simples ao focar/passar o mouse).

| `type` | Controle |
|---|---|
| `int` / `float` | `<input type="range">` (min, max, step) + `<input type="number">` (largura ~90 px), sincronizados. O slider atualiza na hora (já normalizado). O campo numérico guarda o texto local enquanto se digita e só faz o commit (normaliza e despacha `SET_PARAM`) no `blur` ou no `Enter`; se o valor for inválido, volta ao último válido. Float exibe as casas de `decimalsOf(step)`. Para `odd: true`, o step do slider é 2 (já vem no catálogo). Mostra min e max em texto pequeno abaixo do slider |
| `bool` | `Toggle`: `<button role="switch" aria-checked>` com o texto "Sim"/"Não" |
| `select` | ≤ 3 opções → `SegmentedControl` (botões em grupo, `role="radiogroup"`, cada um `role="radio"`); > 3 → `<select>` |

Todo controle tem um `id` estável (`param-${processId}-${paramId}`) ligado ao `<label htmlFor>`.

### 6.9 `AccessoryPanel`

Título "Dados / Imagens acessórias". Com `result`, mostra as seções na ordem, **só as que tiverem conteúdo**:

1. **Histogramas:** grade com um `HistogramChart` por histograma (título = `label`).
2. **Imagens acessórias:** miniaturas (altura 160 px, `object-fit: contain`, fundo xadrez) com o `label` embaixo; clicar abre o modal.
3. **Métricas:** tabela `MetricsTable` com duas colunas (Métrica | Valor), valor via `formatNumber` + `unit`.

Sem `result`: "Os dados acessórios do processo aparecerão aqui." Com `result`, mas sem histogramas nem `aux`: mostra "Sem dados acessórios para este processo" e, abaixo, a tabela de métricas (sempre existe o tempo).

### 6.10 `HistogramChart`

Props: `values` (256 inteiros), `channel`, `label`.

- SVG responsivo: `viewBox="0 0 560 220"`, `width="100%"`. Área de plotagem com margens (esq. 44, dir. 12, sup. 12, inf. 28).
- 256 `<rect>` de largura igual; altura proporcional a `values[i] / max(values)` (se `max === 0`, todas as barras com altura 0).
- Cor por canal: `gray → var(--hist-gray)`, `r → var(--hist-r)`, `g → var(--hist-g)`, `b → var(--hist-b)`.
- Eixo X com marcas em 0, 64, 128, 192 e 255; eixo Y com 0 e o máximo (formatado, ex.: `12,3 mil` usando `Intl.NumberFormat('pt-BR', { notation: 'compact' })`).
- Hover: retângulo invisível por intensidade (ou cálculo pela posição do mouse) com tooltip "Intensidade {i}: {n} pixels" e a barra destacada.
- `role="img"` e `aria-label` com o `label`.
- Memoize com `React.memo`.

### 6.11 `ImageModal`

- Abre com `{ src, title, width, height }`. Renderizado via portal (`createPortal` em `document.body`).
- Fundo escuro (`rgba(0,0,0,.8)`); conteúdo com a imagem em **tamanho real** (sem redimensionar), rolagem em ambos os eixos. Cabeçalho com o título, as dimensões e os botões **Ajustar à tela / Tamanho real** (alterna) e **Fechar ✕**.
- Fecha com `Esc`, clique no fundo ou no botão. Foco vai para o botão Fechar ao abrir e volta ao elemento de origem ao fechar. Bloqueia a rolagem do `body` enquanto estiver aberto.
- `image-rendering: pixelated` no modo tamanho real (útil para ver ruído).

### 6.12 `ToastContainer`

- Canto inferior direito, empilhados. `role="status"` (info/sucesso) ou `role="alert"` (erro). Fecham sozinhos em 5 s (erros de `processing_error`/`invalid_output`: 10 s) e têm botão ✕.

### 6.13 Atalhos (`useKeyboardShortcuts`)

| Atalho | Ação | Condição |
|---|---|---|
| `Ctrl/Cmd+Enter` | Aplicar | botão Aplicar habilitado |
| `Ctrl/Cmd+O` | Abrir PNG | sempre |
| `Ctrl/Cmd+S` | Salvar a saída ativa | há resultado |
| `Esc` | fecha o modal ou o menu | — |

## 7. Fluxos (hooks)

**`useCatalog`**: ao montar → `CATALOG_LOADING` → `api.getProcesses()` → `CATALOG_LOADED`; em erro → `CATALOG_ERROR` com `friendlyMessage`. Expõe `retry`.

**`openFile(file, { asOriginal })`** (`useImageLoader`):
1. valida que é PNG (ver §6.5);
2. `INSPECT_START`;
3. `info = await api.inspectImage(file)`;
4. monta o `ImageRef` (`url = URL.createObjectURL(file)`, `name = stripExtension(file.name)`);
5. `IMAGE_LOADED`;
6. em erro: `INSPECT_ERROR` + toast `friendlyMessage(err)`.

Abrir pelo botão ou por arrastar → `asOriginal: true`. "Usar como entrada" → `asOriginal: false`.

**`run()`** (`useProcessRunner`):
1. `PROCESS_START` (guarda o `requestId` resultante = anterior + 1);
2. `params = visibleParams(process, paramsByProcess[id])`;
3. `res = await api.runProcess(id, input.file, params)`;
4. `PROCESS_SUCCESS({ requestId, result: { ...res, inputName: input.name } })`;
5. em erro: `PROCESS_ERROR({ requestId })` + toast (só se o `requestId` ainda for o atual).

## 8. Visual — `styles/tokens.css`

Tema claro, neutro, com uma cor de destaque. Valores de referência (pode ajustar mantendo o contraste AA):

```css
:root {
  --bg: #f4f5f7; --surface: #ffffff; --surface-2: #f9fafb; --border: #e3e5e8;
  --text: #1c1f23; --text-2: #5b6370; --text-disabled: #a0a6b0;
  --accent: #2f6fed; --accent-hover: #2358c4; --accent-soft: #e8f0fe;
  --danger: #d93025; --success: #188038; --warning: #b06000;
  --hist-gray: #5b6370; --hist-r: #d93025; --hist-g: #188038; --hist-b: #2f6fed;
  --checker-a: #eceef1; --checker-b: #f8f9fa;
  --radius: 8px; --radius-sm: 6px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; --font-mono: ui-monospace, Menlo, monospace;
  --shadow: 0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.1);
}
```

- Painéis: `--surface`, borda `1px solid var(--border)`, `--radius`, `--shadow`, título em 13 px semibold maiúsculo com `letter-spacing: .04em` e cor `--text-2`.
- Foco visível em todos os elementos interativos: `outline: 2px solid var(--accent); outline-offset: 2px` (via `:focus-visible`).
- Botão primário: fundo `--accent`, texto branco; secundário: `--surface` com borda; desabilitado: `--text-disabled`, `cursor: not-allowed`.
- Números (valores de parâmetros e métricas) em `--font-mono` com `font-variant-numeric: tabular-nums`.
- Tema escuro não é obrigatório.

## 9. Critérios de aceite (verificar antes de reportar)

Com `VITE_USE_MOCK=true npm run dev`:

1. Abrir um PNG colorido pelo botão e outro por arrastar e soltar; a barra superior mostra o nome, "RGB 24 bits" e as dimensões.
2. Com RGB, "Equalização de histograma" fica desabilitada, com tooltip; com um PNG cinza, RGB/HSV ficam desabilitados e a equalização fica habilitada.
3. Selecionar processos mostra os parâmetros corretos; slider e campo numérico sincronizados; `kernel_size` só aceita ímpares; digitar 4 vira 5; digitar 999 vira o máximo.
4. Ruído sal/pimenta: as probabilidades só aparecem com "Sal e pimenta", e só os parâmetros visíveis vão para a API.
5. Fatiamento com A > B: mensagem de erro e Aplicar desabilitado.
6. Aplicar mostra o spinner, depois a saída; RGB/HSV mostram 3 abas; equalização mostra 2 histogramas com tooltip; Laplaciano mostra a imagem `aux`; métricas sempre mostram o tempo.
7. Sobel → toast "Processo ainda não implementado no backend." e selo "não implementado" no item.
8. Salvar baixa `{nome}_{processo}_{saida}.png`; o menu permite salvar as saídas `aux`.
9. "Usar como entrada" num canal R torna a entrada cinza (processos se reabilitam conforme o modo) e "Restaurar original" volta para a imagem RGB.
10. Modal: abre com clique em qualquer imagem, mostra o tamanho real, fecha com `Esc`.
11. Atalhos `Ctrl/Cmd+Enter`, `Ctrl/Cmd+O` e `Ctrl/Cmd+S` funcionam.
12. Arquivo não PNG → toast "Selecione um arquivo PNG.".
13. Com o mock desligado e sem backend: tela de erro do catálogo com "Tentar novamente".

Além disso: `npm run build` e `npm run lint` passam **sem erros nem avisos**; nenhum erro ou aviso de React no console (keys, act, etc.).

## 10. Relatório final

Ao terminar, reporte ao líder: o que foi feito, como rodar, o resultado de cada critério de aceite (✅/❌ com observação), desvios desta especificação (com o motivo) e pendências.
