from __future__ import annotations

import os
import sys

from PyQt6 import QtWidgets

from core.patterns.observer.observers import CustomerNotifier, KitchenDisplay, Logger
from core.services.order_service import OrderService
from gui_pyqt6.main_window import MainWindow


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PYCACHE_DIR = os.path.join(PROJECT_ROOT, ".pycache")
os.makedirs(PYCACHE_DIR, exist_ok=True)
if hasattr(sys, "pycache_prefix"):
    sys.pycache_prefix = PYCACHE_DIR
else:
    sys.dont_write_bytecode = True


def main() -> None:
    service = OrderService()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(service)
    observers = [KitchenDisplay(window.append_log), CustomerNotifier(window.append_log), Logger(window.append_log)]
    service.set_observers(observers)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
