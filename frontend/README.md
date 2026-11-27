# Frontend — Processador de Imagens (PDI / UFPB)

Interface React + Vite que conversa com o backend FastAPI em `/api`. Também
funciona **sem backend**, usando uma camada de mock no navegador.

## Requisitos

- Node.js 20 ou superior (testado com Node 26 / npm 11).

## Como rodar

```bash
cd frontend
npm install
```

### Com o mock (sem backend)

```bash
VITE_USE_MOCK=true npm run dev
```

Abre em <http://localhost:5173>. O mock importa o catálogo de
`../shared/processes.json`, simula a inspeção da imagem no canvas e devolve
saídas de exemplo. O processo `sobel` responde `501 not_implemented` para
exercitar o tratamento de erro.

### Com a API real

```bash
npm run dev
```

O Vite redireciona `/api` para `http://127.0.0.1:8000`, então suba o backend
antes. Para usar outra URL, ajuste o proxy em `vite.config.js`.

### Build de produção

```bash
npm run build      # gera dist/ (servido pelo FastAPI na raiz)
npm run preview    # serve o build localmente
```

### Lint

```bash
npm run lint
```

## Estrutura

```
src/
├── api/          client (fetch), mock (canvas) e seleção por VITE_USE_MOCK
├── state/        reducer da aplicação + constantes das ações
├── hooks/        catálogo, carregamento de imagem, execução e atalhos
├── components/   barra de arquivo, processos, painéis, modal e toasts
├── utils/        parâmetros, formatação, data URL, download e mensagens
└── styles/       tokens (cores/espaçamento) e estilos globais
```

O catálogo é a **fonte única de verdade**: formulários, habilitacão por modo e
validação de restrições são derivados de `shared/processes.json`. Mudou um
parâmetro? Altere apenas o JSON.

## Atalhos

| Atalho | Ação |
|---|---|
| `Ctrl/Cmd + Enter` | Aplicar o processo selecionado |
| `Ctrl/Cmd + O` | Abrir um PNG |
| `Ctrl/Cmd + S` | Salvar a saída principal ativa |
| `Esc` | Fechar o modal de imagem |
