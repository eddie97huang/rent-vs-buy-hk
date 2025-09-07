
"""
Hong Kong Rent vs Buy Calculator using numpy_financial

Assumptions modeled monthly with annual growth rates.
- Tracks mortgage amortization, property appreciation, rent inflation
- Includes HK-style "Rates" (here modeled as 5% of market rent per year) and
  a management fee (0.15% p.a. of current property valuation)
- Includes configurable closing costs on purchase and sale
- Compares end-of-horizon net worth (owner equity + side investments vs. renter investments)

Edit the PARAMETERS block or pass your own parameters to simulate_rent_vs_buy().
Requires: numpy, numpy_financial
"""

from dataclasses import dataclass
from typing import Dict, Any
import numpy_financial as npf

@dataclass
class SimulationResult:
    params: Dict[str, Any]
    months: int
    buy_net_worth: float
    rent_net_worth: float
    net_advantage_buy: float
    details: Dict[str, Any]


def simulate_rent_vs_buy(
    house_size_sqft: float = 500,
    house_price_per_sqft: float = 20_000,
    monthly_rent_per_sqft: float = 50,
    down_payment_pct: float = 0.30,   # 30%
    mortgage_rate_annual: float = 0.035,
    mortgage_years: int = 30,
    investment_return_annual: float = 0.07,
    house_appreciation_annual: float = 0.01,
    rent_increase_annual: float = 0.02,
    gov_rate_pct_of_rent_annual: float = 0.05,   # 5% of market rent per year (approx for HK Rates)
    mgmt_fee_pct_of_value_annual: float = 0.0015, # 0.15% p.a. of property valuation
    buy_closing_cost_pct: float = 0.05,  # HK stamp duties 4% + agent fee 1% + legal etc.
    sell_closing_cost_pct: float = 0.01, # agent fee 1% + legal etc.
    horizon_years: int = 30,
    invest_monthly_diffs: bool = True,
) -> SimulationResult:
    """
    Returns end-of-horizon net worths for Buy vs Rent.

    Notes on methodology:
    - RENTER: invests upfront cash avoided by buying (down payment + buy closing cost).
      Then each month invests any savings if renting is cheaper than owning. If renting
      becomes more expensive, we *do not* assume borrowing to make up the difference
      (set invest_monthly_diffs=False to disable monthly flows entirely).
    - OWNER: pays down mortgage, pays rates and mgmt fee; also invests monthly savings if
      owning becomes cheaper than renting.
    - At horizon end, OWNER sells and pays sale closing costs.
    """

    months = horizon_years * 12

    # Derived quantities and monthly factors
    house_price = house_size_sqft * house_price_per_sqft
    monthly_rent = house_size_sqft * monthly_rent_per_sqft
    down_payment = house_price * down_payment_pct
    loan_principal = house_price - down_payment
    r_m = (1.0 + mortgage_rate_annual) ** (1.0 / 12.0) - 1.0
    n_m = mortgage_years * 12

    # Constant mortgage payment (negative sign from numpy_financial convention)
    mort_payment = float(-npf.pmt(r_m, n_m, loan_principal))

    # Monthly growth factors
    f_house = (1.0 + house_appreciation_annual) ** (1.0 / 12.0)
    f_rent  = (1.0 + rent_increase_annual) ** (1.0 / 12.0)
    f_inv   = (1.0 + investment_return_annual) ** (1.0 / 12.0) - 1.0  # monthly rate

    # Closing costs
    buy_closing_cost = house_price * buy_closing_cost_pct

    # Initialize state
    property_value = house_price
    market_rent = monthly_rent
    remaining_balance = loan_principal

    # Side accounts for invested savings
    owner_side_invest = 0.0
    renter_invest = 0.0

    # Upfront cash: renter keeps what buyer would have spent upfront
    renter_invest += (down_payment + buy_closing_cost)

    # Track totals (optional diagnostics)
    total_owner_cash_out = down_payment + buy_closing_cost
    total_renter_cash_out = 0.0

    for m in range(0, months):
        # Owner costs this month
        interest = remaining_balance * r_m
        principal = mort_payment - interest
        principal = max(principal, 0.0)
        remaining_balance = max(remaining_balance - principal, 0.0)

        mgmt_fee = property_value * mgmt_fee_pct_of_value_annual / 12.0
        gov_rates = market_rent * gov_rate_pct_of_rent_annual

        owner_monthly_cost = mort_payment + mgmt_fee + gov_rates

        # Renter cost this month
        renter_monthly_cost = market_rent

        # Update side investments at monthly return
        owner_side_invest *= (1.0 + f_inv)
        renter_invest *= (1.0 + f_inv)

        if invest_monthly_diffs:
            diff = owner_monthly_cost - renter_monthly_cost
            if diff > 0:
                # Renting is cheaper -> renter invests the savings relative to owning
                renter_invest += diff
            else:
                # Owning is cheaper -> owner invests the savings
                owner_side_invest += (-diff)

        # Track totals (optional diagnostics)
        total_renter_cash_out += renter_monthly_cost
        total_owner_cash_out += owner_monthly_cost

        # Update property value & market rent
        property_value *= f_house
        market_rent *= f_rent

    # End of horizon liquidation for owner
    sale_proceeds_before_costs = property_value
    sell_closing_cost = sale_proceeds_before_costs * sell_closing_cost_pct
    owner_equity_realized = sale_proceeds_before_costs - sell_closing_cost - remaining_balance
    owner_equity_realized = max(owner_equity_realized, 0.0)

    # Owner invests realized equity at the same time horizon end (no extra compounding beyond horizon)
    buy_net_worth = owner_equity_realized + owner_side_invest
    rent_net_worth = renter_invest

    return SimulationResult(
        params=dict(
            house_price=house_price,
            monthly_rent=monthly_rent,
            down_payment_pct=down_payment_pct,
            mortgage_rate_annual=mortgage_rate_annual,
            mortgage_years=mortgage_years,
            investment_return_annual=investment_return_annual,
            house_appreciation_annual=house_appreciation_annual,
            rent_increase_annual=rent_increase_annual,
            gov_rate_pct_of_rent_annual=gov_rate_pct_of_rent_annual,
            mgmt_fee_pct_of_value_annual=mgmt_fee_pct_of_value_annual,
            buy_closing_cost_pct=buy_closing_cost_pct,
            sell_closing_cost_pct=sell_closing_cost_pct,
            horizon_years=horizon_years,
            invest_monthly_diffs=invest_monthly_diffs,
        ),
        months=months,
        buy_net_worth=buy_net_worth,
        rent_net_worth=rent_net_worth,
        net_advantage_buy=buy_net_worth - rent_net_worth,
        details=dict(
            remaining_mortgage_balance=remaining_balance,
            property_value_end=property_value,
            monthly_rent_end=market_rent,
            sale_closing_cost=sell_closing_cost,
            owner_equity_realized=owner_equity_realized,
            owner_side_invest_end=owner_side_invest,
            renter_invest_end=renter_invest,
            total_owner_cash_out=total_owner_cash_out,
            total_renter_cash_out=total_renter_cash_out,
            monthly_mortgage_payment=mort_payment,
        ),
    )


if __name__ == "__main__":
    res = simulate_rent_vs_buy(
        house_size_sqft=500,
        house_price_per_sqft=20_000,
        monthly_rent_per_sqft=50,
        down_payment_pct=0.20,
        mortgage_rate_annual=0.035,
        mortgage_years=30,
        investment_return_annual=0.07,
        house_appreciation_annual=0.01,
        rent_increase_annual=0.02,
        gov_rate_pct_of_rent_annual=0.05,
        mgmt_fee_pct_of_value_annual=0.0015,
        buy_closing_cost_pct=0.05,
        sell_closing_cost_pct=0.01,
        horizon_years=30,
        invest_monthly_diffs=True,
    )

    print("--- Parameters ---")
    for k, v in res.params.items():
        print(f"{k}: {v}")

    print("\n--- Results (end of horizon) ---")
    print(f"Buy net worth:   ${res.buy_net_worth:,.0f}")
    print(f"Rent net worth:  ${res.rent_net_worth:,.0f}")
    adv = res.net_advantage_buy
    verdict = "BUY better by" if adv > 0 else "RENT better by"
    print(f"{verdict}: ${abs(adv):,.0f}")

    print("\n--- Details ---")
    for k, v in res.details.items():
        if isinstance(v, (int, float)):
            print(f"{k}: {v:,.2f}")
        else:
            print(f"{k}: {v}")
