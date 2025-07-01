from typing import TypeVar, Union

from consulta_djen.interfaces.partes import (
    JSONAdvogado,
    JSONDestinatariosAdvogados,
    JsonPartes,
)
from consulta_djen.interfaces.publicacao import JSONPublicacoes

Dicts = TypeVar(
    "Dicts",
    bound=Union[JSONAdvogado, JsonPartes, JSONPublicacoes, JSONDestinatariosAdvogados],
)
