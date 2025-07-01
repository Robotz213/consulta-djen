import re

from consulta_djen.types import Dicts


def convert_tostring(
    data: Dicts,
) -> Dicts:
    for k, v in list(data.items()):
        if not v:
            continue

        data[str(k)] = str(v)

    return data


def limpar_ilegais_regex(texto: str) -> str:
    # Remove todos os caracteres de controle (ASCII 0-31), exceto \n, \r e \t
    return re.sub(r"[^\x20-\x7E\n\r\t]", "", texto)


def convertToQueryString(query: dict[str, str]) -> str:
    return "&".join(f"{key}={value}" for key, value in query.items())
