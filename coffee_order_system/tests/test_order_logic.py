from __future__ import annotations

import unittest
from core.models.order import OrderStatus
from core.services.order_service import OrderService
from core.utils import InvalidAddOnError


class OrderLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = OrderService()
        self.order = self.service.create_order()

    def test_total_with_add_ons(self) -> None:
        self.service.add_menu_item(self.order.order_id, "Капучино", ["Кокосовое молоко", "Ванильный сироп"])
        total = self.service.calculate_total(self.order.order_id)
        self.assertAlmostEqual(total, 4.7, places=2)

    def test_invalid_add_on_for_dessert(self) -> None:
        with self.assertRaises(InvalidAddOnError):
            self.service.add_menu_item(self.order.order_id, "Чизкейк", ["Ванильный сироп"])

    def test_status_change(self) -> None:
        self.service.change_order_status(self.order.order_id, OrderStatus.PREPARING)
        self.assertEqual(self.order.status, OrderStatus.PREPARING)


if __name__ == "__main__":
    unittest.main()
