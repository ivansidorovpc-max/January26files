from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, Optional, Sequence

from core.models.order import OrderItem, OrderStatus
from core.services.order_service import OrderService
from core.utils import CoffeeOrderError, InvalidAddOnError


class DetailsWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.title("Детали заказа")
        self.geometry("700x360")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=("product", "addons", "status"), show="headings")
        self.tree.heading("product", text="Товар")
        self.tree.heading("addons", text="Добавки")
        self.tree.heading("status", text="Статус")
        self.tree.column("product", width=220, anchor="w")
        self.tree.column("addons", width=320, anchor="w")
        self.tree.column("status", width=120, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def update_rows(self, items: Sequence[OrderItem], status: OrderStatus) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        status_text = status.value
        for item in items:
            add_ons = ", ".join(add_on.get_name() for add_on in item.add_ons) or "-"
            self.tree.insert("", tk.END, values=(item.product.get_name(), add_ons, status_text))


class DiscountWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Tk,
        apply_callback: Callable[[float, str], None],
        current_percent: float,
        current_label: str,
    ) -> None:
        super().__init__(master)
        self.title("Скидка")
        self.geometry("360x240")
        self.apply_callback = apply_callback
        self.var = tk.StringVar(value="обычный")
        self.custom_var = tk.StringVar()

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Выберите тип скидки").grid(row=0, column=0, sticky="w")
        self._add_radio(frame, "Обычный клиент (0%)", "обычный", 1)
        self._add_radio(frame, "Постоянный клиент (10%)", "постоянный", 2)
        self._add_radio(frame, "VIP клиент (20%)", "vip", 3)
        self._add_radio(frame, "Другая скидка", "custom", 4)

        custom_frame = ttk.Frame(frame)
        custom_frame.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        custom_frame.columnconfigure(1, weight=1)
        ttk.Label(custom_frame, text="Процент:").grid(row=0, column=0, sticky="w")
        self.custom_entry = ttk.Entry(custom_frame, textvariable=self.custom_var)
        self.custom_entry.grid(row=0, column=1, sticky="ew")

        self.apply_button = ttk.Button(frame, text="Применить", command=self._apply)
        self.apply_button.grid(row=6, column=0, sticky="ew", pady=(10, 0))

        self._set_initial(current_percent, current_label)

    def _add_radio(self, parent: ttk.Frame, text: str, value: str, row: int) -> None:
        rb = ttk.Radiobutton(parent, text=text, value=value, variable=self.var, command=self._toggle_custom)
        rb.grid(row=row, column=0, sticky="w")

    def _toggle_custom(self) -> None:
        if self.var.get() == "custom":
            self.custom_entry.configure(state="normal")
        else:
            self.custom_entry.configure(state="disabled")

    def _set_initial(self, percent: float, label: str) -> None:
        if percent == 10:
            self.var.set("постоянный")
        elif percent == 20:
            self.var.set("vip")
        elif percent == 0:
            self.var.set("обычный")
        else:
            self.var.set("custom")
            self.custom_var.set(f"{percent:.0f}")
        self._toggle_custom()

    def _apply(self) -> None:
        choice = self.var.get()
        if choice == "обычный":
            percent = 0.0
            label = "обычный"
        elif choice == "постоянный":
            percent = 10.0
            label = "постоянный"
        elif choice == "vip":
            percent = 20.0
            label = "vip"
        else:
            raw = self.custom_var.get().strip().replace(",", ".")
            try:
                percent = float(raw)
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректный процент.")
                return
            if percent < 0 or percent > 100:
                messagebox.showerror("Ошибка", "Процент должен быть от 0 до 100.")
                return
            label = "другая"
        self.apply_callback(percent, label)
        self.destroy()


class MainWindow(tk.Tk):
    def __init__(self, service: OrderService) -> None:
        super().__init__()
        self.title("Pattern Brew - Заказы")
        self.geometry("980x600")
        self.service = service
        self.current_order_id: Optional[int] = None
        self.details_window: Optional[DetailsWindow] = None
        self._active_order_ids: list[int] = []
        self._menu_map: Dict[str, str] = {}
        self._build_ui()
        self._load_menu()
        self._refresh_active_orders()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=4)
        self.rowconfigure(1, weight=1)

        top_frame = ttk.Frame(self, padding=10)
        top_frame.grid(row=0, column=0, sticky="nsew")
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=2)
        top_frame.columnconfigure(2, weight=1)
        top_frame.rowconfigure(0, weight=1)

        menu_frame = ttk.LabelFrame(top_frame, text="Меню")
        menu_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        menu_frame.columnconfigure(0, weight=1)
        menu_frame.rowconfigure(1, weight=1)
        menu_frame.rowconfigure(3, weight=1)

        ttk.Label(menu_frame, text="Продукты").grid(row=0, column=0, sticky="w")
        self.menu_listbox = tk.Listbox(menu_frame, height=12, exportselection=False)
        self.menu_listbox.grid(row=1, column=0, sticky="nsew", pady=(4, 8))

        ttk.Label(menu_frame, text="Добавки (для напитков)").grid(row=2, column=0, sticky="w")
        self.add_on_listbox = tk.Listbox(menu_frame, selectmode=tk.MULTIPLE, height=8, exportselection=False)
        self.add_on_listbox.grid(row=3, column=0, sticky="nsew", pady=(4, 0))

        order_frame = ttk.LabelFrame(top_frame, text="Текущий заказ")
        order_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        order_frame.columnconfigure(0, weight=1)
        order_frame.rowconfigure(0, weight=1)
        self.order_listbox = tk.Listbox(order_frame, exportselection=False)
        self.order_listbox.grid(row=0, column=0, sticky="nsew")

        control_frame = ttk.LabelFrame(top_frame, text="Управление")
        control_frame.grid(row=0, column=2, sticky="nsew")
        control_frame.columnconfigure(0, weight=1)

        self.total_label = ttk.Label(control_frame, text="Итого: 0.00", font=("Segoe UI", 12, "bold"))
        self.total_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(control_frame, text="Активные заказы").grid(row=1, column=0, sticky="w")
        self.active_orders_listbox = tk.Listbox(control_frame, height=6, exportselection=False)
        self.active_orders_listbox.grid(row=2, column=0, sticky="ew", pady=(4, 10))
        self.active_orders_listbox.bind("<<ListboxSelect>>", self._select_order)

        self.create_order_button = ttk.Button(control_frame, text="Создать заказ", command=self._create_order)
        self.create_order_button.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        self.add_item_button = ttk.Button(control_frame, text="Добавить позицию", command=self._add_item)
        self.add_item_button.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        self.remove_item_button = ttk.Button(control_frame, text="Удалить выбранное", command=self._remove_item)
        self.remove_item_button.grid(row=5, column=0, sticky="ew", pady=(0, 6))

        self.discount_button = ttk.Button(control_frame, text="Скидка", command=self._open_discount)
        self.discount_button.grid(row=6, column=0, sticky="ew", pady=(0, 6))

        self.details_button = ttk.Button(control_frame, text="Детали заказа", command=self._open_details)
        self.details_button.grid(row=7, column=0, sticky="ew", pady=(0, 6))

        ttk.Label(control_frame, text="Статус заказа").grid(row=8, column=0, sticky="w")
        self.status_combo = ttk.Combobox(
            control_frame,
            values=[status.value for status in OrderStatus],
            state="readonly",
        )
        self.status_combo.current(0)
        self.status_combo.grid(row=9, column=0, sticky="ew", pady=(4, 10))

        self.status_button = ttk.Button(control_frame, text="Изменить статус", command=self._change_status)
        self.status_button.grid(row=10, column=0, sticky="ew")

        log_frame = ttk.LabelFrame(self, text="Журнал событий", padding=10)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=6, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def _load_menu(self) -> None:
        self.menu_listbox.delete(0, tk.END)
        self._menu_map.clear()
        for product in self.service.list_beverages() + self.service.list_desserts():
            display = f"{product.get_category().title()}: {product.get_name()}"
            self._menu_map[display] = product.get_name()
            self.menu_listbox.insert(tk.END, display)

        self.add_on_listbox.delete(0, tk.END)
        for add_on in self.service.list_add_ons():
            self.add_on_listbox.insert(tk.END, add_on.get_name())

    def _create_order(self) -> None:
        order = self.service.create_order()
        self.current_order_id = order.order_id
        self.status_combo.current(0)
        self.menu_listbox.selection_clear(0, tk.END)
        self.add_on_listbox.selection_clear(0, tk.END)
        self._refresh_active_orders(order.order_id)
        self._refresh_order()
        self._update_total()

    def _add_item(self) -> None:
        if not self._ensure_order():
            return
        selection = self.menu_listbox.curselection()
        if not selection:
            messagebox.showwarning("Нет выбора", "Выберите продукт для добавления.")
            return
        display_name = self.menu_listbox.get(selection[0])
        product_name = self._menu_map.get(display_name)
        add_on_names = [self.add_on_listbox.get(i) for i in self.add_on_listbox.curselection()]
        try:
            self.service.add_menu_item(self.current_order_id, product_name, add_on_names)
        except InvalidAddOnError as exc:
            messagebox.showerror("Ошибка добавок", str(exc))
            return
        except CoffeeOrderError as exc:
            messagebox.showerror("Ошибка заказа", str(exc))
            return
        self._refresh_order()
        self._update_total()

    def _remove_item(self) -> None:
        if not self._ensure_order():
            return
        selection = self.order_listbox.curselection()
        if not selection:
            messagebox.showwarning("Нет выбора", "Выберите позицию для удаления.")
            return
        try:
            self.service.remove_item(self.current_order_id, selection[0])
        except CoffeeOrderError as exc:
            messagebox.showerror("Ошибка заказа", str(exc))
            return
        self._refresh_order()
        self._update_total()

    def _open_details(self) -> None:
        if not self._ensure_order():
            return
        if self.details_window and self.details_window.winfo_exists():
            self.details_window.lift()
        else:
            self.details_window = DetailsWindow(self)
            self.details_window.protocol("WM_DELETE_WINDOW", self._close_details)
        self._refresh_details()

    def _close_details(self) -> None:
        if self.details_window:
            self.details_window.destroy()
        self.details_window = None

    def _open_discount(self) -> None:
        if not self._ensure_order():
            return
        order = self.service.get_order(self.current_order_id)
        window = DiscountWindow(self, self._apply_discount, order.discount_percent, order.discount_label)
        window.transient(self)
        window.grab_set()

    def _apply_discount(self, percent: float, label: str) -> None:
        try:
            self.service.set_discount(self.current_order_id, percent, label)
        except CoffeeOrderError as exc:
            messagebox.showerror("Ошибка заказа", str(exc))
            return
        self._refresh_order()
        self._update_total()
        self._refresh_details()

    def _change_status(self) -> None:
        if not self._ensure_order():
            return
        status_value = self.status_combo.get()
        new_status = OrderStatus(status_value)
        try:
            self.service.change_order_status(self.current_order_id, new_status)
        except CoffeeOrderError as exc:
            messagebox.showerror("Ошибка заказа", str(exc))
            return
        self._refresh_active_orders()
        self._refresh_order()

    def _refresh_order(self) -> None:
        if not self._ensure_order(show_message=False):
            self.order_listbox.delete(0, tk.END)
            self._refresh_details()
            return
        order = self.service.get_order(self.current_order_id)
        self.order_listbox.delete(0, tk.END)
        for item_name in self.service.list_order_items(self.current_order_id):
            self.order_listbox.insert(tk.END, f"{item_name} | статус: {order.status.value}")
        self._refresh_details()

    def _refresh_active_orders(self, select_order_id: Optional[int] = None) -> None:
        self.active_orders_listbox.delete(0, tk.END)
        self._active_order_ids.clear()
        active_orders = self.service.list_active_orders()
        for order in active_orders:
            self._active_order_ids.append(order.order_id)
            label = f"Заказ №{order.order_id} | {order.status.value}"
            self.active_orders_listbox.insert(tk.END, label)

        if select_order_id in self._active_order_ids:
            index = self._active_order_ids.index(select_order_id)
            self.active_orders_listbox.selection_set(index)
            self.current_order_id = select_order_id
        elif self.current_order_id in self._active_order_ids:
            index = self._active_order_ids.index(self.current_order_id)
            self.active_orders_listbox.selection_set(index)
        elif self._active_order_ids:
            self.current_order_id = self._active_order_ids[0]
            self.active_orders_listbox.selection_set(0)
        else:
            self.current_order_id = None

    def _select_order(self, _event: tk.Event) -> None:
        selection = self.active_orders_listbox.curselection()
        if not selection:
            return
        order_id = self._active_order_ids[selection[0]]
        self.current_order_id = order_id
        order = self.service.get_order(order_id)
        self.status_combo.set(order.status.value)
        self._refresh_order()
        self._update_total()

    def _refresh_details(self) -> None:
        if not self.details_window or not self.details_window.winfo_exists():
            return
        if not self._ensure_order(show_message=False):
            self.details_window.update_rows([], OrderStatus.CREATED)
            return
        order = self.service.get_order(self.current_order_id)
        items = self.service.get_order_items(self.current_order_id)
        self.details_window.update_rows(items, order.status)

    def _update_total(self) -> None:
        if not self._ensure_order(show_message=False):
            self.total_label.configure(text="Итого: 0.00")
            return
        order = self.service.get_order(self.current_order_id)
        total = self.service.calculate_total(self.current_order_id)
        if order.discount_percent > 0:
            self.total_label.configure(text=f"Итого: {total:.2f} (скидка {order.discount_percent:.0f}%)")
        else:
            self.total_label.configure(text=f"Итого: {total:.2f}")

    def _ensure_order(self, show_message: bool = True) -> bool:
        if self.current_order_id is None:
            if show_message:
                messagebox.showinfo("Нет заказа", "Сначала создайте заказ.")
            return False
        return True

    def append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
