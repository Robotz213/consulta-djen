import json
from typing import Generator

import requests

from consulta_djen.interfaces import JsonCNJ
from consulta_djen.interfaces.publicacao import JSONPublicacoes

headers = {
    "Content-Type": "application/json",
}


def data_cnj(url: str) -> Generator[JSONPublicacoes, None, None]:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        json_data = JsonCNJ(**json.loads(response.text))

        for item in json_data["items"]:
            yield item
