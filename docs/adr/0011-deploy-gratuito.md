# 0011 - Deploy em planos gratuitos (Vercel + Render + Supabase)

- Status: aceito
- Data: 2026-11-16

## Contexto

O NoAr é um projeto pessoal e precisa ficar no ar sem custo. Localmente ele
roda como quatro processos (frontend, api, worker e Postgres, ver ADR 0004),
mas nenhum provedor gratuito oferece um processo em segundo plano sempre
ligado, que é exatamente o que o worker é.

Restrições dos planos gratuitos levantadas na hora da decisão:

- **Render:** só web services têm plano gratuito; background workers e cron
  jobs são pagos. O web service dorme após 15 minutos sem tráfego de
  entrada, e a conta tem 750 horas de instância por mês (o suficiente para
  um serviço 24h). O Postgres gratuito do Render expira em 30 dias.
- **Neon:** 100 CU-horas por projeto por mês (cerca de 400 horas da menor
  máquina), com o compute suspenso quando a cota acaba. Como o worker
  consulta o banco continuamente, o banco nunca chega a dormir e a cota
  terminaria por volta do dia 17 do mês.

## Decisão

- **Frontend na Vercel** (plano Hobby), com `web/` como diretório raiz e
  `NEXT_PUBLIC_API_BASE_URL` apontando para a API.
- **API e agendador num único web service gratuito do Render**
  (`render.yaml`). A flag `RUN_WORKER_IN_API=true` faz o `lifespan` da API
  iniciar o `scheduler_loop` ao lado do listener de tempo real. O modo
  padrão continua sendo o worker separado (`docker compose`), e o
  `SELECT ... FOR UPDATE SKIP LOCKED` da ADR 0003 segue valendo, então os
  dois modos podem até coexistir sem checar o mesmo monitor duas vezes.
- **O laço do agendador não morre com uma rodada que falha** (por exemplo,
  banco fora por um instante): loga e tenta de novo no próximo intervalo.
  Separado, o worker tinha o Docker para reiniciá-lo; dentro da API, não há
  supervisor, e as checagens parariam em silêncio.
- **O container aplica as migrações ao iniciar** (`alembic upgrade head`
  antes do uvicorn) e escuta em `$PORT`, porque o plano gratuito do Render
  não tem comando de pré-deploy.
- **Banco no Supabase** (plano gratuito), que não limita horas de compute.
  A conexão usa o *session pooler*: o host direto do Supabase é só IPv6, e o
  modo *session* mantém uma conexão dedicada por cliente, o que preserva o
  `LISTEN` da ADR 0010 (o modo *transaction* o quebraria).
- **Um pinger externo** (por exemplo, cron-job.org) chama `GET /health` a
  cada 10 minutos para o Render não colocar o serviço para dormir.

## Consequências

- Custo zero, ao preço de uma máquina pequena e de checagens paradas por um
  ou dois minutos a cada reinício ou deploy do serviço.
- Se o pinger falhar, o serviço dorme e as checagens param até a próxima
  requisição; a página de status fica desatualizada nesse intervalo.
- Alertas por e-mail não saem em produção enquanto não houver um SMTP real
  configurado (`SMTP_HOST`/`SMTP_PORT`); Telegram e webhook funcionam. Como
  os alertas são best-effort (ADR 0008), isso não afeta as checagens.
- Escalar exige separar o worker de novo (plano pago no Render ou outro
  host), sem mudança de código: basta desligar `RUN_WORKER_IN_API`.
