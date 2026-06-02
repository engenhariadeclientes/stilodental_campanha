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

API_KEY  = os.environ["BOTCONVERSA_API_KEY"]
BASE_URL = "https://backend.botconversa.com.br/api/v1/webhook"
HEADERS  = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

DELAY = 1.2  # segundos entre requests
CAMPO_IDS = {}


def listar_campos_personalizados():
    try:
        resp = requests.get(f"{BASE_URL}/custom_fields/", headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            campos = resp.json()
            for campo in campos:
                CAMPO_IDS[campo["key"]] = campo["id"]
            log.info(f"Campos personalizados carregados: {CAMPO_IDS}")
        else:
            log.error(f"Erro ao listar campos: HTTP {resp.status_code} → {resp.text[:200]}")
    except Exception as e:
        log.error(f"Erro ao listar campos: {e}")


def buscar_contato(telefone: str) -> dict | None:
    try:
        resp = requests.get(
            f"{BASE_URL}/subscriber/get_by_phone/{telefone}/",
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


def criar_contato(telefone: str, primeiro_nome: str, sobrenome: str) -> dict | None:
    payload = {
        "phone": telefone,
        "first_name": primeiro_nome,
        "last_name": sobrenome
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/subscriber/",
            headers=HEADERS,
            json=payload,
            timeout=15
        )
        if resp.status_code in (200, 201):
            return resp.json()
        else:
            log.warning(f"Criação {telefone} → HTTP {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        log.error(f"Erro ao criar {telefone}: {e}")
        return None


def atualizar_campo(subscriber_id: int, campo_key: str, valor: str) -> bool:
    campo_id = CAMPO_IDS.get(campo_key)
    if not campo_id:
        log.warning(f"  Campo '{campo_key}' não encontrado — pulando")
        return False
    try:
        resp = requests.post(
            f"{BASE_URL}/subscriber/{subscriber_id}/custom_fields/{campo_id}/",
            headers=HEADERS,
            json={"value": valor},
            timeout=15
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        log.error(f"Erro ao atualizar campo {campo_key}: {e}")
        return False


def main():
    listar_campos_personalizados()
    if not CAMPO_IDS:
        log.error("Nenhum campo personalizado encontrado. Verifique a API key.")
        return

    df = pd.read_csv("dados_pacientes.csv", dtype=str).fillna("")
    total = len(df)
    criados = 0
    atualizados = 0
    erro = 0

    log.info(f"Iniciando processamento de {total} contatos...")
    log.info("=" * 60)

    for i, row in df.iterrows():
        nome_completo = row["Paciente"]
        telefone      = row["telefone"]
        partes        = nome_completo.strip().split()
        primeiro      = partes[0].capitalize() if partes else ""
        sobrenome     = " ".join(partes[1:]) if len(partes) > 1 else ""
        tel_formatado = f"+{telefone}" if not telefone.startswith("+") else telefone

        if not telefone:
            log.warning(f"[{i+1}/{total}] {nome_completo} — sem telefone, pulando")
            erro += 1
            continue

        log.info(f"[{i+1}/{total}] {nome_completo} ({tel_formatado})")

        contato = buscar_contato(tel_formatado)
        time.sleep(DELAY)

        if contato is None:
            log.info(f"  → Não encontrado, criando...")
            contato = criar_contato(tel_formatado, primeiro, sobrenome)
            time.sleep(DELAY)
            if contato is None:
                log.warning(f"  → ✗ Falha ao criar contato")
                erro += 1
                continue
            criados += 1
            log.info(f"  → Contato criado (ID: {contato.get('id')})")
        else:
            log.info(f"  → Encontrado (ID: {contato.get('id')})")

        subscriber_id = contato.get("id")
        if not subscriber_id:
            log.warning(f"  → ✗ ID não retornado pela API")
            erro += 1
            continue

        campos_para_atualizar = {
    "Telefone":       tel_formatado,
    "Data_Orçamento": row.get("Data_Orcamento", ""),
    "valor_orcado":   row.get("valor_orcado", ""),
    "Proced_Orçado":  row.get("Proced_Orcado", ""),
    "Inatividade":    row.get("Inatividade", ""),
}

        campos_ok = []
        for key, valor in campos_para_atualizar.items():
            if valor and key in CAMPO_IDS:
                ok = atualizar_campo(subscriber_id, key, valor)
                time.sleep(0.5)
                if ok:
                    campos_ok.append(key)

        if campos_ok:
            log.info(f"  → ✓ Campos atualizados: {', '.join(campos_ok)}")
            atualizados += 1
        else:
            log.warning(f"  → Nenhum campo atualizado (verifique os keys no BotConversa)")
            erro += 1

    log.info("=" * 60)
    log.info(f"CONCLUÍDO: {criados} criados | {atualizados} atualizados | {erro} erros")


if __name__ == "__main__":
    main()
