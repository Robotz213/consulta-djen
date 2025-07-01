import json
from time import sleep
from typing import Generator

import requests
from tqdm import tqdm

from consulta_djen.interfaces import JsonCNJ
from consulta_djen.interfaces.publicacao import JSONPublicacoes

headers = {
    "Content-Type": "application/json",
}


def data_cnj(url: str) -> Generator[JSONPublicacoes, None, None]:
    pagina = 1

    response_data = []

    while True:
        url = url + f"&pagina={pagina}"
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            sleep(0.25)
            json_data = JsonCNJ(**json.loads(response.text))

            if len(json_data["items"]) == 0:
                break

            response_data.extend(json_data["items"])
            pagina += 1
            continue

        break

    for item in tqdm(
        response_data,
        desc="Extraindo Publicações",
        unit=" Publicação",
        position=0,
        leave=False,
    ):
        sleep(0.02)
        yield item
