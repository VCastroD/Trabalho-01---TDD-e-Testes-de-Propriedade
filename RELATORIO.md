# ATV1 — Normalização de lote com TDD e teste de propriedade

**Função escolhida:** `normalizar_lote(valores)` — normalização **min-max** de um
lote de scores para a faixa `[0, 1]`, etapa clássica de pré-processamento em
pipeline de ML.

| Arquivo | Papel |
|---|---|
| [`normalizacao.py`](normalizacao.py) | Implementação final |
| [`normalizacao_bugada.py`](normalizacao_bugada.py) | Versão propositalmente bugada (1 linha) |
| [`test_normalizacao.py`](test_normalizacao.py) | 12 casos por exemplo (8 funções, parametrizadas) + 4 testes de propriedade |
| [`test_prova_bug.py`](test_prova_bug.py) | Prova automatizada de que a propriedade pega o bug |
| [`evidencias/`](evidencias/) | Saídas brutas do pytest de cada fase |

```bash
pip install -r requirements.txt
python -m pytest -q          # 20 passed
```

---

## 1. Ciclo TDD completo (Red → Green → Refactor)

Relato passo a passo, com a saída real do `pytest` de cada fase
(arquivos brutos em [`evidencias/`](evidencias/)).

### RED — o teste que falha primeiro

Escrevi o teste antes da função. A implementação existia só como esqueleto
(`return []`), então o teste tinha que falhar pelo motivo certo: resultado errado.

```python
def test_normaliza_lote_para_faixa_unitaria():
    assert normalizar_lote([2.0, 4.0, 6.0]) == [0.0, 0.5, 1.0]
```

```
F                                                                        [100%]
>       assert normalizar_lote([2.0, 4.0, 6.0]) == [0.0, 0.5, 1.0]
E       assert [] == [0.0, 0.5, 1.0]
E         Right contains 3 more items, first extra item: 0.0
1 failed in 0.62s
```

### GREEN — o código mínimo que faz passar

Nada de tratar borda ainda: só a fórmula min-max, o suficiente para o teste virar verde.

```python
def normalizar_lote(valores):
    menor = min(valores)
    maior = max(valores)
    return [(v - menor) / (maior - menor) for v in valores]
```

```
.                                                                        [100%]
1 passed in 0.17s
```

### REFACTOR — endurecer sem mudar o contrato

O gatilho do refactor foi o próprio teste de propriedade, que rodei contra o
código mínimo antes de considerá-lo pronto. Ele achou **dois defeitos reais**
que nenhum exemplo escrito à mão tinha pego:

**(a) Lote constante → divisão por zero.** Contraexemplo minimizado: `[0.0]`.

```
E   ZeroDivisionError: float division by zero
E   Failing test case: test_saida_dentro_da_faixa_unitaria(
E       lote=[0.0],
E   )
```

**(b) Overflow de ponto flutuante → `nan`.** Com magnitudes perto de `1.8e308`,
`maior - menor` estoura para `inf` e a divisão vira `inf/inf`:

```
lote = [1.7976931348623157e+308, -9.9792015476736e+291]
>           assert 0.0 <= y <= 1.0
E           assert 0.0 <= nan
```

O refactor então: separou validação (`_validar`), escala (`_escalar`) e correção
de arredondamento (`_grampear`); tratou lote constante e lote vazio; e passou a
reescalar por `0.5` quando a amplitude estoura — multiplicar por `0.5` é exato em
base 2, então não há perda de precisão nessa magnitude. Contrato público inalterado.

```
................                                                         [100%]
16 passed in 1.68s
```

---

## 2. Testes de propriedade (invariantes)

Estratégia de entrada: `st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1)`
— exatamente o contrato de entrada declarado pela função. São **4 invariantes**,
válidas para *qualquer* lote válido, não para um exemplo:

| # | Invariante | Por que importa no pipeline |
|---|---|---|
| **P1** | `len(saída) == len(entrada)` e todo `y ∈ [0, 1]` | Feature fora da faixa quebra modelo que assume entrada normalizada |
| **P2** | `v[i] <= v[j]` implica `y[i] <= y[j]` (preserva ordem) | Protege o alinhamento score ↔ linha; ranking não pode inverter |
| **P3** | Em lote não constante, `min → 0.0` e `max → 1.0` exatos | É o que distingue min-max de "dividir por qualquer coisa" |
| **P4** | `f(f(x)) == f(x)` (idempotência) | Normalizar duas vezes por engano (retry, reprocessamento) não pode corromper o lote |

---

## 3. Prova de que a propriedade pega um bug real

A versão bugada ([`normalizacao_bugada.py`](normalizacao_bugada.py)) muda **uma linha** —
divide pelo **máximo** em vez da **amplitude**, o erro clássico de min-max:

```python
# normalizacao.py (correto), dentro de _escalar():
faixa = maior - menor
... (v - menor) / faixa ...

# normalizacao_bugada.py — só o denominador muda:
... (v - menor) / maior ...
```

O ponto central: **o teste por exemplo que um humano escreveria passa nessa versão bugada.**
Quando o mínimo do lote é zero, `maior` e `maior - menor` coincidem e o bug some:

```python
normalizar_lote_bugado([0.0, 5.0, 10.0]) == [0.0, 0.5, 1.0]   # passa
```

Rodando as **mesmas** propriedades contra ela (`evidencias/07_prova_bug.txt`):

```
.FFF                                                                     [100%]

P1 faixa unitária      -> ZeroDivisionError: float division by zero
                          Falsifying example: lote=[0.0, -1.0]

P3 âncoras extremas    -> AssertionError: assert 0.0 == 1.0
                          Falsifying example: lote=[1.0, 2.0]

P4 idempotência        -> assert [0.0, 1.0] == [0.0, 0.5]
                          Falsifying example: lote=[-1.0, -2.0]

3 failed, 1 passed in 1.50s
```

O `1 passed` é justamente o teste por exemplo: **exemplo pontual passa, propriedade
falha.** Os contraexemplos foram reduzidos pelo *shrinking* do hypothesis a pares
mínimos de 2 elementos, prontos para virar teste de regressão.

Um detalhe que vale registrar: **P2 (preserva ordem) continua passando** contra a
versão bugada — dividir por uma constante positiva errada não reordena nada. Isso é
esperado, e é o argumento para ter *várias* invariantes: cada uma cobre um eixo
diferente de falha, e uma sozinha não fecha o cerco.

Essa prova não é uma afirmação escrita no README: [`test_prova_bug.py`](test_prova_bug.py)
executa as propriedades contra a versão bugada e **exige que elas falhem**. Se algum
dia a propriedade deixar de pegar o bug, a suíte quebra.

---

## 4. Decisões de design

| Situação | Decisão | Justificativa |
|---|---|---|
| **`NaN` na entrada** | `ValueError` | `NaN` contamina `min`/`max` e se propaga silenciosamente pelo pipeline. Falhar alto no *ingest* é muito mais barato que caçar `NaN` depois do treino. Limpeza de `NaN` é responsabilidade de uma etapa anterior, não desta função. |
| **`±inf` na entrada** | `ValueError` | Amplitude infinita colapsa todo o resto do lote em `0.0`: a normalização perderia toda a informação sem avisar. |
| **Lote constante (`min == max`)** | Todos → `0.0` (`VALOR_LOTE_CONSTANTE`) | Divisão por zero exige uma escolha explícita. Adotei a convenção do `sklearn.preprocessing.MinMaxScaler`, que mapeia coluna constante para o limite inferior da faixa. Constante exportada e nomeada para o valor ser auditável, não um literal solto. |
| **Lote vazio** | Retorna `[]`, sem erro | Batch vazio é normal em streaming/janelamento. É um no-op legítimo — erro aqui só geraria `try/except` defensivo em todo chamador. |
| **Lote de 1 elemento** | Cai no caso constante → `[0.0]` | Consistência: um elemento sozinho não tem amplitude. |
| **`bool` na entrada** | `TypeError` | Em Python `bool` é subclasse de `int`, então `[True, False]` passaria calado. Uma *flag* não é um score; aceitar isso mascara erro de montagem de feature. |
| **Overflow (`maior - menor == inf`)** | Reescala por `0.5` antes de subtrair | Sem isso a saída vira `nan` (bug achado pela propriedade). `* 0.5` é exato em ponto flutuante binário, então o resultado não perde precisão. |
| **Arredondamento de ponto flutuante** | Grampeia (*clamp*) a saída em `[0, 1]` | A divisão pode devolver `1.0000000000000002`. Sem o grampo, P1 seria falsa por um erro de última casa e a garantia de faixa não valeria de verdade. |
| **Empates** | Preservados: valores iguais → saídas iguais | A função é determinística e ponto a ponto; não há desempate a fazer. Reforçado por P2. |
| **Tipo de saída** | Sempre `list[float]`, mesmo com entrada `int` | Saída previsível para o próximo estágio; evita divisão inteira acidental rio abaixo. |
| **Não normaliza *in place*** | Retorna lista nova | A entrada é compartilhada entre features/etapas; mutar seria efeito colateral invisível. |
