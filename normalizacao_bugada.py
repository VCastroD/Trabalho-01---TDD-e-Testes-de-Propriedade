"""Versao propositalmente BUGADA de normalizar_lote (nao usar em producao).

Existe apenas para provar que os testes de propriedade pegam um bug real.
O bug e de uma linha e e um erro classico de min-max: dividir pelo *maximo*
em vez de dividir pela *amplitude* (maximo - minimo). Repare que ele fica
invisivel sempre que o minimo do lote for zero -- que e exatamente o formato
dos exemplos que a gente escreve a mao.
"""

from __future__ import annotations

from typing import Iterable, List

from normalizacao import VALOR_LOTE_CONSTANTE, _grampear, _validar

__all__ = ["normalizar_lote_bugado"]


def normalizar_lote_bugado(valores: Iterable[float]) -> List[float]:
    numeros = _validar(valores)
    if not numeros:
        return []

    menor = min(numeros)
    maior = max(numeros)
    if menor == maior:
        return [VALOR_LOTE_CONSTANTE] * len(numeros)

    # BUG INTENCIONAL: o denominador correto e (maior - menor).
    return [_grampear((v - menor) / maior) for v in numeros]
