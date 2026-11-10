# CLAUDE.md — Agente 2: Avaliador de Conformidade e Risco Contratual

Este arquivo define o contrato de contexto, regras operacionais e especificações técnicas exclusivas do **Agente 2 (Avaliador de Conformidade e Risco)**.

---

## 1. Responsabilidade e Fronteiras de Atuação (Role & Boundary)

O **Agente 2** é um microsserviço especializado em **Auditoria de Governança, Compliance e Análise de Risco Contratual**.

### O que o Agente 2 FAZ:
- Recebe os dados já estruturados do contrato via HTTP (payload JSON entregue pelo orquestrador **n8n**).
- Confronta valores, prazos, penalidades e alçadas contra a base corporativa de regras de negócio.
- Executa ferramentas determinísticas em Python para cálculo de score de conformidade e detecção de violações normativas.
- Emite parecer executivo estruturado e fortemente tipado com **Pydantic v2** (`RelatorioConformidade`).
- Expõe endpoints assíncronos (`POST /run` com `202 Accepted` e `GET /status/{task_id}`) para orquestração externa determinística via **n8n**.

### O que o Agente 2 NÃO FAZ (Fronteira Estrita):
- **NÃO** processa texto bruto de minutas contratuais e **NÃO** faz extração de entidades (essa é a atribuição exclusiva do **Agente 1**).
- **NÃO** chama o Agente 1 diretamente nem depende de acoplamento em código com ele. Toda orquestração é realizada externamente pelo **n8n**.

---

## 2. Hierarquia e Estrutura de Arquivos

```text
agent2/
├── CLAUDE.md              # Este arquivo: diretrizes e contexto exclusivo do Agente 2
├── main.py                # Serviço REST FastAPI com BackgroundTasks (/run e /status)
├── agente_auditoria.py     # Motor de avaliação de regras e geração do parecer
├── tools.py               # Ferramentas determinísticas Python de conformidade e alçada
├── models.py              # Schemas e validações estruturais tipadas com Pydantic v2
├── test_api.py            # Suíte de testes automatizados dos endpoints REST
└── requirements.txt       # Dependências Python específicas do microsserviço
```

---

## 3. Ferramentas Python Integradas (`tools.py`)

1. **`auditar_parametros_contratuais` (`@function_tool`)**:
   - *Finalidade:* Realiza a auditoria determinística de parâmetros contratuais contra as diretrizes corporativas, acionada diretamente pelo Agent via OpenAI Agents SDK:
     - Teto de multa rescisória (alerta caso supere 10.0%).
     - Limite de alçada para aprovação financeira (exige ratificação da Diretoria Executiva acima de R$ 100.000,00).
     - Prazo mínimo de aviso prévio (mínimo de 30 dias).
     - Verificação da regularidade cadastral e score de compliance na fonte estruturada de fornecedores.
   - *Assinatura:* `(valor_total_brl: float, vigencia_meses: int, aviso_previo_dias: int, percentual_multa: float, situacao_fornecedor: str = "ATIVA", score_compliance_fornecedor: float = 90.0) -> str (JSON)`

2. **`consultar_base_regras_negocio_fn`**:
   - *Finalidade:* Fornece os parâmetros vigentes da política interna de riscos e compliance.

3. **Arquitetura do Agente 2:**
   - Instanciado como `Agent(name="AgenteAuditoriaRisco", tools=[auditar_parametros_contratuais], output_type=RelatorioConformidade)`.
   - Executa via `Runner.run` para interpretar o diagnóstico da tool, classificar o risco e redigir o parecer executivo em Markdown.

---

## 4. Contratos de API REST (Endpoints)

O serviço é exposto via **FastAPI** rodando por padrão na porta **`8002`** (diferenciada do Agente 1 para viabilizar execução simultânea).

### 4.1. `POST /run`
Dispara a auditoria de risco de forma assíncrona.
- **Status HTTP:** `202 Accepted`
- **Request Body (JSON):**
  ```json
  {
    "dados_contrato": {
      "titulo": "Contrato de Prestação de Serviços...",
      "financeiro": { "valor_total_brl": 120000.0 },
      "vigencia": { "vigencia_meses": 12, "aviso_previo_dias": 30 },
      "penalidades": { "percentual_multa_rescisoria": 20.0 }
    }
  }
  ```
- **Response Body (JSON):**
  ```json
  {
    "task_id": "a3344d60-8ba6-41ab-9b1a-285ada4c22b9",
    "status": "pending",
    "message": "Auditoria de conformidade iniciada com sucesso em segundo plano."
  }
  ```

### 4.2. `GET /status/{task_id}`
Consulta o progresso e o parecer tipado da auditoria.
- **Status HTTP:** `200 OK` (ou `404 Not Found` se `task_id` inexistente)
- **Response Body — Concluído (`done`):**
  ```json
  {
    "task_id": "a3344d60-8ba6-41ab-9b1a-285ada4c22b9",
    "status": "done",
    "created_at": 1792437581.50,
    "completed_at": 1792437581.51,
    "data": {
      "contrato_titulo": "Contrato de Prestação de Serviços...",
      "score_conformidade": 73.33,
      "nivel_risco_geral": "MEDIO",
      "total_regras_auditadas": 3,
      "itens_conformes": 1,
      "itens_alerta": 2,
      "itens_nao_conformes": 0,
      "itens_auditados": [
        {
          "regra": "Teto de Multa Rescisória",
          "status": "ALERTA",
          "nivel_risco": "MEDIO",
          "descricao_analise": "Multa rescisória fixada em 20.0%, superando a diretriz de governança recomendada de até 10.0%...",
          "fundamentacao": "Política Interna de Riscos Contratuais (Cap. IV, Art. 12)..."
        }
      ],
      "recomendacoes_mitigacao": [
        "Negociar redução da cláusula penal para o patamar padrão de até 10%.",
        "Submeter o contrato à assinatura conjunta da Diretoria Executiva."
      ],
      "parecer_executivo_markdown": "# Parecer de Conformidade e Risco Contratual..."
    },
    "error": null
  }
  ```

---

## 5. Estratégia de Context Engineering Adotada

1. **Separação Rígida de Conhecimento:** Este arquivo delimita expressamente que o Agente 2 opera somente sobre dados estruturados de contratos, mantendo foco na auditoria de conformidade e mitigação de risco.
2. **Contrato de Saída Tipado (`RelatorioConformidade`):** Garante invariantes de modelo via Pydantic v2 (ex: validação de que a soma dos itens auditados coincide com o total).
3. **Desacoplamento Determinístico para o n8n:** O design assíncrono via `POST /run` e polling `GET /status/{task_id}` viabiliza a orquestração limpa por nós HTTP do n8n sem dependência direta de código entre agentes.

---

## 6. Comandos Operacionais

- **Instalar Dependências:**
  ```bash
  pip install -r requirements.txt
  ```
- **Executar o Serviço FastAPI:**
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8002 --reload
  ```
- **Executar a Suíte de Testes dos Endpoints:**
  ```bash
  python test_api.py
  ```
- **Acessar Documentação Interativa:**
  Swagger UI em `http://localhost:8002/docs` e Redoc em `http://localhost:8002/redoc`.
