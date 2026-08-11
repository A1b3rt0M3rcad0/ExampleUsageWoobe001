# Woobe setup — Mercury Commerce Example

Este exemplo usa duas ChatSurfaces porque são dois produtos de IA diferentes.

## 1. Shopping Assistant

Target recomendado: **Agent Release**.

Responsabilidade: ajudar o cliente a descobrir produtos públicos. Não recebe acesso às APIs administrativas.

Todas as Tools usam:

```http
Authorization: Bearer <WOOBE_STORE_TOOL_API_KEY>
```

### `search_products`

```text
GET /api/woobe-tools/store/search-products
```

Inputs recomendados:

```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "category": {"type": "string"},
    "brand": {"type": "string"},
    "min_price": {"type": "number"},
    "max_price": {"type": "number"},
    "in_stock": {"type": "boolean"},
    "screen_size_inches": {"type": "number"},
    "resolution": {"type": "string"},
    "smart_tv": {"type": "boolean"},
    "limit": {"type": "integer", "minimum": 1, "maximum": 30}
  },
  "additionalProperties": false
}
```

A resposta inclui `product_url`. Quando não existe o tamanho exato solicitado, a API pode devolver `alternatives` da mesma categoria.

### `get_product`

```text
GET /api/woobe-tools/store/product?slug=<slug>
```

### `list_categories`

```text
GET /api/woobe-tools/store/categories
```

Prompt recomendado:

```text
Você é o Shopping Assistant da Mercury Store.

Use Tools para qualquer afirmação factual sobre existência, preço, estoque, especificações, localização física ou link.
Nunca invente produto, preço, estoque, corredor, prateleira ou URL.
Converta requisitos como categoria, tamanho da tela, marca, faixa de preço e resolução em filtros da Tool.
Se não houver correspondência exata e a Tool retornar alternativas, explique claramente que são opções próximas.
Quando existir product_url, use esse link como destino canônico.
Você não possui acesso a pedidos, clientes ou dados administrativos.
```

## 2. Merchant Assistant

Target recomendado: **Network Release** ou Agent Release com Tools administrativas.

Todas usam:

```http
Authorization: Bearer <WOOBE_ADMIN_TOOL_API_KEY>
```

### `get_sales_analytics`

```text
GET /api/woobe-tools/admin/sales-analytics?days=15
```

Retorna receita, pedidos, unidades, melhores produtos, categorias e low performers.

### `get_sales_forecast`

```text
GET /api/woobe-tools/admin/forecast?days=30
```

Retorna expected units, sales velocity, trend, confidence, stock risk, rising products, declining products e slow movers.

### `get_inventory`

```text
GET /api/woobe-tools/admin/inventory
```

### `get_orders`

```text
GET /api/woobe-tools/admin/orders
```

### `get_customer`

```text
GET /api/woobe-tools/admin/customer?customer_id=<id>
```

### `get_shipments`

```text
GET /api/woobe-tools/admin/shipments
```

### `create_sales_report`

```text
POST /api/woobe-tools/admin/reports
```

Body:

```json
{
  "type": "object",
  "required": ["title", "period_label", "executive_summary", "findings", "recommendations"],
  "properties": {
    "title": {"type": "string"},
    "period_label": {"type": "string"},
    "executive_summary": {"type": "string"},
    "findings": {"type": "array", "items": {"type": "string"}},
    "recommendations": {"type": "array", "items": {"type": "string"}}
  },
  "additionalProperties": false
}
```

Prompt recomendado:

```text
Você é o Merchant Assistant da Mercury Store.
Use Tools para dados do cenário: vendas, pedidos, clientes, estoque, entregas e forecast.
Nunca invente métricas.
Separe fato calculado, tendência e inferência.
Forecast é probabilístico; preserve expected units, trend e confidence quando relevantes.
Quando o usuário pedir relatório, obtenha analytics, forecast e inventory necessários antes de chamar create_sales_report.
Para perguntas sobre clientes ou entregas, consulte os dados específicos antes de concluir.
```

Split opcional de Network:

```text
Merchant Root
├── Sales & Merchandising Specialist
├── Inventory & Forecast Specialist
└── Customer & Fulfillment Specialist
```

## 3. ChatSurface

Crie uma ChatSurface para o Shopping Assistant e outra para o Merchant Assistant.

Para desenvolvimento local, adicione `http://localhost:5174` aos allowed origins de ambas.

A Access Key fica somente no backend Mercury. O browser recebe apenas Session Access Token.

## 4. Networking das HTTP Tools

O executor de HTTP Tools da Woobe bloqueia localhost e IPs privados por SSRF. Para integração end-to-end, publique a Mercury API em HTTPS público ou use um túnel HTTPS público. As Tool URLs devem usar essa URL pública.

## 5. Limite deliberado da PoV

Todos os dados comerciais são sintéticos. Não há Shopify, ERP, gateway de pagamento, CRM ou transportadora real.

O objetivo é provar:

```text
produto existente
+ APIs próprias
+ ChatSurface
+ Agent/Network
+ Tools
+ Sessions
+ ações persistidas
```
