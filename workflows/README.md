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
     ┌─────┴─────────────────────────┐
     │   LOOP DE POLLING AGENTE 1    │
     │  [Wait 2s]                    │
     │      │                        │
     │  [Agente 1: GET /status]      │
     │      │                        │
     │  [Agente 1 Concluído? (If)] ──┼── (Se pending/false: repete Wait)
     └─────┬─────────────────────────┘
           │ (Se status == 'done')
           ▼
[Roteador: Dados Válidos para Auditoria?] ──(Se inválido)──> [Tratamento de Exceção]
           │ (Se válido: valor > 0 e penalidades)
           ▼
[Agente 2: Submeter POST /run] (Porta 8002 -> Retorna 202 Accepted + task_id)
           │
     ┌─────┴─────────────────────────┐
     │   LOOP DE POLLING AGENTE 2    │
     │  [Wait 2s]                    │
     │      │                        │
     │  [Agente 2: GET /status]      │
     │      │                        │
     │  [Agente 2 Concluído? (If)] ──┼── (Se pending/false: repete Wait)
     └─────┬─────────────────────────┘
           │ (Se status == 'done')
           ▼
[Merge Agente 1 e Agente 2] (Modo Combine / By Position)
           │
           ▼
[Consolidar Dossiê Contratual Final] (Code Node com Decisão de Governança)
           │
           ▼
[AI Agent de Governança Estratégica] (@n8n/n8n-nodes-langchain.agent)
   ├── Conexão ai_languageModel: [LLM Chat Model (OpenRouter)]
   └── Conexão ai_tool: [Tool: Políticas de Governança]
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
6. **Agente 1 Concluído?** (`if`):
   - Avalia se `{{ $json.status }} == "done"`.
   - Se **Falso:** Retorna para o nó *Wait (Polling Agente 1)* em ciclo fechado.
   - Se **Verdadeiro:** Transfere os dados estruturados do contrato para a fase de roteamento.

### Fase 2: Roteamento Inteligente e Decisão
7. **Roteador: Dados Válidos para Auditoria?** (`if`):
   - **Regra de Negócio:** Avalia se o contrato foi extraído com integridade (`valor_total_brl > 0` e cláusulas penais identificadas).
   - **Ramo Falso:** Desvia para o nó **Tratamento de Exceção Contratual**, encerrando a execução com log de auditoria sem onerar custos do Agente 2.
   - **Ramo Verdadeiro:** Prossegue para o Agente 2 e injeta a referência no nó de Merge.

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
11. **Agente 2 Concluído?** (`if`):
    - Avalia se `{{ $json.status }} == "done"`.
    - Se **Falso:** Retorna para o nó *Wait (Polling Agente 2)*.
    - Se **Verdadeiro:** Encaminha o relatório de auditoria para o Merge.

### Fase 4: Merge e Síntese Cognitiva com AI Agent Node
12. **Merge Agente 1 e Agente 2** (`merge`):
    - **Entrada 1:** Dados extraídos pelo Agente 1 (`DadosContratoExtraido`).
    - **Entrada 2:** Relatório de conformidade emitido pelo Agente 2 (`RelatorioConformidade`).
    - **Modo:** `combine` / `mergeByPosition`.
13. **Consolidar Dossiê Contratual Final** (`Code Node`):
    - Agrega os dados estruturados e emite as métricas preliminares de governança corporativa.
14. **AI Agent de Governança Estratégica** (`@n8n/n8n-nodes-langchain.agent`):
    - **Tipo:** LangChain Agent Node (v1.7) integrado nativamente ao n8n.
    - **Entradas de Conexão:**
      - `ai_languageModel`: Conectado a **LLM Chat Model (OpenRouter)** (`@n8n/n8n-nodes-langchain.lmChatOpenAi`), operando com o modelo configurado via OpenRouter.
      - `ai_tool`: Conectado à ferramenta **Tool: Políticas de Governança** (`@n8n/n8n-nodes-langchain.toolCustom`), que consulta de forma determinística os limites corporativos de alçada (R$ 100.000,00) e teto de multas (10% sugerido, 20% crítico).
    - **Responsabilidade:** Interpreta o dossiê consolidado e delibera estrategicamente sobre riscos contratuais, redigindo o parecer definitivo para a Diretoria Executiva.
15. **Dossiê Executivo Homologado** (`Code Node`):
    - Consolida o envelope final com o dossiê técnico e o parecer do AI Agent com timestamp e hash de auditoria.

---

## 3. Sub-workflow Reutilizável: Polling Assíncrono Resiliente

O arquivo [`subworkflow_polling_assincrono.json`](./subworkflow_polling_assincrono.json) foi projetado como um componente reutilizável de mais alto nível para desacoplar a lógica de polling dos fluxos de negócio.

### Como Ele Funciona:
1. **Trigger de Entrada (`executeWorkflowTrigger`):** Recebe o payload `{ "endpoint_status": "http://127.0.0.1:8001/status/", "task_id": "...", "intervalo_segundos": 2, "max_tentativas": 30 }`.
2. **Ciclo de Espera e Tentativas:**
   - Aguarda o intervalo parametrizado (`Wait`).
   - Dispara `GET` no endpoint dinâmico.
   - Avalia se `status == "done"`.
   - Se ainda `pending`, incrementa o contador de tentativas e repete até o teto máximo.
   - Se exceder `max_tentativas`, devolve objeto padronizado com `status: "error"` e código `TIMEOUT_POLLING_EXCEDIDO`.
3. **Reutilização:** Pode ser invocado tanto para o Agente 1 quanto para o Agente 2 através do nó `Execute Workflow` (`n8n-nodes-base.executeWorkflow`), reduzindo drasticamente a complexidade visual do pipeline principal.

---

## 3. Como Importar e Executar no n8n

1. Abra sua instância do n8n (ex: `http://localhost:5678`).
2. No menu lateral, clique em **Workflows** -> **Import from File**.
3. Selecione o arquivo [`workflow_tp4_orquestrador_completo.json`](./workflow_tp4_orquestrador_completo.json).
4. Certifique-se de que os microsserviços estão ativos nas portas correspondentes:
   ```powershell
   # Terminal 1 - Agente 1
   cd agent1
   uvicorn main:app --port 8001

   # Terminal 2 - Agente 2
   cd agent2
   uvicorn main:app --port 8002
   ```
5. Clique em **Execute workflow** na interface do n8n.

---

## 4. Evidência de Execução Real Registrada

A execução ponta a ponta do ciclo assíncrono completo foi validada com os modelos reais e gravada no arquivo:
👉 [`evidencia_execucao_orquestrador_tp4.json`](./evidencia_execucao_orquestrador_tp4.json)

**Métricas da Execução:**
- **Tempo Agente 1 (Extrator):** 14.97s (9 ciclos de polling de 2s)
- **Fornecedor Homologado:** Alfa Consultoria em IA S.A. (Score: 88.5, Limite Alçada: R$ 150.000,00)
- **Tempo Agente 2 (Auditor):** 26.78s (15 ciclos de polling de 2s)
- **Score de Conformidade:** 88.5 / 100.0
- **Nível de Risco Geral:** `ALTO` (devido a multa rescisória contratual de 20% ser superior ao teto de 10-15%)
- **Decisão Final do Orquestrador:** `BLOQUEADO_REVISAO_JURIDICA_OBRIGATORIA`

