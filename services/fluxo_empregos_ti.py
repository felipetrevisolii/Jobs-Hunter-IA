"""Busca organizada, compatibilidade e antirrepeticao de vagas TI."""

import os
import re
import sqlite3
import unicodedata
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

BASE = Path(__file__).resolve().parent.parent
BANCO = BASE / "vagas_enviadas.db"

COLUNAS = [
    "Encontrada em", "Area de TI", "Cargo", "Empresa",
    "Cidade", "Salario", "Modalidade", "Vinculo",
    "Compatibilidade", "Pontuacao", "Status", "Fonte", "Link"
]


def texto(valor):
    s = unicodedata.normalize(
        "NFKD", str(valor or "").lower()
    )
    s = "".join(
        c for c in s if not unicodedata.combining(c)
    )
    return re.sub(
        r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)
    ).strip()


def link_normalizado(link):
    try:
        p = urlsplit(str(link or "").strip())

        if p.scheme not in ("http", "https") or not p.hostname:
            return ""

        dominio = p.hostname.lower().removeprefix("www.")
        caminho = re.sub(r"/+", "/", p.path).rstrip("/") or "/"

        # Preserva IDs importantes, mas ignora rastreamento
        chaves = {
            "id", "jobid", "job_id", "vaga",
            "vaga_id", "codigo"
        }

        qs = sorted(
            (k.lower(), v)
            for k, v in parse_qsl(p.query)
            if k.lower() in chaves
        )

        return urlunsplit((
            "https", dominio, caminho, urlencode(qs), ""
        ))

    except (ValueError, TypeError):
        return ""


def chaves(vaga):
    link = link_normalizado(vaga.get("link"))

    if not link:
        return []

    resultado = ["link:" + link]
    empresa = texto(vaga.get("empresa"))
    titulo = texto(vaga.get("titulo"))
    cidade = texto(vaga.get("cidade"))

    if (
        empresa not in (
            "", "nao informada", "confidencial", "a confirmar"
        )
        and titulo
    ):
        resultado.append(
            "cargo:" + "|".join((empresa, titulo, cidade))
        )

    return resultado


def data_expirada(vaga):
    bruto = str(
        vaga.get("data_publicacao") or ""
    ).strip()[:10]

    if not bruto:
        return False

    try:
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", bruto):
            data = datetime.strptime(
                bruto, "%d/%m/%Y"
            ).date()
        else:
            data = date.fromisoformat(bruto)

        limite = int(os.getenv(
            "IDADE_MAXIMA_VAGA_DIAS", "30"
        ))

        return (date.today() - data).days > limite

    except ValueError:
        return False


def selecionar_vagas(vagas):
    resultado = []
    vistas = set()

    nota_minima = int(os.getenv(
        "PONTUACAO_MINIMA_TI", "55"
    ))

    for vaga in vagas:
        cargo = texto(vaga.get("titulo"))
        vinculo = texto(vaga.get("vinculo"))
        tipo = texto(vaga.get("tipo_oportunidade"))

        # Vagas freelance são rejeitadas neste projeto
        if re.search(
            r"\b(freelancer?|autonomo|por projeto|bico)\b",
            " ".join((cargo, vinculo, tipo))
        ):
            continue

        # Descarta cargos acima do nivel desejado
        if re.search(
            r"\b(pleno|senior|gerente|diretor|coordenador|aprendiz)\b",
            cargo
        ):
            continue

        if (
            int(vaga.get("pontuacao_perfil") or 0) < nota_minima
            or data_expirada(vaga)
        ):
            continue

        identificadores = chaves(vaga)

        if (
            not identificadores
            or any(k in vistas for k in identificadores)
        ):
            continue

        vistas.update(identificadores)
        resultado.append(vaga)

    return sorted(
        resultado,
        key=lambda v: (
            int(v.get("pontuacao_perfil") or 0),
            int(v.get("pontuacao") or 0)
        ),
        reverse=True
    )


def _conexao():
    db = sqlite3.connect(BANCO, timeout=10)

    db.execute("""
        CREATE TABLE IF NOT EXISTS identidades_ti (
            chave TEXT PRIMARY KEY,
            cadastrado_em TEXT NOT NULL
        )
    """)

    return db


def ja_registrada(vaga):
    identificadores = chaves(vaga)

    if not identificadores:
        return True

    with _conexao() as db:
        for chave in identificadores:
            if db.execute(
                "SELECT 1 FROM identidades_ti WHERE chave=?",
                (chave,)
            ).fetchone():
                return True

        existe = db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='vagas_enviadas'
        """).fetchone()

        if existe:
            for (url,) in db.execute(
                "SELECT link FROM vagas_enviadas"
            ):
                if (
                    "link:" + link_normalizado(url)
                    in identificadores
                ):
                    return True

    return False


def registrar_identidade(vaga):
    agora = datetime.now().isoformat(
        timespec="seconds"
    )

    with _conexao() as db:
        db.executemany("""
            INSERT OR IGNORE INTO identidades_ti
            (chave, cadastrado_em) VALUES (?, ?)
        """, [
            (k, agora) for k in chaves(vaga)
        ])


def registrar_vaga_planilha(vaga):
    if os.getenv(
        "GOOGLE_SHEETS_ATIVO", "false"
    ).lower() != "true":
        return False

    try:
        import gspread

        spreadsheet_id = os.environ["GOOGLE_SHEETS_ID"]

        cred = Path(os.getenv(
            "GOOGLE_CREDENTIALS_JSON",
            "credentials_google.json"
        ))

        if not cred.is_absolute():
            cred = BASE / cred

        client = gspread.service_account(
            filename=str(cred)
        )

        planilha = client.open_by_key(spreadsheet_id)
        nome = os.getenv(
            "GOOGLE_SHEETS_ABA_TI", "Vagas_TI"
        )

        try:
            aba = planilha.worksheet(nome)

        except gspread.WorksheetNotFound:
            aba = planilha.add_worksheet(
                title=nome,
                rows=1000,
                cols=len(COLUNAS)
            )

        cabecalho = aba.row_values(1)

        if not cabecalho:
            aba.update(
                range_name="A1:M1",
                values=[COLUNAS]
            )
            aba.freeze(rows=1)

            try:
                aba.set_basic_filter()
            except Exception:
                pass

        elif cabecalho != COLUNAS:
            print("Sheets: cabecalho inesperado.")
            return False

        link = link_normalizado(vaga.get("link"))

        links = aba.col_values(13)[1:]

        if link and any(
            link_normalizado(l) == link for l in links
        ):
            return True

        linha = [
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            vaga.get("area_ti", ""),
            vaga.get("titulo", ""),
            vaga.get("empresa", ""),
            vaga.get("cidade", ""),
            vaga.get("salario", ""),
            vaga.get("modalidade", ""),
            vaga.get("vinculo", ""),
            vaga.get("compatibilidade_perfil", ""),
            vaga.get("pontuacao_perfil", ""),
            "Para avaliar",
            vaga.get("fonte", ""),
            vaga.get("link", "")
        ]

        aba.append_row(
            linha,
            value_input_option="RAW"
        )

        return True

    except Exception as exc:
        print(
            "Sheets: falha ao registrar -",
            type(exc).__name__,
            str(exc)[:160]
        )
        return False


def distribuir_links(links, limite):
    """Intercala resultados de diferentes areas de TI."""

    from collections import OrderedDict, deque
    from urllib.parse import unquote
    from areas_ti import identificar_areas

    grupos = OrderedDict()

    for url in links:
        candidato = (
            unquote(url)
            .replace("-", " ")
            .replace("_", " ")
        )

        areas = identificar_areas(candidato)
        nome = areas[0] if areas else "Outros"

        grupos.setdefault(
            nome, deque()
        ).append(url)

    resultado = []

    while grupos and len(resultado) < limite:
        for area in list(grupos):

            if grupos[area]:
                resultado.append(
                    grupos[area].popleft()
                )

                if len(resultado) >= limite:
                    break

            if not grupos[area]:
                del grupos[area]

    return resultado
