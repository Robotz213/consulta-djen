from typing import TypedDict

from consulta_djen.interfaces.partes import JSONDestinatariosAdvogados, JsonPartes


class JSONPublicacoes(TypedDict):
    id: int
    data_disponibilizacao: str
    siglaTribunal: str
    tipoComunicacao: str
    nomeOrgao: str
    texto: str
    numero_processo: str
    meio: str
    link: str | None
    tipoDocumento: str
    nomeClasse: str
    codigoClasse: str
    numeroComunicacao: int
    ativo: bool
    hash: str
    status: str
    motivo_cancelamento: str | None
    data_cancelamento: str | None
    datadisponibilizacao: str
    meiocompleto: str
    numeroprocessocommascara: str
    destinatarios: list[JsonPartes]
    destinatarioadvogados: list[JSONDestinatariosAdvogados]
