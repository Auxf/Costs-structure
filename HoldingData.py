import tkinter as tk
from tkinter import ttk
from openbb import obb  # Assuming you're using the OpenBB SDK
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Mapping of attribute names to user-friendly labels
attribute_labels = {
    "total_revenue": "Total Revenue",
    "gross_profit": "Gross Profit",
    "ebitda": "EBITDA",
    "ebit": "EBIT",
    "total_pre_tax_income": "Pre-Tax Income",
    "net_income": "Net Income",
}

# Fetch income statement data
def fetch_income_statement(symbol):
    # Fetch data using the OpenBB SDK (or any other method)
    data = obb.equity.fundamental.income(symbol=symbol, period='annual', limit=5, provider="yfinance")
    return data.results  # This assumes 'results' holds the income statement data

# Function to format numbers with commas
def format_number(value):
    if isinstance(value, (int, float)):  # Check if value is numeric
        return f"{value:,.0f}"  # Format with commas and no decimal points
    return value  # Return non-numeric values as is

# Function to generate a waterfall chart with percentages for a single year
def generate_waterfall_chart_percentage(year_data):
    # Extract the necessary fields for the waterfall chart
    total_revenue = year_data.total_revenue

    if not total_revenue or total_revenue == 0:
        return None  # Avoid division by zero if no revenue data available

    # Extract the values and convert them to percentages of total revenue
    waterfall_values = [
        year_data.total_revenue,             # 100% of Total Revenue
        year_data.gross_profit,              # Gross Profit
        year_data.ebitda,                    # EBITDA
        year_data.ebit,                      # EBIT
        year_data.total_pre_tax_income,      # Pre-Tax Income
        year_data.net_income                 # Net Income
    ]
    
    # Convert values to percentages relative to total revenue
    waterfall_percentages = [(value / total_revenue) * 100 if value is not None else 0 for value in waterfall_values]

    waterfall_labels = [
        "Revenue",
        "Cost of Revenue",
        "Operational Expenses",
        "Depreciation & Amortization",
        "Financial expenses",
        "Tax"
    ]

    # Calculate step changes for the waterfall chart
    steps = [waterfall_percentages[0]] + [waterfall_percentages[i] - waterfall_percentages[i-1] for i in range(1, len(waterfall_percentages))]

    # Create a figure for the waterfall chart
    fig, ax = plt.subplots(figsize=(4, 4), dpi=80)

    # Adjust the bottom padding to fit the long x-axis labels
    plt.subplots_adjust(bottom=0.4)  # Increase the bottom padding to make space for the labels

    # Initialize waterfall chart parameters
    running_total = np.cumsum(steps)
    starts = np.hstack((0, running_total[:-1]))  # Starting points for bars

    # Color coding for increasing and decreasing bars
    colors = ['green' if x >= 0 else 'red' for x in steps]

    # Create the waterfall chart
    ax.bar(waterfall_labels, steps, bottom=starts, color=colors, edgecolor='black')

    # Adding labels for the percentage values
    for i in range(len(steps)):
        ax.text(i, starts[i] + steps[i] / 2, f'{steps[i]:.1f}%', ha='center', va='center', color='white', fontsize=8)

    # Rotate x labels for better visibility
    plt.xticks(rotation=45, ha='right')

    # Remove the grid and unnecessary spines
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return fig

# Function to embed waterfall charts below the table
def display_waterfall_charts(income_statement_data, years):
    for i, year_data in enumerate(income_statement_data):
        # Generate the waterfall chart with percentages
        waterfall_chart = generate_waterfall_chart_percentage(year_data)
        
        if waterfall_chart:
            # Display the waterfall chart using Tkinter's FigureCanvasTkAgg
            chart_canvas = FigureCanvasTkAgg(waterfall_chart, master=funnel_frame)
            chart_canvas.draw()
            chart_canvas.get_tk_widget().grid(row=0, column=i, padx=10)

# Function to populate the table
def populate_table(symbol):
    # Clear the previous content of the table
    for i in table.get_children():
        table.delete(i)

    # Fetch the income statement data
    income_statement_data = fetch_income_statement(symbol)

    if not income_statement_data:
        return

    # Get the years from the data (assuming 'period_ending' is a date object)
    years = [year_data.period_ending.year for year_data in income_statement_data]

    # Set the columns with the years as headers
    table["columns"] = ["Characteristic"] + years
    table["show"] = "headings"  # Only show headers

    # Add column headers
    table.heading("Characteristic", text="Characteristic")
    for year in years:
        table.heading(year, text=str(year))

    # List of all attributes to display, preserving a certain order for important fields
    all_attributes = list(attribute_labels.keys())

    # Loop over all attributes to display their values for each year
    for attribute in all_attributes:
        row = [attribute_labels.get(attribute, attribute)]  # Start row with the label for the attribute
        for year_data in income_statement_data:
            value = getattr(year_data, attribute, "N/A")  # Get attribute value or N/A if it doesn't exist
            row.append(format_number(value))  # Format the number with commas
        table.insert("", "end", values=row)

    # Clear previous charts and display the waterfall charts
    for widget in funnel_frame.winfo_children():
        widget.destroy()

    display_waterfall_charts(income_statement_data, years)

# Function to create the main application window
def create_app():
    global table, funnel_frame

    # Create the main application window
    root = tk.Tk()
    root.title("Income Statement Dashboard")

    # Create the table (Treeview widget)
    table_frame = ttk.Frame(root)
    table_frame.pack(fill="both", expand=True)

    # Define the treeview widget
    table = ttk.Treeview(table_frame)
    table.pack(fill="both", expand=True)

    # Add a scrollbar to the table
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    scrollbar.pack(side="right", fill="y")
    table.configure(yscroll=scrollbar.set)

    # Add a symbol input and load button
    symbol_label = ttk.Label(root, text="Enter Symbol:")
    symbol_label.pack(pady=2)

    symbol_entry = ttk.Entry(root)
    symbol_entry.pack(pady=2)

    load_button = ttk.Button(root, text="Load Data", command=lambda: populate_table(symbol_entry.get()))
    load_button.pack(pady=3)

    # Add an Exit button to close the app
    exit_button = ttk.Button(root, text="Exit", command=root.quit)
    exit_button.pack(pady=2)

    # Create a frame for the waterfall charts below the table
    funnel_frame = ttk.Frame(root)
    funnel_frame.pack(fill="both", expand=True)

    # Start the Tkinter event loop
    root.mainloop()

# Run the application
if __name__ == "__main__":
    create_app()
