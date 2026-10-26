"""
Script de Simulação End-to-End Local
Executa o fluxo completo do RPA + Lógica de Cruzamento do N8N + Geração de Recomendações
"""

import os
import csv
import json
from scraper import extrair_clientes_html

def carregar_catalogo_investimentos(caminho_csv: str):
    investimentos = []
    with open(caminho_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            investimentos.append(row)
    return investimentos

def cruzar_e_gerar_recomendacoes(clientes, investimentos):
    recomendacoes = []

    for cliente in clientes:
        perfil = cliente["perfil_investidor"]
        saldo = cliente["saldo_numerico"]
        
        # Filtra os investimentos compatíveis com o perfil do cliente
        produtos_compativeis = [
            inv for inv in investimentos 
            if inv["perfil_recomendado"].lower() == perfil.lower()
            and float(inv["aplicacao_minima"]) <= saldo
        ]

        # Montar mensagem personalizada (simulando nó de IA / Template do N8N)
        produtos_nomes = ", ".join([f"{p['nome_produto']} ({p['rentabilidade_estimada']})" for p in produtos_compativeis[:2]])
        
        mensagem = (
            f"Olá {cliente['nome']}, identificamos que seu perfil financeiro é {perfil.upper()} "
            f"com saldo de {cliente['saldo_formatado']} disponível para aplicação. "
            f"Com base na nossa análise de mercado, recomendamos alocar seus recursos em: {produtos_nomes}. "
            f"Acesse o App Santander para confirmar a operação com segurança!"
        )

        recomendacoes.append({
            "cliente_id": cliente["id"],
            "nome": cliente["nome"],
            "email": cliente["email"],
            "perfil": perfil,
            "saldo": cliente["saldo_formatado"],
            "produtos_sugeridos": produtos_compativeis,
            "mensagem_personalizada": mensagem
        })

    return recomendacoes

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_html = os.path.join(base_dir, "docs", "index.html")
    caminho_csv = os.path.join(base_dir, "docs", "data.csv")

    print("[*] Iniciando teste local integrado do projeto...")
    clientes = extrair_clientes_html(caminho_html)
    investimentos = carregar_catalogo_investimentos(caminho_csv)

    print(f"[+] Total de clientes lidos: {len(clientes)}")
    print(f"[+] Total de opções de investimento: {len(investimentos)}")

    resultado = cruzar_e_gerar_recomendacoes(clientes, investimentos)

    caminho_saida = os.path.join(base_dir, "resultado_recomendacoes.json")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Sucesso! {len(resultado)} recomendações geradas.")
    print(f"[+] Relatório exportado para: {caminho_saida}")
    print("\n--- EXEMPLO DE MENSAGEM GERADA ---")
    print(resultado[0]["mensagem_personalizada"])

if __name__ == "__main__":
    main()
