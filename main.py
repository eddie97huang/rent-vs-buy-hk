import math

house_price = 10000000
monthly_rent = 30000
price_to_rent_ratio = house_price / (monthly_rent * 12)
print(f"Price-to-Rent ratio is {price_to_rent_ratio}")

years = 30
mortgage_rate = 0.035
house_appreciation = 0.02
investment_yield = 0.07

monthly_payment = house_price * mortgage_rate / 12 * math.pow(1 + mortgage_rate / 12, years * 12)/(math.pow(1 + mortgage_rate / 12, years * 12) - 1)

investment_amount = monthly_payment + house_price * 0.003 / 12 - monthly_rent

investment_pv = investment_amount * (math.pow(1 + investment_yield / 12, 12 * years) - 1)/(investment_yield / 12)

print(f"investment: {investment_pv} vs house: {house_price * math.pow(1 + house_appreciation, years)}")
print(f"investment is ahead by {investment_pv - house_price * math.pow(1 + house_appreciation, years)}")
