import json
from contextlib import ContextDecorator
from datetime import datetime, timedelta
from typing import Generator, TypeVar, Union

import openpyxl
import pandas as pd
import pytz
import requests

from consulta_djen.interfaces import JsonCNJ
from consulta_djen.interfaces.partes import (
    JSONAdvogado,
    JSONDestinatariosAdvogados,
    JsonPartes,
)
from consulta_djen.interfaces.publicacao import JSONPublicacoes


def convertToQueryString(query) -> str:
    return "&".join(f"{key}={value}" for key, value in query.items())


today = datetime.now(pytz.timezone("America/Manaus")).strftime("%Y-%m-%d")
inicio = (datetime.now(pytz.timezone("America/Manaus")) - timedelta(days=5)).strftime(
    "%Y-%m-%d"
)
query = {
    "siglaTribunal": "TJAM",
    "dataDisponibilizacaoInicio": inicio,
    "dataDisponibilizacaoFim": today,
    "nomeParte": "AMAZONAS DISTRIBUIDORA DE ENERGIA S.A.",
}
url = (
    "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
    + "?"
    + convertToQueryString(query)
)
headers = {
    "Content-Type": "application/json",
}

wb = openpyxl.Workbook()

Dicts = TypeVar(
    "Dicts",
    bound=Union[JSONAdvogado, JsonPartes, JSONPublicacoes, JSONDestinatariosAdvogados],
)


@ContextDecorator()
def iter_partes(
    list_partes: list[JsonPartes] | list[JSONAdvogado],
) -> Generator[JsonPartes | JSONAdvogado, None, None]:
    for item in list_partes:
        yield item


def data_cnj() -> Generator[JSONPublicacoes, None, None]:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        json_data = JsonCNJ(**json.loads(response.text))

        for item in json_data["items"]:
            yield item


def convert_tostring(
    data: Dicts,
) -> Dicts:
    for k, v in list(data.items()):
        if not v:
            continue

        data[str(k)] = str(v)

    return data


def separar_intimacoes() -> None:
    publicacoes = []
    advogados = []
    partes = []

    for item in data_cnj():
        advs: list[JSONDestinatariosAdvogados] = []
        parts: list[JsonPartes] = []
        data = JSONPublicacoes(**item)
        data.pop("destinatarioadvogados", [])
        data.pop("destinatarios", [])

        nproc = item["numero_processo"]
        item["texto"] = item["texto"].replace("<p>", "").replace("</p>", "\n")
        data["numero_processo"] = (
            f"{nproc[:7]}-{nproc[7:9]}.{nproc[9:13]}.{nproc[13:14]}.{nproc[14:16]}.{nproc[16:20]}"
        )

        for advogado in item["destinatarioadvogados"]:
            data_adv = JSONDestinatariosAdvogados(**advogado)
            data_adv.pop("advogado")

            for key, value in list(advogado["advogado"].items()):
                data_adv[f"advogado_{key}"] = value

            data_adv = convert_tostring(data_adv)
            advs.append(data_adv)

        for parte in item["destinatarios"]:
            data_partes = JsonPartes(**parte)

            data_partes = convert_tostring(data_partes)

            parts.append(data_partes)

        data = convert_tostring(data)

        if data["data_disponibilizacao"]:
            try:
                data["data_disponibilizacao"] = datetime.strptime(
                    str(data["data_disponibilizacao"]), "%Y-%m-%d"
                )

            except ValueError:
                data["data_disponibilizacao"] = datetime.strptime(
                    str(data["data_disponibilizacao"]), "%d-%m-%Y"
                )

        if data["data_cancelamento"]:
            try:
                data["data_cancelamento"] = datetime.strptime(
                    str(data["data_cancelamento"]), "%Y-%m-%d"
                )
            except ValueError:
                data["data_cancelamento"] = datetime.strptime(
                    str(data["data_cancelamento"]), "%d-%m-%Y"
                )

        publicacoes.append(data)
        advogados.extend(advs)
        partes.extend(parts)

    # Depois de coletar todos os dados, crie os DataFrames uma única vez
    df_publicacoes = pd.DataFrame(publicacoes)
    df_advogados = pd.DataFrame(advogados)
    df_partes = pd.DataFrame(partes)

    # Salve em Excel ou outro formato conforme necessário
    with pd.ExcelWriter(f"Intimaçoes {today}.xlsx") as writer:
        df_publicacoes.to_excel(writer, sheet_name="Publicações", index=False)
        df_advogados.to_excel(writer, sheet_name="Advogados", index=False)
        df_partes.to_excel(writer, sheet_name="Partes", index=False)


separar_intimacoes()
