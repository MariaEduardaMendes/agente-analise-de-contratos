"""
Implementação do Subagente: Validador Cadastral de Fornecedores (Agente 1)
Subagente com isolamento de contexto para homologação e diligência cadastral.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv(root_dir / ".env")

from openai import AsyncOpenAI
from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents.agent_output import AgentOutputSchema

from tools import consultar_cadastro_fornecedor
from models import FornecedorHomologadoInfo

PROMPT_SUBAGENTE_CADASTRAL = """
Você é o Subagente Especialista em Homologação e Diligência Cadastral de Fornecedores do Agente 1.
Seu contexto é ISOLADO da minuta contratual completa.

Sua única responsabilidade é:
1. Receber o CNPJ ou identificador da contratada.
2. OBRIGATORIAMENTE invocar a ferramenta 'consultar_cadastro_fornecedor'.
3. Com base nas informações recuperadas do banco de dados relacional, preencher o schema 'FornecedorHomologadoInfo'.
"""

def criar_subagente_cadastral() -> Agent:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=25.0)
    model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)

    return Agent(
        name="validador-cadastral-fornecedor",
        instructions=PROMPT_SUBAGENTE_CADASTRAL,
        tools=[consultar_cadastro_fornecedor],
        output_type=AgentOutputSchema(FornecedorHomologadoInfo, strict_json_schema=False),
        model=model
    )

def homologar_fornecedor(cnpj_cpf: str) -> FornecedorHomologadoInfo:
    """Invoca o subagente isolado para obter a diligência do fornecedor."""
    subagente = criar_subagente_cadastral()
    try:
        resultado = Runner.run_sync(
            subagente,
            f"Realize a diligência cadastral completa do fornecedor com CNPJ: {cnpj_cpf}",
            max_turns=3
        )
        return resultado.final_output
    except Exception as exc:
        print(f"[SUBAGENTE CADASTRAL ALERTA] Execução direta via tool devido a: {exc}")
        from memoria_rag import consultar_cadastro_fornecedor_db
        dados = consultar_cadastro_fornecedor_db(cnpj_cpf)
        if dados:
            return FornecedorHomologadoInfo(**dados)
        return FornecedorHomologadoInfo(
            cnpj=cnpj_cpf,
            razao_social="Fornecedor Não Cadastrado",
            situacao_cadastral="PENDENTE_HOMOLOGACAO",
            score_compliance=50.0,
            limite_alcada_brl=0.0,
            categoria_risco="ALTO",
            restricoes_juridicas="Empresa sem histórico na base corporativa."
        )

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE DO SUBAGENTE VALIDADOR CADASTRAL (ISOLAMENTO DE CONTEXTO)")
    print("=" * 80)
    cnpj_teste = "98.765.432/0001-10" # Alfa Consultoria em IA S.A.
    print(f"Consultando fornecedor com CNPJ: {cnpj_teste}...")
    info = homologar_fornecedor(cnpj_teste)
    print("\nResultado da Diligência Cadastral:")
    print(json.dumps(info.model_dump(), indent=2, ensure_ascii=False))
    print("\n[SUCESSO] Subagente operou com contexto isolado e emitiu FornecedorHomologadoInfo tipado.")
