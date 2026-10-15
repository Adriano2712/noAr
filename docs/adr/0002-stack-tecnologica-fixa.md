# 0002 - Stack tecnológica fixa

- Status: aceito
- Data: 2026-10-15

## Contexto

NoAr é um projeto de portfólio cujo objetivo é demonstrar competência em
agendamento confiável, concorrência, modelagem de séries temporais, segurança
aplicada e operação. A stack precisa ser madura, bem documentada e não exigir
nenhum serviço pago.

## Decisão

- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 assíncrono com
  asyncpg, Alembic, httpx assíncrono.
- Banco: PostgreSQL 16. Sem Redis — o agendamento usa o próprio Postgres
  (ver ADR 0003).
- Worker: processo separado, mesma base de código do backend, assíncrono.
- Frontend: Next.js (App Router) + TypeScript + Tailwind, gráficos com
  Recharts, tipos do cliente gerados a partir do OpenAPI exposto pela API.
- Tempo real: Server-Sent Events (SSE), sem WebSocket — o fluxo é
  predominantemente servidor -> cliente (status mudando, novos eventos).
- Gerenciador de pacotes Python: uv (único binário para venv, resolução de
  dependências e lockfile; mais rápido e com menos partes móveis que
  Poetry + pip).
- Gerenciador de pacotes Node: npm (já vem com o Node; não há monorepo JS
  com múltiplos pacotes que justifique pnpm/workspaces).
- Qualidade: ruff, mypy (strict nos módulos de domínio), pytest, Vitest,
  Playwright, pre-commit.
- CI: GitHub Actions, espelhando exatamente os comandos rodados localmente
  via `task ci`.

## Consequências

- Stack moderna e amplamente documentada, boa para portfólio.
- Sem dependência de serviços de nuvem pagos em nenhuma fase do
  desenvolvimento (ver ADR 0004).
- Troca de qualquer item desta lista exige um novo ADR.
