import pandas as pd
from datetime import datetime
from datetime import timedelta
import openpyxl
import random
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

########## Reading data ##########

clients_table = pd.read_excel('Data.xlsx', sheet_name='Clients')
client_list = clients_table['Client ID'].tolist()

products_table = pd.read_excel('Data.xlsx', sheet_name='Products')
product_list = products_table['Product ID'].tolist()

price_table = pd.read_excel('Data.xlsx', sheet_name='Product price')

########## Stating variables ##########

sales = 3500
discount_rates = [0, 3, 5, 7, 10]
start_date = datetime(2022, 1, 1)
today = pd.Timestamp.today().date()
end_date = datetime(2026, 8, 31).date()
forecast_limit = datetime(2026, 12, 31).date()

########## Creating price map ##########

price_map = price_table.set_index(['Product ID', 'Year'])[['Unit price', 'Unit cost']].to_dict('index')

########## Generating sales data ##########

results = []

for i in range(sales):
    year = start_date.year
    start_date += timedelta(days=random.choice([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2]))
    operation_ID = f'S{i + 1:05d}'
    client_ID = random.choice(client_list)
    product_ID = random.choice(product_list)
    growth_rate = 1.05 ** (year - 2022)
    random_factor = random.uniform(0.90, 1.15)
    quantity = round(random.randrange(50, 751, 5) * growth_rate * random_factor)
    unit = 'KG'
    discount_per = random.choice(discount_rates)

    ########## Adding mapped price and cost ##########

    cost_factor = random.uniform(0.9, 1.1)
    price_data = price_map[(product_ID, year)]
    unit_price = price_data['Unit price']
    unit_cost = price_data['Unit cost'] * cost_factor

    ########## Calculating sales data ##########

    gross_sales = quantity * unit_price
    discount_amount = gross_sales * discount_per / 100
    net_sales = gross_sales - discount_amount
    total_cost = quantity * unit_cost
    gross_profit = net_sales - total_cost
    gross_profit_per = gross_profit / net_sales

    ########## Appending results ##########

    results.append({
        'Operation_ID': operation_ID,
        'Date': start_date.date(),
        'Client_ID': client_ID,
        'Product_ID': product_ID,
        'Quantity': quantity,
        'Unit': unit,
        'Unit_price': unit_price,
        'Unit_cost': unit_cost,
        'Gross_sales': gross_sales,
        'Discount_%': discount_per,
        'Discount_amount': discount_amount,
        'Net_sales': net_sales,
        'Total_cost': total_cost,
        'Gross_profit': gross_profit,
        'Gross_profit_%': gross_profit_per,
    })

########## Saving results to excel ##########

sales_df = pd.DataFrame(results)
sales_forecast = sales_df[(sales_df['Date'] > end_date) & (sales_df['Date'] <= forecast_limit)]
sales_df = sales_df[sales_df['Date'] <= end_date]
sales_df.to_excel('Coffee sales data.xlsx', sheet_name='Sales data', index=False)
sales_forecast.to_excel('Coffee sales FC.xlsx', sheet_name='Sales FC data', index=False)

########## Saving results to PostgreSQL database ##########

########## PostgreSQL connection credentials ##########

user = "postgres"
password = "PGadmin"
host = "localhost"
port = 5432
database = "coffee_sales_db"

########## Connecting to PostgreSQL ##########

admin_engine = create_engine(
URL.create(
        "postgresql+psycopg2",
        username = user,
        password = password,
        host = host,
        port = port,
        database = "postgres"
    ),
    isolation_level = "AUTOCOMMIT"
)

########## Checking if database exists ##########

with admin_engine.connect() as connection:

    result = connection.execute(text("SELECT 1 FROM pg_database WHERE datname = :database"), {"database": database})
    database_exists = result.scalar() is not None

    ########## Creating database if it doesn't exist ##########

    if not database_exists:
        connection.execute(text(f'CREATE DATABASE "{database}"'))
        print(f"Database '{database}' created.")

    else:
        print(f"Database '{database}' already exists.")

########## Connect to coffee_sales_db ##########

engine = create_engine(
    URL.create(
        "postgresql+psycopg2",
        username = user,
        password = password,
        host = host,
        port = port,
        database = database
    )
)

########## Saving sales data ##########

sales_df.to_sql('coffee_sales', engine, if_exists='replace', index=False)