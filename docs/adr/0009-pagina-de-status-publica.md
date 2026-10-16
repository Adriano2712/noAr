# 0009 - Página de status pública, opt-in por monitor

- Status: aceito
- Data: 2026-10-16

## Contexto

O projeto promete uma página de status pública. Era preciso decidir o que
fica visível (todos os monitores da conta? só alguns?) e como alguém de
fora alcança essa página sem autenticação.

## Decisão

- **Opt-in por monitor** (`monitors.is_public`, padrão `false`). Nada fica
  público sem o dono decidir explicitamente, monitor a monitor, na própria
  página de detalhe.
- **URL pela própria conta, sem slug customizado**: `GET /status/{owner_id}`
  (API) e `/status/{owner_id}` (frontend), usando o UUID do usuário direto.
  Um slug bonito e escolhido pelo usuário (`/status/minha-empresa`) é uma
  evolução natural, mas exige validação de unicidade e UI própria — fica
  registrado aqui como próximo passo, não implementado.
- **A página mostra nome, URL e estado** de cada monitor público, mais
  uptime % das últimas 100 checagens. Mostrar a URL é o padrão de mercado
  (UptimeRobot, Better Uptime) para monitores que o próprio dono optou por
  tornar públicos — a guarda fica no opt-in, não em esconder o endereço
  depois.
- **Sempre 200, nunca 404**: `GET /status/{owner_id}` devolve lista vazia
  tanto para uma conta sem monitores públicos quanto para um UUID que não
  existe. Sem essa decisão, dar 404 só no segundo caso permitiria descobrir
  por tentativa e erro quais UUIDs correspondem a contas reais.
- **Sem atualização automática nesta fase**: a página busca os dados uma
  vez, ao carregar. Atualização ao vivo é natural de implementar junto com
  SSE, quando essa fase chegar — por ora, quem quiser ver o estado mais
  recente recarrega a página.

## Consequências

- Endpoint novo sem autenticação (`noar/api/routers/status.py`) — não lê
  nem usa o usuário logado, então não há guarda de autorização para
  esquecer aqui; o único filtro que importa é `is_public`.
- Sem rate limiting nesta fase: é escopo de operação/produção, não deste
  projeto de portfólio. Fica como limitação conhecida.
- Testado: isolamento entre monitores públicos/privados, 200 vazio para
  conta inexistente, cálculo de uptime, e validado ao vivo marcando o
  monitor de demonstração como público e consultando a API real.
