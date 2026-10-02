# Relatório de Implementação: Memória Persistente (SQLiteSession) e Busca Semântica (RAG)

Este documento registra a implementação de memória persistente em duas camadas para o sistema multi-agente de análise de contratos:
1. **Camada de Histórico de Conversação:** `SQLiteSession` integrada ao **OpenAI Agents SDK** para retenção contínua entre execuções distintas.
2. **Camada de Recuperação Semântica (RAG):** Pipeline com embeddings vetoriais (`text-embedding-3-small`) e busca por similaridade de cosseno em SQLite.

---

## 🎯 1. Arquitetura da Solução de Memória

Para que o agente evolua de um componente efêmero para um sistema corporativo funcional, o ecossistema foi estruturado em duas camadas de persistência:

```mermaid
graph TD
    subgraph "Camada 1: Histórico de Conversação (Sessão)"
        User[Usuário / Diretor Jurídico] -->|Interação 1: Define Diretrizes| S1(SQLiteSession)
        S1 --> DB1[(SQLite: sessoes_historico)]
        User -->|Interação 2: Nova Execução| S1
        DB1 -.->|Restaura Histórico Completo| S1
    end

    subgraph "Camada 2: Memória Semântica Corporativa (RAG)"
        Precedentes[Precedentes & Contratos Anteriores] --> Emb[text-embedding-3-small]
        Emb --> DB2[(SQLite: rag_documentos <br/> Vetores 1536d)]
        NovaSessao[Nova Sessão / Outro Caso] --> ToolRAG[@function_tool: buscar_precedentes_contratuais_rag]
        ToolRAG <-->|Busca Vetorial por Cosseno| DB2
    end
```

---

## 🗄️ 2. Camada 1: SQLiteSession (Histórico de Conversação)

A classe `SQLiteSession` foi implementada no módulo [`agent/memoria_rag.py`](../agent/memoria_rag.py), herdando diretamente da interface abstrata `SessionABC` do OpenAI Agents SDK (`agents.memory.SessionABC`).

### 2.1 Estrutura da Tabela SQLite (`sessoes_historico`)
- **`id`**: Identificador autoincremental primário.
- **`session_id`**: Identificador único da sessão conversacional (indexado para busca rápida).
- **`item_data`**: Payload JSON serializado contendo o histórico estruturado dos turnos de mensagens entre usuário e assistente.
- **`created_at`**: Registro temporal da inserção.

### 2.2 Métodos do Protocolo `SessionABC`
- **`add_items(items: list[TResponseInputItem])`**: Serializa os turnos da conversa (usuário e assistente) e insere no banco.
- **`get_items(limit: int | None)`**: Recupera em ordem cronológica o histórico exato associado ao `session_id`.
- **`pop_item()`**: Remove o último turno (útil para retentativas ou backtracks).
- **`clear_session()`**: Limpa o histórico de uma sessão específica.

### 2.3 Evidência de Continuidade entre Runs Distintos
No script [`agent/demo_memoria_rag.py`](../agent/demo_memoria_rag.py):
1. **Run 1:** O usuário estabelece as diretrizes da TechSolutions (teto de multa de 10% e foro em São Paulo/SP). O diálogo é persistido.
2. **Run 2:** Em nova execução independente, a sessão `sessao_auditoria_techsolutions_01` é instanciada novamente do zero. O agente recupera o histórico e responde à pergunta *"Quais são as nossas regras para multa rescisória e foro?"*, mantendo coerência sem necessidade de reintroduzir o contexto.

---

## 🔍 3. Camada 2: Pipeline RAG com Embeddings e Vector Store

O pipeline RAG indexa precedentes contratuais, aditivos prévios e jurisprudência em formato vetorial de alta dimensionalidade.

### 3.1 Modelo de Embeddings e Armazenamento
- **Modelo:** `text-embedding-3-small` (vetores de 1536 dimensões gerados via OpenRouter/OpenAI API).
- **Fallback:** Gerador vetorial determinístico baseado em dispersão de hash criptográfico para execução offline/contingência.
- **Métrica de Similaridade:** Similaridade de Cosseno:
$$\text{CosSim}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$

### 3.2 Estrutura da Base Vetorial SQLite (`rag_documentos`)
- **`documento_id`**: Código identificador único do precedente (ex: `PRECEDENTE-ALFA-2025-01`).
- **`titulo`**: Nome e modalidade do termo contratual ou aditivo.
- **`conteudo`**: Texto integral da cláusula ou deliberação histórica.
- **`categoria`**: Classificação temática (`jurisprudencia`, `aditivo_anterior` ou `politica_interna`).
- **`metadados`**: Metadados adicionais em JSON.
- **`vetor_embedding`**: Vetor serializado em formato JSON contendo os 1536 floats derivados do modelo de embeddings.

### 3.3 Ferramenta Exposta ao Agente (`@function_tool`)
- **Função:** `buscar_precedentes_contratuais_rag(query: str) -> str`
- **Operação:** Gera o embedding da consulta textual, calcula a similaridade de cosseno contra os registros da base e retorna o precedente mais aderente enriquecido com score e metadados.

---

## 🧪 4. Demonstração Prática: Uso de Conhecimento Prévio em Nova Sessão

No teste executado em [`agent/demo_memoria_rag.py`](../agent/demo_memoria_rag.py), foi criada uma sessão totalmente nova (`sessao_nova_auditoria_2026_x`), **sem nenhum histórico prévio de mensagens**.

O usuário submete a seguinte dúvida sobre um novo contrato:
> *"Estamos analisando um novo contrato da Alfa Consultoria em IA que contém multa rescisória de 20%. Já tivemos algum precedente ou aditivo anterior com essa empresa sobre essa mesma cláusula? O que foi acordado?"*

### Fluxo de Execução do Agente:
1. O agente identifica a necessidade de consulta de precedentes e aciona `buscar_precedentes_contratuais_rag("precedente multa rescisoria Alfa Consultoria IA")`.
2. O RAG calcula a proximidade semântica dos embeddings e localiza o documento **`PRECEDENTE-ALFA-2025-01`** com **score de similaridade 0.6525**.
3. **Resposta Emitida pelo Agente:**
> *"Sim! Localizei em nosso banco de precedentes o documento 'Aditivo Contratual nº 1 - Alfa Consultoria em IA e TechSolutions (2025)' (Similaridade Semântica: 0.6525).*  
> *Histórico Relevante: No contrato firmado em 2025 com a Alfa Consultoria em IA S.A., a minuta original também previa multa rescisória de 20%. A TechSolutions contestou a desproporcionalidade e foi firmado o Termo Aditivo nº 1 reduzindo a penalidade para 10% sobre o saldo remanescente, com aviso prévio de 30 dias.*  
> *Recomendação para este novo contrato: Rejeitar a multa de 20% proposta e exigir a aplicação do mesmo padrão de 10% já aceito e praticado pela Alfa Consultoria no aditivo anterior."*

---

## 📊 5. Evidência em Arquivo (`agent/registro_memoria_rag.json`)

O arquivo [`agent/registro_memoria_rag.json`](../agent/registro_memoria_rag.json) consolida os dados da demonstração:

```json
{
  "sqlite_session": {
    "session_id": "sessao_auditoria_techsolutions_01",
    "banco_sqlite": "banco_memoria_contratos.db",
    "total_mensagens_persistidas": 4,
    "continuidade_comprovada": true
  },
  "rag_embeddings": {
    "modelo_embeddings": "text-embedding-3-small",
    "dimensao_vetores": 1536,
    "consulta_realizada": "precedente multa rescisoria Alfa Consultoria IA",
    "top_match": {
      "documento_id": "PRECEDENTE-ALFA-2025-01",
      "titulo": "Aditivo Contratual nº 1 - Alfa Consultoria em IA e TechSolutions (2025)",
      "score_similaridade": 0.6525,
      "conteudo_recuperado": "Em contrato anterior de desenvolvimento de IA firmado em 2025 com a Alfa Consultoria em IA S.A., a cláusula de multa rescisória de 20% foi contestada pela TechSolutions e reduzida via Termo Aditivo para 10% sobre o saldo remanescente, com fixação de aviso prévio de 30 dias e foro em São Paulo/SP."
    },
    "integracao_em_nova_sessao": true
  }
}
```
