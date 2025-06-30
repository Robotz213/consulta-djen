from datetime import datetime
from typing import List, TypedDict

from consulta_djen.interfaces.partes import JSONDestinatariosAdvogados, JsonPartes


class JSONPublicacoes(TypedDict):
    id: int
    data_disponibilizacao: str | datetime
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
    data_cancelamento: str | datetime
    datadisponibilizacao: str | datetime
    meiocompleto: str
    numeroprocessocommascara: str
    destinatarios: List[JsonPartes]
    destinatarioadvogados: List[JSONDestinatariosAdvogados]
