import os
from pathlib import Path
from dotenv import load_dotenv

from scrapers.trabalhabrasil import buscar_vagas as buscar_trabalhabrasil
from scrapers.empregacampinas import buscar_vagas as buscar_empregacampinas
from scrapers.infojobs import buscar_vagas as buscar_infojobs
from services.filtro_novas_oportunidades import filtrar_vagas
from services.avaliador_perfil import avaliar_vaga
from services.banco import (criar_tabela, vaga_ja_enviada, salvar_vaga,
                            status_entrega, registrar_canal)
from services.telegram_sender import enviar_telegram, enviar_resumo_diario
from services.fluxo_empregos_ti import (
    registrar_vaga_planilha, selecionar_vagas,
    ja_registrada, registrar_identidade
)
from services.logger_config import configurar_logger

logger = configurar_logger()
BASE_DIR = Path(__file__).resolve().parent


def booleano(nome, padrao='false'):
    return os.getenv(nome, padrao).lower() == 'true'


def main():
    load_dotenv(BASE_DIR / '.env')
    criar_tabela()
    logger.info('Job Hunter IA TI iniciado.')
    salario_minimo = int(os.getenv('SALARIO_MINIMO', '2500'))
    salario_faixa_boa = int(os.getenv('SALARIO_FAIXA_BOA', '3000'))
    salario_meta = int(os.getenv('SALARIO_META', '3500'))
    if not 0 < salario_minimo <= salario_faixa_boa <= salario_meta:
        raise ValueError('Salários devem obedecer 0 < SALARIO_MINIMO <= SALARIO_FAIXA_BOA <= SALARIO_META')
    cidades = [t.strip() for t in os.getenv('CIDADES','Campinas,Valinhos').split(',') if t.strip()]
    cargos = [t.strip() for t in os.getenv('CARGOS_BUSCA','Suporte Técnico,Analista de Suporte,Help Desk,Infraestrutura,Assistente de TI,Suporte Sistemas').split(',') if t.strip()]
    logger.info(f'Cidades permitidas (presencial/híbrido): {cidades}; vagas remotas: Brasil')
    logger.info(f'Faixas salariais (R$/mês): mínimo {salario_minimo}; boa oportunidade {salario_faixa_boa}; meta {salario_meta}. Sem salário: {booleano("ACEITAR_SALARIO_NAO_INFORMADO", "true")}')
    logger.info('Vínculo priorizado: CLT. Vínculo não informado: condicionado a conferência.')
    logger.info(f'Busca de TI por termos: {cargos}')
    logger.info('Envio automático de currículo por e-mail: desativado definitivamente no main.py.')

    fontes = [('Trabalha Brasil', buscar_trabalhabrasil),
              ('Emprega Campinas', buscar_empregacampinas),
              ('InfoJobs', buscar_infojobs)]
    coletadas = []
    fontes_resultado = []
    for nome, busca in fontes:
        try:
            vagas = busca()
            coletadas.extend(vagas)
            fontes_resultado.append({'fonte':nome,'quantidade':len(vagas),'status':'ok'})
            logger.info(f'{nome}: {len(vagas)} vagas coletadas')
        except Exception as erro:
            logger.exception(f'Erro em {nome}: {erro}')
            fontes_resultado.append({'fonte':nome,'quantidade':0,'status':'erro','erro':str(erro)})

    aprovadas, diag = filtrar_vagas(
        coletadas, cargos, cidades, salario_minimo, retornar_diagnostico=True,
        aceitar_salario_nao_informado=booleano('ACEITAR_SALARIO_NAO_INFORMADO','true'),
        aceitar_vinculo_nao_informado=booleano('ACEITAR_VINCULO_NAO_INFORMADO','true'),
        salario_faixa_boa=salario_faixa_boa, salario_meta=salario_meta
    )
    logger.info(f'Filtros de TI: {diag}')
    for vaga in aprovadas:
        avaliar_vaga(vaga)
    aprovadas.sort(
        key=lambda v: (
            v.get('pontuacao_perfil', 0),
            v.get('pontuacao', 0)
        ), reverse=True
    )
    aprovadas = selecionar_vagas(aprovadas)
    links_vistos = set()
    novas = []
    for vaga in aprovadas:
        link = vaga.get('link')
        if not link or link in links_vistos or vaga_ja_enviada(link) or ja_registrada(vaga):
            continue
        links_vistos.add(link)
        novas.append(vaga)
        if len(novas) >= int(os.getenv("MAX_VAGAS_POR_EXECUCAO", "10")):
            break

    if booleano("MODO_TESTE"):
        logger.info(f"TESTE: {len(novas)} vagas novas")
        for v in novas:
            logger.info(
                f"{v.get('pontuacao_perfil')} pts | "
                f"{v.get('area_ti')} | "
                f"{v.get('titulo')} | "
                f"{v.get('link')}"
            )
        return

    entregues = 0
    for vaga in novas:
        link = vaga['link']
        # Apenas registra e notifica a vaga. Nenhum e-mail é enviado.
        # Campos temporários para manter compatibilidade com Telegram/Sheets.
        vaga['email_candidatura'] = 'Não encontrado'
        vaga['curriculo_enviado'] = 'Não'
        status = status_entrega(link)
        if not status['sheets_ok']:
            if not booleano('GOOGLE_SHEETS_ATIVO') or registrar_vaga_planilha(vaga):
                registrar_canal(link, 'sheets_ok')
                status['sheets_ok'] = True
        if not status['telegram_ok']:
            if enviar_telegram([vaga]):
                registrar_canal(link, 'telegram_ok')
                status['telegram_ok'] = True
        if status['sheets_ok'] and status['telegram_ok']:
            salvar_vaga(vaga)
            registrar_identidade(vaga)
            entregues += 1
        else:
            logger.warning(f'Entrega parcial; tentar novamente na próxima execução: {link}')

    logger.info(f'Coletadas {len(coletadas)}; aprovadas {len(aprovadas)}; novas {len(novas)}; entregues {entregues}')
    enviar_resumo_diario(
        total_coletadas=len(coletadas), vagas_dentro_criterios=len(aprovadas),
        vagas_novas=entregues, emails_encontrados=0,
        curriculos_enviados=0, fontes_resultado=fontes_resultado
    )
    logger.info('Job Hunter IA TI finalizado.')


if __name__ == '__main__':
    main()
