"""Normalizacao min-max de lotes de scores para pipelines de ML.

A funcao publica e :func:`normalizar_lote`, que mapeia um lote de valores
numericos para a faixa [0, 1] preservando a ordem relativa entre eles.
As decisoes de projeto (NaN, inf, lote constante, lote vazio, overflow)
estao documentadas em RELATORIO.md e reproduzidas nas docstrings.
"""

from __future__ import annotations

import math
from typing import Iterable, List

__all__ = ["normalizar_lote", "VALOR_LOTE_CONSTANTE"]

#: Valor atribuido a todos os elementos quando o lote nao tem variacao.
#: Segue a convencao do ``sklearn.preprocessing.MinMaxScaler``, que colapsa
#: colunas constantes no limite inferior da faixa de destino.
VALOR_LOTE_CONSTANTE = 0.0


def normalizar_lote(valores: Iterable[float]) -> List[float]:
    """Normaliza ``valores`` para a faixa [0, 1] pelo metodo min-max.

    Invariantes garantidos para qualquer entrada valida:

    1. ``len(saida) == len(entrada)``;
    2. todo elemento da saida pertence a [0.0, 1.0];
    3. a ordem e preservada: ``v[i] <= v[j]`` implica ``y[i] <= y[j]``;
    4. em lote nao constante, o minimo vira exatamente 0.0 e o maximo 1.0;
    5. a operacao e idempotente: ``f(f(x)) == f(x)``.

    :raises TypeError: se algum elemento nao for ``int``/``float`` (``bool``
        e recusado de proposito: uma flag nao e um score).
    :raises ValueError: se algum elemento for ``NaN`` ou infinito.
    """
    numeros = _validar(valores)
    if not numeros:
        return []

    menor = min(numeros)
    maior = max(numeros)
    if menor == maior:
        return [VALOR_LOTE_CONSTANTE] * len(numeros)

    return [_grampear(y) for y in _escalar(numeros, menor, maior)]


def _validar(valores: Iterable[float]) -> List[float]:
    """Materializa o lote e rejeita entradas que nao sao scores finitos."""
    numeros = list(valores)
    for posicao, valor in enumerate(numeros):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(
                f"valor nao numerico na posicao {posicao}: {valor!r}"
            )
        if math.isnan(valor):
            raise ValueError(f"NaN na posicao {posicao}: lote invalido")
        if math.isinf(valor):
            raise ValueError(f"infinito na posicao {posicao}: lote invalido")
    return numeros


def _escalar(numeros: List[float], menor: float, maior: float):
    """Aplica ``(v - menor) / (maior - menor)`` sem estourar para infinito.

    Com valores proximos a ``+/-1.8e308`` a subtracao ``maior - menor`` estoura
    e a divisao produz ``inf/inf == nan``. Nesse caso reescalamos tudo por 0.5
    antes de subtrair -- multiplicar por 0.5 e exato em base 2, entao nao ha
    perda de precisao para os valores que importam nessa magnitude.
    """
    faixa = maior - menor
    if math.isinf(faixa):
        menor, maior = menor * 0.5, maior * 0.5
        faixa = maior - menor
        return ((v * 0.5 - menor) / faixa for v in numeros)
    return ((v - menor) / faixa for v in numeros)


def _grampear(y: float) -> float:
    """Corrige sobras de arredondamento do ponto flutuante (ex.: 1.0000000000000002)."""
    if y < 0.0:
        return 0.0
    if y > 1.0:
        return 1.0
    return y
