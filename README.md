# NoAr

NoAr verifica sites e APIs em intervalos regulares, guarda o histórico, abre
incidentes quando algo cai, avisa por e-mail, Telegram e webhook, e publica
uma página de status. É multiusuário: cada conta enxerga apenas os seus
dados.

Projeto de portfólio: foco em agendamento confiável, concorrência, modelagem
de dados de série temporal, segurança aplicada (SSRF e isolamento entre
contas) e operação. Veja as decisões de arquitetura em [`docs/adr/`](docs/adr).

> **Status:** Fase 4 — frontend ligado à API. Cadastro, login e um painel
> listando os monitores da conta logada (criar, pausar, retomar, excluir),
> com tipos do cliente gerados a partir do OpenAPI da API. Ainda não há
> histórico de checks/incidentes, gráficos, SSE em tempo real, verificação
> de e-mail, alertas nem página de status — isso vem nas próximas fases.

## Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 assíncrono
  (asyncpg), Alembic, httpx assíncrono. Gerenciado com [uv](https://docs.astral.sh/uv/).
- **Worker:** processo separado, mesma base de código do backend.
- **Banco:** PostgreSQL 16. Sem Redis — agendamento via Postgres
  (`SELECT ... FOR UPDATE SKIP LOCKED`, ver [ADR 0003](docs/adr/0003-agendamento-via-postgres-sem-fila-externa.md)).
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind, gráficos com
  Recharts. Cliente de API tipado a partir do OpenAPI da API
  ([openapi-typescript](https://openapi-ts.dev/) + [openapi-fetch](https://openapi-ts.dev/openapi-fetch/)).
- **Tempo real:** Server-Sent Events (SSE).
- **Qualidade:** ruff, mypy, pytest, Vitest, Playwright, pre-commit.
- **CI:** GitHub Actions, espelhando os comandos locais (`task ci`).

Detalhes e justificativas completas em [ADR 0002](docs/adr/0002-stack-tecnologica-fixa.md).

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) com WSL2
- [go-task](https://taskfile.dev/installation/)
- Python 3.12+ e [uv](https://docs.astral.sh/uv/) (só para rodar lint/testes
  fora do Docker)
- Node.js 22+ (só para rodar lint/testes do frontend fora do Docker)

## Rodando o projeto

Copie o arquivo de ambiente de exemplo (todos os valores são fictícios):

```bash
cp .env.example .env
```

Suba a stack completa:

```bash
task up
# equivalente: docker compose up -d
```

Serviços disponíveis depois do `up`:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Mailpit (e-mails de teste) | http://localhost:8025 |
| Demo target (site falso monitorado) | http://localhost:8081 |
| Webhook receiver (demonstração) | http://localhost:8082 |

Para parar:

```bash
task down
# equivalente: docker compose down
```

## Comandos de desenvolvimento

Todo comando do Taskfile tem um equivalente sem go-task, mostrado entre
parênteses.

| Comando | O que faz |
|---|---|
| `task up` | Sobe a stack completa (`docker compose up -d`) |
| `task down` | Derruba a stack (`docker compose down`) |
| `task logs` | Acompanha os logs de todos os serviços (`docker compose logs -f`) |
| `task backend:install` | Instala dependências do backend (`cd backend && uv sync`) |
| `task backend:lint` | Lint do backend (`cd backend && uv run ruff check .`) |
| `task backend:format` | Formata o backend (`cd backend && uv run ruff format .`) |
| `task backend:typecheck` | Checagem de tipos do backend (`cd backend && uv run mypy src`) |
| `task backend:test` | Testes do backend (`cd backend && uv run pytest`); requer Postgres acessível em `localhost:5432` (`task up`, ou pelo menos `docker compose up -d db`) |
| `task db:upgrade` | Aplica as migrações pendentes no Postgres local |
| `task db:revision -- "mensagem"` | Gera uma nova migração a partir de mudanças nos modelos |
| `task db:seed` | Cria um usuário + monitor de demonstração apontando pro `demo-target` (requer `task up`) |
| `task web:install` | Instala dependências do frontend (`cd web && npm install`) |
| `task web:lint` | Lint do frontend (`cd web && npm run lint`) |
| `task web:typecheck` | Checagem de tipos do frontend (`cd web && npm run typecheck`) |
| `task web:test` | Testes unitários do frontend (`cd web && npm run test`) |
| `task web:e2e` | Testes end-to-end, contra um build de produção próprio (porta 3100, sem o servidor de dev do `docker compose`); requer `api`/`db` rodando |
| `task web:generate-types` | Regenera `web/lib/api/schema.d.ts` a partir do OpenAPI da API; requer `task up` |
| `task ci` | Roda tudo que a CI roda: lint + tipos + testes, backend e frontend |

## Adicionando uma dependência no frontend

`npm install` no host não é suficiente: o `web` roda em Docker com
`node_modules` num volume anônimo, criado uma vez a partir do `Dockerfile`.
Depois de instalar no host, rode também `docker compose exec web npm install`
(ou `docker compose up -d --build web` para reconstruir a imagem) para o
container enxergar o pacote novo.

## Estrutura do repositório

```
backend/    api (FastAPI) e worker, mesma base de código Python
web/        frontend Next.js
demo-target/   página estática servida pelo serviço demo-target
docs/adr/   decisões de arquitetura (ADRs)
```

## Autenticação

`POST /auth/register` (e-mail + senha) e `POST /auth/login` (devolve um
token JWT). Use `Authorization: Bearer <token>` nas chamadas a `/monitors` e
`/auth/me`. Detalhes e trade-offs em [ADR 0006](docs/adr/0006-autenticacao-via-jwt-bearer.md).

## Segurança

Este projeto monitora URLs informadas por usuários, o que expõe risco de
SSRF (Server-Side Request Forgery). Tanto o cadastro de monitor quanto o
worker bloqueiam esquemas diferentes de `http`/`https` e IPs
privados/loopback/link-local resolvidos na hora (ver
[ADR 0005](docs/adr/0005-protecao-basica-contra-ssrf.md)); a guarda ainda não
fecha a janela de DNS rebinding, documentado na própria ADR como
endurecimento futuro.

## Licença

[MIT](LICENSE)
