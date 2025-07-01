import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Self

import pandas as pd
import pytz
import requests
from clear import clear
from dotenv import dotenv_values
from tqdm import tqdm

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

environ = dotenv_values()
out_dir = Path(__file__).cwd().joinpath("out")

out_dir.mkdir(exist_ok=True)
clear()


def log_task_exception(task) -> None:
    try:
        task.result()
    except Exception as e:
        print(f"Erro em download_certidao: {e}")


# Semáforo global para limitar downloads simultâneos
download_semaphore = asyncio.Semaphore(3)


class PublicacoesDJEN:
    publicacoes = []
    advogados = []
    partes = []
    pos = 2

    @classmethod
    def initialize(cls) -> Self:
        return cls()

    async def queue(self) -> None:
        async for nome, oab in self.tuple_data():
            url = await self.handle_url(nome, oab)
            await self.separar_intimacoes(url)

        df_publicacoes = pd.DataFrame(self.publicacoes)
        df_advogados = pd.DataFrame(self.advogados)
        df_partes = pd.DataFrame(self.partes)

        # Salve em Excel ou outro formato conforme necessário
        with pd.ExcelWriter(f"Intimaçoes {today}.xlsx") as writer:
            df_publicacoes.to_excel(writer, sheet_name="Publicações", index=False)
            df_advogados.to_excel(writer, sheet_name="Advogados", index=False)
            df_partes.to_excel(writer, sheet_name="Partes", index=False)

    async def adjust_data(self, data: JSONPublicacoes) -> JSONPublicacoes:
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

        return data

    async def separar_intimacoes(self, url: str) -> None:
        for item in data_cnj(url):
            parts: list[JsonPartes] = []
            # Mantém a ordem dos campos conforme a definição da classe JSONPublicacoes
            data = JSONPublicacoes(
                **{field: item.get(field) for field in JSONPublicacoes.__annotations__}
            )
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

            advs: list[JSONDestinatariosAdvogados] = list(await self.format_advs(item))
            parts: list[JsonPartes] = list(await self.format_partes(item))

            data = convert_tostring(data)
            data = await self.adjust_data(data)

            if environ.get("DOWNLOAD_CERTIDAO"):
                task = asyncio.create_task(
                    self.download_task(
                        data["hash"], data["numero_processo"], data["id"]
                    )
                )

                task.add_done_callback(log_task_exception)
                await asyncio.sleep(0.5)

            self.publicacoes.append(data)
            self.advogados.extend(advs)
            self.partes.extend(parts)

    async def tuple_data(
        self,
    ) -> AsyncGenerator[tuple[str, str] | tuple[str, None], Any]:
        oabs: list[str] = []
        nomes_partes = environ.get("NOMES_PARTES")
        list_names: list[str] = json.loads(nomes_partes)
        if environ.get("OAB"):
            oabs = json.loads(environ.get("OAB"))

        for i in range(0, len(list_names)):
            if len(oabs) > 0:
                for oab in oabs:
                    yield (list_names[i], oab)

                continue

            yield (list_names[i], None)

    async def handle_url(self, nome: str, oab: str | None = None) -> str:
        query = {
            "dataDisponibilizacaoInicio": today,
            "nomeParte": nome,
        }

        if oab:
            query["numeroOab"] = oab

        url = (
            "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
            + "?"
            + convertToQueryString(query)
        )

        return url

    async def format_advs(
        self, item: JSONPublicacoes
    ) -> list[JSONDestinatariosAdvogados]:
        advogados: list[JSONDestinatariosAdvogados] = []
        for advogado in item["destinatarioadvogados"]:
            data_adv = JSONDestinatariosAdvogados(**advogado)
            data_adv.pop("advogado")

            for key, value in list(advogado["advogado"].items()):
                data_adv[f"advogado_{key}"] = value

            advogados.append(convert_tostring(data_adv))

        return advogados

    async def format_partes(self, item: JSONPublicacoes) -> list[JsonPartes]:
        partes: list[JsonPartes] = []
        for parte in item["destinatarios"]:
            partes.append(convert_tostring(JsonPartes(**parte)))

        return partes

    async def download_task(self, hashstr: str, numproc: str, id_: str) -> None:
        async def download_certidao(hashstr: str, numproc: str, id_: str) -> None:
            async with download_semaphore:
                if self.pos >= 5:
                    self.pos = 2

                url = f"https://comunicaapi.pje.jus.br/api/v1/comunicacao/{hashstr}/certidao"
                response = requests.get(url, timeout=60)

                if response.status_code == 200:
                    total = int(
                        response.headers.get("content-length", len(response.content))
                    )
                    file_path = out_dir.joinpath(f"Certidão - {numproc} - {id_}.pdf")
                    filename = file_path.name

                    pbar = tqdm(
                        desc=filename,
                        total=total,
                        unit="iB",
                        unit_scale=True,
                        unit_divisor=1024,
                        position=self.pos,
                        leave=False,
                    )
                    self.pos += 1
                    with file_path.open("wb") as file:
                        for data in response.iter_content(chunk_size=1024):
                            await asyncio.sleep(0.1)
                            size = file.write(data)
                            pbar.update(size)

                    pbar.clear()
                    await asyncio.sleep(0.5)
                    pbar.close()

        asyncio.create_task(download_certidao(hashstr, numproc, id_))
