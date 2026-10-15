# 0005 - Proteção básica contra SSRF na checagem HTTP

- Status: aceito
- Data: 2026-10-15

## Contexto

O worker faz requisições HTTP de saída para a URL de cada monitor. Mais à
frente, essas URLs serão fornecidas por usuários através do CRUD de
monitores — é exatamente o cenário clássico de SSRF (Server-Side Request
Forgery): um usuário malicioso cadastra um monitor apontando para um
endereço interno (`169.254.169.254` de metadados de nuvem, serviços na rede
privada, `localhost`, etc.) para usar o worker como proxy de acesso a
recursos que não deveria alcançar.

## Decisão

Antes de cada checagem, `noar.security.ssrf.ensure_safe_url()`:

- Aceita apenas os esquemas `http` e `https`.
- Resolve o hostname e rejeita qualquer IP privado (RFC1918), loopback,
  link-local, reservado, multicast ou não especificado.
- Não segue redirecionamentos (`follow_redirects=False`), para que um 3xx
  nunca seja usado para alcançar um destino bloqueado através de um
  redirecionamento.

Uma flag `ssrf_allow_private_networks` (desligada por padrão) permite
desligar a checagem de IP privado. Ela só é ligada no `docker-compose.yml`
local, porque o próprio ambiente de demonstração precisa que o worker
alcance o serviço `demo-target` na rede privada do Compose — nunca deve ser
ligada em um ambiente onde URLs vêm de um usuário não confiável.

## Consequências

- Cobre o caso comum de SSRF (URL resolve diretamente para um endereço
  bloqueado).
- **Não** fecha a janela de "DNS rebinding": o hostname é resolvido aqui,
  mas o `httpx.AsyncClient` faz sua própria resolução ao conectar
  milissegundos depois — um DNS que muda de resposta entre as duas
  resoluções escaparia da guarda. Fechar essa janela exigiria fixar o IP
  resolvido na conexão (ex.: transporte customizado no httpx) e fica como
  endurecimento futuro, não implementado agora.
- Testes cobrem esquema bloqueado, hostname sem resolução, e cada categoria
  de IP bloqueado, usando um resolver falso (sem rede real).
