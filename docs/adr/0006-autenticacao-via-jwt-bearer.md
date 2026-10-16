# 0006 - Autenticação via token JWT no header Authorization

- Status: aceito
- Data: 2026-10-15

## Contexto

O frontend (porta 3000) e a API (porta 8000) rodam em origens diferentes
mesmo em desenvolvimento local. Era preciso escolher entre sessão via cookie
httpOnly (revogável, mas exige CORS com credentials e cuidado com SameSite
entre portas diferentes) ou token JWT no header `Authorization` (API
totalmente stateless, sem fricção de cookie cross-origin, mas sem lista de
revogação nesta fase).

## Decisão

- `POST /auth/login` recebe e-mail/senha (formato `OAuth2PasswordRequestForm`,
  padrão do FastAPI) e devolve um token JWT assinado com `API_SECRET_KEY`
  (HS256), válido por `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão: 24h).
- O frontend manda `Authorization: Bearer <token>` em cada chamada à API.
- Senha com hash via argon2 (`argon2-cffi`), recomendado pela OWASP.
- CORS liberado apenas para `CORS_ALLOWED_ORIGINS` (lista separada por vírgula;
  padrão cobre o Next em dev e o build de produção que o Playwright usa nos
  testes e2e — ver [web/playwright.config.ts](../../web/playwright.config.ts)).

## Consequências

- Sem fricção de cookie cross-origin/CSRF entre `localhost:3000` e
  `localhost:8000` em desenvolvimento.
- **Sem revogação de token**: um token roubado (ex.: via XSS no frontend)
  continua válido até expirar. Mitigação parcial: expiração relativamente
  curta (24h, configurável). Revogação de verdade (denylist ou sessão
  híbrida) fica como evolução futura caso o projeto passe a lidar com dados
  mais sensíveis.
- Sem "logout" no servidor nesta fase — o frontend simplesmente descarta o
  token guardado.
- Sem verificação de e-mail nem recuperação de senha nesta fase; dá pra usar
  o Mailpit (já no Compose) quando essas features forem implementadas.
