import os
from datetime import datetime

import requests


def formatar_moeda(valor):
    try:
        valor = int(valor)
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "Não calculado"


def enviar_mensagem_telegram(mensagem):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        print("ERRO: TELEGRAM_BOT_TOKEN não encontrado no .env")
        return False

    if not chat_id:
        print("ERRO: TELEGRAM_CHAT_ID não encontrado no .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": mensagem
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
        print("Mensagem enviada no Telegram.")
        return True
    except Exception as erro:
        print("Erro ao enviar Telegram:")
        print(erro)
        return False


def enviar_telegram(vagas):
    import re

    sucesso_geral = True

    for vaga in vagas:

        fonte = vaga.get("fonte") or "N\u00e3o informada"
        cargo = vaga.get("titulo") or "N\u00e3o informado"
        empresa = vaga.get("empresa") or "N\u00e3o informada"
        cidade = vaga.get("cidade") or "N\u00e3o informada"
        salario = vaga.get("salario") or "N\u00e3o informado"
        link = vaga.get("link") or "Link n\u00e3o informado"

        # Procura os beneficios informados na vaga
        beneficios = (
            vaga.get("beneficios")
            or vaga.get("benef\u00edcios") or vaga.get("benef?cios")
            or ""
        )

        if isinstance(beneficios, (list, tuple, set)):
            beneficios = ", ".join(map(str, beneficios))

        # Se nao houver campo especifico, procura na descricao
        if not str(beneficios).strip():
            descricao = str(vaga.get("descricao") or "")

            encontrado = re.search(
                r"(?im)^[ \t]*benef[i\u00ed]cios?[ \t]*:[ \t]*([^\r\n]+)",
                descricao
            )

            beneficios = (
                encontrado.group(1).strip()
                if encontrado else "N\u00e3o informado"
            )

        beneficios = str(beneficios).strip()[:180]

        mensagem = (
            "NOVA VAGA DE TI\n\n"
            f"Fonte: {fonte}\n"
            f"Cargo: {cargo}\n"
            f"Empresa: {empresa}\n"
            f"Cidade: {cidade}\n"
            f"Sal\u00e1rio: {salario}\n"
            f"Benef\u00edcios: {beneficios}\n\n"
            f"Candidatar-se: {link}"
        )

        enviado = enviar_mensagem_telegram(mensagem)

        if not enviado:
            sucesso_geral = False

    return sucesso_geral



def enviar_resumo_diario(
    total_coletadas,
    vagas_dentro_criterios,
    vagas_novas,
    emails_encontrados,
    curriculos_enviados,
    fontes_resultado
):
    enviar_resumo = os.getenv("ENVIAR_RESUMO_DIARIO", "true").lower()

    if enviar_resumo != "true":
        print("Resumo diário desativado no .env")
        return

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    linhas_fontes = []

    for fonte in fontes_resultado:
        nome = fonte.get("fonte", "Fonte não informada")
        quantidade = fonte.get("quantidade", 0)
        status = fonte.get("status", "ok")

        if status == "ok":
            linhas_fontes.append(f"✅ {nome}: {quantidade} vagas coletadas")
        else:
            erro = fonte.get("erro", "Erro não informado")
            linhas_fontes.append(f"⚠️ {nome}: erro - {erro}")

    texto_fontes = "\n".join(linhas_fontes)

    mensagem = f"""
📊 Relatório diário - Job Hunter IA

🕒 Execução: {agora}

📦 Total de vagas coletadas: {total_coletadas}
🎯 Vagas dentro dos critérios: {vagas_dentro_criterios}
🚨 Vagas novas enviadas: {vagas_novas}
🖱️ Candidaturas: realizadas manualmente pelo candidato

🔎 Fontes consultadas:
{texto_fontes}
"""

    enviar_mensagem_telegram(mensagem)