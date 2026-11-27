# Especificação do Projeto — Processador de Imagens (PDI / UFPB)

Documentação de referência para o desenvolvimento. Requisitos originais: [`../descricao_projeto_pdi.pdf`](../descricao_projeto_pdi.pdf).

| Documento | Conteúdo |
|---|---|
| [README.md](README.md) | Visão geral, plano de execução, arquitetura, estrutura de pastas, execução |
| [API.md](API.md) | Contrato HTTP entre frontend e backend |
| [PROCESSOS.md](PROCESSOS.md) | Catálogo dos processos: parâmetros, tipos de imagem, saídas esperadas |
| [FRONTEND.md](FRONTEND.md) | Layout, componentes, estado e interações da interface |
| [BACKEND.md](BACKEND.md) | Estrutura do backend, contrato dos handlers de PDI e regra dos stubs |
| [ETAPA2_FRONTEND.md](ETAPA2_FRONTEND.md) | Especificação detalhada de implementação do frontend (tarefa da Etapa 2) |
| [ETAPA3_BACKEND.md](ETAPA3_BACKEND.md) | Especificação detalhada de implementação do esqueleto do backend (tarefa da Etapa 3) |
| [`/shared/processes.json`](../../shared/processes.json) | Catálogo de processos em JSON (fonte única de verdade) |

---

## 1. Plano de execução

| Etapa | Escopo | Entregável | Responsável |
|---|---|---|---|
| **1. Arquitetura** | Especificação do sistema e do contrato front/back | Esta pasta + `shared/processes.json` | Claude (concluída) |
| **2. Frontend** | Todas as telas, componentes e interações, seguindo o layout da Figura 1 do PDF. Inclui uma **camada de mock** para funcionar sem o backend | `frontend/` rodando com `npm run dev` (mock ou API real) | Agente delegado |
| **3. Esqueleto do backend** | FastAPI com todos os endpoints, validação, I/O de imagem e tratamento de erros. **Os handlers de PDI ficam como stubs** (`NotImplementedError`) | `backend/` rodando, com endpoints de processo retornando `501` até serem implementados | Claude |
| **4. Implementação de PDI** | Escrever os algoritmos nos stubs de `backend/app/processing/` | Processos funcionando | Grupo (manual) |

Critérios de pronto:
- **Etapa 2:** com o mock, dá para abrir um PNG, ver se ele é cinza ou RGB, ver os processos habilitados/desabilitados, ajustar parâmetros, aplicar, ver as saídas e os dados acessórios, salvar, encadear o resultado como nova entrada e ver os erros (incluindo o `501`).
- **Etapa 3:** o frontend real (sem mock) conversa com o backend; `GET /api/processes` devolve o catálogo; todo processo retorna `501 not_implemented`; os testes de infraestrutura passam.

---

## 2. Arquitetura

```
┌──────────────────────── Navegador ────────────────────────┐
│ React (Vite)                                               │
│  ├─ UI: menu de arquivo, processos, entrada, saída,        │
│  │      parâmetros, dados acessórios                       │
│  └─ api/client.js ──(fetch, multipart)──┐                  │
└─────────────────────────────────────────┼──────────────────┘
                                          ▼  /api/*
┌──────────────────────── FastAPI ──────────────────────────┐
│ api/routes      → recebe o arquivo e os parâmetros         │
│ core/catalog    → carrega shared/processes.json            │
│ core/validation → valida/normaliza parâmetros e o modo     │
│ services/image_io → PNG ⇄ numpy.ndarray (uint8)            │
│ processing/*    → handlers de PDI  ◄── IMPLEMENTADOS PELO  │
│                                       GRUPO (stubs)        │
└────────────────────────────────────────────────────────────┘
```

### Decisões de arquitetura

| # | Decisão | Motivo |
|---|---|---|
| D1 | **API sem estado:** cada requisição envia o PNG + parâmetros | Não precisa de armazenamento nem sessão; as imagens são pequenas; mais fácil de depurar |
| D2 | **Catálogo declarativo** em `shared/processes.json` | O frontend monta a lista e os formulários de parâmetros sozinho; o backend valida com o mesmo arquivo; adicionar ou ajustar um parâmetro é feito em um só lugar |
| D3 | Imagens de resposta como **data URL PNG em base64** dentro do JSON | Uma resposta só traz várias imagens + histogramas + métricas; vai direto no `<img src>`; salvar é só baixar |
| D4 | **Salvar é feito no frontend** (download do data URL) | Não precisa de endpoint |
| D5 | O **modo da imagem** (cinza/RGB) é detectado pelo backend (`/api/images/inspect`) | O canvas do navegador sempre devolve RGBA e não sabe se o PNG é de 8 bits em escala de cinza |
| D6 | Execução por **botão "Aplicar"** (sem recalcular a cada mudança de parâmetro) | Evita sobrecarregar o backend com filtros pesados (FFT, mediana adaptativa) |
| D7 | **"Usar resultado como entrada"** (encadear processos) | Permite cenários comuns da avaliação, como aplicar ruído e depois um filtro de mediana |
| D8 | Infraestrutura usa **Pillow só para I/O**. Os algoritmos usam NumPy, a critério do grupo | Os algoritmos ficam explícitos e explicáveis nas perguntas individuais |
| D9 | Em produção, o FastAPI **serve o build do React** (`frontend/dist`) | Um comando só para executar, cumprindo o requisito de "fácil execução" |

---

## 3. Estrutura do repositório

```
pdi_project/
├── docs/
│   ├── descricao_projeto_pdi.pdf
│   └── especificacao/          ← esta documentação
├── shared/
│   └── processes.json          ← catálogo de processos (front + back)
├── frontend/                   ← Etapa 2 (React + Vite)
├── backend/                    ← Etapa 3 (FastAPI)
│   └── app/processing/         ← Etapa 4 (algoritmos do grupo)
├── run.py                      ← build do front (se preciso) + sobe o backend
└── README.md                   ← instruções de execução para o avaliador
```

---

## 4. Execução

Requisitos: **Python 3.11+** e **Node.js 20+**.

**Desenvolvimento** (dois terminais):
```bash
# backend → http://127.0.0.1:8000
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python run.py

# frontend → http://localhost:5173 (o Vite redireciona /api para :8000)
cd frontend && npm install && npm run dev
# sem backend: VITE_USE_MOCK=true npm run dev
```

**Apresentação/entrega** (um comando):
```bash
python run.py    # gera frontend/dist se não existir e serve tudo em http://127.0.0.1:8000
```

---

## 5. Convenções gerais

- **Imagens internas:** `numpy.ndarray` com `dtype=uint8`; cinza = `(H, W)`, RGB = `(H, W, 3)`.
- **Idioma:** a interface e as mensagens ao usuário em português; identificadores de código e IDs de processo/parâmetro em inglês `snake_case`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`…), como já é feito no repositório.
- **Aderência ao PDF:** processos, parâmetros e saídas seguem estritamente o enunciado. Ver [PROCESSOS.md](PROCESSOS.md#critério-de-aderência-ao-pdf).
