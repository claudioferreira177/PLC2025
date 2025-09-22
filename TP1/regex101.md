# Testes no regex101

**Regex:**  
^1*(?:0(?:0|10)*(?:1)?)?$


**Flavor:** PCRE (ou ECMAScript)  
**Flags:** `m` (multiline — uma string por linha)

## Como usar
1. Abre https://regex101.com
2. Cola a regex acima.
3. Marca a flag `m` (multiline).
4. Em “Test String”, cola o conteúdo de `tests.txt`.
   - Garante que a **linha vazia** está mesmo vazia (representa `ε`).
5. Confirma que todas as linhas da secção “SHOULD MATCH” dão match, e as “SHOULD NOT MATCH” não dão.

> Opcional: usa o painel **Unit Tests** do regex101 e cria testes com “should match / should not match” para obter “All tests passed”.
