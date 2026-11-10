# CLAUDE.md — Agente 1: Extrator Enriquecido de Contratos

Este arquivo define o contrato de contexto, regras operacionais e especificações técnicas exclusivas do **Agente 1 (Extrator Enriquecido de Contratos)**.

---

## 1. Responsabilidade e Fronteiras de Atuação (Role & Boundary)

O **Agente 1** é um microsserviço especializado em **Processamento e Extração Estruturada de Linguagem Natural Jurídica**.

### O que o Agente 1 FAZ:
- Recebe minutas contratuais em texto bruto via HTTP.
- Decompõe seções documentais (preâmbulo, objeto, valores, prazos, rescisão).
- Executa ferramentas determinísticas em Python para normalização temporal e consistência financeira.
- Valida estruturalmente todas as saídas utilizando modelos **Pydantic v2**.
- Expõe endpoints assíncronos (`/run` e `/status/{task_id}`) para orquestração externa determinística via **n8n**.

### O que o Agente 1 NÃO FAZ (Fronteira Estrita):
- **NÃO** realiza auditoria de conformidade legal, análise de risco ou verificação de regras de negócio corporativas. Essa responsabilidade pertence estritamente ao **Agente 2**.
- **NÃO** chama o Agente 2 diretamente via código interno. A comunicação entre os agentes é desacoplada e realizada unicamente pelo **n8n**.

---

## 2. Hierarquia e Estrutura de Arquivos

```text
agent1/
├── CLAUDE.md                      # Este arquivo: diretrizes e contexto do Agente 1
├── main.py                        # Serviço REST FastAPI com BackgroundTasks (/run e /status)
├── agente_extracao.py             # Pipeline central de extração e orquestração de tools
├── tools.py                       # Ferramentas determinísticas Python (@function_tool)
├── models.py                      # Schemas de dados e validações estruturais Pydantic v2
├── memoria_rag.py                 # Persistência de sessão e busca vetorial RAG
├── contrato_exemplo.txt           # Minuta de contrato para testes e homologação
├── test_api.py                    # Suíte de testes automatizados dos endpoints REST
└── requirements.txt               # Dependências Python específicas do microsserviço
```

---

## 3. Ferramentas Python Integradas (`tools.py`)

O Agente 1 possui três ferramentas determinísticas decoradas com `@function_tool` e tipagem estrita (PEP 484):

1. **`normalizar_prazos_e_datas`**:
   - *Finalidade:* Converte datas para padrão ISO-8601 (`YYYY-MM-DD`), calcula prazo final de vigência somando meses contratados e calcula dias corridos e prazo de aviso prévio.
   - *Assinatura:* `(data_inicio_str: str, meses_vigencia: int, dias_aviso_previo: int = 30) -> str (JSON)`

2. **`extrair_e_validar_tabela_financeira`**:
   - *Finalidade:* Realiza auditoria matemática estrita: multiplica quantidade de parcelas pelo valor unitário, confronta com o valor total e calcula discrepâncias centésimais.
   - *Assinatura:* `(valor_total: float, parcelas_qtd: int, valor_parcela: float, periodicidade: str = "mensal") -> str (JSON)`

3. **`consultar_cadastro_fornecedor`**:
   - *Finalidade:* Consulta a fonte de dados estruturada corporativa em banco relacional (`cadastro_fornecedores`) para recuperar situação cadastral, score de compliance e limite de alçada homologado.
   - *Assinatura:* `(cnpj_cpf: str) -> str (JSON)`
   - *Assinatura:* `(valor_total: float, parcelas_qtd: int, valor_parcela: float, periodicidade: str = 'mensal') -> str (JSON)`

---

## 4. Contratos de API REST (Endpoints)

O serviço é exposto via **FastAPI** rodando por padrão na porta **`8001`**.

### 4.1. `POST /run`
Inicia a extração de forma assíncrona.
- **Status HTTP:** `202 Accepted`
- **Request Body (JSON):**
  ```json
  {
    "texto_contrato": "Texto integral da minuta contratual..."
  }
  ```
- **Response Body (JSON):**
  ```json
  {
    "task_id": "13f30f50-268c-4c2c-bcde-caeafda925e1",
    "status": "pending",
    "message": "Processamento de extração iniciado com sucesso em segundo plano."
  }
  ```

### 4.2. `GET /status/{task_id}`
Consulta o progresso e o resultado da extração.
- **Status HTTP:** `200 OK` (ou `404 Not Found` se `task_id` inexistente)
- **Response Body — Em Processamento (`pending`):**
  ```json
  {
    "task_id": "...",
    "status": "pending",
    "created_at": 1792433716.57,
    "completed_at": null,
    "data": null,
    "error": null
  }
  ```
- **Response Body — Concluído com Sucesso (`done`):**
  ```json
  {
    "task_id": "...",
    "status": "done",
    "created_at": 1792433716.57,
    "completed_at": 1792433716.58,
    "data": {
      "titulo": "Contrato de Prestação de Serviços...",
      "contratante": { "nome": "...", "cnpj_cpf": "...", "papel": "CONTRATANTE" },
      "contratada": { "nome": "...", "cnpj_cpf": "...", "papel": "CONTRATADA" },
      "objeto": "...",
      "financeiro": {
        "moeda": "BRL",
        "valor_total_brl": 120000.0,
        "parcelas_quantidade": 12,
        "valor_parcela_brl": 10000.0,
        "periodicidade": "mensal",
        "soma_consistente": true,
        "discrepancia_centavos": 0.0,
        "cronograma_resumo": "12 parcelas de R$ 10,000.00 (mensal)"
      },
      "vigencia": {
        "data_inicio_iso": "2026-01-15",
        "data_fim_calculada_iso": "2027-01-15",
        "vigencia_meses": 12,
        "dias_corridos_totais": 365,
        "aviso_previo_dias": 30,
        "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"
      },
      "penalidades": {
        "percentual_multa_rescisoria": 20.0,
        "base_calculo": "saldo remanescente do contrato",
        "gatilho_aplicacao": "rescisao_imotivada_sem_justa_causa"
      },
      "secoes_analisadas": ["PREAMBULO", "OBJETO", "PRECO_E_CONDICOES", "VIGENCIA", "RESCISAO_E_PENALIDADES"]
    },
    "error": null
  }
  ```
- **Response Body — Erro (`error`):**
  ```json
  {
    "task_id": "...",
    "status": "error",
    "data": null,
    "error": "Descrição detalhada da falha durante a extração"
  }
  ```

---

## 5. Estratégia de Context Engineering Adotada

1. **Separação Rígida de Conhecimento:** Este arquivo restringe o contexto do Claude Code à camada de extração e API do Agente 1, evitando alucinações sobre regras de negócio que pertencem ao Agente 2.
2. **Contratos Tipados como Especificação:** As entradas e saídas utilizam a especificação de tipos Pydantic v2 (`DadosContratoExtraido`), assegurando serialização determinística para o n8n.
3. **Padrão Assíncrono Desacoplado:** O uso do padrão `202 Accepted` com `task_id` e polling `/status` protege o sistema contra timeouts HTTP em contratos extensos.

---

## 6. Comandos Operacionais

- **Instalar Dependências:**
  ```bash
  pip install -r requirements.txt
  ```
- **Executar o Serviço FastAPI:**
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8001 --reload
  ```
- **Executar a Suíte de Testes dos Endpoints:**
  ```bash
  python test_api.py
  ```
- **Acessar Documentação Interativa:**
  Swagger UI em `http://localhost:8001/docs` e Redoc em `http://localhost:8001/redoc`.
