"""Un solo formato de cifras en todo el proyecto: el de EE. UU., con coma para los miles."""


def number(value: int) -> str:
    return f"{value:,}"


def usd(value: int) -> str:
    """'USD' explícito en vez de '$', que en Latinoamérica también usan otras monedas."""
    return f"{value:,} USD"


def rate(value: float) -> str:
    return f"{value:,.2f}"


def hours(value: float) -> str:
    return f"{value:,.1f}"


def pct(fraction: float, decimals: int = 1) -> str:
    return f"{fraction * 100:,.{decimals}f} %"
