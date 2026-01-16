from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PYCACHE_DIR = os.path.join(PROJECT_ROOT, ".pycache")
os.makedirs(PYCACHE_DIR, exist_ok=True)
if hasattr(sys, "pycache_prefix"):
    sys.pycache_prefix = PYCACHE_DIR
else:
    sys.dont_write_bytecode = True

from core.patterns.observer.observers import CustomerNotifier, KitchenDisplay, Logger
from core.services.order_service import OrderService
from gui.main_window import MainWindow


def main() -> None:
    service = OrderService()
    app = MainWindow(service)
    observers = [KitchenDisplay(app.append_log), CustomerNotifier(app.append_log), Logger(app.append_log)]
    service.set_observers(observers)
    app.mainloop()


if __name__ == "__main__":
    main()
