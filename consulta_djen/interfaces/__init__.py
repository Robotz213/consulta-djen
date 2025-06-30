from typing import TypedDict

from consulta_djen.interfaces.publicacao import JSONPublicacoes


class JsonCNJ(TypedDict):
    status: str
    message: str
    count: int
    items: list[JSONPublicacoes]
