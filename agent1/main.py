"""
API REST do Agente 1: Extrator Enriquecido de Contratos
Serviço desacoplado construído com FastAPI e BackgroundTasks.

Endpoints:
- POST /run: Dispara a extração assíncrona do contrato, retornando 202 Accepted com task_id imediato.
- GET /status/{task_id}: Consulta o status do processamento ('pending', 'done', 'error') e o resultado extraído.
- GET /health: Healthcheck da aplicação.
"""

import sys
import uuid
import time
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

# Garante que os módulos locais da pasta agent sejam importados corretamente
diretorio_atual = Path(__file__).resolve().parent
if str(diretorio_atual) not in sys.path:
    sys.path.insert(0, str(diretorio_atual))

from agente_extracao import extrair_contrato_completo
from models import DadosContratoExtraido

app = FastAPI(
    title="Agente 1 - Serviço REST de Extração de Contratos",
    description=(
        "Microsserviço HTTP para extração estruturada de entidades contratuais, "
        "resolução temporal de datas (ISO-8601) e validação matemática de cronograma financeiro."
    ),
    version="1.0.0"
)

class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"

class RunRequest(BaseModel):
    texto_contrato: str = Field(
        ...,
        description="Texto bruto da minuta contratual a ser analisada e extraída.",
        min_length=10
    )

class RunResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str

class StatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: float
    completed_at: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Repositório em memória para persistência de status das tarefas
tarefas_db: Dict[str, Dict[str, Any]] = {}

def processar_contrato_background(task_id: str, texto_contrato: str):
    """
    Função executada de forma não-bloqueante em segundo plano (BackgroundTasks).
    Atualiza o estado da tarefa para 'done' ou 'error'.
    """
    try:
        # Simula ou executa a extração estruturada e enriquecimento com tools
        contrato_extraido: DadosContratoExtraido = extrair_contrato_completo(texto_contrato)
        
        tarefas_db[task_id]["status"] = TaskStatus.DONE
        tarefas_db[task_id]["completed_at"] = time.time()
        tarefas_db[task_id]["data"] = contrato_extraido.model_dump()
        print(f"[AGENTE 1 API] Tarefa {task_id} finalizada com SUCESSO.")
    except Exception as exc:
        tarefas_db[task_id]["status"] = TaskStatus.ERROR
        tarefas_db[task_id]["completed_at"] = time.time()
        tarefas_db[task_id]["error"] = str(exc)
        print(f"[AGENTE 1 API] Erro ao processar tarefa {task_id}: {exc}")

@app.get("/health", tags=["Monitoramento"])
def health_check():
    """Verifica a integridade e disponibilidade do serviço."""
    return {"status": "healthy", "service": "agente-1-extracao", "timestamp": time.time()}

@app.post(
    "/run",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RunResponse,
    tags=["Execução"],
    summary="Dispara a extração do contrato de forma assíncrona"
)
def run_extracao(requisicao: RunRequest, background_tasks: BackgroundTasks):
    """
    Recebe o texto bruto do contrato e inicia o processamento assíncrono.
    Retorna imediatamente 202 Accepted com o identificador 'task_id'.
    """
    task_id = str(uuid.uuid4())
    tarefas_db[task_id] = {
        "status": TaskStatus.PENDING,
        "created_at": time.time(),
        "completed_at": None,
        "data": None,
        "error": None
    }
    
    # Enfileira a tarefa assíncrona sem bloquear a resposta HTTP
    background_tasks.add_task(processar_contrato_background, task_id, requisicao.texto_contrato)
    
    return RunResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Processamento de extração iniciado com sucesso em segundo plano."
    )

@app.get(
    "/status/{task_id}",
    response_model=StatusResponse,
    tags=["Monitoramento"],
    summary="Consulta o status e o resultado de uma tarefa"
)
def get_status(task_id: str):
    """
    Consulta o estado de processamento de uma tarefa específica.
    Estados possíveis: 'pending', 'done', 'error'.
    """
    if task_id not in tarefas_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com task_id '{task_id}' não encontrada."
        )
    
    info = tarefas_db[task_id]
    return StatusResponse(
        task_id=task_id,
        status=info["status"],
        created_at=info["created_at"],
        completed_at=info["completed_at"],
        data=info["data"],
        error=info["error"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
