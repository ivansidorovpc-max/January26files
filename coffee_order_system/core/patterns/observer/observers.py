from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from ...models.order import Order


def _default_sink(message: str) -> None:
    print(message)


class OrderObserver(ABC):
    @abstractmethod
    def update(self, order: Order, event: str) -> None:
        pass


class KitchenDisplay(OrderObserver):
    def __init__(self, sink: Callable[[str], None] | None = None) -> None:
        self._sink = sink or _default_sink

    def update(self, order: Order, event: str) -> None:
        message = self._format_message(order, event)
        self._sink(f"[КУХНЯ] {message}")

    def _format_message(self, order: Order, event: str) -> str:
        if event == "создан":
            return f"Новый заказ №{order.order_id} создан."
        if event == "статус_изменен":
            return f"Заказ №{order.order_id}: статус {order.status.value}."
        return f"Заказ №{order.order_id}: событие {event}."


class CustomerNotifier(OrderObserver):
    def __init__(self, sink: Callable[[str], None] | None = None) -> None:
        self._sink = sink or _default_sink

    def update(self, order: Order, event: str) -> None:
        message = self._format_message(order, event)
        self._sink(f"[КЛИЕНТ] {message}")

    def _format_message(self, order: Order, event: str) -> str:
        if event == "создан":
            return f"Ваш заказ №{order.order_id} создан."
        if event == "статус_изменен":
            return f"Ваш заказ №{order.order_id}: {order.status.value}."
        return f"Обновление заказа №{order.order_id}: {event}."


class Logger(OrderObserver):
    def __init__(self, sink: Callable[[str], None] | None = None) -> None:
        self._sink = sink or _default_sink

    def update(self, order: Order, event: str) -> None:
        message = self._format_message(order, event)
        self._sink(f"[ЛОГ] {message}")

    def _format_message(self, order: Order, event: str) -> str:
        if event == "создан":
            return f"Заказ №{order.order_id} создан."
        if event == "статус_изменен":
            return f"Статус заказа №{order.order_id} изменен на {order.status.value}."
        return f"Заказ №{order.order_id}: событие {event}."
