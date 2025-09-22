# TP1 — Strings binárias **sem** a substring `011`

## Autor

<img src="../img/perfil.jpg" alt="Foto de perfil" width="120" align="left"/>

- **Nome:** Cláudio Ferreira  
- **ID:** A108577  

<br clear="left"/>

---

## Resumo
- O objetivo deste trabalho é definir uma **expressão regular** que aceite todas as strings binárias `{0,1}*` que **não contenham a substring `011`**.  
- Regex proposta: 

```regex
^1*(?:0(?:0|10)*(?:1)?)?$
```
- A verificação foi feita com: Testes positivos e negativos preparados em tests.txt | Simulações no regex101

---

## Resultados
- **Regex:** [`regex.txt`](./regex.txt)
- **Como testar no regex101:** [`regex101.md`](./regex101.md)
- **Casos de teste:** [`tests.txt`](./tests.txt)
- **Prova/Explicação:** [`PROVA.md`](./PROVA.md)
  

