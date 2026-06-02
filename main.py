import os
import time
import pandas as pd
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

API_KEY = os.environ["BOTCONVERSA_API_KEY"]
BASE_URL = "https://api.botconversa.com.br/api/v1"
HEADERS = {"api-key": API_KEY, "Content-Type": "application/json"}

DELAY = 1.2  # segundos entre requests


def buscar_contato(telefone: str) -> dict | None:
    try:
        resp = requests.get(
            f"{BASE_URL}/contact/getByPhone/{telefone}",
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            log.warning(f"Busca {telefone} → HTTP {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        log.error(f"Erro ao buscar {telefone}: {e}")
        return None


def atualizar_contato(telefone: str, campos: dict) -> bool:
    payload = {
        "phone": telefone,
        "custom_fields": campos
    }
    try:
        resp = requests.patch(
            f"{BASE_URL}/contact/updateByPhone",
            headers=HEADERS,
            json=payload,
            timeout=15
        )
        if resp.status_code in (200, 201):
            return True
        else:
            log.warning(f"Atualização {telefone} → HTTP {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        log.error(f"Erro ao atualizar {telefone}: {e}")
        return False


def main():
    df = pd.read_csv("dados_pacientes.csv", dtype=str).fillna("")

    total = len(df)
    sucesso = 0
    nao_encontrado = 0
    erro = 0

    log.info(f"Iniciando atualização de {total} contatos...")
    log.info("=" * 60)

    for i, row in df.iterrows():
        nome     = row["Paciente"]
        telefone = row["telefone"]

        if not telefone:
            log.warning(f"[{i+1}/{total}] {nome} — sem telefone, pulando")
            erro += 1
            continue

        log.info(f"[{i+1}/{total}] {nome} ({telefone})")

        # Buscar contato
        contato = buscar_contato(telefone)
        time.sleep(DELAY)

        if contato is None:
            log.warning(f"  → Não encontrado no BotConversa")
            nao_encontrado += 1
            continue

        # Montar campos personalizados com o que temos
        campos = {}

        if row.get("primeiro_nome"):
            campos["primeiro-nome"] = row["primeiro_nome"]

        if row.get("telefone"):
            campos["telefone"] = row["telefone"]

        if row.get("Data_Orcamento"):
            campos["Data_Orcamento"] = row["Data_Orcamento"]

        if row.get("valor_orcado"):
            campos["valor_orcado"] = row["valor_orcado"]

        if row.get("Proced_Orcado"):
            campos["Proced_Orcado"] = row["Proced_Orcado"]

        if row.get("Inatividade"):
            campos["Inatividade"] = row["Inatividade"]

        ok = atualizar_contato(telefone, campos)
        time.sleep(DELAY)

        if ok:
            campos_str = " | ".join(f"{k}: {v}" for k, v in campos.items())
            log.info(f"  → ✓ {campos_str}")
            sucesso += 1
        else:
            log.warning(f"  → ✗ Falha na atualização")
            erro += 1

    log.info("=" * 60)
    log.info(f"CONCLUÍDO: {sucesso} atualizados | {nao_encontrado} não encontrados | {erro} erros")


if __name__ == "__main__":
    main()
