import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Item:
    cod: str
    nome: str
    quant: int
    preco: float  # em euros

    @property
    def preco_cents(self) -> int:
        return int(round(self.preco * 100))

class Store:
    def __init__(self, path: Path):
        self.path = path
        self.items: List[Item] = []

    def load(self) -> None:
        """Carrega items de stock.json."""
        if not self.path.exists():
            self.items = []
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.items = [Item(**row) for row in data]

    def save(self) -> None:
        """Guarda items em stock.json."""
        data = [item.__dict__ for item in self.items]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def find(self, cod: str) -> Optional[Item]:
        """Procura item pelo código (case-insensitive)."""
        key = (cod or "").strip().upper()
        for it in self.items:
            if it.cod.upper() == key:
                return it
        return None

    def table_rows(self) -> List[tuple]:
        """Linhas para impressão em LISTAR."""
        return [(i.cod, i.nome, i.quant, f"{i.preco:.2f}") for i in self.items]

    # Extra opcional: administrador pode repor/adição rápida
    def add_or_update(self, cod: str, nome: str, quant: int, preco: float) -> None:
        it = self.find(cod)
        if it:
            it.nome = nome or it.nome
            it.quant += quant
            it.preco = preco if preco is not None else it.preco
        else:
            self.items.append(Item(cod=cod.upper(), nome=nome, quant=quant, preco=preco))

