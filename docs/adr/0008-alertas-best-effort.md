# 0008 - Alertas por conta, disparados best-effort

- Status: aceito
- Data: 2026-10-16

## Contexto

Quando um incidente abre ou fecha, o usuário precisa ser avisado. Havia duas
decisões a tomar: onde configurar os canais (por conta ou por monitor) e o
que acontece quando um canal falha ao enviar.

## Decisão

- **Configuração por conta, não por monitor.** Cada usuário tem
  `telegram_chat_id` e `webhook_url` opcionais (`PATCH /auth/me`); o e-mail
  usa o endereço já cadastrado. Mais simples que configuração por monitor, e
  nada na visão do projeto pede granularidade por monitor ainda.
- **Dispara só em abertura/fechamento de incidente**, não a cada checagem.
- **Best-effort**: `dispatch_alert` (`noar/alerts/dispatch.py`) tenta os três
  canais independentemente; uma falha em um (SMTP fora do ar, Telegram sem
  token, webhook recusando a conexão) é logada e não impede os outros nem
  propaga para quem chamou — o processamento da checagem (estado do monitor,
  histórico) já foi commitado antes do dispatch ser sequer tentado.
- **`webhook_url` passa pela mesma guarda de SSRF** (ADR 0005) que a URL de
  monitor, ao salvar (`PATCH /auth/me`) e ao enviar — é o mesmo risco, o
  worker faz uma requisição de saída para uma URL fornecida por usuário.
  `scripts/seed_demo_monitor.py` aponta o webhook de demonstração para o
  `webhook-receiver` direto via SQLAlchemy, não pela API: a guarda da API
  está correta rejeitando um endereço da rede privada do Compose (é
  exatamente isso que precisa rejeitar em produção), então os dados de
  demonstração contornam a guarda em vez de enfraquecê-la.
- **Telegram sem bot real configurado**: se `TELEGRAM_BOT_TOKEN` estiver
  vazio (padrão), o canal é pulado silenciosamente mesmo que o usuário tenha
  preenchido o `chat_id` — consistente com "bot real nunca obrigatório"
  (ADR 0004).

## Consequências

- Um canal fora do ar nunca derruba os outros nem o processamento da
  checagem em si.
- Testes usam `httpx.MockTransport` (telegram/webhook) e mock de
  `aiosmtplib.send` (e-mail) — nenhum depende de rede real ou dos
  serviços do Compose estarem no ar.
- Validado ao vivo: derrubar o `demo-target` gerou e-mail no Mailpit e
  payload no `webhook-receiver` para abertura e fechamento do incidente.
