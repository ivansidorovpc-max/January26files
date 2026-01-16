
class CoffeeOrderError(Exception):
    pass


class ProductNotFoundError(CoffeeOrderError):
    pass


class OrderNotFoundError(CoffeeOrderError):
    pass


class OrderStateError(CoffeeOrderError):
    pass


class InvalidAddOnError(CoffeeOrderError):
    pass
