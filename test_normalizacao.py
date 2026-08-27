"""Suite de testes de normalizar_lote: exemplos, bordas e propriedades."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from normalizacao import VALOR_LOTE_CONSTANTE, normalizar_lote

# ---------------------------------------------------------------- estrategias

# Um "lote valido" e uma lista nao vazia de floats finitos: exatamente o
# contrato de entrada declarado por normalizar_lote.
finito = st.floats(allow_nan=False, allow_infinity=False)
lote_valido = st.lists(finito, min_size=1)


# ------------------------------------------------------- testes por exemplo


def test_normaliza_lote_para_faixa_unitaria():
    """Teste que abriu o ciclo TDD (fase red)."""
    assert normalizar_lote([2.0, 4.0, 6.0]) == [0.0, 0.5, 1.0]


def test_aceita_inteiros_e_devolve_floats():
    assert normalizar_lote([1, 3, 5]) == [0.0, 0.5, 1.0]


def test_lote_vazio_e_no_op():
    assert normalizar_lote([]) == []


def test_lote_constante_colapsa_no_valor_documentado():
    assert normalizar_lote([7.0, 7.0, 7.0]) == [VALOR_LOTE_CONSTANTE] * 3


def test_lote_de_um_elemento_e_constante():
    assert normalizar_lote([42.0]) == [VALOR_LOTE_CONSTANTE]


def test_nao_estoura_com_magnitudes_extremas():
    saida = normalizar_lote([-1.5e308, 0.0, 1.5e308])
    assert saida == [0.0, 0.5, 1.0]
    assert not any(math.isnan(y) for y in saida)


@pytest.mark.parametrize("ruim", [float("nan"), float("inf"), float("-inf")])
def test_rejeita_nan_e_infinito(ruim):
    with pytest.raises(ValueError):
        normalizar_lote([1.0, ruim, 3.0])


@pytest.mark.parametrize("ruim", ["0.5", None, True])
def test_rejeita_nao_numericos(ruim):
    with pytest.raises(TypeError):
        normalizar_lote([1.0, ruim, 3.0])


# ---------------------------------------------------- testes de propriedade


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_faixa_unitaria(lote):
    """P1: a saida tem o mesmo tamanho e vive inteiramente em [0, 1]."""
    saida = normalizar_lote(lote)
    assert len(saida) == len(lote)
    for y in saida:
        assert 0.0 <= y <= 1.0


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_preserva_ordem(lote):
    """P2: normalizar nao reordena nada -- v[i] <= v[j] => y[i] <= y[j].

    E o invariante que protege o alinhamento score <-> linha no pipeline.
    """
    saida = normalizar_lote(lote)
    pares = sorted(zip(lote, saida))
    for (_, y_anterior), (_, y_atual) in zip(pares, pares[1:]):
        assert y_anterior <= y_atual


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_ancoras_nos_extremos(lote):
    """P3: em lote nao constante, o minimo vira 0.0 e o maximo vira 1.0."""
    if min(lote) == max(lote):
        return
    saida = normalizar_lote(lote)
    assert min(saida) == 0.0
    assert max(saida) == 1.0


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_idempotencia(lote):
    """P4: normalizar o que ja esta normalizado nao muda nada."""
    uma_vez = normalizar_lote(lote)
    assert normalizar_lote(uma_vez) == uma_vez
