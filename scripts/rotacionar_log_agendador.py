from pathlib import Path
import argparse
import sys

LIMITE_PADRAO = 5 * 1024 * 1024
HISTORICOS_PADRAO = 3

def rotacionar(arquivo, limite, historicos):
    if not arquivo.exists():
        return False

    if not arquivo.is_file():
        raise ValueError("Caminho do log nao e arquivo.")

    if arquivo.stat().st_size < limite:
        return False

    for numero in range(historicos, 0, -1):
        origem = (
            arquivo if numero == 1
            else arquivo.with_name(
                f"{arquivo.name}.{numero - 1}"
            )
        )

        destino = arquivo.with_name(
            f"{arquivo.name}.{numero}"
        )

        if origem.exists():
            origem.replace(destino)

    return True

def main():
    parser = argparse.ArgumentParser()

    padrao = (
        Path(__file__).resolve().parents[1]
        / "logs"
        / "agendador_windows.log"
    )

    parser.add_argument(
        "--arquivo", type=Path, default=padrao
    )
    parser.add_argument(
        "--limite", type=int, default=LIMITE_PADRAO
    )
    parser.add_argument(
        "--historicos", type=int,
        default=HISTORICOS_PADRAO
    )

    args = parser.parse_args()

    if args.limite < 1 or args.historicos < 1:
        parser.error("Limites devem ser positivos.")

    try:
        if rotacionar(
            args.arquivo,
            args.limite,
            args.historicos
        ):
            print("Log do agendador arquivado.")
    except (OSError, ValueError) as erro:
        print(f"Erro ao rotacionar log: {erro}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())