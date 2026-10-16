# 0007 - Testes e2e rodam contra um build de produção, não o servidor de dev

- Status: aceito
- Data: 2026-10-16

## Contexto

Os primeiros testes e2e (Playwright) contra o `web` do `docker compose`
(servidor de dev do Next, Turbopack) eram extremamente instáveis: navegações
que nunca disparavam o evento `load`, cliques caindo num submit nativo de
formulário (o HTML pré-hidratação ainda não tinha os handlers do React), e
o Fast Refresh do HMR remontando o DOM no meio de uma interação do teste
(atividade de arquivo no bind mount do Docker já é suficiente para disparar
isso). Nenhum desses sintomas é um bug da aplicação — são efeitos colaterais
do próprio modo de desenvolvimento.

## Decisão

`web/playwright.config.ts` usa a opção `webServer` do Playwright para rodar
`npm run build && npm run start` numa porta própria (3100), separada da
porta 3000 do servidor de dev do `docker compose`. Sem HMR, sem Fast
Refresh — a página fica estável assim que carrega.

Como o build de produção é servido numa origem diferente (`localhost:3100`),
a API precisou passar a aceitar múltiplas origens de CORS
(`CORS_ALLOWED_ORIGINS`, ver [ADR 0006](0006-autenticacao-via-jwt-bearer.md)),
já que o navegador trata porta diferente como origem diferente.

## Consequências

- `task web:e2e` não depende do container `web` estar rodando — só precisa
  de `api`/`db` (via `task up` ou `docker compose up -d db api`); o próprio
  Playwright constrói e sobe o frontend.
- Cada execução recompila o frontend (alguns segundos a mais), mas o
  resultado é determinístico — sem flakiness por recompilação no meio do
  teste.
- Testa exatamente o que seria publicado (build de produção), não um modo
  que nunca roda fora da máquina do desenvolvedor.
