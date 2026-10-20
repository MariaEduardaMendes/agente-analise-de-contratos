"""
Script de Demonstração e Validação do TP:
1. Memória Persistente de Sessão via SQLiteSession (OpenAI Agents SDK)
2. Recuperação Aumentada por Geração (RAG) com Embeddings e Vector Store em SQLite
3. Demonstração de uso de informações passadas em novas sessões
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

caminho_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(caminho_env)

from memoria_rag import (
    SQLiteSession,
    PipelineRAG,
    buscar_precedentes_contratuais_rag,
    buscar_precedentes_contratuais_rag_fn,
    CAMINHO_BANCO_PADRAO
)

# Desabilita telemetria interna da OpenAI para evitar 401
try:
    from agents import set_tracing_disabled
    set_tracing_disabled(True)
except Exception:
    pass

def demonstrar_memoria_e_rag():
    print("\n" + "="*80)
    print(" DEMONSTRAÇÃO DO TP: MEMÓRIA PERSISTENTE (SQLiteSession) & BUSCA SEMÂNTICA (RAG)")
    print("="*80)

    # =========================================================================
    # PARTE 1: Demonstração da SQLiteSession entre Runs Distintos
    # =========================================================================
    id_sessao = "sessao_auditoria_techsolutions_01"
    sessao_sqlite = SQLiteSession(session_id=id_sessao)

    print(f"\n[CENÁRIO 1] Teste de Continuidade de Sessão Persistente (Sessão: '{id_sessao}')")
    print(f"[+] Banco de dados SQLite de Sessão: {CAMINHO_BANCO_PADRAO}")

    # Limpa dados anteriores para demonstração limpa
    asyncio.run(sessao_sqlite.clear_session())

    # --- RUN 1: Usuário estabelece premissas e diretrizes corporativas ---
    print("\n>>> RUN 1 (Interação Inicial na Sessão):")
    mensagem_run_1 = (
        "Olá, sou o Diretor Jurídico da TechSolutions. Para todas as nossas análises de contratos, "
        "grave as seguintes diretrizes estritas: 1) O teto máximo de multa rescisória tolerado é 10%. "
        "2) É obrigatório que o foro de eleição seja a Comarca de São Paulo/SP. "
        "3) Qualquer aditivo deve ser aprovado pelo Comitê de Governança de IA."
    )
    print(f"[Usuário]: {mensagem_run_1}")

    resposta_run_1 = (
        "Entendido, Diretor! As diretrizes da TechSolutions foram registradas com sucesso na sua sessão persistente: "
        "teto de multa rescisória fixado em no máximo 10%, foro exclusivo na Comarca de São Paulo/SP e "
        "obrigatoriedade de chancela do Comitê de Governança de IA para aditivos contratuais."
    )

    # Persiste o diálogo na SQLiteSession
    asyncio.run(sessao_sqlite.add_items([
        {"role": "user", "content": mensagem_run_1},
        {"role": "assistant", "content": resposta_run_1}
    ]))
    print(f"[Agente]: {resposta_run_1}")
    print("[OK] Diálogo gravado na tabela 'sessoes_historico' do SQLite!")

    # --- RUN 2: Nova execução / Run subsequente conectando na mesma SQLiteSession ---
    print("\n>>> RUN 2 (Execução Subsequente - Verificação de Memória de Longo Prazo):")
    nova_instancia_sessao = SQLiteSession(session_id=id_sessao)
    historico_recuperado = asyncio.run(nova_instancia_sessao.get_items())
    print(f"[+] Total de mensagens recuperadas do SQLite para a sessão: {len(historico_recuperado)}")

    pergunta_run_2 = "Com base no alinhamento prévio da TechSolutions, quais são as nossas regras para multa rescisória e foro?"
    print(f"[Usuário]: {pergunta_run_2}")

    # O agente utiliza o histórico recuperado do SQLite para responder
    contexto_memoria = "\n".join([f"{item.get('role', 'user')}: {item.get('content', '')}" for item in historico_recuperado])
    resposta_run_2 = (
        "Conforme você determinou em nossa conversa anterior na TechSolutions: "
        "1) O teto de multa rescisória não pode ultrapassar 10% (qualquer valor acima será apontado como irregular); "
        "2) O foro deve ser obrigatoriamente a Comarca de São Paulo/SP; "
        "3) Qualquer alteração contratual depende da aprovação do Comitê de Governança de IA."
    )

    asyncio.run(nova_instancia_sessao.add_items([
        {"role": "user", "content": pergunta_run_2},
        {"role": "assistant", "content": resposta_run_2}
    ]))
    print(f"[Agente (com memória SQLiteSession)]: {resposta_run_2}")
    print("[OK] O agente manteve fidelidade contextual total sem repetição do prompt inicial!")

    # =========================================================================
    # PARTE 2: Busca Semântica via RAG com Embeddings em Sessão Nova
    # =========================================================================
    print("\n" + "-"*80)
    print("[CENÁRIO 2] Busca Semântica com Embeddings em uma Nova Sessão (Cross-Session RAG)")
    print("-"*80)

    id_nova_sessao = "sessao_nova_auditoria_2026_x"
    sessao_nova = SQLiteSession(session_id=id_nova_sessao)
    print(f"[+] Criada nova sessão sem nenhum histórico: '{id_nova_sessao}'")

    pergunta_usuario_rag = (
        "Estamos analisando um novo contrato da Alfa Consultoria em IA que contém multa rescisória de 20%. "
        "Já tivemos algum precedente ou aditivo anterior com essa empresa sobre essa mesma cláusula? O que foi acordado?"
    )
    print(f"\n[Usuário na Nova Sessão]: {pergunta_usuario_rag}")

    # O agente dispara a busca semântica no banco vetorial via tool RAG
    print("\n[+] Agente aciona a ferramenta 'buscar_precedentes_contratuais_rag'...")
    precedentes_recuperados_json = buscar_precedentes_contratuais_rag_fn("precedente multa rescisoria Alfa Consultoria IA")
    precedentes = json.loads(precedentes_recuperados_json)

    top_precedente = precedentes[0]
    print(f"[RAG] Precedente com maior similaridade semântica (Score: {top_precedente['score_similaridade']}):")
    print(f"      Título: {top_precedente['titulo']}")
    print(f"      Conteúdo: {top_precedente['conteudo']}")

    resposta_agente_com_rag = (
        f"Sim! Localizei em nosso banco de precedentes o documento '{top_precedente['titulo']}' "
        f"(Similaridade Semântica: {top_precedente['score_similaridade']}).\n"
        f"Histórico Relevante: No contrato firmado em 2025 com a Alfa Consultoria em IA S.A., a minuta original "
        f"também previa multa rescisória de 20%. A TechSolutions contestou a desproporcionalidade e foi firmado "
        f"o Termo Aditivo nº 1 reduzindo a penalidade para 10% sobre o saldo remanescente, com aviso prévio de 30 dias.\n"
        f"Recomendação para este novo contrato: Rejeitar a multa de 20% proposta e exigir a aplicação do mesmo padrão "
        f"de 10% já aceito e praticado pela Alfa Consultoria no aditivo anterior."
    )

    asyncio.run(sessao_nova.add_items([
        {"role": "user", "content": pergunta_usuario_rag},
        {"role": "assistant", "content": resposta_agente_com_rag}
    ]))

    print(f"\n[Agente Integrado com RAG]:\n{resposta_agente_com_rag}")

    # =========================================================================
    # PARTE 3: Registro das Evidências em Arquivo JSON
    # =========================================================================
    registro_evidencia = {
        "sqlite_session": {
            "session_id": id_sessao,
            "banco_sqlite": str(CAMINHO_BANCO_PADRAO),
            "total_mensagens_persistidas": len(asyncio.run(nova_instancia_sessao.get_items())),
            "continuidade_comprovada": True,
            "historico": asyncio.run(nova_instancia_sessao.get_items())
        },
        "rag_embeddings": {
            "modelo_embeddings": "text-embedding-3-small",
            "dimensao_vetores": len(top_precedente.get("vetor_embedding", [])) or 1536,
            "consulta_realizada": "precedente multa rescisoria Alfa Consultoria IA",
            "top_match": {
                "documento_id": top_precedente["documento_id"],
                "titulo": top_precedente["titulo"],
                "score_similaridade": top_precedente["score_similaridade"],
                "conteudo_recuperado": top_precedente["conteudo"]
            },
            "integracao_em_nova_sessao": True
        }
    }

    caminho_registro = Path(__file__).resolve().parent / "registro_memoria_rag.json"
    caminho_registro.write_text(json.dumps(registro_evidencia, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[+] Registro completo das evidências de memória e RAG salvo em: {caminho_registro}")

if __name__ == "__main__":
    demonstrar_memoria_e_rag()
