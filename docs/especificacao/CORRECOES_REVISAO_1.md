# Correções — Revisão 1 (26/11/2026)

Resultado da revisão do estado parcial das Etapas 2 e 3. Cada agente corrige **só a sua seção**, respeitando o escopo de escrita da sua especificação (ETAPA2_FRONTEND.md §0 / ETAPA3_BACKEND.md §0). Não faça commits.

**Já resolvido pelo líder:** em `shared/processes.json`, no `salt_pepper_noise`, `salt_probability` e `pepper_probability` passaram a ter `step: 0.005` (antes `0.01`), para o default `0.025` ser exibido sem arredondamento. Nenhuma mudança é necessária no frontend por causa disso.

---

## BACKEND (OpenCode #2) — siga a ordem

| # | Sev. | Onde | Problema | Correção |
|---|---|---|---|---|
| B1 | **alta** | `backend/app/main.py` (catch-all `api_not_found`) | O 405 nunca sai, sempre 404. Com FastAPI 0.165 / Starlette 1.10, o `include_router` cria `_IncludedRouter` sem `.path`, então a varredura de `app.router.routes` pula todas as rotas. `POST /api/health`, `GET /api/process/threshold` etc. devolvem 404 em vez de `405 method_not_allowed` (§3/§10.1) | Não dependa de internals do roteador: crie um `api_router = APIRouter(prefix="/api")`, faça `include_router` dos 4 routers nele e inclua-o no app. No catch-all, itere sobre `api_router.routes` (`APIRoute` com `.path` completo) usando `route.matches(scope)`: se algum der `Match.PARTIAL` → 405; senão → 404. Confirme que `GET /api/xyz` → 404 JSON e `GET /api/health` → 200 |
| B2 | média | `backend/tests/test_image_io.py` (~100-102, `test_decode_truncated_png_is_invalid`) | **Bug no teste:** `png[:-20]` só remove o IEND e um pedaço do IDAT; o Pillow ainda decodifica. O código está correto | Trunque de verdade: `png[: len(png) // 2]` e/ou `png[:-40]` → `invalid_image`. Opcional: um caso "cortado só no IEND" documentando que é aceito |
| B3 | média | `backend/tests/test_api.py` (`test_frontend_missing_returns_html`) | **Bug no teste:** falha quando `frontend/dist` existe (o build do frontend já foi gerado). O teste usa o caminho real em vez de um isolado | Crie o app com `create_app(frontend_dist=tmp_path / "nao_existe")`. Revise os outros testes que dependam do estado real de `frontend/dist` |
| B4 | média | `README.md` (raiz) | Não foi escrito | Escreva todo o conteúdo do ETAPA3 §13 |
| B5 | baixa | `backend/app/api/routes/process.py` (~43-50) | `read_upload` roda antes de `catalog.get`: id inexistente sem arquivo → 400, mas o §9 manda 404 primeiro | Chame `catalog.get(process_id)` antes de `read_upload` (ou mova a leitura para dentro do runner, depois do passo 1). Acrescente um teste |
| B6 | baixa | `backend/pytest.ini` (3-4) | O filtro de warning usa `UserWarning`, mas a categoria real é `StarletteDeprecationWarning` | Ajuste o filtro para a categoria/mensagem correta (só para avisos de terceiros) |

**Critério de pronto:** `pytest -q` 100% verde, sem avisos; curls do §14.3 + `POST /api/health` → 405 JSON; `python run.py` **sem** `--no-build` (com o build real do frontend) servindo a interface em `/`; `python run.py --dev` sobe com reload.

---

## FRONTEND (OpenCode) — siga a ordem

| # | Sev. | Onde | Problema | Correção |
|---|---|---|---|---|
| F1 | média | `frontend/src/hooks/useProcessRunner.js` (~25-33) | O ref `running` pode deixar o "Aplicar" habilitado, mas sem efeito: depois de trocar a imagem ou restaurar o original durante um processamento, `status` volta a `idle`, mas `running.current` fica `true` até a resposta antiga chegar | Remova o bloqueio por ref global; o controle fica todo por `requestId`/`status` do reducer (o botão já é desabilitado por `status !== 'idle'`) |
| F2 | baixa | `frontend/src/state/appReducer.js` (`INSPECT_START`) e `hooks/useImageLoader.js` | `INSPECT_START` não invalida o processamento em curso, e duas aberturas seguidas competem (vence a que termina por último) | `INSPECT_START` incrementa `requestId` (descarta o processamento em curso) e usa um `inspectId` próprio; `useImageLoader` só despacha `IMAGE_LOADED`/`INSPECT_ERROR` se o `inspectId` ainda for o atual |
| F3 | baixa | `App.jsx` / `InputPanel.jsx` | Soltar um PNG fora do painel faz o navegador abrir o arquivo e perder o estado | `window` com `dragover`/`drop` → `preventDefault()` (num `useEffect` no App). Opcional: aceitar o drop na janela inteira |
| F4 | baixa | `frontend/src/api/client.js` (~12-32) | Com o backend desligado, o proxy do Vite responde 500/502/503/504 sem JSON e a mensagem fica genérica ("HTTP 500") | Resposta `!ok` **sem** `error.code` no JSON e com status 500/502/503/504 → `ApiError(status, 'network_error', 'Não foi possível conectar ao servidor. Verifique se o backend está rodando.')` |
| F5 | baixa | `components/ImageModal/ImageModal.jsx` | `aria-modal="true"` sem prender o foco (o Tab sai do modal) | Prenda o foco entre os elementos focáveis do modal (Tab/Shift+Tab) |
| F6 | baixa | `components/FileMenu/SaveMenu.jsx` | O menu (`role="menu"`) não foca o primeiro item ao abrir nem navega por setas | Foque o primeiro `menuitem` ao abrir; ↑/↓ circulam; Enter/Espaço ativam; Esc fecha e devolve o foco ao botão |

**Critério de pronto:** `npm run build` e `npm run lint` sem erros nem avisos; critérios do ETAPA2 §9 reverificados; teste de fumaça **sem mock** contra o backend real (`python backend/run.py` + `npm run dev`): o catálogo carrega, `inspect` funciona e um processo stub mostra o toast de 501.
