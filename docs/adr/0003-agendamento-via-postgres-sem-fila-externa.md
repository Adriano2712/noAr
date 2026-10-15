# 0003 - Agendamento de checagens via Postgres, sem fila externa

- Status: aceito
- Data: 2026-10-15

## Contexto

O worker do NoAr precisa checar monitores vencidos em intervalos regulares,
suportar múltiplas instâncias rodando em paralelo sem checagens duplicadas ou
perdidas, e se recuperar sozinho se um worker morrer no meio de uma checagem.
A abordagem comum para isso é uma fila (Redis, RabbitMQ, SQS). Mas a restrição
de custo zero e "tudo roda no Docker Compose da minha máquina" torna uma peça
de infraestrutura a mais (fila + seu operador) um custo de complexidade sem
benefício real nesta escala.

## Decisão

O agendamento usa exclusivamente o PostgreSQL já presente no projeto:

- A tabela `monitors` tem `next_check_at` e `locked_until`.
- O worker, em loop, seleciona monitores vencidos com
  `SELECT ... FOR UPDATE SKIP LOCKED LIMIT N`, define `locked_until` (lease) e
  `next_check_at = agora + intervalo + jitter`, e confirma a transação.
- As checagens rodam com concorrência limitada (semáforo), gravam o resultado
  e atualizam o estado do monitor.
- Se o worker morrer no meio, o lease expira e outro worker reassume.
- Vários workers podem rodar em paralelo sem coordenação extra, graças ao
  `SKIP LOCKED`.

## Consequências

- Um serviço a menos no Compose (sem Redis/fila), menos partes móveis.
- `SELECT ... FOR UPDATE SKIP LOCKED` é um padrão conhecido e testável; mas
  escala pior que uma fila dedicada em volumes muito altos — aceitável para o
  escopo deste projeto (portfólio, não produção com milhões de monitores).
- Exige testes específicos para concorrência (vários workers simultâneos,
  worker que morre com lease ativo) na fase em que a tabela `monitors` e o
  worker forem implementados.
