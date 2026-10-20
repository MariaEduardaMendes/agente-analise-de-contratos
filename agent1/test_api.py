"""
Script de Testes e Validação da API REST do Agente 1
Testa diretamente os endpoints /run e /status/{task_id} utilizando o TestClient do FastAPI.
Gera os registros de requisições e respostas para documentação do TP3.
"""

import time
import json
from pathlib import Path
from fastapi.testclient import TestClient

from main import app, tarefas_db

client = TestClient(app)

def testar_fluxo_completo():
    print("=" * 80)
    print("TESTE DE CONTRATOS REST: AGENTE 1 (POST /run e GET /status/{task_id})")
    print("=" * 80)
    
    # 1. Carrega contrato de teste
    caminho_contrato = Path(__file__).resolve().parent / "contrato_exemplo.txt"
    texto_contrato = caminho_contrato.read_text(encoding="utf-8")
    
    # 2. Testa POST /run
    print("\n[1] Disparando requisição POST /run...")
    payload_envio = {"texto_contrato": texto_contrato}
    resposta_run = client.post("/run", json=payload_envio)
    
    print(f"Status HTTP: {resposta_run.status_code} (Esperado: 202 Accepted)")
    corpo_run = resposta_run.json()
    print("Corpo da Resposta:")
    print(json.dumps(corpo_run, indent=2, ensure_ascii=False))
    
    assert resposta_run.status_code == 202, "Erro: Status HTTP deve ser 202 Accepted"
    task_id = corpo_run["task_id"]
    assert task_id, "Erro: task_id não foi retornado"
    
    # 3. Testa GET /status/{task_id}
    print(f"\n[2] Consultando GET /status/{task_id}...")
    resposta_status = client.get(f"/status/{task_id}")
    print(f"Status HTTP: {resposta_status.status_code}")
    corpo_status = resposta_status.json()
    print("Corpo da Resposta:")
    print(json.dumps(corpo_status, indent=2, ensure_ascii=False))
    
    assert resposta_status.status_code == 200, "Erro: Status HTTP deve ser 200"
    assert corpo_status["status"] in ("pending", "done"), f"Status inesperado: {corpo_status['status']}"
    assert corpo_status["data"] is not None, "Erro: Dados extraídos não foram encontrados"
    assert "titulo" in corpo_status["data"], "Erro: Campo 'titulo' ausente nos dados extraídos"
    
    # 4. Testa GET /status/{task_id_invalido} (Caso de Erro 404)
    print("\n[3] Testando consulta a task inexistente (404 Not Found)...")
    resposta_404 = client.get("/status/task-inexistente-12345")
    print(f"Status HTTP: {resposta_404.status_code} (Esperado: 404)")
    print("Corpo da Resposta 404:", resposta_404.json())
    assert resposta_404.status_code == 404
    
    # 5. Salva evidências de teste em arquivo JSON para inclusão na documentação
    registro_testes = {
        "post_run": {
            "endpoint": "POST /run",
            "status_code": resposta_run.status_code,
            "request_payload": {"texto_contrato": texto_contrato[:120] + "... [truncado]"},
            "response_body": corpo_run
        },
        "get_status_done": {
            "endpoint": f"GET /status/{task_id}",
            "status_code": resposta_status.status_code,
            "response_body": corpo_status
        },
        "get_status_404": {
            "endpoint": "GET /status/task-inexistente-12345",
            "status_code": resposta_404.status_code,
            "response_body": resposta_404.json()
        }
    }
    
    caminho_evidencia = Path(__file__).resolve().parent / "evidencia_testes_endpoints.json"
    caminho_evidencia.write_text(json.dumps(registro_testes, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCESSO] Todos os testes passaram e as evidências foram salvas em: {caminho_evidencia.name}")

if __name__ == "__main__":
    testar_fluxo_completo()
