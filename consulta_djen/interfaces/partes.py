from typing import TypedDict


class JSONAdvogado(TypedDict):
    id: int
    nome: str
    numero_oab: str
    uf_oab: str


class JsonPartes(TypedDict):
    polo: str
    nome: str
    comunicacao_id: int


class JSONDestinatariosAdvogados(TypedDict):
    id: int
    comunicacao_id: int
    advogado_id: int
    created_at: str
    updated_at: str
    advogado: JSONAdvogado
