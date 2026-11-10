"""
Modelos de Dados Pydantic v2 do Agente 1 (Extrator Enriquecido)
Define contratos de dados fortemente tipados com validação de tipos,
valores numéricos positivos, formato de documentos e consistência matemática.
"""

import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


class ParteContratante(BaseModel):
    """Identificação e qualificação das partes envolvidas no contrato."""
    nome: str = Field(..., description="Nome completo ou Razão Social da parte")
    cnpj_cpf: str = Field(..., description="CNPJ ou CPF no formato pontuado ou numérico")
    papel: str = Field(..., description="Papel contratual: CONTRATANTE ou CONTRATADA")

    @field_validator("cnpj_cpf")
    @classmethod
    def validar_documento(cls, v: str) -> str:
        digitos = re.sub(r"\D", "", v)
        if len(digitos) not in (11, 14):
            raise ValueError(f"Documento inválido: {v}. Deve possuir 11 dígitos (CPF) ou 14 dígitos (CNPJ).")
        return v


class ParcelaCronograma(BaseModel):
    """Detalhamento de cada parcela do cronograma financeiro."""
    parcela_numero: int = Field(..., description="Número ordinal da parcela")
    valor: float = Field(..., description="Valor monetário da parcela em Reais (BRL)")
    periodicidade: str = Field("mensal", description="Periodicidade da parcela")


class CronogramaFinanceiro(BaseModel):
    """Estrutura financeira validada pela tool de tabela financeira."""
    moeda: str = Field("BRL", description="Moeda contratada")
    valor_total_brl: float = Field(..., description="Valor global do contrato em Reais")
    parcelas_quantidade: int = Field(..., description="Número total de parcelas")
    valor_parcela_brl: float = Field(..., description="Valor unitário de cada parcela")
    periodicidade: str = Field("mensal", description="Periodicidade do parcelamento")
    soma_consistente: bool = Field(..., description="Indica se a soma das parcelas confere com o valor global")
    discrepancia_centavos: float = Field(0.0, description="Diferença em centavos por arredondamento")
    cronograma_resumo: str = Field(..., description="Resumo descritivo das condições de pagamento")

    @field_validator("valor_total_brl", "valor_parcela_brl")
    @classmethod
    def validar_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Valores financeiros contratuais devem ser estritamente positivos.")
        return v


class PeriodoVigencia(BaseModel):
    """Prazos e datas normalizadas pela tool de normalização temporal."""
    data_inicio_iso: str = Field(..., description="Data inicial no formato ISO-8601 (YYYY-MM-DD)")
    data_fim_calculada_iso: str = Field(..., description="Data final calculada no formato ISO-8601 (YYYY-MM-DD)")
    vigencia_meses: int = Field(..., description="Duração formal do contrato em meses")
    dias_corridos_totais: int = Field(..., description="Total de dias corridos computados no período")
    aviso_previo_dias: int = Field(30, description="Dias exigidos de antecedência para aviso de rescisão")
    vigencia_formatada: str = Field(..., description="Descrição amigável do intervalo temporal")


class ClausulaPenal(BaseModel):
    """Extração factual das penalidades e multas contratuais."""
    percentual_multa_rescisoria: float = Field(..., description="Percentual estipulado para rescisão imotivada")
    base_calculo: str = Field(..., description="Base sobre a qual incide a multa (ex: saldo remanescente, valor global)")
    gatilho_aplicacao: str = Field(..., description="Condição de aplicação (ex: rescisao_sem_justa_causa)")


class FornecedorHomologadoInfo(BaseModel):
    """Dados cadastrais de negócio recuperados da fonte estruturada corporativa (cadastro_fornecedores)."""
    cnpj: str = Field(..., description="CNPJ cadastrado")
    razao_social: str = Field(..., description="Razão social oficial homologada")
    situacao_cadastral: str = Field("ATIVA", description="Situação cadastral (ATIVA, SUSPENSA, INAPTA)")
    score_compliance: float = Field(..., description="Score histórico de compliance corporativo (0 a 100)")
    limite_alcada_brl: float = Field(..., description="Limite financeiro de alçada aprovado para o fornecedor")
    categoria_risco: str = Field(..., description="Classificação corporativa de risco (BAIXO, MEDIO, ALTO)")
    restricoes_juridicas: Optional[str] = Field(None, description="Histórico ou restrições registradas no CEIS/CNJ")


class DadosContratoExtraido(BaseModel):
    """
    Schema mestre de saída do Agente 1 (Extrator Enriquecido).
    Contém todos os dados factuais extraídos, enriquecidos e sanitizados,
    prontos para serem consumidos como entrada pelo Agente 2 (Avaliador de Risco).
    """
    titulo: str = Field(..., description="Título ou tipo identificador do instrumento contratual")
    contratante: ParteContratante = Field(..., description="Dados da Contratante extraídos da minuta")
    contratada: ParteContratante = Field(..., description="Dados da Contratada extraídos da minuta")
    objeto: str = Field(..., description="Descrição concisa e objetiva do escopo dos serviços")
    
    # Entidades enriquecidas e normalizadas pelas Tools
    financeiro: CronogramaFinanceiro = Field(..., description="Dados financeiros validados matematicamente")
    vigencia: PeriodoVigencia = Field(..., description="Prazos de vigência normalizados no padrão ISO")
    penalidades: ClausulaPenal = Field(..., description="Cláusula penal e multa rescisória extraídas")
    
    # Fonte estruturada corporativa (Cadastro de Fornecedores)
    fornecedor_homologado: Optional[FornecedorHomologadoInfo] = Field(
        default=None,
        description="Informações cadastrais estruturadas de negócio obtidas do banco corporativo"
    )
    
    # Rastreabilidade de extração
    secoes_analisadas: List[str] = Field(
        default_factory=lambda: ["PREAMBULO", "OBJETO", "PRECO_E_CONDICOES", "VIGENCIA", "RESCISAO_E_PENALIDADES"],
        description="Lista das seções estruturais identificadas e processadas"
    )
