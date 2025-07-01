from datetime import datetime
from typing import List, TypedDict

from consulta_djen.interfaces.partes import JSONDestinatariosAdvogados, JsonPartes


class JSONPublicacoes(TypedDict):
    id: int
    numero_processo: str
    tipoComunicacao: str
    tipoDocumento: str
    nomeOrgao: str
    data_disponibilizacao: str | datetime
    texto: str
    nomeClasse: str
    siglaTribunal: str
    meio: str
    link: str | None
    codigoClasse: str
    numeroComunicacao: int
    ativo: bool
    hash: str
    status: str
    motivo_cancelamento: str | None
    data_cancelamento: str | datetime
    meiocompleto: str
    numeroprocessocommascara: str
    destinatarios: List[JsonPartes]
    destinatarioadvogados: List[JSONDestinatariosAdvogados]
