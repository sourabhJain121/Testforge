class BaseEntity:
    def __init__(self, entity_id: str):
        self._id = entity_id

    @property
    def id(self) -> str:
        return self._id

class BankAccount(BaseEntity):
    def __init__(self, entity_id: str, balance: float = 0.0):
        super().__init__(entity_id)
        self.balance = balance

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.balance += amount
        return self.balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Withdrawal must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance
