"""
Processo de RPA com Python e N8N - Santander Bootcamps (DIO)
Módulo: Coleta e Extração Automatizada de Dados (RPA)

Este script realiza a leitura da página de clientes (HTML), faz a raspagem
estruturada dos dados via BeautifulSoup, trata os tipos e dispara o payload
para o Webhook de orquestração do N8N.
"""

import os
import re
import json
import argparse
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests


def extrair_clientes_html(caminho_ou_url: str) -> List[Dict[str, Any]]:
    """
    Extrai os dados da tabela de clientes contida no HTML.
    Aceita caminho local de arquivo ou URL HTTP/HTTPS.
    """
    if caminho_ou_url.startswith("http://") or caminho_ou_url.startswith("https://"):
        print(f"[*] Fazendo requisição HTTP para: {caminho_ou_url}")
        response = requests.get(caminho_ou_url, timeout=15)
        response.raise_for_status()
        html_content = response.text
    else:
        if not os.path.exists(caminho_ou_url):
            raise FileNotFoundError(f"Arquivo HTML não encontrado: {caminho_ou_url}")
        print(f"[*] Lendo arquivo HTML local: {caminho_ou_url}")
        with open(caminho_ou_url, "r", encoding="utf-8") as f:
            html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    tabela = soup.find("table", {"id": "tabela-clientes"})
    
    if not tabela:
        # Fallback para qualquer tabela encontrada
        tabela = soup.find("table")
        if not tabela:
            raise ValueError("Nenhuma tabela encontrada no documento HTML.")

    linhas = tabela.find("tbody").find_all("tr") if tabela.find("tbody") else tabela.find_all("tr")[1:]
    clientes = []

    for linha in linhas:
        colunas = linha.find_all("td")
        if len(colunas) < 5:
            continue

        cliente_id = colunas[0].get_text(strip=True)
        nome = colunas[1].get_text(strip=True)
        email = colunas[2].get_text(strip=True)
        saldo_raw = colunas[3].get_text(strip=True)
        perfil = colunas[4].get_text(strip=True)

        # Tratar saldo numérico (Ex: "R$ 15.000,00" -> 15000.00)
        saldo_limpo = re.sub(r"[^\d,]", "", saldo_raw).replace(",", ".")
        saldo_float = float(saldo_limpo) if saldo_limpo else 0.0

        clientes.append({
            "id": cliente_id,
            "nome": nome,
            "email": email,
            "saldo_formatado": saldo_raw,
            "saldo_numerico": saldo_float,
            "perfil_investidor": perfil
        })

    return clientes


def enviar_para_n8n(webhook_url: str, dados_clientes: List[Dict[str, Any]]) -> bool:
    """
    Dispara os dados dos clientes para o Webhook configurado no N8N.
    """
    payload = {
        "origem": "RPA_Python_Scraper",
        "quantidade_clientes": len(dados_clientes),
        "clientes": dados_clientes
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"\n[>] Enviando {len(dados_clientes)} clientes para o N8N: {webhook_url}")
    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            print(f"[+] Sucesso! Status Code: {response.status_code}")
            print(f"[+] Resposta do N8N: {response.text[:200]}")
            return True
        else:
            print(f"[-] N8N retornou status code inesperado: {response.status_code}")
            print(f"[-] Detalhes: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[!] Não foi possível conectar ao Webhook do N8N ({webhook_url}): {e}")
        print("[!] Certifique-se de que o workflow do N8N está ativo (Active) ou em modo 'Listen for Test Event'.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="RPA de Extração de Clientes para Orquestração no N8N"
    )
    caminho_padrao_html = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "index.html"
    )
    
    parser.add_argument(
        "--source",
        default=caminho_padrao_html,
        help="Caminho local para o index.html ou URL do GitHub Pages"
    )
    parser.add_argument(
        "--webhook",
        default="http://localhost:5678/webhook/clientes-rpa",
        help="URL do Webhook do N8N para receber os dados"
    )
    parser.add_argument(
        "--output-json",
        default="clientes_extraidos.json",
        help="Arquivo JSON para salvar uma cópia local dos dados coletados"
    )
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Apenas extrai e salva em JSON sem enviar requisição ao N8N"
    )

    args = parser.parse_args()

    print("=" * 65)
    print("  SANTANDER OPEN FINANCE & N8N - RPA BOT DE INVESTIMENTOS")
    print("=" * 65)

    try:
        clientes = extrair_clientes_html(args.source)
        print(f"\n[+] Extração concluída com sucesso! Total: {len(clientes)} clientes.")
        
        for idx, cli in enumerate(clientes, 1):
            print(f"  {idx}. [{cli['perfil_investidor']:11}] {cli['nome']:25} | Saldo: {cli['saldo_formatado']}")

        # Salvar cópia local em JSON
        caminho_saida = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            args.output_json
        )
        with open(caminho_saida, "w", encoding="utf-8") as f:
            json.dump(clientes, f, ensure_ascii=False, indent=2)
        print(f"\n[+] Cópia local salva com sucesso em: {caminho_saida}")

        # Enviar para o n8n se solicitado
        if not args.no_send:
            enviar_para_n8n(args.webhook, clientes)
        else:
            print("[*] Flag --no-send utilizada: envio ao webhook ignorado.")

    except Exception as err:
        print(f"\n[X] Erro durante a execução do RPA: {err}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
