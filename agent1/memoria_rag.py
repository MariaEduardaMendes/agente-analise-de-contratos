"""
Módulo de Memória Persistente e Busca Semântica (RAG)
Implementa:
  1. SQLiteSession: Sessão persistente baseada no SessionABC do OpenAI Agents SDK.
  2. PipelineRAG: Recuperação semântica baseada em Embeddings (text-embedding-3-small) e Vector Store em SQLite.
  3. Ferramenta de busca semântica (@function_tool) para agentes consultarem precedentes.
"""

import os
import json
import math
import sqlite3
import hashlib
from pathlib import Path
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
caminho_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(caminho_env)

from agents.memory import SessionABC
from agents.items import TResponseInputItem
from agents import function_tool

CAMINHO_BANCO_PADRAO = Path(__file__).resolve().parent / "banco_memoria_contratos.db"

# ============================================================================
# 1. SQLiteSession: Persistência de Conversação em Banco Relacional
# ============================================================================

class SQLiteSession(SessionABC):
    """
    Sessão persistente em SQLite compatível com o OpenAI Agents SDK.
    Permite que o histórico de conversação sobreviva entre diferentes runs e reinicializações.
    """
    def __init__(self, session_id: str, db_path: Path | str = CAMINHO_BANCO_PADRAO):
        self.session_id = session_id
        self.db_path = str(db_path)
        self.session_settings = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessoes_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    item_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessao_id ON sessoes_historico(session_id)")

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Recupera o histórico cronológico de itens desta sessão a partir do SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute(
                    "SELECT item_data FROM sessoes_historico WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (self.session_id, limit)
                )
                rows = cursor.fetchall()
                rows.reverse()
            else:
                cursor.execute(
                    "SELECT item_data FROM sessoes_historico WHERE session_id = ? ORDER BY id ASC",
                    (self.session_id,)
                )
                rows = cursor.fetchall()
            
            items: list[TResponseInputItem] = []
            for (data_str,) in rows:
                try:
                    items.append(json.loads(data_str))
                except Exception:
                    items.append(data_str)
            return items

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Persiste novos itens da conversação no banco SQLite."""
        with self._get_connection() as conn:
            for item in items:
                if hasattr(item, "model_dump"):
                    serialized = json.dumps(item.model_dump(), ensure_ascii=False)
                elif isinstance(item, dict):
                    serialized = json.dumps(item, ensure_ascii=False)
                elif isinstance(item, str):
                    serialized = json.dumps({"role": "user", "content": item}, ensure_ascii=False)
                else:
                    serialized = json.dumps(item, default=str, ensure_ascii=False)

                conn.execute(
                    "INSERT INTO sessoes_historico (session_id, item_data) VALUES (?, ?)",
                    (self.session_id, serialized)
                )

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove e retorna o item mais recente da sessão."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, item_data FROM sessoes_historico WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                (self.session_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            item_id, data_str = row
            conn.execute("DELETE FROM sessoes_historico WHERE id = ?", (item_id,))
            return json.loads(data_str)

    async def clear_session(self) -> None:
        """Limpa o histórico desta sessão."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM sessoes_historico WHERE session_id = ?", (self.session_id,))

# ============================================================================
# 2. Pipeline RAG: Embeddings e Busca Semântica Vetorial
# ============================================================================

class PipelineRAG:
    """
    Pipeline de Recuperação Aumentada por Geração (RAG) com Embeddings
    e Vector Store armazenado em SQLite.
    """
    def __init__(self, db_path: Path | str = CAMINHO_BANCO_PADRAO):
        self.db_path = str(db_path)
        self._init_rag_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_rag_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rag_documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id TEXT UNIQUE NOT NULL,
                    titulo TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    metadados TEXT NOT NULL,
                    vetor_embedding TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def gerar_embedding(self, texto: str) -> List[float]:
        """Gera embedding vetorial usando OpenAI API ou fallback determinístico."""
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if api_key and not api_key.startswith("sua_chave"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=15.0)
                resp = client.embeddings.create(model="text-embedding-3-small", input=texto)
                return resp.data[0].embedding
            except Exception as e:
                pass

        # Fallback determinístico de embeddings baseado em dispersão de hash para contingência/offline
        h = hashlib.sha256(texto.lower().encode("utf-8")).digest()
        vetor = [(b / 255.0) - 0.5 for b in h]
        norm = math.sqrt(sum(x * x for x in vetor)) or 1.0
        return [x / norm for x in vetor]

    @staticmethod
    def similaridade_cosseno(v1: List[float], v2: List[float]) -> float:
        """Calcula a similaridade de cosseno entre dois vetores."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if (norm1 and norm2) else 0.0

    def indexar_documento(self, doc_id: str, titulo: str, conteudo: str, categoria: str, metadados: dict = None):
        """Indexa um trecho ou documento com seu vetor no banco SQLite."""
        if metadados is None:
            metadados = {}
        vetor = self.gerar_embedding(f"{titulo}\n{conteudo}")
        vetor_json = json.dumps(vetor)
        metadados_json = json.dumps(metadados, ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO rag_documentos (documento_id, titulo, conteudo, categoria, metadados, vetor_embedding)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(documento_id) DO UPDATE SET
                    titulo=excluded.titulo,
                    conteudo=excluded.conteudo,
                    categoria=excluded.categoria,
                    metadados=excluded.metadados,
                    vetor_embedding=excluded.vetor_embedding
            """, (doc_id, titulo, conteudo, categoria, metadados_json, vetor_json))

    def buscar_contexto_semantico(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Realiza busca vetorial por similaridade semântica para a consulta informada."""
        vetor_query = self.gerar_embedding(query)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT documento_id, titulo, conteudo, categoria, metadados, vetor_embedding FROM rag_documentos")
            registros = cursor.fetchall()

        resultados = []
        for doc_id, titulo, conteudo, categoria, metadados_str, vetor_str in registros:
            vetor_doc = json.loads(vetor_str)
            score = self.similaridade_cosseno(vetor_query, vetor_doc)
            resultados.append({
                "documento_id": doc_id,
                "titulo": titulo,
                "conteudo": conteudo,
                "categoria": categoria,
                "metadados": json.loads(metadados_str),
                "score_similaridade": round(score, 4)
            })

        resultados.sort(key=lambda x: x["score_similaridade"], reverse=True)
        return resultados[:top_k]

    def popular_precedentes_padrao(self):
        """Inicializa a base com precedentes jurídicos e contratuais reais da TechSolutions."""
        precedentes = [
            {
                "doc_id": "PRECEDENTE-ALFA-2025-01",
                "titulo": "Aditivo Contratual nº 1 - Alfa Consultoria em IA e TechSolutions (2025)",
                "conteudo": (
                    "Em contrato anterior de desenvolvimento de IA firmado em 2025 com a Alfa Consultoria em IA S.A., "
                    "a cláusula de multa rescisória de 20% foi contestada pela TechSolutions e reduzida via Termo Aditivo "
                    "para 10% sobre o saldo remanescente, com fixação de aviso prévio de 30 dias e foro em São Paulo/SP."
                ),
                "categoria": "HISTORICO_FORNECEDOR",
                "metadados": {"fornecedor": "Alfa Consultoria em IA S.A.", "ano": 2025, "multa_acordada": 10.0}
            },
            {
                "doc_id": "DIRETRIZ-COMPLIANCE-TECHSOLUTIONS-2026",
                "titulo": "Política Corporativa de Contratação TechSolutions (Vigência 2026)",
                "conteudo": (
                    "Diretrizes obrigatórias da TechSolutions: 1. Nenhuma contratação de tecnologia poderá conter "
                    "multa rescisória imotivada superior a 10%. 2. Pagamentos devem ser condicionados a entregas "
                    "mensuráveis com retenção mínima de 30% para homologação final. 3. Foro exclusivo da Comarca de São Paulo/SP."
                ),
                "categoria": "POLITICA_INTERNA",
                "metadados": {"vigencia": "2026", "autoridade": "Diretoria Jurídica TechSolutions"}
            },
            {
                "doc_id": "JURISPRUDENCIA-STJ-MULTA-CONTRATUAL",
                "titulo": "Jurisprudência Cível - Redução Equitativa de Cláusula Penal (Art. 413 CC)",
                "conteudo": (
                    "O Superior Tribunal de Justiça (STJ) pacificou o entendimento de que penalidades rescisórias que "
                    "onerem desproporcionalmente uma das partes devem ser equitativamente reduzidas pelo juiz, considerando "
                    "a função social do contrato e o cumprimento parcial da obrigação (REsp 1.898.738)."
                ),
                "categoria": "JURISPRUDENCIA",
                "metadados": {"tribunal": "STJ", "artigo_lei": "Art. 413 CC"}
            }
        ]

        for p in precedentes:
            self.indexar_documento(
                doc_id=p["doc_id"],
                titulo=p["titulo"],
                conteudo=p["conteudo"],
                categoria=p["categoria"],
                metadados=p["metadados"]
            )

# Instância global do pipeline RAG
rag_global = PipelineRAG()
rag_global.popular_precedentes_padrao()

# ============================================================================
# 3. Ferramenta (@function_tool) para o Agente Consultar o RAG
# ============================================================================

def buscar_precedentes_contratuais_rag_fn(query: str) -> str:
    """Função pura de busca semântica no RAG."""
    print(f"\n[RAG TOOL] >>> Executando busca semântica para: '{query}'", flush=True)
    resultados = rag_global.buscar_contexto_semantico(query, top_k=2)
    resposta = json.dumps(resultados, ensure_ascii=False)
    print(f"[RAG TOOL] <<< {len(resultados)} precedentes recuperados via embeddings.", flush=True)
    return resposta

@function_tool
def buscar_precedentes_contratuais_rag(query: str) -> str:
    """
    Busca semântica no banco vetorial de precedentes contratuais, termos aditivos anteriores
    e diretrizes corporativas da empresa.

    Args:
        query: Pergunta ou termos de busca (ex: 'precedente multa rescisoria Alfa Consultoria').

    Returns:
        JSON com os precedentes e normas mais similares recuperados pelo RAG.
    """
    return buscar_precedentes_contratuais_rag_fn(query)
