from __future__ import annotations

from typing import Dict, List, Sequence

from ..models.order import Order, OrderItem, OrderStatus
from ..models.product import AddOn, Beverage, Dessert
from ..patterns.observer.observers import CustomerNotifier, KitchenDisplay, Logger, OrderObserver
from ..utils import InvalidAddOnError, OrderNotFoundError
from .menu_factory import MenuFactory


class OrderService:
    def __init__(
        self,
        menu_factory: MenuFactory | None = None,
        observers: Sequence[OrderObserver] | None = None,
    ) -> None:
        self._menu_factory = menu_factory or MenuFactory()
        self._orders: Dict[int, Order] = {}
        self._next_id = 1
        if observers is None:
            observers = [KitchenDisplay(), CustomerNotifier(), Logger()]
        self._observers = list(observers)

    def set_observers(self, observers: Sequence[OrderObserver]) -> None:
        self._observers = list(observers)

    def list_beverages(self) -> List[Beverage]:
        return self._menu_factory.list_beverages()

    def list_desserts(self) -> List[Dessert]:
        return self._menu_factory.list_desserts()

    def list_add_ons(self) -> List[AddOn]:
        return self._menu_factory.list_add_ons()

    def list_active_orders(self) -> List[Order]:
        return [order for order in self._orders.values() if order.status != OrderStatus.PAID]

    def create_order(self) -> Order:
        order = Order(self._next_id)
        self._next_id += 1
        for observer in self._observers:
            order.add_observer(observer)
        self._orders[order.order_id] = order
        order.notify("создан")
        return order

    def get_order(self, order_id: int) -> Order:
        try:
            return self._orders[order_id]
        except KeyError as exc:
            raise OrderNotFoundError(f"Заказ '{order_id}' не найден.") from exc

    def add_menu_item(
        self,
        order_id: int,
        product_name: str,
        add_on_names: Sequence[str] | None = None,
    ) -> OrderItem:
        add_on_names = add_on_names or []
        product = self._menu_factory.get_product(product_name)
        if isinstance(product, AddOn):
            raise InvalidAddOnError("Нельзя добавлять добавку как отдельный продукт.")
        add_ons = [self._menu_factory.get_add_on(name) for name in add_on_names]
        if isinstance(product, Dessert) and add_ons:
            raise InvalidAddOnError("Добавки можно применять только к напиткам.")
        item = OrderItem(product=product, add_ons=add_ons)
        order = self.get_order(order_id)
        order.add_item(item)
        return item

    def remove_item(self, order_id: int, index: int) -> None:
        order = self.get_order(order_id)
        order.remove_item(index)

    def set_discount(self, order_id: int, percent: float, label: str) -> None:
        order = self.get_order(order_id)
        order.set_discount(percent, label)

    def calculate_total(self, order_id: int) -> float:
        order = self.get_order(order_id)
        subtotal = sum(item.get_price() for item in order.items)
        total = subtotal * (1 - order.discount_percent / 100)
        order.total = total
        return total

    def change_order_status(self, order_id: int, new_status: OrderStatus) -> None:
        order = self.get_order(order_id)
        order.set_status(new_status)

    def list_order_items(self, order_id: int) -> List[str]:
        order = self.get_order(order_id)
        return [item.get_name() for item in order.items]

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        order = self.get_order(order_id)
        return list(order.items)
