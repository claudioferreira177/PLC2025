# TP1 — Strings binárias **sem** a substring `011`

## 👤 Autor

<img src="../img/perfil.jpg" alt="Foto de perfil" width="120" align="left"/>

- **Nome:** Cláudio Ferreira  
- **ID:** A108577  

<br clear="left"/>

---

## 📌 Resumo
**Objetivo**: Definir uma **expressão regular** que aceite todas as strings binárias `{0,1}*` que **não contenham** a substring proibida `011`.   

**Regex proposta**: 
```regex
^1*(?:0(?:0|10)*(?:1)?)?$
```

**Verificação**:
- A verificação foi feita com:
  ✅ Testes positivos e negativos preparados em tests.txt
  🔗 Simulações no regex101

---

## 📂 Estrutura do Trabalho
- 📜 [`regex.txt`](./regex.txt) -> Contém apenas a expressão regular final.
- 🔍 [`regex101.md`](./regex101.md) -> Demonstração da regex no site regex101 (com print).
- 🧪 [`tests.txt`](./tests.txt) -> Strings válidas e inválidas para validar a regex.
- 📖 [`PROVA.md`](./PROVA.md) -> Explicação detalhada da construção e prova da correção.

## ✅ Conclusão
- A expressão regular foi validada em todos os testes e rejeita corretamente as strings com a substring proibida 011, aceitando todas as restantes.

