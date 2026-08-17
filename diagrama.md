graph TD
    A[Usuário / Webhook] -->|Envia Texto do Contrato| B(n8n: Nó de Entrada)
    
    subgraph Agente 1: Extração
    B -->|Texto Bruto| C[Script Python: OpenAI SDK]
    C -->|Prompt + Structured Outputs| D((LLM))
    D -->|Retorna JSON Validado| C
    end
    
    subgraph Agente 2: Avaliação e Ferramentas
    C -->|Payload JSON| E[Script Python: Agente Validador]
    E <-->|Consulta Regras de Negócio| F[(Banco de Dados SQLite/DuckDB)]
    E -->|Analisa Conformidade| G((LLM))
    end
    
    G -->|Gera Parecer| E
    E -->|Relatório Markdown| H(n8n: Nó de Saída)
    H -->|Entrega Relatório| I[Usuário / Sistema de Destino]
    
    classDef agent fill:#f9f0ff,stroke:#d4b3ff,stroke-width:2px;
    class C,E agent;