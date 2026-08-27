Implemente uma função Python de sua escolha relacionada a pipelines de ML (validação de score, normalização de lote, deduplicação de dados, seleção de classe, detecção de outliers, ou outra função equivalente).

A entrega deve demonstrar, de forma visível, os seguintes 4 elementos:

Ciclo TDD completo (Red → Green → Refactor), evidenciado por uma das opções:
Histórico de commits no Git, com 1 commit por fase (red / green /refactor)
Relato escrito passo a passo, mostrando o teste falhando, o código mínimo que faz passar, e o refactor final.
Pelo menos 1 teste de propriedade (invariante), de preferência usando a biblioteca hypothesis, testando um comportamento que vale para qualquer entrada válida (não apenas um exemplo pontual).
Prova de que a propriedade pega um bug real: crie uma versão propositalmente "bugada" da sua função e mostre que o teste de propriedade falha contra ela (ou seja, o teste realmente teria pego o bug em produção).
Documentação breve das decisões de design tomadas (ex.: como tratar NaN, inf, divisão por zero, empates, etc. Conform aplicável à função escolhida).