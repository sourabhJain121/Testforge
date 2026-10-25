from typing import Union, Dict

class CurrencyExchange:
    def __init__(self, spreads: Dict[str, Dict[str, float]], fee_waivers: Dict[str, float], rounding: int = 2):
        """
        Initialize the currency exchange calculator.

        :param spreads: A dictionary of dictionaries representing tiered spreads for each currency pair.
        :param fee_waivers: A dictionary representing fee waivers for certain currencies.
        :param rounding: The number of decimal places to round the results to.
        """
        self.spreads = spreads
        self.fee_waivers = fee_waivers
        self.rounding = rounding

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert an amount from one currency to another, applying tiered spreads and fee waivers.

        :param amount: The amount to convert.
        :param from_currency: The currency to convert from.
        :param to_currency: The currency to convert to.
        :return: The converted amount.
        """
        if from_currency == to_currency:
            return round(amount, self.rounding)

        if from_currency not in self.spreads or to_currency not in self.spreads[from_currency]:
            raise ValueError(f"Invalid currency pair: {from_currency} to {to_currency}")

        spread = self.spreads[from_currency][to_currency]
        fee_waiver = self.fee_waivers.get(from_currency, 0)

        if amount < 0:
            raise ValueError("Amount must be non-negative")

        if amount == 0:
            return 0

        converted_amount = amount * (1 + spread)
        if from_currency in self.fee_waivers:
            converted_amount *= (1 - fee_waiver)

        return round(converted_amount, self.rounding)