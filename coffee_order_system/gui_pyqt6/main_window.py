from __future__ import annotations

from typing import Callable, Optional, Sequence

from PyQt6 import QtCore, QtWidgets

from core.models.order import OrderItem, OrderStatus
from core.services.order_service import OrderService
from core.utils import CoffeeOrderError, InvalidAddOnError


class DetailsWindow(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали заказа")
        self.resize(700, 360)
        self.setStyleSheet(parent.styleSheet())
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Товар", "Добавки", "Статус"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def update_rows(self, items: Sequence[OrderItem], status: OrderStatus) -> None:
        self.table.setRowCount(0)
        status_text = status.value
        for item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            add_ons = ", ".join(add_on.get_name() for add_on in item.add_ons) or "-"
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(item.product.get_name()))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(add_ons))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(status_text))


class DiscountDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        apply_callback: Callable[[float, str], None],
        current_percent: float,
        current_label: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Скидка")
        self.resize(360, 240)
        self.setStyleSheet(parent.styleSheet())
        self.apply_callback = apply_callback
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Выберите тип скидки")
        layout.addWidget(title)

        self.group = QtWidgets.QButtonGroup(self)
        self.rb_regular = QtWidgets.QRadioButton("Обычный клиент (0%)")
        self.rb_loyal = QtWidgets.QRadioButton("Постоянный клиент (10%)")
        self.rb_vip = QtWidgets.QRadioButton("VIP клиент (20%)")
        self.rb_custom = QtWidgets.QRadioButton("Другая скидка")

        self.group.addButton(self.rb_regular)
        self.group.addButton(self.rb_loyal)
        self.group.addButton(self.rb_vip)
        self.group.addButton(self.rb_custom)

        layout.addWidget(self.rb_regular)
        layout.addWidget(self.rb_loyal)
        layout.addWidget(self.rb_vip)
        layout.addWidget(self.rb_custom)

        custom_layout = QtWidgets.QHBoxLayout()
        custom_layout.addWidget(QtWidgets.QLabel("Процент:"))
        self.custom_entry = QtWidgets.QLineEdit()
        custom_layout.addWidget(self.custom_entry)
        layout.addLayout(custom_layout)

        self.apply_button = QtWidgets.QPushButton("Применить")
        self.apply_button.clicked.connect(self._apply)
        layout.addWidget(self.apply_button)

        self.rb_custom.toggled.connect(self._toggle_custom)
        self._set_initial(current_percent, current_label)

    def _set_initial(self, percent: float, label: str) -> None:
        if percent == 10:
            self.rb_loyal.setChecked(True)
        elif percent == 20:
            self.rb_vip.setChecked(True)
        elif percent == 0:
            self.rb_regular.setChecked(True)
        else:
            self.rb_custom.setChecked(True)
            self.custom_entry.setText(f"{percent:.0f}")
        self._toggle_custom()

    def _toggle_custom(self) -> None:
        self.custom_entry.setEnabled(self.rb_custom.isChecked())

    def _apply(self) -> None:
        if self.rb_regular.isChecked():
            percent = 0.0
            label = "обычный"
        elif self.rb_loyal.isChecked():
            percent = 10.0
            label = "постоянный"
        elif self.rb_vip.isChecked():
            percent = 20.0
            label = "vip"
        else:
            raw = self.custom_entry.text().strip().replace(",", ".")
            try:
                percent = float(raw)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите корректный процент.")
                return
            if percent < 0 or percent > 100:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Процент должен быть от 0 до 100.")
                return
            label = "другая"
        self.apply_callback(percent, label)
        self.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, service: OrderService) -> None:
        super().__init__()
        self.setWindowTitle("Pattern Brew - Заказы")
        self.resize(980, 600)
        self.service = service
        self.current_order_id: Optional[int] = None
        self.details_window: Optional[DetailsWindow] = None
        self._menu_map: dict[str, str] = {}

        central = QtWidgets.QWidget()
        central.setObjectName("AppRoot")
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        header = QtWidgets.QFrame()
        header.setObjectName("HeaderCard")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        title_layout = QtWidgets.QVBoxLayout()
        self.title_label = QtWidgets.QLabel("Pattern Brew")
        self.title_label.setObjectName("Title")
        self.subtitle_label = QtWidgets.QLabel("Умная система управления заказами")
        self.subtitle_label.setObjectName("Subtitle")
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        self.order_info_label = QtWidgets.QLabel("Нет активного заказа")
        self.order_info_label.setObjectName("OrderInfo")
        self.order_info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.order_info_label)
        main_layout.addWidget(header, 0)

        top_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(top_layout, 4)

        menu_group = QtWidgets.QGroupBox("Меню")
        top_layout.addWidget(menu_group, 1)
        menu_group.setMinimumWidth(230)
        menu_layout = QtWidgets.QVBoxLayout(menu_group)
        menu_layout.addWidget(QtWidgets.QLabel("Продукты"))
        self.menu_list = QtWidgets.QListWidget()
        self.menu_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        menu_layout.addWidget(self.menu_list, 1)
        menu_layout.addWidget(QtWidgets.QLabel("Добавки (для напитков)"))
        self.add_on_list = QtWidgets.QListWidget()
        self.add_on_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        menu_layout.addWidget(self.add_on_list, 1)

        order_group = QtWidgets.QGroupBox("Текущий заказ")
        top_layout.addWidget(order_group, 2)
        order_group.setMinimumWidth(360)
        order_layout = QtWidgets.QVBoxLayout(order_group)
        self.order_list = QtWidgets.QListWidget()
        order_layout.addWidget(self.order_list)

        control_group = QtWidgets.QGroupBox("Управление")
        top_layout.addWidget(control_group, 1)
        control_group.setMinimumWidth(260)
        control_layout = QtWidgets.QVBoxLayout(control_group)
        control_layout.setSpacing(8)

        self.total_label = QtWidgets.QLabel("Итого: 0.00")
        font = self.total_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.total_label.setFont(font)
        control_layout.addWidget(self.total_label)

        control_layout.addWidget(QtWidgets.QLabel("Активные заказы"))
        self.active_orders = QtWidgets.QListWidget()
        self.active_orders.itemSelectionChanged.connect(self._select_order)
        control_layout.addWidget(self.active_orders)

        self.create_order_button = QtWidgets.QPushButton("Создать заказ")
        self.create_order_button.clicked.connect(self._create_order)
        control_layout.addWidget(self.create_order_button)

        self.add_item_button = QtWidgets.QPushButton("Добавить позицию")
        self.add_item_button.clicked.connect(self._add_item)
        control_layout.addWidget(self.add_item_button)

        self.remove_item_button = QtWidgets.QPushButton("Удалить выбранное")
        self.remove_item_button.clicked.connect(self._remove_item)
        control_layout.addWidget(self.remove_item_button)

        self.discount_button = QtWidgets.QPushButton("Скидка")
        self.discount_button.clicked.connect(self._open_discount)
        control_layout.addWidget(self.discount_button)

        self.details_button = QtWidgets.QPushButton("Детали заказа")
        self.details_button.clicked.connect(self._open_details)
        control_layout.addWidget(self.details_button)

        control_layout.addWidget(QtWidgets.QLabel("Статус заказа"))
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems([status.value for status in OrderStatus])
        control_layout.addWidget(self.status_combo)

        self.status_button = QtWidgets.QPushButton("Изменить статус")
        self.status_button.clicked.connect(self._change_status)
        control_layout.addWidget(self.status_button)

        log_group = QtWidgets.QGroupBox("Журнал событий")
        main_layout.addWidget(log_group, 1)
        log_layout = QtWidgets.QVBoxLayout(log_group)
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        self._apply_style()
        self._load_menu()
        self._refresh_active_orders()

    def _load_menu(self) -> None:
        self.menu_list.clear()
        self._menu_map.clear()
        for product in self.service.list_beverages() + self.service.list_desserts():
            display = f"{product.get_category().title()}: {product.get_name()}"
            self._menu_map[display] = product.get_name()
            self.menu_list.addItem(display)

        self.add_on_list.clear()
        for add_on in self.service.list_add_ons():
            self.add_on_list.addItem(add_on.get_name())

    def _create_order(self) -> None:
        order = self.service.create_order()
        self.current_order_id = order.order_id
        self.status_combo.setCurrentIndex(0)
        self.menu_list.clearSelection()
        self.add_on_list.clearSelection()
        self._refresh_active_orders(select_order_id=order.order_id)
        self._refresh_order()
        self._update_total()

    def _add_item(self) -> None:
        if not self._ensure_order():
            return
        item = self.menu_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Нет выбора", "Выберите продукт для добавления.")
            return
        display_name = item.text()
        product_name = self._menu_map.get(display_name)
        add_on_names = [x.text() for x in self.add_on_list.selectedItems()]
        try:
            self.service.add_menu_item(self.current_order_id, product_name, add_on_names)
        except InvalidAddOnError as exc:
            QtWidgets.QMessageBox.warning(self, "Ошибка добавок", str(exc))
            return
        except CoffeeOrderError as exc:
            QtWidgets.QMessageBox.warning(self, "Ошибка заказа", str(exc))
            return
        self._refresh_order()
        self._update_total()

    def _remove_item(self) -> None:
        if not self._ensure_order():
            return
        row = self.order_list.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Нет выбора", "Выберите позицию для удаления.")
            return
        try:
            self.service.remove_item(self.current_order_id, row)
        except CoffeeOrderError as exc:
            QtWidgets.QMessageBox.warning(self, "Ошибка заказа", str(exc))
            return
        self._refresh_order()
        self._update_total()

    def _open_details(self) -> None:
        if not self._ensure_order():
            return
        if not self.details_window:
            self.details_window = DetailsWindow(self)
            self.details_window.finished.connect(self._details_closed)
        self.details_window.show()
        self.details_window.raise_()
        self._refresh_details()

    def _details_closed(self) -> None:
        self.details_window = None

    def _open_discount(self) -> None:
        if not self._ensure_order():
            return
        order = self.service.get_order(self.current_order_id)
        dialog = DiscountDialog(self, self._apply_discount, order.discount_percent, order.discount_label)
        dialog.exec()

    def _apply_discount(self, percent: float, label: str) -> None:
        try:
            self.service.set_discount(self.current_order_id, percent, label)
        except CoffeeOrderError as exc:
            QtWidgets.QMessageBox.warning(self, "Ошибка заказа", str(exc))
            return
        self._refresh_order()
        self._update_total()
        self._refresh_details()

    def _change_status(self) -> None:
        if not self._ensure_order():
            return
        status_value = self.status_combo.currentText()
        new_status = OrderStatus(status_value)
        try:
            self.service.change_order_status(self.current_order_id, new_status)
        except CoffeeOrderError as exc:
            QtWidgets.QMessageBox.warning(self, "Ошибка заказа", str(exc))
            return
        self._refresh_active_orders()
        self._refresh_order()

    def _refresh_order(self) -> None:
        if not self._ensure_order(show_message=False):
            self.order_list.clear()
            self._refresh_details()
            return
        order = self.service.get_order(self.current_order_id)
        self.order_list.clear()
        for item_name in self.service.list_order_items(self.current_order_id):
            self.order_list.addItem(f"{item_name} | статус: {order.status.value}")
        self.order_info_label.setText(f"Заказ №{order.order_id} · статус {order.status.value}")
        self._refresh_details()

    def _refresh_details(self) -> None:
        if not self.details_window:
            return
        if not self._ensure_order(show_message=False):
            self.details_window.update_rows([], OrderStatus.CREATED)
            return
        order = self.service.get_order(self.current_order_id)
        items = self.service.get_order_items(self.current_order_id)
        self.details_window.update_rows(items, order.status)

    def _update_total(self) -> None:
        if not self._ensure_order(show_message=False):
            self.total_label.setText("Итого: 0.00")
            return
        order = self.service.get_order(self.current_order_id)
        total = self.service.calculate_total(self.current_order_id)
        if order.discount_percent > 0:
            self.total_label.setText(f"Итого: {total:.2f} (скидка {order.discount_percent:.0f}%)")
        else:
            self.total_label.setText(f"Итого: {total:.2f}")

    def _refresh_active_orders(self, select_order_id: Optional[int] = None) -> None:
        self.active_orders.clear()
        active = self.service.list_active_orders()
        current_index = None
        for index, order in enumerate(active):
            label = f"Заказ №{order.order_id} | {order.status.value}"
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, order.order_id)
            self.active_orders.addItem(item)
            if select_order_id == order.order_id:
                current_index = index
            if select_order_id is None and self.current_order_id == order.order_id:
                current_index = index

        if current_index is not None:
            self.active_orders.setCurrentRow(current_index)
            self.current_order_id = self.active_orders.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)
        elif self.active_orders.count() > 0:
            self.active_orders.setCurrentRow(0)
            self.current_order_id = self.active_orders.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)
        else:
            self.current_order_id = None
            self.order_info_label.setText("Нет активного заказа")
        self._refresh_order()
        self._update_total()

    def _select_order(self) -> None:
        item = self.active_orders.currentItem()
        if not item:
            return
        self.current_order_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        order = self.service.get_order(self.current_order_id)
        self.status_combo.setCurrentText(order.status.value)
        self.order_info_label.setText(f"Заказ №{order.order_id} · статус {order.status.value}")
        self._refresh_order()
        self._update_total()

    def _ensure_order(self, show_message: bool = True) -> bool:
        if self.current_order_id is None:
            if show_message:
                QtWidgets.QMessageBox.information(self, "Нет заказа", "Сначала создайте заказ.")
            return False
        return True

    def append_log(self, message: str) -> None:
        self.log_text.append(message)

    def _apply_style(self) -> None:
        app_font = self.font()
        app_font.setFamily("Georgia")
        self.setFont(app_font)
        self.setStyleSheet(
            """
            QWidget#AppRoot {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f1e7, stop:1 #efe2d0);
                color: #2b1f1a;
            }
            QFrame#HeaderCard {
                background: rgba(255, 250, 244, 0.9);
                border: 1px solid #d8c9b8;
                border-radius: 14px;
            }
            QLabel#Title {
                font-size: 22px;
                font-weight: 700;
                color: #3b2418;
            }
            QLabel#Subtitle {
                color: #6b4a3a;
            }
            QLabel#OrderInfo {
                color: #5b3a2e;
                font-weight: 600;
            }
            QGroupBox {
                background: rgba(255, 250, 244, 0.88);
                border: 1px solid #d8c9b8;
                border-radius: 12px;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #5b3a2e;
                font-weight: 600;
            }
            QListWidget, QTextEdit, QComboBox, QTableWidget, QLineEdit {
                background: #fffaf4;
                border: 1px solid #d8c9b8;
                border-radius: 8px;
                padding: 6px;
                selection-background-color: #d4a373;
                selection-color: #2b1f1a;
            }
            QTableWidget {
                gridline-color: #e2d2c1;
            }
            QPushButton {
                background: #6f4e37;
                color: #fffaf4;
                border: none;
                border-radius: 10px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #81563e;
            }
            QPushButton:pressed {
                background: #5a3e2d;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 2px 0 2px 0;
            }
            QScrollBar::handle:vertical {
                background: #d4a373;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )
