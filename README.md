# ExampleUsageWoobe001 — Mercury Commerce

Aplicação de referência para demonstrar a Woobe integrada a um produto que faz sentido mesmo sem IA.

O produto fictício agora é a **Mercury Store**, um e-commerce completo o suficiente para ter duas superfícies de IA distintas:

- **Shopping Assistant** para o cliente encontrar produtos usando linguagem natural.
- **Merchant Assistant** para o lojista analisar vendas, estoque, clientes, entregas e gerar relatórios.

Todo o domínio comercial é **100% mockado**. A aplicação não espera Shopify, ERP, transportadora, CRM ou qualquer outra fonte externa.

## O que o exemplo demonstra

### Lado do cliente

O catálogo contém dezenas de produtos com atributos estruturados, preço, estoque, categoria, localização física e URL canônica.

Perguntas esperadas:

- `Vocês têm uma TV de tela plana de 27 polegadas?`
- `Quero uma TV 4K de pelo menos 43 polegadas.`
- `Tem headset bluetooth por até R$ 500?`
- `Quero um teclado mecânico ABNT2.`
- `Onde fica o Sony WH-1000XM6 na loja?`
- `Me manda o link desse produto.`

O LLM interpreta a necessidade; a Tool consulta os fatos. O link retornado é o `product_url` da API da loja, não uma URL inventada pelo modelo.

### Lado do lojista

O Merchant Console usa 120 dias de pedidos sintéticos para oferecer dashboard, pedidos, estoque, clientes, entregas e relatórios.

Perguntas esperadas:

- `Quais foram os produtos que mais venderam nos últimos 15 dias?`
- `Quais categorias mais faturaram?`
- `Quais produtos tiveram pior performance?`
- `O que pode ficar sem estoque nos próximos 30 dias?`
- `Quais produtos estão ganhando tração?`
- `Quais produtos estão parados e podem entrar em promoção?`
- `Qual cliente VIP está com entrega atrasada?`
- `Gere um relatório dos últimos 15 dias com melhores, piores e previsão de 30 dias.`

A previsão é simples e determinística: usa velocidade dos últimos 30 dias, período anterior e semana recente. Ela existe para a PoV e não é apresentada como previsão comercial de produção.

## Arquitetura

```text
                         MERCURY STORE
                     aplicação cliente fictícia

        Customer                             Merchant
           │                                    │
           ▼                                    ▼
  Shopping Assistant                    Merchant Assistant
           │                                    │
      ChatSurface                          ChatSurface
           │                                    │
           ▼                                    ▼
     Agent Release                     Agent/Network Release
           │                                    │
    public catalog Tools                 private merchant Tools
           │                                    │
           └───────────────┬────────────────────┘
                           ▼
                    Mercury Mock API
                           │
             ┌─────────────┴─────────────┐
             │                           │
        Catalog data              120d sales history
                                  orders / customers
                                  inventory / shipments
```

## Docker quick start

```bash
cp .env.example .env
docker compose up --build -d
```

Abra:

```text
http://localhost:5174
```

Merchant Console:

```text
Email: admin@mercury.demo
Senha: demo123
```

A aplicação e todos os mocks sobem sem credenciais Woobe. Os painéis de ChatSurface exibem uma mensagem de configuração até você preencher as credenciais reais.

## Configuração Woobe

Preencha no `.env`:

```dotenv
WOOBE_STORE_CHAT_SURFACE_PUBLIC_ID=csf_...
WOOBE_STORE_CHAT_SURFACE_ACCESS_KEY=woobe_surface_...
WOOBE_ADMIN_CHAT_SURFACE_PUBLIC_ID=csf_...
WOOBE_ADMIN_CHAT_SURFACE_ACCESS_KEY=woobe_surface_...
WOOBE_STORE_TOOL_API_KEY=...
WOOBE_ADMIN_TOOL_API_KEY=...
```

Veja [`docs/WOOBE_SETUP.md`](docs/WOOBE_SETUP.md).

## Segurança da PoV

As Tools do Shopping Assistant são separadas das Tools administrativas.

O Shopping Assistant acessa apenas catálogo público. Ele não recebe Tools de pedidos, clientes, forecast ou relatórios.

O Merchant Assistant usa outra chave de Tool e outra ChatSurface. A separação de privilégio não depende apenas de prompt.

A PoV continua deliberadamente single-merchant. O ChatSurface MVP atual não deve ser tratado como delegated Tool identity multi-tenant.

## Stack

- FastAPI
- SQLite apenas para Sessions ChatSurface e relatórios gerados
- dataset comercial sintético em memória
- React + TypeScript + Vite
- Nginx
- Docker Compose
- Woobe ChatSurface
