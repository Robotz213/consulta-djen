import json

import requests

from consulta_djen.interfaces import JsonCNJ


def convertToQueryString(query):
    return "&".join(f"{key}={value}" for key, value in query.items())


query = {
    "siglaTribunal": "TJAM",
    "dataDisponibilizacaoInicio": "2025-06-30",
    "dataDisponibilizacaoFim": "2025-06-30",
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


response = requests.get(url, headers=headers)
if response.status_code == 200:
    json_data = json.loads(response.text)

    for k, v in list(JsonCNJ(**json_data).items()):
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    print(f"{k}:")
                    for sub_k, sub_v in item.items():
                        if isinstance(sub_v, str) and len(sub_v) > 50:
                            print(f"  {sub_k}: {sub_v[:50]}...")
                        else:
                            print(f"  {sub_k}: {sub_v}")
                else:
                    print(f"{k}: {item}")
        print(f"{k}: {v}...")
