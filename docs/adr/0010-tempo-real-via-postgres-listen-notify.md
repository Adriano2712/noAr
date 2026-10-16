# 0010 - Tempo real via Postgres LISTEN/NOTIFY + SSE

- Status: aceito
- Data: 2026-10-16

## Contexto

Faltava a última peça da visão original: o dashboard e a página de status
atualizarem sozinhos quando um monitor muda de estado, sem precisar recarregar
a página. O projeto não usa Redis nem fila externa (ver ADR 0003), então o
mecanismo de pub/sub também precisava viver só no Postgres.

## Decisão

- **Postgres `LISTEN`/`NOTIFY` como pub/sub**, não uma fila nova. O worker
  (`noar/worker/processor.py`) chama `pg_notify` só quando o estado do
  monitor realmente muda (`UNKNOWN -> UP`, `UP -> DOWN`, etc.) — não em toda
  checagem — para não gerar uma tempestade de notificações a cada ciclo.
  O payload carrega `monitor_id`, `owner_id`, `is_public` e `state`, dados
  suficientes para o consumidor filtrar sem bater no banco de novo.
- **Conexão dedicada para o LISTEN** (`noar/realtime/listener.py`), fora do
  pool do SQLAlchemy: uma conexão do pool pode ser reciclada no meio do
  caminho, o que derrubaria silenciosamente o LISTEN. Essa conexão roda num
  laço com reconexão automática (`run_listener`, iniciado no `lifespan` do
  FastAPI em `api/main.py`).
- **Fan-out em processo via `EventHub`** (`noar/realtime/hub.py`): um
  `asyncio.Queue` por assinante (SSE conectado), alimentado pela conexão de
  LISTEN. Um assinante lento tem a fila limitada (100 itens) e simplesmente
  perde eventos além disso — loga um aviso, não derruba nem bloqueia o
  publicador.
- **Dois endpoints SSE**, cada um filtrando no próprio gerador
  (`noar/api/routers/realtime.py`):
  - `GET /monitors/stream` — autenticado, todos os eventos do dono logado.
  - `GET /status/{owner_id}/stream` — público, só eventos com
    `is_public=true` daquele dono (mesma regra de opt-in da ADR 0009).
- **Token via query string (`?token=`) para o endpoint autenticado**: a API
  `EventSource` do browser não permite customizar headers, então não dá para
  mandar o JWT como `Authorization: Bearer`. A alternativa (um endpoint que
  trocasse um cookie de sessão) é mais correta para produção, mas é
  infraestrutura nova só para isso; para este projeto local, o trade-off
  aceito é token na URL — o que implica ele parar em logs de acesso e no
  histórico do browser. Documentado também no docstring de
  `get_current_user_from_query_token` em `api/dependencies.py`.
- **A dependência de autenticação do SSE abre sua própria sessão de banco**,
  em vez de usar `Depends(get_session)` como as outras rotas. Para uma
  resposta de streaming, "a requisição" só termina quando o cliente
  desconecta — então uma sessão `Depends` ficaria presa (`idle in
  transaction`) pela duração inteira da conexão SSE, por conta de uma única
  consulta que só precisa rodar uma vez, no início.
- **Escopo: só mudança de estado, sem gráfico ao vivo.** O SSE empurra
  "monitor X mudou para down", e o cliente reage recarregando os dados
  daquele monitor (ou atualizando o campo `state` na lista, no caso do
  dashboard e da página de status). Atualizar o gráfico de tempo de resposta
  em tempo real exigiria transmitir cada checagem, não só transições —
  ficou fora por não estar na visão original e por aumentar o volume de
  eventos sem necessidade clara.
- **Pausar/retomar um monitor pela API não emite evento.** O NOTIFY só é
  disparado pelo worker, dentro de `process_monitor`. Uma pausa manual muda
  o estado no banco mas só aparece na tela depois do próximo refresh — uma
  limitação conhecida e aceita, não um requisito desta fase.

## Consequências

- Nenhuma dependência nova: `asyncpg` já era usado pelo worker; o pub/sub
  inteiro é Postgres + um laço assíncrono.
- Pegadinha de ordem de rotas descoberta ao escrever os testes: o Starlette
  casa rotas na ordem de registro, e `GET /monitors/{monitor_id}` (de
  `monitors.router`) casava com `/monitors/stream` antes de chegar em
  `realtime.router`, tratando `"stream"` como UUID e devolvendo 422. Corrigido
  registrando `realtime.router` antes de `monitors.router` em `api/main.py`,
  com comentário explicando o motivo.
- Testado: `EventHub` isolado (publish/subscribe/fila cheia/cancelamento),
  um NOTIFY real contra o Postgres de teste chegando até o hub via
  `listener.py`, e os dois endpoints SSE (autenticação, filtro por dono,
  filtro por `is_public`) exercitando `_event_stream` diretamente — o
  `httpx.ASGITransport` usado nos outros testes de API não serve aqui porque
  ele só retorna depois que a resposta termina, e esse endpoint nunca
  termina por natureza.
- Frontend: hook `useMonitorEvents` (`web/lib/realtime/useMonitorEvents.ts`)
  encapsula o `EventSource`; `AuthContext` passou a expor o token JWT puro
  (antes só expunha o usuário) para montar a URL autenticada. jsdom não
  implementa `EventSource`, então os testes usam um stub
  (`web/lib/realtime/mockEventSource.ts`) registrado globalmente em
  `vitest.setup.ts`.
- Validado manualmente contra a stack real (`docker compose up`): um cliente
  SSE conectado em `/monitors/stream` recebeu, em tempo real, os eventos
  `down` e `up` ao parar e religar o `demo-target`. Nessa mesma validação,
  consultando `pg_stat_activity` com uma conexão SSE aberta, apareceu uma
  sessão `idle in transaction` presa por toda a duração da conexão —
  exatamente o problema de `Depends(get_session)` descrito acima. Corrigido
  trocando por uma sessão própria, de vida curta; revalidado em seguida que
  `pg_stat_activity` não mostra mais nenhuma sessão presa com a conexão SSE
  ainda aberta.
- No caminho, descoberto e corrigido também um problema de ambiente: o
  serviço `worker` roda
  `uv run python -m noar.worker.main` sem `--reload` (diferente do `api`,
  que roda com `--reload`), então ele mantém em memória o código de quando
  o container iniciou. Qualquer alteração em `noar/worker/**` (como a
  adição do `notify` nesta fase) só é refletida depois de
  `docker compose restart worker` — sem isso, o worker continua processando
  checagens com a versão antiga do código, silenciosamente. Vale lembrar
  disso ao editar o worker durante o desenvolvimento local.
