"""Unit conversions used throughout the inventory."""

G_PER_KG = 1000.0
KG_PER_T = 1000.0
WH_PER_KWH = 1000.0


def g_to_kg(grams: float) -> float:
    return grams / G_PER_KG


def tonne_km(mass_kg: float, distance_km: float) -> float:
    """Freight activity in tonne-kilometres."""
    return (mass_kg / KG_PER_T) * distance_km


def wh_to_kwh(wh: float) -> float:
    return wh / WH_PER_KWH


def gross_input(net_mass_kg: float, scrap_rate: float) -> float:
    """Material input needed to deliver a net part mass given process scrap (0 <= scrap < 1)."""
    if not 0 <= scrap_rate < 1:
        raise ValueError(f"scrap_rate must be in [0, 1): {scrap_rate}")
    return net_mass_kg / (1.0 - scrap_rate)


CO2_PER_C = 44.0 / 12.0
