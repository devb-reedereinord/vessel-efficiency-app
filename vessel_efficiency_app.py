import streamlit as st
import matplotlib.pyplot as plt
from typing import List, Dict

# Constants
EMISSION_FACTORS = {
    'VLSFO': 3.114,
    'MGO': 3.206,
    'LNG': 2.750,
    'Methanol': 1.375,
    'Ammonia': 0.000
}

FUEL_PRICES = {
    'VLSFO': 600,
    'MGO': 700,
    'LNG': 800,
    'Methanol': 900,
    'Ammonia': 1000
}

DISCOUNT_RATE = 0.07
YEARS = 10
EFFICIENCY_DEGRADATION_RATE = 0.01
DRYDOCK_CYCLE = 5

class Vessel:
    def __init__(self, dwt: float, fuel_type: str, annual_fuel_consumption: float):
        self.dwt = dwt
        self.fuel_type = fuel_type
        self.annual_fuel_consumption = annual_fuel_consumption

def calculate_emissions(fuel_type: str, fuel_consumed: float) -> float:
    return fuel_consumed * EMISSION_FACTORS[fuel_type]

def calculate_carbon_tax(emissions: float, tax_rate: float) -> float:
    return emissions * tax_rate

def apply_tech_efficiency_reduction(base_fuel: float, efficiency_gain: float) -> float:
    return base_fuel * (1 - efficiency_gain)

def get_degradation_multiplier(year: int) -> float:
    return (1 + EFFICIENCY_DEGRADATION_RATE) ** (year % DRYDOCK_CYCLE)

def calculate_npv(cash_flows: List[float], discount_rate: float = DISCOUNT_RATE) -> float:
    return sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))

def calculate_payback_period(cash_flows):
    cumulative = 0
    for i, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= 0:
            return i + 1
    return f"> {YEARS}"

def plot_emissions_and_costs(years: int, scenarios: Dict[str, Dict[str, List[float]]]):
    fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for label, data in scenarios.items():
        axs[0].plot(range(1, years + 1), data['emissions'], label=label)
        axs[1].plot(range(1, years + 1), data['costs'], label=label)
    axs[0].set_ylabel('Annual Emissions (tCO2)')
    axs[0].set_title('Emissions Over Time')
    axs[0].legend()
    axs[0].grid(True)
    axs[1].set_ylabel('Annual Cost ($)')
    axs[1].set_xlabel('Year')
    axs[1].set_title('Cost Over Time')
    axs[1].legend()
    axs[1].grid(True)
    plt.tight_layout()
    st.pyplot(fig)

# Streamlit UI
st.sidebar.header("Vessel Parameters")
dwt = st.sidebar.number_input("DWT", value=50000)
fuel_type = st.sidebar.selectbox("Fuel Type", list(EMISSION_FACTORS.keys()), index=0)
annual_consumption = st.sidebar.number_input("Annual Fuel Consumption (t)", value=10000)
tax_rate = st.sidebar.number_input("Carbon Tax ($/tCO2)", value=100)
opex = st.sidebar.number_input("Annual OPEX ($)", value=20000)
capex = st.sidebar.number_input("CAPEX ($)", value=500000)
efficiency_gain = st.sidebar.slider("Efficiency Gain from Tech Upgrade (%)", 0.0, 0.5, 0.1, 0.01)

vessel = Vessel(dwt=dwt, fuel_type=fuel_type, annual_fuel_consumption=annual_consumption)
scenarios = {}
npv_summary = {}
payback_summary = {}

# Baseline
emissions, costs, cash_flows = [], [], []
for year in range(YEARS):
    mult = get_degradation_multiplier(year)
    fuel = vessel.annual_fuel_consumption * mult
    e = calculate_emissions(vessel.fuel_type, fuel)
    t = calculate_carbon_tax(e, tax_rate)
    fc = fuel * FUEL_PRICES[vessel.fuel_type]
    total = fc + t + opex
    emissions.append(e)
    costs.append(total)
    cash_flows.append(-total)
scenarios["Baseline"] = {"emissions": emissions, "costs": costs}
npv_summary["Baseline"] = calculate_npv(cash_flows)

# Tech Upgrade
emissions, costs, cash_flows = [], [], []
for year in range(YEARS):
    mult = get_degradation_multiplier(year)
    fuel = apply_tech_efficiency_reduction(vessel.annual_fuel_consumption * mult, efficiency_gain)
    e = calculate_emissions(vessel.fuel_type, fuel)
    t = calculate_carbon_tax(e, tax_rate)
    fc = fuel * FUEL_PRICES[vessel.fuel_type]
    total = fc + t + opex + (capex if year == 0 else 0)
    emissions.append(e)
    costs.append(total)
    cash_flows.append(-total)
scenarios["Tech Upgrade"] = {"emissions": emissions, "costs": costs}
npv_summary["Tech Upgrade"] = calculate_npv(cash_flows)
payback_summary["Tech Upgrade"] = calculate_payback_period(cash_flows)

# Alternative Fuels
for alt_fuel in EMISSION_FACTORS:
    if alt_fuel == vessel.fuel_type:
        continue
    emissions, costs, cash_flows = [], [], []
    for year in range(YEARS):
        mult = get_degradation_multiplier(year)
        fuel = vessel.annual_fuel_consumption * mult
        e = calculate_emissions(alt_fuel, fuel)
        t = calculate_carbon_tax(e, tax_rate)
        fc = fuel * FUEL_PRICES[alt_fuel]
        total = fc + t + opex + (capex if year == 0 else 0)
        emissions.append(e)
        costs.append(total)
        cash_flows.append(-total)
    label = f"Switch to {alt_fuel}"
    scenarios[label] = {"emissions": emissions, "costs": costs}
    npv_summary[label] = calculate_npv(cash_flows)
    payback_summary[label] = calculate_payback_period(cash_flows)

# Show Plots and Summary
st.header("Emissions and Cost Comparison")
plot_emissions_and_costs(YEARS, scenarios)

st.header("NPV and Payback Period Summary")
st.table({
    "Scenario": list(npv_summary.keys()),
    "NPV ($)": [f"{npv_summary[k]:,.0f}" for k in npv_summary],
    "Payback Period (years)": [payback_summary.get(k, "-") for k in npv_summary]
})
