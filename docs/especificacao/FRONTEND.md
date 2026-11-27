# Especificação do Frontend

**Stack:** React 18 + Vite, JavaScript (sem TypeScript), CSS puro com variáveis (CSS Modules ou um arquivo por componente). **Sem bibliotecas de UI ou gráficos**: o histograma é um componente SVG próprio. Dependências além de `react`/`react-dom` precisam de justificativa.

## 1. Layout (Figura 1 do PDF)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Opções de arquivo]  Abrir PNG │ Salvar resultado │ Usar como entrada │ Restaurar original    nome.png · RGB · 512×384 │
├────────────┬─────────────────────────────────────────────────────────┤
│            │ ┌───────── Imagem de entrada ─────┐ ┌──── Imagem de saída ───────┐ │
│  Seleção   │ │                                 │ │ [R] [G] [B]  (abas se >1)   │ │
│     de     │ │                                 │ │                             │ │
│ processos  │ └─────────────────────────────────┘ └─────────────────────────────┘ │
│            │ ┌──────── Parâmetros do processo selecionado ──────────────────────┐ │
│ ▸ Cor      │ │ Filtro de média gaussiana  ⓘ    [Restaurar padrões] [Aplicar ▶] │ │
│ ▸ Intens.  │ │ Tamanho da janela ──●──── [5]   Desvio padrão σ ─●───── [1.0]   │ │
│ ▸ Espacial │ └──────────────────────────────────────────────────────────────────┘ │
│ ▸ Freq.    │ ┌──────── Dados / Imagens acessórias ─────────────────────────────┐ │
│ ▸ Ruído    │ │ [histogramas]  [imagens aux]  [métricas: tempo, …]              │ │
│            │ └──────────────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────┘
```

- CSS Grid: barra superior fixa; barra lateral com ~240 px e rolagem própria; área principal com entrada e saída lado a lado (50/50), parâmetros embaixo e dados acessórios por último.
- Pensado primeiro para desktop (mínimo 1280×720). Em telas estreitas (< 1024 px), entrada e saída ficam empilhadas.
- As imagens usam `object-fit: contain` dentro do painel, com fundo xadrez discreto. Clicar na imagem abre um **modal em tamanho real** com rolagem (útil para ver ruído e detalhes de filtros).
- Visual limpo e neutro, com uma cor de destaque. Estados de foco visíveis.

## 2. Componentes

```
src/
├── main.jsx
├── App.jsx                     # layout + estado global (useReducer)
├── api/
│   ├── client.js               # getProcesses, inspectImage, runProcess (fetch)
│   ├── mock.js                 # mesma interface, sem backend
│   └── index.js                # exporta client ou mock conforme VITE_USE_MOCK
├── state/
│   └── appReducer.js           # ações e estado (ver §3)
├── components/
│   ├── FileMenu/               # barra superior: ações de arquivo + informações da imagem
│   ├── ProcessSidebar/         # categorias recolhíveis, itens habilitados/desabilitados
│   ├── ImagePanel/             # painel genérico: título, imagem, selo (modo, dimensões), vazio, carregando
│   ├── OutputPanel/            # ImagePanel + abas quando há várias saídas main
│   ├── ParamsPanel/            # formulário dinâmico + Aplicar/Restaurar
│   │   └── ParamField.jsx      # int/float → slider + campo numérico; bool → toggle; select → botões segmentados (≤3) ou <select>
│   ├── AccessoryPanel/         # histogramas, imagens aux (miniaturas clicáveis), tabela de métricas
│   ├── HistogramChart/         # SVG, 256 barras, eixos 0–255, cor por canal, tooltip com o valor
│   ├── ImageModal/             # visualização em tamanho real
│   └── Toast/                  # mensagens de erro/sucesso
├── utils/
│   ├── download.js             # salvar data URL como arquivo
│   ├── dataUrl.js              # data URL ⇄ Blob/File
│   └── params.js               # defaults, visible_if, odd, clamp, constraints
└── styles/
    └── tokens.css              # cores, espaçamentos, tipografia
```

## 3. Estado da aplicação

```js
{
  catalog: { categories: [], processes: [] } | null,
  catalogStatus: 'loading' | 'ready' | 'error',
  input: { file: File, url: string, name: string, mode: 'gray'|'rgb', width, height } | null,
  original: /* mesmo formato: a primeira imagem aberta, para "Restaurar original" */ null,
  selectedProcessId: string | null,
  paramsByProcess: { [processId]: { [paramId]: value } }, // guarda os valores de cada processo
  result: /* resposta do POST /api/process (API.md) */ null,
  activeOutputId: string | null,          // aba selecionada no OutputPanel
  status: 'idle' | 'inspecting' | 'processing',
  error: { code, message } | null
}
```

## 4. Interações (todas obrigatórias)

| # | Interação | Comportamento |
|---|---|---|
| I1 | **Abrir PNG** | Botão ou **arrastar e soltar** na área de entrada. Aceita só `.png` (`accept="image/png"`). Chama `inspectImage`; guarda o `mode`; define `input` e `original`; limpa o `result`. Mostra um erro se não for suportado |
| I2 | **Habilitar por modo** | Processos cujo `modes` não contém `input.mode` ficam **desabilitados** (cinza, sem clique) com tooltip: *"Disponível apenas para imagens em escala de cinza"* (ou RGB). Sem imagem, todos ficam desabilitados com *"Abra uma imagem"*. Se o processo selecionado ficar inválido após trocar a imagem, a seleção é limpa |
| I3 | **Selecionar processo** | Destaca o item; o ParamsPanel mostra nome, descrição, os campos (com os valores guardados em `paramsByProcess` ou os defaults) e a ajuda (ⓘ) |
| I4 | **Editar parâmetros** | Slider e campo numérico sincronizados; clamp em min/max; `odd` arredonda para o ímpar mais próximo; `visible_if` mostra/esconde o campo; constraints violadas desabilitam "Aplicar" e mostram a mensagem |
| I5 | **Restaurar padrões** | Volta os parâmetros do processo atual aos defaults |
| I6 | **Aplicar** | Envia `runProcess(id, input.file, params visíveis)`. Durante a execução: spinner sobre a saída e botão desabilitado. Também dispara com `Ctrl/Cmd+Enter` |
| I7 | **Ver resultado** | Saídas `main` vão para o OutputPanel (abas com `label` se houver mais de uma); saídas `aux`, histogramas e métricas vão para o AccessoryPanel. Painel vazio mostra *"Sem dados acessórios para este processo"* |
| I8 | **Salvar resultado** | Baixa a saída `main` ativa (nome em API.md). Menu suspenso permite escolher qualquer saída, inclusive `aux`. Desabilitado sem resultado |
| I9 | **Usar resultado como entrada** | Converte a saída ativa em `File`, chama `inspectImage` de novo (o modo pode mudar, ex.: RGB → canal R vira cinza), define como `input`, limpa o `result` e **mantém o `original`** |
| I10 | **Restaurar original** | `input = original`; limpa o `result` |
| I11 | **Erros** | Toast com `error.message`. Para `501 not_implemented`, mostrar uma mensagem amigável: *"Processo ainda não implementado no backend"*. Para catálogo indisponível, uma tela de erro com "Tentar novamente" |
| I12 | **Ampliar imagem** | Clicar em qualquer imagem (entrada, saída, aux) abre o ImageModal. `Esc` fecha |
| I13 | **Informações** | Barra superior: nome, modo (`Cinza 8 bits` / `RGB 24 bits`), dimensões. Métricas sempre incluem o tempo de processamento |

## 5. Camada de API e mock

`api/index.js` exporta a mesma interface, real ou mock:

```js
getProcesses(): Promise<Catalog>
inspectImage(file: File): Promise<{ mode, width, height, source_mode, filename }>
runProcess(processId: string, file: File, params: object): Promise<ProcessResult>
// Em erro HTTP: lança ApiError { status, code, message, details }
```

**Mock** (`VITE_USE_MOCK=true`), para desenvolver sem o backend:
- `getProcesses` importa `../../shared/processes.json` (Vite permite importar JSON; configurar `server.fs.allow` para a raiz do repositório) e marca `implemented: true`.
- `inspectImage` decodifica no canvas e trata como `gray` se R = G = B em todos os pixels (aproximação aceitável só no mock).
- `runProcess` espera ~400 ms e devolve a imagem de entrada como saída `main`, com estes extras:
  - `rgb_split` / `hsv_split`: 3 saídas `main` (cada canal extraído no canvas);
  - `histogram_equalization`: histogramas `before`/`after` calculados no canvas;
  - `laplacian_sharpen`: uma saída `aux` `laplacian` (cópia da entrada);
  - `sobel`: devolve um `ApiError` `501 not_implemented`, para testar o tratamento de erro;
  - sempre a métrica "Tempo de processamento".

## 6. Configuração do Vite

- `server.proxy`: `/api` → `http://127.0.0.1:8000`.
- `build.outDir`: `dist` (servido pelo FastAPI em produção, na raiz `/`).
- Scripts: `dev`, `build`, `preview`, `lint` (ESLint padrão do Vite).

## 7. Fora do escopo do frontend
- Qualquer algoritmo de PDI (fora o que o mock precisa para simular).
- Desfazer/refazer, edição em lote, autenticação.
