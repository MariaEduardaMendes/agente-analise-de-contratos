"""
Script de Testes e Validação da API REST do Agente 2 (Conformidade e Risco)
Valida os endpoints /run (202 Accepted) e /status/{task_id} (200 OK com saída tipada Pydantic).
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def testar_fluxo_agente_2():
    print("=" * 80)
    print("TESTE DE CONTRATOS REST: AGENTE 2 (POST /run e GET /status/{task_id})")
    print("=" * 80)
    
    # 1. Payload de exemplo que o n8n recebe do Agente 1 e repassa ao Agente 2
    dados_contrato_mock = {
        "titulo": "Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
        "contratante": {
            "nome": "Empresa Contratante S.A.",
            "cnpj_cpf": "98.765.432/0001-10",
            "papel": "CONTRATANTE"
        },
        "contratada": {
            "nome": "TechSolutions Ltda.",
            "cnpj_cpf": "12.345.678/0001-90",
            "papel": "CONTRATADA"
        },
        "objeto": "Desenvolvimento, homologação e implantação de agentes inteligentes.",
        "financeiro": {
            "moeda": "BRL",
            "valor_total_brl": 120000.0,
            "parcelas_quantidade": 12,
            "valor_parcela_brl": 10000.0,
            "periodicidade": "mensal",
            "soma_consistente": True,
            "discrepancia_centavos": 0.0
        },
        "vigencia": {
            "data_inicio_iso": "2026-01-15",
            "data_fim_calculada_iso": "2027-01-15",
            "vigencia_meses": 12,
            "dias_corridos_totais": 365,
            "aviso_previo_dias": 30
        },
        "penalidades": {
            "percentual_multa_rescisoria": 20.0,
            "base_calculo": "saldo remanescente do contrato",
            "gatilho_aplicacao": "rescisao_imotivada"
        }
    }
    
    # 2. Testa POST /run
    print("\n[1] Disparando POST /run no Agente 2...")
    resposta_run = client.post("/run", json={"dados_contrato": dados_contrato_mock})
    print(f"Status HTTP: {resposta_run.status_code} (Esperado: 202 Accepted)")
    corpo_run = resposta_run.json()
    print("Corpo:", json.dumps(corpo_run, indent=2, ensure_ascii=False))
    
    assert resposta_run.status_code == 202
    task_id = corpo_run["task_id"]
    assert task_id
    
    # 3. Testa GET /status/{task_id}
    print(f"\n[2] Consultando GET /status/{task_id}...")
    resposta_status = client.get(f"/status/{task_id}")
    print(f"Status HTTP: {resposta_status.status_code}")
    corpo_status = resposta_status.json()
    print("Corpo:", json.dumps(corpo_status, indent=2, ensure_ascii=False))
    
    assert resposta_status.status_code == 200
    assert corpo_status["status"] == "done"
    data = corpo_status["data"]
    assert data["contrato_titulo"] == dados_contrato_mock["titulo"]
    assert "score_conformidade" in data
    assert "nivel_risco_geral" in data
    assert len(data["itens_auditados"]) >= 3, f"Esperado pelo menos 3 itens auditados, obteve {len(data['itens_auditados'])}"
    assert len(data["recomendacoes_mitigacao"]) > 0
    
    # 4. Testa GET /status para task inexistente (404)
    print("\n[3] Testando 404 para ID inexistente...")
    resp_404 = client.get("/status/task-inexistente")
    assert resp_404.status_code == 404
    print("Status 404 validado com sucesso!")
    
    print("\n[SUCESSO] Todos os testes do Agente 2 foram concluídos com 100% de êxito!")

if __name__ == "__main__":
    testar_fluxo_agente_2()
