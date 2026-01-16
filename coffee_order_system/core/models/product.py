from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class PricedItem(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_category(self) -> str:
        pass

    @abstractmethod
    def get_price(self) -> float:
        pass


@dataclass(frozen=True)
class Product(PricedItem):
    name: str
    category: str
    base_price: float

    def get_name(self) -> str:
        return self.name

    def get_category(self) -> str:
        return self.category

    def get_price(self) -> float:
        return self.base_price


class Beverage(Product):
    pass


class Dessert(Product):
    pass


class AddOn(Product):
    pass
