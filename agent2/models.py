"""
Modelos Pydantic v2 do Agente 2 (Avaliador de Conformidade e Risco)
Define os schemas tipados de entrada (recebidos via orquestração n8n)
e os schemas estritos do parecer/relatório de conformidade emitido.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class NivelRisco(str, Enum):
    BAIXO = "BAIXO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class StatusConformidade(str, Enum):
    CONFORME = "CONFORME"
    ALERTA = "ALERTA"
    NAO_CONFORME = "NAO_CONFORME"


class ItemAuditoria(BaseModel):
    """Representa um item individual verificado durante a auditoria contratual."""
    regra: str = Field(..., description="Nome da regra de governança ou jurídica avaliada.")
    status: StatusConformidade = Field(..., description="Status de conformidade do item.")
    nivel_risco: NivelRisco = Field(..., description="Nível de risco atribuído ao item.")
    descricao_analise: str = Field(..., description="Parecer analítico detalhado sobre o item.")
    fundamentacao: str = Field(..., description="Base normativa, legal ou diretriz de compliance corporativa.")


class RelatorioConformidade(BaseModel):
    """Modelo tipado de saída oficial do Agente 2."""
    contrato_titulo: str = Field(..., description="Título do contrato analisado.")
    score_conformidade: float = Field(
        ...,
        description="Nota geral de aderência e compliance do contrato de 0 a 100.",
        ge=0.0,
        le=100.0
    )
    nivel_risco_geral: NivelRisco = Field(..., description="Classificação consolidada do risco do contrato.")
    total_regras_auditadas: int = Field(..., description="Quantidade total de verificações realizadas.", ge=1)
    itens_conformes: int = Field(..., description="Número de regras atendidas sem ressalvas.")
    itens_alerta: int = Field(..., description="Número de regras que demandam atenção ou alçada superior.")
    itens_nao_conformes: int = Field(..., description="Número de violações diretas de diretrizes.")
    itens_auditados: List[ItemAuditoria] = Field(..., description="Lista discriminada de todas as verificações.")
    recomendacoes_mitigacao: List[str] = Field(..., description="Ações recomendadas para mitigar riscos identificados.")
    parecer_executivo_markdown: str = Field(..., description="Resumo formal formatado em Markdown para os tomadores de decisão.")

    @model_validator(mode="after")
    def validar_consistencia_quantitativa(self):
        total = self.itens_conformes + self.itens_alerta + self.itens_nao_conformes
        if total != self.total_regras_auditadas:
            raise ValueError(
                f"Soma dos itens ({total}) diverge do total de regras auditadas ({self.total_regras_auditadas})."
            )
        return self
