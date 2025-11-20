# Arquitetura do Statistical Feature Builder (SFB)

## Visão Geral

O SFB é um microserviço Python/FastAPI que se integra à arquitetura Decision Intelligence da Pulse, operando na camada de **Analytics Compute Service**.

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                    PULSE ECOSYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                │
│  │  Worker  │────▶│   SFB    │────▶│   LLM    │                │
│  │ (Coleta) │     │(Análise) │     │(Interpre-│                │
│  │          │     │Estatística│    │  tação)  │                │
│  └──────────┘     └──────────┘     └──────────┘                │
│       │                 │                 │                      │
│       │                 │                 │                      │
│       └─────────────────┴─────────────────┘                     │
│                         ▼                                        │
│                  ┌──────────────┐                                │
│                  │ Orquestrador │                                │
│                  │   (Pulse)    │                                │
│                  └──────────────┘                                │
│                         │                                        │
│                         ▼                                        │
│                  ┌──────────────┐                                │
│                  │    Buddy     │                                │
│                  │  (UI/Chat)   │                                │
│                  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Internos

### 1. API Layer (`app/routers/`)

**Responsabilidades:**
- Expor endpoints REST (FastAPI)
- Validação de requisições (Pydantic)
- Tratamento de erros HTTP
- Documentação automática (OpenAPI)

**Principais Endpoints:**
- `POST /v1/generate` - Geração de pacote estatístico
- `GET /v1/health` - Health check

### 2. Core Layer (`app/core/`)

#### StatisticalEngine (`statistics.py`)

Motor de cálculos estatísticos usando NumPy, SciPy e scikit-learn.

**Métodos principais:**
- `calculate_descriptive_statistics()` - Estatísticas descritivas
- `detect_outliers()` - Detecção de outliers (Z-score)
- `analyze_trends()` - Regressão linear e forecasting
- `test_normality()` - Teste de Shapiro-Wilk
- `calculate_correlations()` - Correlações de Pearson e Spearman

#### DataProcessor (`processor.py`)

Orquestrador do processamento de dados.

**Responsabilidades:**
- Extração de valores numéricos
- Validação de dados
- Mascaramento de campos sensíveis
- Coordenação dos cálculos estatísticos
- Montagem da resposta final

### 3. Middleware Layer (`app/middleware/`)

#### Authentication (`auth.py`)

- OAuth2 com Bearer tokens
- Validação de scopes (sfb.read, sfb.write)
- JWT decoding

#### Rate Limiter (`rate_limiter.py`)

- Limite de 500 req/min por cliente
- Implementação in-memory (considerando Redis para produção)
- Limpeza automática de entradas antigas

#### Logging (`logging.py`)

- Logging estruturado (JSON)
- Request ID tracking
- Métricas de performance
- Integração com OpenTelemetry

### 4. Models Layer (`app/models/`)

**Schemas Pydantic:**

```python
GenerateRequest
  ├─ dataset: str
  ├─ period: str
  ├─ filters: Optional[Dict]
  └─ data: List[Dict]

GenerateResponse
  ├─ dataset: str
  ├─ period: str
  ├─ generated_at: datetime
  ├─ processing_time_ms: float
  └─ statistical_package: StatisticalPackage
      ├─ statistics: Statistics
      ├─ trends: Trends
      ├─ correlations: Optional[Dict]
      └─ outliers: List[Outlier]
```

### 5. Configuration (`app/config.py`)

- Gerenciamento de variáveis de ambiente
- Pydantic Settings
- Valores padrão seguros

## Fluxo de Processamento

```
1. REQUEST RECEIVED
   ├─ Authentication Middleware
   │  └─ Valida token OAuth2
   ├─ Rate Limiter Middleware
   │  └─ Verifica limite de requisições
   └─ Logging Middleware
      └─ Gera request_id e inicia logging

2. REQUEST VALIDATION
   ├─ Pydantic validation
   └─ Retorna 422 se inválido

3. DATA PROCESSING
   ├─ Extract values from payload
   ├─ Validate data quality
   │  ├─ Mínimo 3 pontos
   │  ├─ Sem NaN/Inf
   │  └─ Valores numéricos
   ├─ Mask sensitive fields (se habilitado)
   └─ Convert to NumPy arrays

4. STATISTICAL ANALYSIS
   ├─ Descriptive Statistics
   │  ├─ Mean, median, std dev
   │  ├─ Quartiles (Q1, Q3, IQR)
   │  └─ Skewness, kurtosis
   ├─ Trend Analysis
   │  ├─ Linear regression
   │  ├─ R² calculation
   │  ├─ Forecasting
   │  └─ Trend direction
   ├─ Outlier Detection
   │  ├─ Z-score calculation
   │  ├─ Threshold: |z| > 3
   │  └─ Timestamp tracking
   └─ Distribution Analysis
      ├─ Normality test (Shapiro-Wilk)
      └─ Distribution classification

5. RESPONSE BUILDING
   ├─ Assemble StatisticalPackage
   ├─ Add metadata
   ├─ Calculate processing time
   └─ Return JSON response

6. LOGGING & OBSERVABILITY
   ├─ Log completion
   ├─ Export traces (OpenTelemetry)
   └─ Update metrics (Prometheus)
```

## Padrões de Design

### 1. Dependency Injection

FastAPI usa dependency injection para:
- Autenticação (`Depends(get_current_user)`)
- Rate limiting
- Configuração

### 2. Factory Pattern

`StatisticalEngine` e `DataProcessor` são instanciados como singletons na camada de roteamento.

### 3. Strategy Pattern

Diferentes estratégias de análise podem ser aplicadas dependendo do tipo de dados.

### 4. Middleware Pattern

Stack de middlewares para cross-cutting concerns:
- Logging
- CORS
- Request tracking

## Segurança

### Camadas de Segurança

1. **Network Level**
   - HTTPS obrigatório (produção)
   - Ingress com TLS
   - Rate limiting no Nginx

2. **Application Level**
   - OAuth2 authentication
   - Scope-based authorization
   - Request validation
   - Data masking

3. **Container Level**
   - Non-root user (uid 1000)
   - Read-only filesystem (quando possível)
   - Dropped capabilities
   - Security context constraints

## Escalabilidade

### Horizontal Scaling

```yaml
HPA Configuration:
  min: 2 replicas
  max: 10 replicas
  triggers:
    - CPU: 70%
    - Memory: 80%
```

### Performance Optimizations

1. **NumPy/SciPy** - Operações vetorizadas
2. **Async/Await** - I/O não bloqueante
3. **Connection pooling** - Reuso de conexões
4. **Caching** - Considerar Redis para rate limiting

### Resource Limits

```yaml
Requests:
  CPU: 500m
  Memory: 512Mi
Limits:
  CPU: 1000m
  Memory: 1Gi
```

## Observabilidade

### Logging

**Estrutura dos logs:**
```json
{
  "timestamp": "2025-02-20T12:00:00Z",
  "level": "INFO",
  "request_id": "uuid",
  "dataset": "sales_revenue",
  "period": "2025-01",
  "processing_time_ms": 125.5,
  "exec_status": "success"
}
```

### Tracing

- OpenTelemetry instrumentation
- Exportação para Grafana Tempo
- Distributed tracing

### Metrics

**Métricas expostas:**
- Request count
- Response time (histogram)
- Error rate
- CPU/Memory usage
- Active requests

## Deployment

### Ambientes

1. **Development**
   - Docker Compose
   - OAuth disabled
   - Verbose logging

2. **Staging**
   - Kubernetes
   - OAuth enabled
   - Limited replicas

3. **Production**
   - Kubernetes (multi-AZ)
   - Full observability stack
   - Auto-scaling habilitado
   - TLS obrigatório

### CI/CD Pipeline

```
Code Push → Build → Test → Docker Build → Push to Registry → K8s Deploy
```

## Integração com Ecossistema Pulse

### 1. Worker Integration

Worker chama SFB via HTTP:
```python
response = requests.post(
    "https://sfb.pulse.ai/v1/generate",
    headers={"Authorization": f"Bearer {token}"},
    json=payload
)
```

### 2. Orchestrator Integration

Orquestrador registra SFB como componente:
```json
{
  "component_id": "statistical_feature_builder_v1",
  "type": "service",
  "executor": "http"
}
```

### 3. LLM Integration

Output do SFB alimenta prompts LLM:
```
Análise os seguintes dados estatísticos e forneça insights:
[statistical_package]
```

## Considerações Futuras

### Machine Learning

- Detecção de anomalias (Isolation Forest)
- Forecasting avançado (ARIMA, Prophet)
- Clustering automático
- Feature engineering automatizado

### Data Sources

- Integração direta com bancos de dados
- Streaming analytics (Kafka)
- Cache distribuído (Redis)

### Performance

- Processamento paralelo (Dask)
- GPU acceleration (CuPy)
- Batch processing

## Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [NumPy User Guide](https://numpy.org/doc)
- [SciPy Documentation](https://docs.scipy.org)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
