"""
API REST do Agente 2: Avaliador de Conformidade e Risco Contratual
Microsserviço independente construído com FastAPI e BackgroundTasks.

Endpoints:
- POST /run: Dispara a auditoria assíncrona recebendo os dados do contrato, retornando 202 Accepted com task_id.
- GET /status/{task_id}: Consulta o status da auditoria ('pending', 'done', 'error') e o relatório tipado emitido.
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

# Garante que os módulos locais da pasta agent_conformidade sejam importados
diretorio_atual = Path(__file__).resolve().parent
if str(diretorio_atual) not in sys.path:
    sys.path.insert(0, str(diretorio_atual))

from agente_auditoria import avaliar_conformidade_contrato
from models import RelatorioConformidade

app = FastAPI(
    title="Agente 2 - Serviço REST de Conformidade e Risco Contratual",
    description=(
        "Microsserviço HTTP para auditoria automatizada de minutas e contratos estruturados, "
        "confronto contra políticas de compliance corporativo e emissão de parecer de risco tipado."
    ),
    version="1.0.0"
)

class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"

class RunRequestConformidade(BaseModel):
    dados_contrato: Dict[str, Any] = Field(
        ...,
        description="Payload JSON contendo os dados estruturados do contrato (gerado pelo Agente 1 via n8n)."
    )

class RunResponseConformidade(BaseModel):
    task_id: str
    status: TaskStatus
    message: str

class StatusResponseConformidade(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: float
    completed_at: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Repositório em memória para persistência de status das auditorias
tarefas_db: Dict[str, Dict[str, Any]] = {}

def processar_auditoria_background(task_id: str, dados_contrato: Dict[str, Any]):
    """
    Executa a auditoria em background sem bloquear a resposta HTTP.
    Atualiza o estado da tarefa para 'done' ou 'error'.
    """
    try:
        relatorio: RelatorioConformidade = avaliar_conformidade_contrato(dados_contrato)
        
        tarefas_db[task_id]["status"] = TaskStatus.DONE
        tarefas_db[task_id]["completed_at"] = time.time()
        tarefas_db[task_id]["data"] = relatorio.model_dump()
        print(f"[AGENTE 2 API] Tarefa de auditoria {task_id} finalizada com SUCESSO.")
    except Exception as exc:
        tarefas_db[task_id]["status"] = TaskStatus.ERROR
        tarefas_db[task_id]["completed_at"] = time.time()
        tarefas_db[task_id]["error"] = str(exc)
        print(f"[AGENTE 2 API] Erro ao processar tarefa {task_id}: {exc}")

@app.get("/health", tags=["Monitoramento"])
def health_check():
    """Verifica a integridade e disponibilidade do serviço do Agente 2."""
    return {"status": "healthy", "service": "agente-2-conformidade", "timestamp": time.time()}

@app.post(
    "/run",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RunResponseConformidade,
    tags=["Execução"],
    summary="Dispara a auditoria de conformidade de forma assíncrona"
)
def run_auditoria(requisicao: RunRequestConformidade, background_tasks: BackgroundTasks):
    """
    Recebe os dados do contrato estruturado e dispara a auditoria de risco.
    Retorna imediatamente 202 Accepted com 'task_id'.
    """
    task_id = str(uuid.uuid4())
    tarefas_db[task_id] = {
        "status": TaskStatus.PENDING,
        "created_at": time.time(),
        "completed_at": None,
        "data": None,
        "error": None
    }
    
    # Enfileira a execução assíncrona
    background_tasks.add_task(processar_auditoria_background, task_id, requisicao.dados_contrato)
    
    return RunResponseConformidade(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Auditoria de conformidade iniciada com sucesso em segundo plano."
    )

@app.get(
    "/status/{task_id}",
    response_model=StatusResponseConformidade,
    tags=["Monitoramento"],
    summary="Consulta o status e o parecer de uma tarefa de auditoria"
)
def get_status(task_id: str):
    """
    Consulta o estado de processamento de uma tarefa específica do Agente 2.
    Estados possíveis: 'pending', 'done', 'error'.
    """
    if task_id not in tarefas_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa de auditoria com task_id '{task_id}' não encontrada."
        )
    
    info = tarefas_db[task_id]
    return StatusResponseConformidade(
        task_id=task_id,
        status=info["status"],
        created_at=info["created_at"],
        completed_at=info["completed_at"],
        data=info["data"],
        error=info["error"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
