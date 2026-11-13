"""
Simulador e Verificador End-to-End da Orquestração n8n (TP4)
Testa o ciclo assíncrono completo contra os dois microserviços HTTP:
1. Submissão assíncrona ao Agente 1 (POST /run)
2. Polling ativo até status 'done' (GET /status/{task_id})
3. Lógica de roteamento condicional baseada na integridade dos dados extraídos
4. Submissão assíncrona ao Agente 2 (POST /run) com o payload tipado do Agente 1
5. Polling ativo até status 'done' (GET /status/{task_id})
6. Merge dos dados e consolidação do dossiê contratual final com parecer de governança
"""

import sys
import time
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timezone

root_dir = Path(__file__).resolve().parent.parent


def validar_estrutura_workflows_n8n():
    """Valida a integridade estrutural, nós, conexões e expressões dos JSONs exportados do n8n."""
    print("\n[VALIDAÇÃO ESTRUTURAL DOS WORKFLOWS n8n]")
    wf_principal_path = root_dir / "workflows" / "workflow_tp4_orquestrador_completo.json"
    sub_wf_path = root_dir / "workflows" / "subworkflow_polling_assincrono.json"

    wf = json.loads(wf_principal_path.read_text(encoding="utf-8"))
    nodes_wf = {n["name"]: n for n in wf["nodes"]}
    conns_wf = wf["connections"]

    # Verifica nós críticos e integridade das conexões do workflow principal
    nos_obrigatorios = [
        "Agente 1: Submeter POST /run",
        "Agente 1: Consultar GET /status",
        "Agente 1 Concluído?",
        "Agente 1 Falhou?",
        "Roteador: Dados Válidos para Auditoria?",
        "Empacotar Saída Agente 1",
        "Agente 2: Submeter POST /run",
        "Agente 2: Consultar GET /status",
        "Agente 2 Concluído?",
        "Agente 2 Falhou?",
        "Empacotar Saída Agente 2",
        "Merge Agente 1 e Agente 2",
        "Consolidar Dossiê Contratual Final",
        "AI Agent de Governança Estratégica",
        "LLM Chat Model (OpenRouter)",
        "Tool: Políticas de Governança",
    ]
    for nome in nos_obrigatorios:
        assert nome in nodes_wf, f"Nó obrigatório ausente no workflow principal: {nome}"

    # Verifica que todas as referências em connections existem em nodes
    for src, tipos in conns_wf.items():
        assert src in nodes_wf, f"Origem inexistente em connections: {src}"
        for outputs in tipos.values():
            for branch in outputs:
                for edge in branch:
                    assert edge["node"] in nodes_wf, f"Destino inexistente em connections: {edge['node']}"

    # Verifica tipos de nós AI Agent + LLM + Tool
    assert nodes_wf["AI Agent de Governança Estratégica"]["type"] == "@n8n/n8n-nodes-langchain.agent"
    assert nodes_wf["LLM Chat Model (OpenRouter)"]["type"] == "@n8n/n8n-nodes-langchain.lmChatOpenAi"
    assert nodes_wf["Tool: Políticas de Governança"]["type"] == "@n8n/n8n-nodes-langchain.toolCode"

    # Verifica que Consolidar consome os dados mesclados do Merge
    js_consolidar = nodes_wf["Consolidar Dossiê Contratual Final"]["parameters"]["jsCode"]
    assert "agente1_resultado" in js_consolidar and "agente2_resultado" in js_consolidar, (
        "Nó Consolidar deve ler os campos mesclados do nó Merge"
    )
    print(f" -> [OK] {wf_principal_path.name}: {len(nodes_wf)} nós e todas as conexões/AI nodes íntegros.")

    # Validação do Sub-workflow reutilizável
    sub = json.loads(sub_wf_path.read_text(encoding="utf-8"))
    nodes_sub = {n["name"]: n for n in sub["nodes"]}
    conns_sub = sub["connections"]
    for nome in [
        "Trigger de Execução (Sub-workflow)",
        "Inicializar Contador de Polling",
        "Incrementar Tentativa",
        "Aguardar Intervalo (Wait)",
        "Consultar Status HTTP GET",
        "Consolidar Estado do Polling",
        "Tarefa Finalizada (Status Done)?",
        "Erro ou Tentativas Esgotadas?",
    ]:
        assert nome in nodes_sub, f"Nó obrigatório ausente no sub-workflow: {nome}"

    for src, tipos in conns_sub.items():
        assert src in nodes_sub, f"Origem inexistente no sub-workflow: {src}"
        for outputs in tipos.values():
            for branch in outputs:
                for edge in branch:
                    assert edge["node"] in nodes_sub, f"Destino inexistente no sub-workflow: {edge['node']}"

    # Garante que não há referência estática quebrada de contador no If do sub-workflow
    if_conds = json.dumps(nodes_sub["Erro ou Tentativas Esgotadas?"]["parameters"])
    assert "$json.tentativa_atual" in if_conds and "$json.max_tentativas" in if_conds, (
        "Sub-workflow deve comparar o estado dinâmico de tentativa_atual vs max_tentativas"
    )
    print(f" -> [OK] {sub_wf_path.name}: {len(nodes_sub)} nós e máquina de estados do polling validados.")

def iniciar_servidor(pasta: str, porta: int):
    """Inicia o microserviço FastAPI em processo isolado na porta especificada."""
    python_exe = sys.executable
    log_file = open(root_dir / "workflows" / f"{pasta}_server.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [python_exe, "-u", "-m", "uvicorn", "main:app", "--port", str(porta), "--host", "127.0.0.1"],
        cwd=str(root_dir / pasta),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True
    )
    return proc, log_file

def aguardar_servico(url: str, nome: str, timeout: int = 25):
    """Aguarda o endpoint de health check responder."""
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                print(f" -> [{nome}] Servidor pronto e saudável em {url}")
                return True
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"Servidor {nome} não respondeu em {url} dentro de {timeout}s.")

def executar_orquestracao_n8n_completa():
    print("=" * 80)
    print("INICIANDO TESTE DE ORQUESTRAÇÃO COMPLETA n8n (TP4)")
    print("Pipeline Assíncrono com Polling, Roteamento e Merge entre Agente 1 e Agente 2")
    print("=" * 80)

    url_agente1 = "http://127.0.0.1:8001"
    url_agente2 = "http://127.0.0.1:8002"

    proc_agente1, log1 = None, None
    proc_agente2, log2 = None, None

    try:
        print("\n[INICIALIZAÇÃO DOS MICROSSERVIÇOS]")
        # Verifica se já estão rodando ou se precisam ser iniciados
        try:
            r1 = requests.get(f"{url_agente1}/health", timeout=1)
            if r1.status_code == 200:
                print(f" -> Agente 1 já ativo em {url_agente1}")
        except Exception:
            print(f" -> Iniciando Agente 1 na porta 8001...")
            proc_agente1, log1 = iniciar_servidor("agent1", 8001)
            aguardar_servico(url_agente1, "Agente 1")

        try:
            r2 = requests.get(f"{url_agente2}/health", timeout=1)
            if r2.status_code == 200:
                print(f" -> Agente 2 já ativo em {url_agente2}")
        except Exception:
            print(f" -> Iniciando Agente 2 na porta 8002...")
            proc_agente2, log2 = iniciar_servidor("agent2", 8002)
            aguardar_servico(url_agente2, "Agente 2")

        # 1. Minuta contratual enviada ao n8n
        minuta_contrato = (
            "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL\n\n"
            "CONTRATANTE: TechSolutions Ltda., inscrita no CNPJ sob o nº 12.345.678/0001-90, com sede na Av. Paulista, 1000, São Paulo/SP.\n"
            "CONTRATADA: Alfa Consultoria em IA S.A., inscrita no CNPJ sob o nº 98.765.432/0001-10, com sede no Rio de Janeiro/RJ.\n\n"
            "CLÁUSULA PRIMEIRA - DO OBJETO\n"
            "O presente instrumento tem por objeto a prestação de serviços técnicos especializados de desenvolvimento, integração "
            "e suporte de agentes inteligentes autônomos para análise contratual.\n\n"
            "CLÁUSULA SEGUNDA - DO VALOR E FORMA DE PAGAMENTO\n"
            "Pela prestação dos serviços, a CONTRATANTE pagará à CONTRATADA o valor global de R$ 120.000,00 (cento e vinte mil reais), "
            "dividido em 12 (doze) parcelas mensais e sucessivas de R$ 10.000,00 (dez mil reais).\n\n"
            "CLÁUSULA TERCEIRA - DA VIGÊNCIA\n"
            "O prazo de vigência deste contrato é de 12 (doze) meses, iniciando-se em 15 de janeiro de 2026 e encerrando-se em 15 de janeiro de 2027. "
            "O contrato poderá ser rescindido antecipadamente mediante aviso prévio por escrito de 30 (trinta) dias.\n\n"
            "CLÁUSULA QUARTA - DA RESCISÃO E MULTA\n"
            "Em caso de rescisão imotivada por iniciativa de qualquer das partes antes do término do prazo estipulado, "
            "a parte que der causa incorrerá em multa compensatória de 20% (vinte por cento) sobre o saldo remanescente do contrato."
        )

        # 2. Submissão ao Agente 1 (HTTP POST /run)
        print("\n[NÓ n8n: Agente 1 - Submeter POST /run]")
        resp_post1 = requests.post(f"{url_agente1}/run", json={"texto_contrato": minuta_contrato}, timeout=10)
        assert resp_post1.status_code == 202, f"Erro status Agente 1 POST /run: {resp_post1.status_code}"
        dados_post1 = resp_post1.json()
        task_id_1 = dados_post1["task_id"]
        print(f" -> Resposta HTTP: 202 Accepted | Task ID: {task_id_1} | Status Inicial: {dados_post1['status']}")

        # 3. Polling de Status do Agente 1 (HTTP GET /status/{task_id})
        print("\n[NÓ n8n: Agente 1 - Loop de Polling GET /status/{task_id}]")
        agente1_concluido = False
        resultado_agente1 = None
        tentativas = 0
        max_tentativas = 20

        while not agente1_concluido and tentativas < max_tentativas:
            tentativas += 1
            resp_status1 = requests.get(f"{url_agente1}/status/{task_id_1}", timeout=10)
            assert resp_status1.status_code == 200, f"Erro status Agente 1 GET /status: {resp_status1.status_code}"
            payload_status1 = resp_status1.json()
            print(f" -> Polling #{tentativas}: status='{payload_status1['status']}'")

            if payload_status1["status"] == "done":
                agente1_concluido = True
                resultado_agente1 = payload_status1
                print(" -> Agente 1 concluiu extração com SUCESSO!")
                break
            elif payload_status1["status"] == "error":
                raise RuntimeError(f"Agente 1 falhou no processamento: {payload_status1.get('error')}")

            time.sleep(2)

        assert agente1_concluido, "Agente 1 não concluiu no tempo esperado."
        dados_extraidos = resultado_agente1["data"]
        print(f" -> Objeto Extraído: '{dados_extraidos.get('titulo')}'")
        print(f" -> Fornecedor Homologado: {dados_extraidos.get('fornecedor_homologado', {}).get('razao_social')}")

        # 4. Lógica de Roteamento (Nó If / Switch)
        print("\n[NÓ n8n: Roteador - Avaliação de Integridade Contratual]")
        valor_total = dados_extraidos.get("financeiro", {}).get("valor_total_brl", 0)
        tem_penalidades = dados_extraidos.get("penalidades") is not None

        if valor_total > 0 and tem_penalidades:
            print(f" -> Condição atendida: Valor total = R$ {valor_total:,.2f} > 0 e Cláusula Penal identificada.")
            print(" -> ROTEAMENTO ATIVADO: Encaminhando dados para Agente 2 (Auditoria de Risco).")
        else:
            print(" -> ALERTA: Dados insuficientes para auditoria. Rota de exceção ativada.")
            return

        # 5. Submissão ao Agente 2 (HTTP POST /run)
        print("\n[NÓ n8n: Agente 2 - Submeter POST /run]")
        resp_post2 = requests.post(f"{url_agente2}/run", json={"dados_contrato": dados_extraidos}, timeout=10)
        assert resp_post2.status_code == 202, f"Erro status Agente 2 POST /run: {resp_post2.status_code}"
        dados_post2 = resp_post2.json()
        task_id_2 = dados_post2["task_id"]
        print(f" -> Resposta HTTP: 202 Accepted | Task ID: {task_id_2} | Status Inicial: {dados_post2['status']}")

        # 6. Polling de Status do Agente 2 (HTTP GET /status/{task_id})
        print("\n[NÓ n8n: Agente 2 - Loop de Polling GET /status/{task_id}]")
        agente2_concluido = False
        resultado_agente2 = None
        tentativas = 0
        max_tentativas = 40

        while not agente2_concluido and tentativas < max_tentativas:
            tentativas += 1
            resp_status2 = requests.get(f"{url_agente2}/status/{task_id_2}", timeout=10)
            assert resp_status2.status_code == 200, f"Erro status Agente 2 GET /status: {resp_status2.status_code}"
            payload_status2 = resp_status2.json()
            print(f" -> Polling #{tentativas}: status='{payload_status2['status']}'")

            if payload_status2["status"] == "done":
                agente2_concluido = True
                resultado_agente2 = payload_status2
                print(" -> Agente 2 concluiu auditoria de risco com SUCESSO!")
                break
            elif payload_status2["status"] == "error":
                raise RuntimeError(f"Agente 2 falhou na auditoria: {payload_status2.get('error')}")

            time.sleep(2)

        assert agente2_concluido, "Agente 2 não concluiu no tempo esperado."
        dados_auditoria = resultado_agente2["data"]

        # 7. Nó de Merge & Consolidação Final (Nó Merge + Code)
        print("\n[NÓ n8n: Merge & Consolidar Dossiê Contratual]")
        score = dados_auditoria.get("score_conformidade", 0)
        nivel_risco = dados_auditoria.get("nivel_risco_geral", "ALTO")
        if nivel_risco == "ALTO":
            decisao = "BLOQUEADO_REVISAO_JURIDICA_OBRIGATORIA"
        elif nivel_risco == "MEDIO":
            decisao = "APROVADO_DIRETORIA_EXECUTIVA"
        else:
            decisao = "APROVADO_SUMARIAMENTE"

        dossie_final = {
            "metadata_pipeline": {
                "orquestrador": "n8n Workflow Engine v1.x/v2.x",
                "ciclo": "Assíncrono Completo com Polling e Roteamento de Risco",
                "timestamp_conclusao": datetime.now(timezone.utc).isoformat(),
                "agente_extracao": {
                    "task_id": task_id_1,
                    "status": resultado_agente1["status"],
                    "tempo_processamento_s": round(resultado_agente1["completed_at"] - resultado_agente1["created_at"], 2)
                },
                "agente_auditoria": {
                    "task_id": task_id_2,
                    "status": resultado_agente2["status"],
                    "tempo_processamento_s": round(resultado_agente2["completed_at"] - resultado_agente2["created_at"], 2)
                }
            },
            "contrato": {
                "titulo": dados_extraidos.get("titulo"),
                "partes": {
                    "contratante": dados_extraidos.get("contratante"),
                    "contratada": dados_extraidos.get("contratada")
                },
                "objeto": dados_extraidos.get("objeto"),
                "financeiro": dados_extraidos.get("financeiro"),
                "vigencia": dados_extraidos.get("vigencia"),
                "penalidades": dados_extraidos.get("penalidades"),
                "fornecedor_homologado": dados_extraidos.get("fornecedor_homologado")
            },
            "auditoria_conformidade": {
                "score_conformidade": score,
                "nivel_risco_geral": nivel_risco,
                "total_regras_auditadas": dados_auditoria.get("total_regras_auditadas"),
                "itens_conformes": dados_auditoria.get("itens_conformes"),
                "itens_alerta": dados_auditoria.get("itens_alerta"),
                "itens_nao_conformes": dados_auditoria.get("itens_nao_conformes"),
                "itens_auditados": dados_auditoria.get("itens_auditados"),
                "recomendacoes_mitigacao": dados_auditoria.get("recomendacoes_mitigacao"),
                "parecer_executivo_markdown": dados_auditoria.get("parecer_executivo_markdown")
            },
            "decisao_governanca": decisao
        }

        # Salva evidência completa
        caminho_evidencia = root_dir / "workflows" / "evidencia_execucao_orquestrador_tp4.json"
        with open(caminho_evidencia, "w", encoding="utf-8") as f:
            json.dump(dossie_final, f, indent=2, ensure_ascii=False)

        print(f" -> Dossiê gerado com sucesso!")
        print(f" -> Score de Conformidade: {score}/100 | Nível de Risco: {nivel_risco}")
        print(f" -> Decisão de Governança: {decisao}")
        print(f" -> Evidência consolidada gravada em: {caminho_evidencia.name}")
        print("=" * 80)
        print("ORQUESTRAÇÃO CONCLUÍDA COM 100% DE SUCESSO!")
        print("=" * 80)

    finally:
        # Encerra processos se foram iniciados por este script
        if proc_agente1:
            proc_agente1.terminate()
        if proc_agente2:
            proc_agente2.terminate()
        if log1:
            log1.close()
        if log2:
            log2.close()

if __name__ == "__main__":
    validar_estrutura_workflows_n8n()
    executar_orquestracao_n8n_completa()
