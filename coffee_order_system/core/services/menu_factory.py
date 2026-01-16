from __future__ import annotations

from typing import Dict, List

from ..models.product import AddOn, Beverage, Dessert, Product
from ..utils import ProductNotFoundError


class MenuFactory:

    def __init__(self) -> None:
        self._beverages: Dict[str, Beverage] = {
            "Эспрессо": Beverage("Эспрессо", "напиток", 2.5),
            "Капучино": Beverage("Капучино", "напиток", 3.5),
            "Латте": Beverage("Латте", "напиток", 4.0),
        }
        self._desserts: Dict[str, Dessert] = {
            "Чизкейк": Dessert("Чизкейк", "десерт", 4.5),
            "Круассан": Dessert("Круассан", "десерт", 3.0),
        }
        self._add_ons: Dict[str, AddOn] = {
            "Ванильный сироп": AddOn("Ванильный сироп", "добавка", 0.5),
            "Карамельный сироп": AddOn("Карамельный сироп", "добавка", 0.5),
            "Кокосовое молоко": AddOn("Кокосовое молоко", "добавка", 0.7),
            "Миндальное молоко": AddOn("Миндальное молоко", "добавка", 0.7),
            "Шот эспрессо": AddOn("Шот эспрессо", "добавка", 1.0),
            "Взбитые сливки": AddOn("Взбитые сливки", "добавка", 0.6),
        }

    def list_beverages(self) -> List[Beverage]:
        return list(self._beverages.values())

    def list_desserts(self) -> List[Dessert]:
        return list(self._desserts.values())

    def list_add_ons(self) -> List[AddOn]:
        return list(self._add_ons.values())

    def get_beverage(self, name: str) -> Beverage:
        try:
            return self._beverages[name]
        except KeyError as exc:
            raise ProductNotFoundError(f"Напиток '{name}' не найден.") from exc

    def get_dessert(self, name: str) -> Dessert:
        try:
            return self._desserts[name]
        except KeyError as exc:
            raise ProductNotFoundError(f"Десерт '{name}' не найден.") from exc

    def get_add_on(self, name: str) -> AddOn:
        try:
            return self._add_ons[name]
        except KeyError as exc:
            raise ProductNotFoundError(f"Добавка '{name}' не найдена.") from exc

    def get_product(self, name: str) -> Product:
        if name in self._beverages:
            return self._beverages[name]
        if name in self._desserts:
            return self._desserts[name]
        if name in self._add_ons:
            return self._add_ons[name]
        raise ProductNotFoundError(f"Продукт '{name}' не найден.")
