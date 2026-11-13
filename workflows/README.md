# Orquestrador n8n Multi-Agentes — Análise e Auditoria de Contratos (TP4)

Este diretório contém o workflow completo de orquestração assíncrona entre o **Agente 1 (Extrator e Normalizador)** e o **Agente 2 (Auditor de Risco e Conformidade)**, construído para a plataforma **n8n**.

O **n8n atua como o único orquestrador do sistema**: os dois agentes operam como microsserviços REST desacoplados em processos e portas distintas (Porta `8001` para o Agente 1 e Porta `8002` para o Agente 2), comunicando-se exclusivamente por meio de contratos HTTP tipados mediados pelo n8n.

---

## 1. Arquitetura do Workflow no n8n

O arquivo [`workflow_tp4_orquestrador_completo.json`](./workflow_tp4_orquestrador_completo.json) implementa o ciclo assíncrono completo em 4 fases:

```
[Trigger Manual / Webhook]
           │
           ▼
[Preparar Minuta Contratual]
           │
           ▼
[Agente 1: Submeter POST /run] (Porta 8001 -> Retorna 202 Accepted + task_id)
           │
     ┌─────┴─────────────────────────────┐
     │     LOOP DE POLLING AGENTE 1      │
     │  [Wait 2s]                        │
     │      │                            │
     │  [Agente 1: GET /status]          │
     │      │                            │
     │  [Agente 1 Concluído? (If)]       │
     │      │ (False)                    │
     │  [Agente 1 Falhou? (If)] ──(True)─┼──> [Tratamento de Exceção Contratual]
     │      │ (False: pending)           │
     └──────┴────────────────────────────┘
           │ (Se status == 'done')
           ▼
[Roteador: Dados Válidos para Auditoria?] ──(Se inválido)──> [Tratamento de Exceção Contratual]
           │ (Se válido: valor_total_brl > 0 e penalidades)
           ├─────────────────────────────────────────────────┐
           ▼                                                 ▼
[Agente 2: Submeter POST /run] (Porta 8002)     [Empacotar Saída Agente 1]
           │                                                 │
     ┌─────┴─────────────────────────────┐                   │
     │     LOOP DE POLLING AGENTE 2      │                   │
     │  [Wait 2s]                        │                   │
     │      │                            │                   │
     │  [Agente 2: GET /status]          │                   │
     │      │                            │                   │
     │  [Agente 2 Concluído? (If)]       │                   │
     │      │ (False)                    │                   │
     │  [Agente 2 Falhou? (If)] ──(True)─┼──> [Exceção]      │
     └──────┴────────────────────────────┘                   │
           │ (Se status == 'done')                           │
           ▼                                                 │
[Empacotar Saída Agente 2]                                   │
           │                                                 │
           └──────────────────────┬──────────────────────────┘
                                  ▼
                    [Merge Agente 1 e Agente 2] (combine / combineByPosition)
                                  │
                                  ▼
                    [Consolidar Dossiê Contratual Final] (Lê item mesclado do Merge)
                                  │
                                  ▼
                    [AI Agent de Governança Estratégica] (@n8n/n8n-nodes-langchain.agent)
                       ├── ai_languageModel: [LLM Chat Model (OpenRouter)]
                       └── ai_tool: [Tool: Políticas de Governança] (@n8n/n8n-nodes-langchain.toolCode)
                                  │
                                  ▼
                    [Dossiê Executivo Homologado] (Entrega Estruturada Final)
```

---

## 2. Descrição dos Nós do Workflow Principal

### Fase 1: Ingestão e Agente 1 (Extrator)
1. **Disparo Manual (Input Contrato)**: Nó trigger (`manualTrigger`) que inicia a execução sob demanda.
2. **Preparar Minuta Contratual** (`Code Node`): Injeta o texto integral do contrato (`texto_contrato`) e metadados da solicitação.
3. **Agente 1: Submeter POST /run** (`httpRequest`):
   - **Método:** `POST`
   - **URL:** `http://127.0.0.1:8001/run`
   - **Headers:** `Content-Type: application/json`
   - **Body:** `{ "texto_contrato": "..." }`
   - **Resposta:** `202 Accepted` com `{"task_id": "...", "status": "pending"}`
4. **Wait (Polling Agente 1)** (`wait`): Pausa a execução por 2 segundos antes de cada verificação.
5. **Agente 1: Consultar GET /status** (`httpRequest`):
   - **Método:** `GET`
   - **URL:** `http://127.0.0.1:8001/status/{{ $('Agente 1: Submeter POST /run').item.json.task_id }}`
6. **Agente 1 Concluído?** (`if`) e **Agente 1 Falhou?** (`if`):
   - Avalia se `{{ $json.status }} == "done"`.
   - Se **Verdadeiro:** Encaminha os dados extraídos para a fase de roteamento.
   - Se **Falso:** Verifica se `status == "error"`; em caso afirmativo desvia imediatamente para **Tratamento de Exceção Contratual** (evitando loop infinito), caso contrário (`pending`) retorna ao *Wait (Polling Agente 1)*.

### Fase 2: Roteamento Inteligente e Decisão
7. **Roteador: Dados Válidos para Auditoria?** (`if`):
   - **Regra de Negócio:** Avalia com combinador `and` se `valor_total_brl > 0` e se há objeto de `penalidades` extraído.
   - **Ramo Falso:** Desvia para o nó **Tratamento de Exceção Contratual**, encerrando a execução com log de auditoria sem onerar o Agente 2.
   - **Ramo Verdadeiro:** Prossegue em paralelo lógico para o Agente 2 e para **Empacotar Saída Agente 1** (`{ agente1_resultado: $json }`), preservando integralmente o retorno do Agente 1 antes do `Merge`.

### Fase 3: Agente 2 (Auditor de Conformidade e Risco)
8. **Agente 2: Submeter POST /run** (`httpRequest`):
   - **Método:** `POST`
   - **URL:** `http://127.0.0.1:8002/run`
   - **Headers:** `Content-Type: application/json`
   - **Body:** `{ "dados_contrato": {{ JSON.stringify($json.data) }} }`
   - **Resposta:** `202 Accepted` com `{"task_id": "...", "status": "pending"}`
9. **Wait (Polling Agente 2)** (`wait`): Pausa de 2 segundos entre sondagens.
10. **Agente 2: Consultar GET /status** (`httpRequest`):
    - **Método:** `GET`
    - **URL:** `http://127.0.0.1:8002/status/{{ $('Agente 2: Submeter POST /run').item.json.task_id }}`
11. **Agente 2 Concluído?** (`if`) e **Agente 2 Falhou?** (`if`):
    - Encaminha para **Empacotar Saída Agente 2** quando `status == "done"`, trata falha imediata se `status == "error"`, ou repete a espera se `pending`.

### Fase 4: Merge Sem Perdas e Síntese Cognitiva com AI Agent Node
12. **Merge Agente 1 e Agente 2** (`merge` v3 — `mode: "combine"`, `combineBy: "combineByPosition"`):
    - **Entrada 1 (`index: 0`):** `{ agente1_resultado }` vindo de **Empacotar Saída Agente 1** (`DadosContratoExtraido`).
    - **Entrada 2 (`index: 1`):** `{ agente2_resultado }` vindo de **Empacotar Saída Agente 2** (`RelatorioConformidade`).
    - O empacotamento em chaves distintas evita qualquer colisão entre campos homônimos (`task_id`, `status`, `data`).
13. **Consolidar Dossiê Contratual Final** (`Code Node`):
    - Lê diretamente `itemMesclado.agente1_resultado` e `itemMesclado.agente2_resultado` do fluxo entregue pelo nó `Merge` e calcula métricas e decisão preliminar de governança.
14. **AI Agent de Governança Estratégica** (`@n8n/n8n-nodes-langchain.agent` v1.7):
    - **Entradas de Conexão:**
      - `ai_languageModel`: Conectado a **LLM Chat Model (OpenRouter)** (`@n8n/n8n-nodes-langchain.lmChatOpenAi` configurado com `baseURL: https://openrouter.ai/api/v1`).
      - `ai_tool`: Conectado à ferramenta **Tool: Políticas de Governança** (`@n8n/n8n-nodes-langchain.toolCode`, linguagem JavaScript), que retorna os limites corporativos vigentes de alçada (R$ 100.000,00) e teto de multas (10% recomendado, 20% crítico).
    - **Responsabilidade:** Analisa o dossiê mesclado, consulta a tool e emite o parecer estratégico definitivo.
15. **Dossiê Executivo Homologado** (`Code Node`):
    - Consolida o envelope final com o dossiê técnico e a deliberação executiva do AI Agent.

---

## 3. Sub-workflow Reutilizável: Polling Assíncrono Resiliente

O arquivo [`subworkflow_polling_assincrono.json`](./subworkflow_polling_assincrono.json) foi projetado como um componente reutilizável de alto nível para desacoplar a lógica de polling dos fluxos de negócio e ser invocado isoladamente via nó `Execute Workflow` (`n8n-nodes-base.executeWorkflow`).

### Máquina de Estados Sem Perda de Contexto:
1. **Trigger de Execução (`executeWorkflowTrigger`) + `Inicializar Contador de Polling`:** Recebe `{ "endpoint_status": "http://127.0.0.1:8001/status/", "task_id": "...", "intervalo_segundos": 2, "max_tentativas": 30 }` e inicia `tentativa_atual = 0`.
2. **`Incrementar Tentativa` -> `Aguardar Intervalo (Wait)` -> `Consultar Status HTTP GET`:** Incrementa o contador dinâmico e consulta a API preservando os parâmetros na execução atual.
3. **`Consolidar Estado do Polling`:** Recombina `$('Incrementar Tentativa').last().json` com a resposta HTTP atual, garantindo que `endpoint_status`, `tentativa_atual` e `max_tentativas` nunca sejam sobrescritos entre iterações.
4. **`Tarefa Finalizada (Status Done)?` e `Erro ou Tentativas Esgotadas?`:**
   - Se `status == "done"`: devolve objeto padronizado `{ sucesso: true, task_id, status, tentativas_realizadas, created_at, completed_at, data }`.
   - Se `status == "error"` ou `tentativa_atual >= max_tentativas`: encerra o ciclo imediatamente retornando `{ sucesso: false, status: "error", motivo: "ERRO_EXECUCAO_AGENTE" | "TIMEOUT_POLLING_EXCEDIDO" }`.
   - Caso contrário: retorna o item consolidado para `Incrementar Tentativa`, prosseguindo para a próxima iteração.

---

## 4. Como Importar e Executar no n8n

1. Abra sua instância do n8n (ex: `http://localhost:5678`).
2. Importe [`subworkflow_polling_assincrono.json`](./subworkflow_polling_assincrono.json) e [`workflow_tp4_orquestrador_completo.json`](./workflow_tp4_orquestrador_completo.json) em **Workflows** -> **Import from File**.
3. Certifique-se de que os microsserviços estão ativos nas portas correspondentes:
   ```powershell
   # Terminal 1 - Agente 1
   cd agent1
   uvicorn main:app --port 8001

   # Terminal 2 - Agente 2
   cd agent2
   uvicorn main:app --port 8002
   ```
4. Clique em **Execute workflow** na interface do n8n ou execute o verificador automatizado `python workflows/test_orquestracao_pipeline.py`.

---

## 5. Evidência de Execução Real Registrada

A execução ponta a ponta do ciclo assíncrono completo foi validada com os modelos reais e gravada no arquivo:
👉 [`evidencia_execucao_orquestrador_tp4.json`](./evidencia_execucao_orquestrador_tp4.json)
