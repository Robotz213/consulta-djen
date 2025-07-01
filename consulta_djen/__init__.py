from datetime import datetime, timedelta

import pandas as pd
import pytz

from consulta_djen.cnj import data_cnj
from consulta_djen.interfaces.partes import (
    JSONDestinatariosAdvogados,
    JsonPartes,
)
from consulta_djen.interfaces.publicacao import JSONPublicacoes
from consulta_djen.utils import (
    convert_tostring,
    convertToQueryString,
    limpar_ilegais_regex,
)

today = datetime.now(pytz.timezone("America/Manaus")).strftime("%Y-%m-%d")
inicio = (datetime.now(pytz.timezone("America/Manaus")) - timedelta(days=5)).strftime(
    "%Y-%m-%d"
)


class PublicacoesDJEN:
    publicacoes = []
    advogados = []
    partes = []

    def __init__(self) -> None:
        # Depois de coletar todos os dados, crie os DataFrames uma única vez

        self.queue()

        df_publicacoes = pd.DataFrame(self.publicacoes)
        df_advogados = pd.DataFrame(self.advogados)
        df_partes = pd.DataFrame(self.partes)

        # Salve em Excel ou outro formato conforme necessário
        with pd.ExcelWriter(f"Intimaçoes {today}.xlsx") as writer:
            df_publicacoes.to_excel(writer, sheet_name="Publicações", index=False)
            df_advogados.to_excel(writer, sheet_name="Advogados", index=False)
            df_partes.to_excel(writer, sheet_name="Partes", index=False)

    def handle_url(self, nome: str) -> str:
        query = {
            "dataDisponibilizacaoInicio": inicio,
            "dataDisponibilizacaoFim": today,
            "nomeParte": nome,
        }
        url = (
            "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
            + "?"
            + convertToQueryString(query)
        )

        return url

    def queue(self) -> None:
        nomes = [
            "AMAZONAS DISTRIBUIDORA DE ENERGIA",
            "AMAZONAS ENERGIA",
        ]

        for nome in nomes:
            url = self.handle_url(nome)
            self.separar_intimacoes(url)

    def format_advs(self, item: JSONPublicacoes) -> JSONDestinatariosAdvogados | None:
        for advogado in item["destinatarioadvogados"]:
            data_adv = JSONDestinatariosAdvogados(**advogado)
            data_adv.pop("advogado")

            for key, value in list(advogado["advogado"].items()):
                data_adv[f"advogado_{key}"] = value

            return convert_tostring(data_adv)

    def format_partes(self, item: JSONPublicacoes) -> JsonPartes | None:
        for parte in item["destinatarios"]:
            return convert_tostring(JsonPartes(**parte))

    def separar_intimacoes(self, url: str) -> None:
        for item in data_cnj(url):
            parts: list[JsonPartes] = []
            data = JSONPublicacoes(**item)
            data.pop("destinatarioadvogados", [])
            data.pop("destinatarios", [])

            nproc = item["numero_processo"]

            # Remove illegal characters for Excel
            texto_limpo = limpar_ilegais_regex(
                item["texto"].replace("<p>", "").replace("</p>", "\n")
            )
            data["texto"] = texto_limpo
            data["numero_processo"] = (
                f"{nproc[:7]}-{nproc[7:9]}.{nproc[9:13]}.{nproc[13:14]}.{nproc[14:16]}.{nproc[16:20]}"
            )

            advs: list[JSONDestinatariosAdvogados] = list(self.format_advs(item))
            parts: list[JsonPartes] = list(self.format_partes(item))
            data = convert_tostring(data)

            if data["data_disponibilizacao"]:
                try:
                    data["data_disponibilizacao"] = datetime.strptime(
                        str(data["data_disponibilizacao"]), "%Y-%m-%d"
                    )

                except ValueError:
                    data["data_disponibilizacao"] = datetime.strptime(
                        str(data["data_disponibilizacao"]),
                        "%d-%m-%Y",
                    )

            if data["data_cancelamento"]:
                try:
                    data["data_cancelamento"] = datetime.strptime(
                        str(data["data_cancelamento"]),
                        "%Y-%m-%d",
                    )
                except ValueError:
                    data["data_cancelamento"] = datetime.strptime(
                        str(data["data_cancelamento"]),
                        "%d-%m-%Y",
                    )

            self.publicacoes.append(data)
            self.advogados.extend(advs)
            self.partes.extend(parts)
