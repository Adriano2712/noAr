# 0004 - Ambiente de desenvolvimento 100% local e de custo zero

- Status: aceito
- Data: 2026-10-15

## Contexto

NoAr é um projeto pessoal de portfólio. Não há orçamento para serviços pagos,
e o objetivo é que qualquer pessoa consiga clonar o repositório e rodar a
aplicação completa localmente, sem criar conta em nenhum provedor externo.

## Decisão

- Nenhum serviço pago, nenhuma conta de nuvem, nenhum banco ou fila externos.
  Tudo roda via Docker Compose na máquina do desenvolvedor.
- Não há fase de deploy em nuvem no desenvolvimento deste projeto. A "demo" é
  local: `docker compose up` mais dados de exemplo. Deploy em nuvem fica
  registrado apenas como evolução futura em documentação, sem implementação.
- E-mail em desenvolvimento sempre via Mailpit (servidor SMTP falso com
  interface web). SMTP real é opcional por variável de ambiente.
- Telegram: bot real é opcional (token no `.env`, só local). Os testes
  automatizados usam um servidor Telegram falso.
- Webhook: o Compose inclui um serviço receptor de demonstração
  (`webhook-receiver`) para visualizar os alertas chegando.
- Observabilidade externa (Sentry e semelhantes) fica desligada por padrão.
  Um perfil opcional do Compose (`observability`) sobe Prometheus e Grafana
  locais, lendo `/metrics`.
- A interface de tarefas é o Taskfile.yml (go-task), funcionando tanto no
  PowerShell quanto no Linux/bash; todo comando documentado tem o equivalente
  em `docker compose` puro.

## Consequências

- Qualquer pessoa roda o projeto completo sem precisar de cartão de crédito
  ou conta em nuvem.
- CI (GitHub Actions) usa o plano gratuito de repositório público e roda os
  mesmos comandos documentados localmente via `task ci`.
- Recursos que dependem de serviços pagos (ex.: SMTP real, bot real do
  Telegram, observabilidade externa) ficam sempre opcionais, nunca
  obrigatórios para rodar ou testar o projeto.
