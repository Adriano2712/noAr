# 0001 - Registrar decisões arquiteturais com ADRs

- Status: aceito
- Data: 2026-10-15

## Contexto

O projeto NoAr vai evoluir em várias fases ao longo de um período longo. Decisões
tomadas no início (stack, modelagem, estratégia de agendamento) precisam ficar
registradas de forma curta e pesquisável, para que o motivo de cada escolha não
se perca conforme o código muda.

## Decisão

Toda decisão arquitetural relevante vira um ADR curto em `docs/adr/`, numerado
sequencialmente, seguindo o formato: Status, Contexto, Decisão, Consequências.

## Consequências

- Decisões ficam documentadas perto do código, versionadas junto com ele.
- ADRs antigos não são editados retroativamente; uma decisão revista vira um
  novo ADR que referencia o anterior.
