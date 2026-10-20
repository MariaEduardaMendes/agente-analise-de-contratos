# Contrato de Integração REST e Especificação do Workflow n8n

**Projeto:** Sistema Multi-Agente de Análise e Auditoria de Contratos  
**Entrega:** TP3 — Integração Introdutória via n8n e Contratos de Microsserviços  
**Autora:** Maria Eduarda Mendes  
**Repositório:** `MariaEduardaMendes/agente-analise-de-contratos`  

---

## 1. Visão Geral da Arquitetura de Integração

Nesta etapa do projeto, o **n8n** é introduzido como o **orquestrador determinístico central** do ecossistema. 

Para assegurar total desacoplamento e escalabilidade:
1. Os agentes operam como **microsserviços HTTP independentes**, sem qualquer chamada direta de código entre si.
2. Cada agente expõe endpoints padronizados assíncronos (`POST /run` retornando `202 Accepted` e `GET /status/{task_id}`).
3. O n8n é o único responsável por capturar o evento de entrada, despachar o job para o primeiro agente, coletar o resultado estruturado e encaminhá-lo ao segundo agente.

```
┌─────────────────┐      HTTP POST /run       ┌────────────────────────┐
│                 │ ────────────────────────> │   Agente 1 (FastAPI)   │
│                 │ <──────────────────────── │   Porta 8001 (/run)    │
│                 │      202 Accepted         └────────────────────────┘
│                 │                                        │ BackgroundTask
│                 │      HTTP GET /status                  ▼
│       n8n       │ ────────────────────────> ┌────────────────────────┐
│  Orquestrador   │ <──────────────────────── │   Status: 'done'       │
│  Determinístico │      Payload Extraído     │   DadosContratoExtraido│
│                 │                           └────────────────────────┘
│                 │
│                 │      HTTP POST /run       ┌────────────────────────┐
│                 │ ────────────────────────> │   Agente 2 (FastAPI)   │
│                 │ <──────────────────────── │   Porta 8002 (/run)    │
│                 │      202 Accepted         └────────────────────────┘
│                 │                                        │ BackgroundTask
│                 │      HTTP GET /status                  ▼
│                 │ ────────────────────────> ┌────────────────────────┐
│                 │ <──────────────────────── │   Status: 'done'       │
│                 │      Relatório Risco      │   RelatorioConformidade│
└─────────────────┘                           └────────────────────────┘
```

---

## 2. O Workflow n8n Implementado (`workflow_tp3_agente_extracao.json`)

O arquivo [`workflow_tp3_agente_extracao.json`](workflow_tp3_agente_extracao.json) implementa a validação ponta a ponta do consumo HTTP do primeiro agente pelo n8n.

### 2.1 Nós do Workflow Construído e Homologado:
1. **Trigger de Entrada (`When clicking ‘Execute workflow’`):** Dispara a automação sob demanda na interface do n8n.
2. **Nó `HTTP Request` — Disparo do Agente 1 (`POST /run`):**
   - URL: `http://172.17.0.1:8001/run` (acesso do container n8n ao host do serviço).
   - Envia o texto da minuta no corpo JSON da requisição.
   - Recebe a resposta imediata `202 Accepted` com `task_id` e status `pending`.
3. **Nó `Wait`:**
   - Pausa a execução por 2 segundos enquanto a `BackgroundTask` do FastAPI executa a extração, o cálculo de datas ISO e a validação matemática das parcelas.
4. **Nó `HTTP Request1` — Consulta de Status do Agente 1 (`GET /status`):**
   - URL: `http://172.17.0.1:8001/status/{{ $json.task_id }}`.
   - Captura os dados estruturados no formato Pydantic `DadosContratoExtraido`.


### 2.2 Como Importar no n8n:
1. Abra a interface do n8n em seu navegador (`http://localhost:5678`).
2. No menu superior direito de workflows, selecione **"Import from File"** (ou arraste o arquivo).
3. Selecione o arquivo `n8n/workflow_tp3_agente_extracao.json`.
4. Clique em **"Execute Workflow"** para testar.

---

## 3. Especificação dos Contratos REST dos Dois Agentes

### 3.1 Agente 1: Extrator Enriquecido de Contratos (Porta `8001`)

| Endpoint | Método | Descrição | Status HTTP |
| :--- | :---: | :--- | :---: |
| `/run` | `POST` | Recebe a minuta em texto e inicia extração assíncrona | `202 Accepted` |
| `/status/{task_id}` | `GET` | Consulta o status e retorna entidades extraídas | `200 OK` / `404 Not Found` |
| `/health` | `GET` | Healthcheck do serviço | `200 OK` |

#### Contrato de Entrada — `POST /run`:
```json
{
  "texto_contrato": "Texto integral da minuta contratual em formato bruto..."
}
```

#### Contrato de Saída Imediata — `POST /run` (`202 Accepted`):
```json
{
  "task_id": "ca1bae57-cb6d-4451-8778-d4b2326ebbca",
  "status": "pending",
  "message": "Processamento de extração iniciado com sucesso em segundo plano."
}
```

#### Contrato de Saída — `GET /status/{task_id}` (`200 OK` com dados concluídos):
- **Estados Possíveis:** `pending`, `done`, `error`.
```json
{
  "task_id": "ca1bae57-cb6d-4451-8778-d4b2326ebbca",
  "status": "done",
  "created_at": 1792438112.03,
  "completed_at": 1792438112.04,
  "data": {
    "titulo": "Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
    "contratante": {
      "nome": "Empresa Contratante S.A.",
      "cnpj_cpf": "98.765.432/0001-10",
      "papel": "CONTRATANTE"
    },
    "contratada": {
      "nome": "TechSolutions Ltda.",
      "cnpj_cpf": "12.345.678/0001-90",
      "papel": "CONTRATADA"
    },
    "objeto": "Desenvolvimento, homologação e implantação de agentes inteligentes integrados a sistemas legados.",
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

---

### 3.2 Agente 2: Avaliador de Conformidade e Risco (Porta `8002`)

| Endpoint | Método | Descrição | Status HTTP |
| :--- | :---: | :--- | :---: |
| `/run` | `POST` | Recebe dados estruturados e inicia auditoria assíncrona | `202 Accepted` |
| `/status/{task_id}` | `GET` | Consulta o status e retorna parecer tipado | `200 OK` / `404 Not Found` |
| `/health` | `GET` | Healthcheck do serviço | `200 OK` |

#### Contrato de Entrada — `POST /run`:
O n8n consome a chave `"data"` gerada pelo Agente 1 e injeta diretamente no Agente 2:
```json
{
  "dados_contrato": {
    "titulo": "Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
    "financeiro": {
      "valor_total_brl": 120000.0,
      "parcelas_quantidade": 12,
      "valor_parcela_brl": 10000.0
    },
    "vigencia": {
      "vigencia_meses": 12,
      "aviso_previo_dias": 30
    },
    "penalidades": {
      "percentual_multa_rescisoria": 20.0
    }
  }
}
```

#### Contrato de Saída — `GET /status/{task_id}` (`200 OK` com parecer concluído):
- **Estados Possíveis:** `pending`, `done`, `error`.
```json
{
  "task_id": "d6b391b8-3895-4388-a3dc-0e7e426d30bc",
  "status": "done",
  "created_at": 1792438113.58,
  "completed_at": 1792438113.58,
  "data": {
    "contrato_titulo": "Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
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
        "descricao_analise": "Multa rescisória fixada em 20.0%, superando a diretriz de governança recomendada de até 10.0% sobre o saldo remanescente.",
        "fundamentacao": "Política Interna de Riscos Contratuais (Cap. IV, Art. 12) e Jurisprudência Cível."
      },
      {
        "regra": "Alçada de Aprovação Financeira",
        "status": "ALERTA",
        "nivel_risco": "ALTO",
        "descricao_analise": "Valor global do contrato (R$ 120,000.00) excede a alçada gerencial (R$ 100,000.00), demandando obrigatoriamente ratificação formal da Diretoria Executiva.",
        "fundamentacao": "Manual de Alçadas e Governança Financeira - Alçada Nível 1."
      },
      {
        "regra": "Prazo Mínimo de Aviso Prévio",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Aviso prévio pactuado (30 dias) atende integralmente ao requisito de segurança.",
        "fundamentacao": "Diretriz Operacional de Continuidade de Negócios."
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

## 4. Orquestração Multi-Agente no TP4 (Visão de Expansão)

No **TP4**, o fluxo demonstrativo construído neste TP3 será expandido para a **orquestração determinística completa** entre os dois agentes, seguindo o padrão de **Saga / Polling Assíncrono**:

### Passo a Passo da Orquestração no TP4:
1. **Gatilho Único:** O webhook do n8n recebe a minuta submetida por um canal de mensageria (ex: Telegram, Chatbot ou upload de arquivo).
2. **Acionamento do Agente 1 (Extração):** O n8n faz `POST http://localhost:8001/run` enviando a minuta e armazena o `task_id_1`.
3. **Polling Loop 1:** Um loop no n8n consulta `GET http://localhost:8001/status/{task_id_1}` até que o status seja `done`.
4. **Transformação de Dados no n8n (Data Mapping):** Sem que os agentes conversem entre si, o n8n extrai o campo `data` retornado pelo Agente 1 e monta o payload de conformidade `{"dados_contrato": $json.data}`.
5. **Acionamento do Agente 2 (Auditoria):** O n8n faz `POST http://localhost:8002/run` com os dados mapeados e armazena o `task_id_2`.
6. **Polling Loop 2:** O n8n consulta `GET http://localhost:8002/status/{task_id_2}` até obter status `done`.
7. **Consolidação Final:** O n8n concatena a tabela de metadados extraídos pelo Agente 1 com o parecer executivo em Markdown emitido pelo Agente 2, enviando um relatório final completo ao usuário.

### Vantagens Desta Abordagem:
- **Zero Acoplamento:** Se a política de compliance do Agente 2 mudar ou se o Agente 1 for reescrito em outra tecnologia, nenhum dos agentes quebra.
- **Tolerância a Falhas:** Se um agente demorar minutos para processar, o padrão `202 Accepted` e o polling evitam timeout na conexão HTTP.
- **Rastreabilidade Total:** O histórico de execuções do n8n registra cada payload intermediário, funcionando como auditoria visual do pipeline.
