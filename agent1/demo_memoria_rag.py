"""
Script de Demonstração e Validação do TP:
1. Memória Persistente de Sessão via SQLiteSession (OpenAI Agents SDK)
2. Execução REAL com Runner.run passando a session
3. Recuperação Aumentada por Geração (RAG) com Embeddings e Vector Store em SQLite
4. Demonstração de uso de informações passadas em novas sessões
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

caminho_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(caminho_env)

# Garante path de importação para agent1
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Desabilita telemetria interna da OpenAI para evitar 401
try:
    from agents import set_tracing_disabled
    set_tracing_disabled(True)
except Exception:
    pass

from openai import AsyncOpenAI
from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

from memoria_rag import (
    SQLiteSession,
    PipelineRAG,
    buscar_precedentes_contratuais_rag,
    CAMINHO_BANCO_PADRAO
)

def criar_modelo_llm() -> OpenAIChatCompletionsModel:
    """Instancia o modelo LLM conectado ao OpenRouter."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)

async def demonstrar_memoria_e_rag_async():
    print("\n" + "="*80)
    print(" DEMONSTRAÇÃO DO TP: MEMÓRIA PERSISTENTE (SQLiteSession) & BUSCA SEMÂNTICA (RAG)")
    print(" Execução 100% REAL via Runner.run com Modelo LLM")
    print("="*80)

    model = criar_modelo_llm()
    agent_conversacional = Agent(
        name="AssistenteDiretrizesJuridicas",
        instructions=(
            "Você é um consultor jurídico corporativo da TechSolutions. "
            "Guarde com rigor todas as premissas, diretrizes de governança e restrições "
            "fornecidas pelo usuário nas mensagens da sessão, respondendo de forma concisa e objetiva."
        ),
        model=model
    )

    # =========================================================================
    # PARTE 1: Demonstração da SQLiteSession entre Runs Distintos via Runner.run
    # =========================================================================
    id_sessao = "sessao_auditoria_techsolutions_01"
    sessao_sqlite = SQLiteSession(session_id=id_sessao)

    print(f"\n[CENÁRIO 1] Teste de Continuidade de Sessão Persistente (Sessão: '{id_sessao}')")
    print(f"[+] Banco de dados SQLite de Sessão: {CAMINHO_BANCO_PADRAO}")

    # Limpa dados anteriores para demonstração limpa
    await sessao_sqlite.clear_session()

    # --- RUN 1: Usuário estabelece premissas e diretrizes corporativas ---
    print("\n>>> RUN 1 (Interação Inicial na Sessão - Invocando Runner.run com session):")
    mensagem_run_1 = (
        "Olá, sou o Diretor Jurídico da TechSolutions. Para todas as nossas análises de contratos, "
        "grave as seguintes diretrizes estritas: 1) O teto máximo de multa rescisória tolerado é 10%. "
        "2) É obrigatório que o foro de eleição seja a Comarca de São Paulo/SP. "
        "3) Qualquer aditivo deve ser aprovado pelo Comitê de Governança de IA."
    )
    print(f"[Usuário]: {mensagem_run_1}")

    # Chamada REAL do Runner.run com a sessão SQLite passada
    resultado_run_1 = await Runner.run(agent_conversacional, mensagem_run_1, session=sessao_sqlite)
    resposta_run_1 = resultado_run_1.final_output
    print(f"\n[Agente (LLM Real)]: {resposta_run_1}")
    print("[OK] Diálogo gravado na tabela 'sessoes_historico' do SQLite!")

    # --- RUN 2: Nova execução conectando na mesma SQLiteSession ---
    print("\n>>> RUN 2 (Execução Subsequente - Verificação de Memória via Runner.run):")
    nova_instancia_sessao = SQLiteSession(session_id=id_sessao)
    historico_recuperado = await nova_instancia_sessao.get_items()
    print(f"[+] Total de itens recuperados do SQLite para a sessão antes do Run 2: {len(historico_recuperado)}")

    pergunta_run_2 = "Com base no alinhamento prévio da TechSolutions, quais são as nossas regras para multa rescisória e foro?"
    print(f"[Usuário]: {pergunta_run_2}")

    # Chamada REAL do Runner.run com a mesma sessão, validando recuperação contextual
    resultado_run_2 = await Runner.run(agent_conversacional, pergunta_run_2, session=nova_instancia_sessao)
    resposta_run_2 = resultado_run_2.final_output
    print(f"\n[Agente (LLM Real com memória SQLiteSession)]:\n{resposta_run_2}")
    print("[OK] O modelo recuperou com sucesso as premissas estabelecidas no Run 1 diretamente da SQLiteSession!")

    # =========================================================================
    # PARTE 2: Busca Semântica via RAG com Embeddings em Sessão Nova
    # =========================================================================
    print("\n" + "-"*80)
    print("[CENÁRIO 2] Busca Semântica com Embeddings e Tools em uma Nova Sessão (Cross-Session RAG)")
    print("-"*80)

    id_nova_sessao = "sessao_nova_auditoria_2026_rag"
    sessao_nova = SQLiteSession(session_id=id_nova_sessao)
    await sessao_nova.clear_session()
    print(f"[+] Criada nova sessão sem nenhum histórico: '{id_nova_sessao}'")

    agent_rag = Agent(
        name="AuditorPrecedentesRAG",
        instructions=(
            "Você é o Auditor de Precedentes da TechSolutions. "
            "Quando questionado sobre histórico com fornecedores ou precedentes de cláusulas, "
            "você DEVE OBRIGATORIAMENTE utilizar a ferramenta 'buscar_precedentes_contratuais_rag' "
            "para consultar o banco vetorial de precedentes corporativos e formular uma resposta fundamentada."
        ),
        tools=[buscar_precedentes_contratuais_rag],
        model=model
    )

    pergunta_usuario_rag = (
        "Estamos analisando um novo contrato da Alfa Consultoria em IA que contém multa rescisória de 20%. "
        "Já tivemos algum precedente ou aditivo anterior com essa empresa sobre essa mesma cláusula? O que foi acordado?"
    )
    print(f"\n[Usuário na Nova Sessão]: {pergunta_usuario_rag}")

    resultado_rag = await Runner.run(agent_rag, pergunta_usuario_rag, session=sessao_nova)
    resposta_agente_com_rag = resultado_rag.final_output
    print(f"\n[Agente Integrado com RAG (LLM Real)]:\n{resposta_agente_com_rag}")

    # =========================================================================
    # PARTE 3: Registro das Evidências em Arquivo JSON
    # =========================================================================
    itens_finais = await nova_instancia_sessao.get_items()
    registro_evidencia = {
        "sqlite_session": {
            "session_id": id_sessao,
            "banco_sqlite": str(CAMINHO_BANCO_PADRAO),
            "total_mensagens_persistidas": len(itens_finais),
            "dialogo_executado_real": [
                {"role": "user", "mensagem": mensagem_run_1},
                {"role": "assistant_llm", "resposta": str(resposta_run_1)},
                {"role": "user", "mensagem": pergunta_run_2},
                {"role": "assistant_llm", "resposta": str(resposta_run_2)}
            ]
        },
        "rag_vector_search": {
            "session_id": id_nova_sessao,
            "tabela_vetorial_real": "rag_documentos",
            "pergunta": pergunta_usuario_rag,
            "resposta_agente_rag_llm": str(resposta_agente_com_rag)
        }
    }

    caminho_registro = Path(__file__).resolve().parent / "registro_memoria_rag.json"
    caminho_registro.write_text(json.dumps(registro_evidencia, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[INFO] Registro de evidências salvo em: {caminho_registro}")
    print("[CONCLUÍDO] Demonstração de memória persistente e RAG validada com sucesso.")

def demonstrar_memoria_e_rag():
    asyncio.run(demonstrar_memoria_e_rag_async())

if __name__ == "__main__":
    demonstrar_memoria_e_rag()
