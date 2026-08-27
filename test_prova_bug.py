"""Prova de que os testes de propriedade pegariam o bug em producao.

A ideia: rodar as MESMAS propriedades contra ``normalizar_lote_bugado`` e
exigir que elas falhem. Se algum dia a propriedade parar de falhar contra a
versao bugada, este arquivo quebra -- ou seja, a prova e verificada pelo CI,
nao e so uma afirmacao no README.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from normalizacao_bugada import normalizar_lote_bugado

lote_valido = st.lists(
    st.floats(allow_nan=False, allow_infinity=False), min_size=1
)


def _falseia(propriedade) -> Exception:
    """Executa a propriedade e devolve o erro que a falseou."""
    try:
        propriedade()
    except Exception as erro:  # AssertionError, ZeroDivisionError, grupos...
        return erro
    raise AssertionError(
        f"{propriedade.__name__} passou contra a versao bugada: "
        "a prova do bug nao vale mais"
    )


# ------------------------------------------- propriedades sob a versao bugada
# Nome sem prefixo test_ de proposito: o pytest nao deve coleta-las
# diretamente (elas DEVEM falhar); quem as executa e _falseia().


@settings(max_examples=500)
@given(lote_valido)
def propriedade_faixa_unitaria(lote):
    for y in normalizar_lote_bugado(lote):
        assert 0.0 <= y <= 1.0


@settings(max_examples=500)
@given(lote_valido)
def propriedade_ancoras_nos_extremos(lote):
    if min(lote) == max(lote):
        return
    saida = normalizar_lote_bugado(lote)
    assert min(saida) == 0.0
    assert max(saida) == 1.0


@settings(max_examples=500)
@given(lote_valido)
def propriedade_idempotencia(lote):
    uma_vez = normalizar_lote_bugado(lote)
    assert normalizar_lote_bugado(uma_vez) == uma_vez


# --------------------------------------------------------------- a prova


def test_o_exemplo_escrito_a_mao_NAO_pega_o_bug():
    """O teste que um humano escreveria passa na versao bugada.

    Com minimo zero, ``maior`` e ``maior - menor`` coincidem e o bug some.
    E por isso que exemplo pontual nao basta.
    """
    assert normalizar_lote_bugado([0.0, 5.0, 10.0]) == [0.0, 0.5, 1.0]


def test_propriedade_faixa_unitaria_pega_o_bug():
    assert _falseia(propriedade_faixa_unitaria) is not None


def test_propriedade_ancoras_pega_o_bug():
    assert _falseia(propriedade_ancoras_nos_extremos) is not None


def test_propriedade_idempotencia_pega_o_bug():
    assert _falseia(propriedade_idempotencia) is not None
