# Statistical Feature Builder (SFB)

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688)
![License](https://img.shields.io/badge/license-Proprietary-red)

**Statistical Feature Builder (SFB)** é um microserviço especializado em processamento estatístico de dados analíticos, desenvolvido pela **Pulse Data & AI**.

## 🎯 Visão Geral

O SFB é um componente da arquitetura **Decision Intelligence** da Pulse, responsável por transformar dados brutos em pacotes estatísticos prontos para consumo por IA generativa.

### Capacidades Principais

- 📊 **Estatísticas Descritivas**: Média, mediana, quartis, variância, assimetria, curtose
- 📈 **Análise de Tendências**: Regressão linear, forecasting, variações período-a-período
- 🔍 **Detecção de Outliers**: Detecção baseada em Z-score com classificação de severidade
- 📉 **Análise de Distribuição**: Testes de normalidade e classificação de distribuições
- 🔗 **Análise de Correlação**: Correlações Pearson e Spearman (multi-dataset)

## 🏗️ Arquitetura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Worker    │─────▶│     SFB     │─────▶│     LLM     │
│  (Coleta)   │      │ (Estatística)│      │(Interpretação)│
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │    Buddy    │
                     │  (Exibição) │
                     └─────────────┘
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Docker (opcional)
- Kubernetes (para deploy em produção)

### Instalação Local

```bash
# Clone o repositório
git clone <repo-url>
cd SFB

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# Execute o serviço
python -m uvicorn app.main:app --reload
```

O serviço estará disponível em: `http://localhost:8000`

- **Documentação interativa**: http://localhost:8000/docs
- **Documentação alternativa**: http://localhost:8000/redoc

### Docker

```bash
# Build da imagem
docker build -t pulse/sfb:1.0.0 .

# Execute o container
docker run -p 8000:8000 pulse/sfb:1.0.0
```

### Docker Compose

```bash
# Apenas o serviço SFB
docker-compose up sfb

# Com observabilidade completa (Tempo, Prometheus, Grafana)
docker-compose --profile observability up
```

### Kubernetes

```bash
# Crie o namespace
kubectl create namespace pulse-services

# Deploy do serviço
kubectl apply -f k8s/deployment.yaml

# Deploy do HPA (autoscaling)
kubectl apply -f k8s/hpa.yaml

# Deploy do Ingress
kubectl apply -f k8s/ingress.yaml

# Verifique o status
kubectl get pods -n pulse-services
kubectl get svc -n pulse-services
```

## 📡 Uso da API

### Autenticação

A API usa OAuth2 com Bearer tokens:

```bash
curl -X POST https://sfb.pulse.ai/v1/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @request.json
```

**Scopes necessários:**
- `sfb.read`: Leitura
- `sfb.write`: Escrita (necessário para `/generate`)

### Exemplo de Request

```json
{
  "dataset": "sales_revenue",
  "period": "2025-01",
  "filters": {
    "region": "southeast",
    "product_category": "electronics"
  },
  "data": [
    {"timestamp": "2025-01-01", "value": 1500.50},
    {"timestamp": "2025-01-02", "value": 2300.75},
    {"timestamp": "2025-01-03", "value": 1800.25},
    {"timestamp": "2025-01-04", "value": 2100.00},
    {"timestamp": "2025-01-05", "value": 1950.50}
  ]
}
```

### Exemplo de Response

```json
{
  "dataset": "sales_revenue",
  "period": "2025-01",
  "generated_at": "2025-02-20T12:00:00Z",
  "processing_time_ms": 125.5,
  "statistical_package": {
    "statistics": {
      "count": 5,
      "mean": 1930.20,
      "median": 1950.50,
      "min": 1500.50,
      "max": 2300.75,
      "std_dev": 289.87,
      "variance": 84024.67,
      "q1": 1800.25,
      "q3": 2100.00,
      "iqr": 299.75,
      "skewness": -0.15,
      "kurtosis": -1.25
    },
    "trends": {
      "day_over_day_pct": -7.14,
      "month_over_month_pct": null,
      "regression_slope": 87.5,
      "regression_intercept": 1755.0,
      "r_squared": 0.45,
      "forecast_next_period": 2280.0,
      "trend_direction": "upward"
    },
    "outliers": [],
    "distribution_type": "approximately_normal",
    "normality_test_p_value": 0.35,
    "is_normal_distribution": true
  }
}
```

### Python Client Example

```python
import requests

url = "https://sfb.pulse.ai/v1/generate"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "dataset": "sales_revenue",
    "period": "2025-01",
    "data": [
        {"timestamp": "2025-01-01", "value": 1500.50},
        {"timestamp": "2025-01-02", "value": 2300.75},
        # ... more data points
    ]
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

print(f"Mean: {result['statistical_package']['statistics']['mean']}")
print(f"Trend: {result['statistical_package']['trends']['trend_direction']}")
```

## 🔧 Configuração

Todas as configurações são feitas via variáveis de ambiente. Veja o arquivo [.env.example](.env.example) para a lista completa.

### Principais Configurações

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OAUTH2_ENABLED` | Habilitar autenticação OAuth2 | `true` |
| `RATE_LIMIT_ENABLED` | Habilitar rate limiting | `true` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Limite de requisições por minuto | `500` |
| `DATA_MASKING_ENABLED` | Habilitar mascaramento de dados sensíveis | `true` |
| `OTEL_ENABLED` | Habilitar OpenTelemetry | `true` |
| `LOG_LEVEL` | Nível de log (debug, info, warning, error) | `info` |

## 📊 Observabilidade

### Logs

O SFB usa logging estruturado em JSON com os seguintes campos:

- `request_id`: ID único da requisição
- `timestamp`: Data/hora em UTC
- `dataset`: Nome do dataset processado
- `period`: Período analisado
- `processing_time_ms`: Tempo de processamento
- `exec_status`: Status de execução (success/error)

### Métricas

Integração com Prometheus para métricas de:
- Taxa de requisições
- Tempo de resposta
- Taxa de erros
- Uso de recursos (CPU, memória)

### Traces

Integração com OpenTelemetry/Grafana Tempo para tracing distribuído.

## 🔒 Segurança

- ✅ Autenticação OAuth2
- ✅ Rate limiting (500 req/min)
- ✅ Mascaramento de dados sensíveis
- ✅ Validação de payload
- ✅ Container não-root
- ✅ CORS configurável
- ✅ HTTPS obrigatório em produção

## 📝 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| `E001` | Dataset inválido ou inexistente |
| `E002` | Payload fora do padrão esperado |
| `E003` | Falha interna no cálculo estatístico |
| `E004` | Timeout ao processar dados |
| `E005` | Autorização inválida ou ausente |
| `E006` | Rate limit excedido |

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio pytest-cov

# Executar testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html
```

## 🚢 Deploy

### Ambiente de Desenvolvimento

```bash
docker-compose up
```

### Ambiente de Produção (Kubernetes)

1. Configure o secret para o `SECRET_KEY`:

```bash
kubectl create secret generic sfb-secrets \
  --from-literal=secret-key="YOUR_STRONG_SECRET_KEY" \
  -n pulse-services
```

2. Deploy:

```bash
kubectl apply -f k8s/
```

3. Verifique:

```bash
kubectl get pods -n pulse-services
kubectl logs -f deployment/sfb-deployment -n pulse-services
```

## 🔗 Integração com Orquestrador

### Registro do Componente

```json
{
  "component_id": "statistical_feature_builder_v1",
  "type": "service",
  "executor": "http",
  "method": "POST",
  "endpoint": "https://sfb.pulse.ai/v1/generate",
  "inputs": {
    "dataset_name": "string",
    "period": "string",
    "data": "array"
  },
  "outputs": {
    "statistical_package": "object"
  }
}
```

## 📚 Documentação Adicional

- [API Reference](http://localhost:8000/docs)
- [Arquitetura Decision Intelligence](docs/architecture.md)
- [Guia de Desenvolvimento](docs/development.md)
- [FAQ](docs/faq.md)

## 🤝 Contribuindo

Este é um projeto proprietário da Pulse. Contribuições internas são bem-vindas.

## 📄 Licença

Proprietary - Pulse Data & AI © 2025

## 👥 Autores

**Pulse Data & AI Team**

## 📞 Suporte

Para suporte, entre em contato com a equipe Pulse Data & AI.

---

**Desenvolvido com ❤️ pela Pulse Data & AI**
