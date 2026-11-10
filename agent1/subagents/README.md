# Subagentes do Agente 1 (Extrator Enriquecido de Contratos)

Este diretório contém a especificação formal e arquitetura dos subagentes especializados que operam sob governança do Agente 1.

---

## 1. Subagente: `validador-cadastral-fornecedor`
- **Arquivo de Especificação:** [`validador_cadastral.md`](./validador_cadastral.md)
- **Implementação Python:** [`../subagente_cadastral.py`](../subagente_cadastral.py)
- **Papel (*Role*):** Especialista em Homologação e Diligência Cadastral de Fornecedores
- **Ferramentas (*Tools*):** `consultar_cadastro_fornecedor`
- **Contrato de Saída:** `FornecedorHomologadoInfo` (Pydantic v2)

---

## 2. Justificativa Técnica do Isolamento de Contexto

A decisão de isolar a diligência cadastral em um subagente independente é fundamentada em três pilares arquiteturais:

### A. Economia de Tokens e Otimização da Janela de Contexto (*Context Budget*)
Minutas contratuais de tecnologia frequentemente contêm entre 10 e 50 páginas com descrições técnicas de produto, SLAs, anexos e fórmulas de reajuste. O Agente 1 (Extrator Principal) necessita processar essa grande massa textual para estruturar as cláusulas principais. 
Ao delegar a homologação cadastral para um subagente dedicado que recebe **apenas o CNPJ e o nome das partes**, eliminamos a necessidade de passar o texto integral da minuta para essa etapa, poupando tokens e reduzindo a latência global.

### B. Eliminação de Ambiguidade de Papéis (*Role Confusion & Anti-Hallucination*)
O Agente 1 possui como missão primordial a **fidelidade estrita ao texto da minuta** (extração factual). Se o mesmo modelo for incumbido de realizar a diligência de conformidade cadastral e verificar antecedentes empresariais no banco de dados corporativo, ele corre o risco de contaminar o texto da minuta com informações históricas do fornecedor (ou vice-versa). O isolamento de contexto garante que a consulta ao cadastro relacional corporativo ocorra em uma sessão isolada, retornando dados estruturados e limpos.

### C. Princípio do Menor Privilégio (*Least Privilege Security*)
Apenas o subagente `validador-cadastral-fornecedor` necessita de acesso à ferramenta de consulta ao banco de dados relacional `cadastro_fornecedores`. O pipeline principal de normalização matemática de datas e parcelas não requer nem deve possuir permissão para ler tabelas cadastrais confidenciais, minimizando a superfície de risco.

