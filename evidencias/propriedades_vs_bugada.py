"""Roda as mesmas propriedades contra a versao bugada, como testes normais."""
from hypothesis import given, settings, strategies as st
from normalizacao_bugada import normalizar_lote_bugado as normalizar_lote

lote_valido = st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1)


def test_exemplo_escrito_a_mao():
    assert normalizar_lote([0.0, 5.0, 10.0]) == [0.0, 0.5, 1.0]


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_faixa_unitaria(lote):
    saida = normalizar_lote(lote)
    assert len(saida) == len(lote)
    for y in saida:
        assert 0.0 <= y <= 1.0


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_ancoras_nos_extremos(lote):
    if min(lote) == max(lote):
        return
    saida = normalizar_lote(lote)
    assert min(saida) == 0.0
    assert max(saida) == 1.0


@settings(max_examples=500)
@given(lote_valido)
def test_propriedade_idempotencia(lote):
    uma_vez = normalizar_lote(lote)
    assert normalizar_lote(uma_vez) == uma_vez
