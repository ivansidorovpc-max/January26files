from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, TYPE_CHECKING

from ..utils import OrderStateError
from .product import AddOn, PricedItem, Product


class OrderStatus(Enum):
    CREATED = "создан"
    PREPARING = "готовится"
    READY = "готов"
    PAID = "оплачен"


@dataclass(frozen=True)
class OrderItem(PricedItem):
    product: Product
    add_ons: List[AddOn] = field(default_factory=list)

    def get_name(self) -> str:
        if not self.add_ons:
            return self.product.get_name()
        extras = ", ".join(add_on.get_name() for add_on in self.add_ons)
        return f"{self.product.get_name()} (+ {extras})"

    def get_category(self) -> str:
        return self.product.get_category()

    def get_price(self) -> float:
        return self.product.get_price() + sum(add_on.get_price() for add_on in self.add_ons)


class Order:
    def __init__(self, order_id: int) -> None:
        self.order_id = order_id
        self._items: List[OrderItem] = []
        self._status = OrderStatus.CREATED
        self._observers: List["OrderObserver"] = []
        self.total = 0.0
        self.discount_percent = 0.0
        self.discount_label = "обычный"

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def items(self) -> List[OrderItem]:
        return list(self._items)

    def add_item(self, item: OrderItem) -> None:
        self._items.append(item)

    def remove_item(self, index: int) -> None:
        if index < 0 or index >= len(self._items):
            raise IndexError("Индекс позиции заказа вне диапазона.")
        self._items.pop(index)

    def set_status(self, new_status: OrderStatus) -> None:
        if not isinstance(new_status, OrderStatus):
            raise OrderStateError("Неверный тип статуса заказа.")
        if new_status == self._status:
            raise OrderStateError("Заказ уже находится в этом статусе.")
        self._status = new_status
        self.notify("статус_изменен")

    def set_discount(self, percent: float, label: str) -> None:
        if percent < 0 or percent > 100:
            raise OrderStateError("Процент скидки вне диапазона 0-100.")
        self.discount_percent = percent
        self.discount_label = label

    def add_observer(self, observer: "OrderObserver") -> None:
        self._observers.append(observer)

    def notify(self, event: str) -> None:
        for observer in list(self._observers):
            observer.update(self, event)


if TYPE_CHECKING:
    from ..patterns.observer.observers import OrderObserver
