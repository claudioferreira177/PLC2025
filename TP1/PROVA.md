# TP1 — Especificação e prova da expressão regular

## Enunciado
Linguagem de todas as strings binárias em {0,1}* que **não** contêm a substring `011`.

## Intuição e Construção

1. **Strings apenas com `1`’s (ou vazia)**  
   - Sempre válidas → `1*`

2. **Strings que contenham pelo menos um `0`**  
   - Depois do **primeiro `0`**, temos de impedir que surja `011`.  
   - As opções seguras são:  
     - Outro `0` → `00`  
     - O bloco `10` → `010` (continua seguro)  
   - Opcionalmente, pode terminar com um `1` → `...01` no fim.  
   - Portanto, após o **primeiro `0`**: `(0(0|10)*(1)?)`

3. **Antes do primeiro `0`**  
   - Podemos ter qualquer número de `1`’s → `1*`

🔹 **Regex final**:  
```regex
^1*(?:0(?:0|10)*(?:1)?)?$
```

## Prova de Correção

- **Somente strings válidas são aceites:**  
  A construção permite `00`, `010`, ou termina com `01`, nunca gerando `011`.  

- **Todas as strings inválidas são rejeitadas:**  
  Se ocorrer `011`, a expressão não consegue consumir o segundo `1` depois de `0`.  


## Exemplos

✅ **Aceites:**  
- ε (string vazia)  
- 1, 1111111  
- 000001  
- 1111010101000  
- 0, 00, 010, 1010, 1001, 01010 

❌ **Rejeitados:**  
- 011  
- 111010110111  
- 000000011000000000  
- 1011011  
- 11011  
- 001101


