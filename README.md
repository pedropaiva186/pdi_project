# Processador de Imagens — PDI

Aplicação web para processamento digital de imagens em PNG, desenvolvida para a
disciplina de **Processamento Digital de Imagens (PDI)** da **UFPB**. O usuário envia
uma imagem, escolhe um processo (limiarização, filtros espaciais, filtragem no
domínio da frequência, ruído, etc.), ajusta os parâmetros e visualiza o resultado.

A aplicação tem duas partes:

- **Backend** em Python (FastAPI), que valida as entradas, executa os processos e
  devolve o resultado em JSON.
- **Frontend** em React + Vite, compilado para arquivos estáticos e servido pelo
  próprio backend.

## Requisitos

- **Python 3.11+** (testado com 3.14).
- **Node.js 20+**, necessário apenas para compilar a interface. Se o build do
  frontend já existir (`frontend/dist/`), o Node não é exigido para executar.

## Execução rápida (apresentação)

```bash
# 1. Criar e ativar o ambiente virtual (na raiz do projeto)
python3 -m venv backend/.venv
source backend/.venv/bin/activate          # Windows: backend\.venv\Scripts\activate

# 2. Instalar as dependências do backend
pip install -r backend/requirements.txt

# 3. Subir tudo (compila o frontend se necessário e inicia o servidor)
python run.py
```

Abra **http://127.0.0.1:8000** no navegador (o `python run.py` tenta abrir a página
automaticamente).

Opções do `run.py`:

| Opção | Efeito |
|---|---|
| `--host 127.0.0.1` / `--port 8000` | endereço e porta do servidor |
| `--rebuild` | força a recompilação do frontend |
| `--no-build` | não compila o frontend (serve o que já está em `frontend/dist/`) |
| `--no-browser` | não abre o navegador |
| `--dev` | Uvicorn com recarga automática (ver *Desenvolvimento*) |

Se o frontend não estiver compilado e não houver `npm`, o servidor sobe só com a
API; em `/` aparece uma página com a instrução para compilar a interface.

A documentação interativa da API fica em **http://127.0.0.1:8000/docs**.

## Desenvolvimento

Com dois terminais (o backend na porta 8000 e o Vite na porta 5173, que encaminha
`/api` para o backend):

```bash
# Terminal 1 — backend com recarga automática
python backend/run.py

# Terminal 2 — frontend com hot reload
cd frontend
npm install
npm run dev
```

A interface de desenvolvimento fica em **http://localhost:5173**.

Para trabalhar no frontend sem o backend, use o mock de dados:

```bash
cd frontend
VITE_USE_MOCK=true npm run dev
```

## Testes

```bash
pip install -r backend/requirements-dev.txt
cd backend
pytest
```

Os testes geram as imagens em memória e usam o catálogo real
(`shared/processes.json`); nenhum arquivo binário é gravado no repositório.

## Implementando os processos

O backend já está pronto para receber as implementações. Cada processo do catálogo
tem um **handler** em `backend/app/processing/` (módulos `color.py`, `intensity.py`,
`spatial.py`, `frequency.py` e `noise.py`), registrado em `registry.py`. Hoje todos
são **stubs**: levantam `NotImplementedError`, e a API responde **`501 not_implemented`**.

O contrato do handler está documentado em `backend/app/processing/types.py`:

- Entrada: `(array, params)`, em que `array` é `uint8` com forma `(H, W)` (tons de
  cinza) ou `(H, W, 3)` (RGB), conforme `modes` do processo no catálogo.
- Saída: um `ProcessResult` com as imagens (`OutputImage`, `role="main"` ou `"aux"`),
  histogramas e métricas. **Toda imagem de saída deve ser `uint8`**; use `np.clip`
  e `astype(np.uint8)` ou uma normalização explícita. Saídas inválidas geram
  `500 invalid_output` com a mensagem de correção.
- O status de implementação é **detectado automaticamente**: quando um handler deixa
  de levantar `NotImplementedError`, o processo passa a aparecer como
  `implemented: true` em `GET /api/processes`, e a interface o libera.

Cada stub traz em sua docstring a entrada aceita, os parâmetros, as saídas esperadas
e dicas teóricas (com referência a Gonzalez & Woods).

## Estrutura do projeto

```
run.py                  # execução para apresentação (build do frontend + servidor)
README.md
backend/                # API FastAPI
  app/
    main.py             # fábrica do app, rotas e frontend estático
    core/               # catálogo, validação de parâmetros, erros
    services/           # leitura de PNG, uploads, runner de processos
    processing/         # ÁREA DOS PROCESSOS (handlers e stubs)
    api/routes/         # endpoints HTTP
  tests/                # pytest
frontend/               # interface React + Vite
shared/
  processes.json        # catálogo dos processos (fonte única para front e back)
docs/especificacao/     # especificações de implementação (ver abaixo)
```

O contrato HTTP está em `docs/especificacao/API.md`. As especificações de implementação
estão em `docs/especificacao/` (índice em [docs/especificacao/README.md](docs/especificacao/README.md)),
e o enunciado do projeto está em [docs/descricao_projeto_pdi.pdf](docs/descricao_projeto_pdi.pdf).
