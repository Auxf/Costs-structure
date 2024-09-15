import tkinter as tk
from tkinter import ttk
from openbb import obb  #Need to install OpenBB library
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Mapping of attributes and their real names
attribute_labels = {
    "total_revenue": "Total Revenue",
    "gross_profit": "Gross Profit",
    "ebitda": "EBITDA",
    "ebit": "EBIT",
    "total_pre_tax_income": "Pre-Tax Income",
    "net_income": "Net Income",
}

def fetch_income_statement(symbol):
    #change period with quarter, limit is the number of past statements imported and provider is the source of information (may needs API keys)
    data = obb.equity.fundamental.income(symbol=symbol, period='annual', limit=5, provider="yfinance")
    return data.results

def format_number(value):
    if isinstance(value, (int, float)):
        return f"{value:,.0f}"
    return value

def generate_waterfall_chart_percentage(year_data):
    total_revenue = year_data.total_revenue

    if not total_revenue or total_revenue == 0:
        return None


    waterfall_values = [
        year_data.total_revenue,             # 100% of Total Revenue
        year_data.gross_profit,              # Gross Profit (shows the costs of revenue)
        year_data.ebitda,                    # EBITDA (shows the operational costs)
        year_data.ebit,                      # EBIT (shows the D&A costs)
        year_data.total_pre_tax_income,      # Pre-Tax Income (shows the fiancial expenses such as interests)
        year_data.net_income                 # Net Income (shows the tax expenses)
    ]
    
    waterfall_percentages = [(value / total_revenue) * 100 if value is not None else 0 for value in waterfall_values]

    waterfall_labels = [
        "Revenue",
        "Cost of Revenue",
        "Operational Expenses",
        "Depreciation & Amortization",
        "Financial expenses",
        "Tax"
    ]

    steps = [waterfall_percentages[0]] + [waterfall_percentages[i] - waterfall_percentages[i-1] for i in range(1, len(waterfall_percentages))]

    fig, ax = plt.subplots(figsize=(4, 4), dpi=80)

    plt.subplots_adjust(bottom=0.4)

    running_total = np.cumsum(steps)
    starts = np.hstack((0, running_total[:-1]))

    colors = ['green' if x >= 0 else 'red' for x in steps]

    ax.bar(waterfall_labels, steps, bottom=starts, color=colors, edgecolor='black')

    for i in range(len(steps)):
        ax.text(i, starts[i] + steps[i] / 2, f'{steps[i]:.1f}%', ha='center', va='center', color='white', fontsize=8)

    plt.xticks(rotation=45, ha='right')

    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return fig

def display_waterfall_charts(income_statement_data, years):
    for i, year_data in enumerate(income_statement_data):
        waterfall_chart = generate_waterfall_chart_percentage(year_data)
        
        if waterfall_chart:
            chart_canvas = FigureCanvasTkAgg(waterfall_chart, master=funnel_frame)
            chart_canvas.draw()
            chart_canvas.get_tk_widget().grid(row=0, column=i, padx=10)

def populate_table(symbol):
    for i in table.get_children():
        table.delete(i)

    income_statement_data = fetch_income_statement(symbol)

    if not income_statement_data:
        return

    years = [year_data.period_ending.year for year_data in income_statement_data]

    table["columns"] = ["Characteristic"] + years
    table["show"] = "headings"

    table.heading("Characteristic", text="Characteristic")
    for year in years:
        table.heading(year, text=str(year))

    all_attributes = list(attribute_labels.keys())

    for attribute in all_attributes:
        row = [attribute_labels.get(attribute, attribute)]
        for year_data in income_statement_data:
            value = getattr(year_data, attribute, "N/A")
            row.append(format_number(value))
        table.insert("", "end", values=row)

    for widget in funnel_frame.winfo_children():
        widget.destroy()

    display_waterfall_charts(income_statement_data, years)

def create_app():
    global table, funnel_frame

    root = tk.Tk()
    root.title("Income Statement Dashboard")

    table_frame = ttk.Frame(root)
    table_frame.pack(fill="both", expand=True)

    table = ttk.Treeview(table_frame)
    table.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    scrollbar.pack(side="right", fill="y")
    table.configure(yscroll=scrollbar.set)

    symbol_label = ttk.Label(root, text="Enter Symbol:")
    symbol_label.pack(pady=2)

    symbol_entry = ttk.Entry(root)
    symbol_entry.pack(pady=2)

    load_button = ttk.Button(root, text="Load Data", command=lambda: populate_table(symbol_entry.get()))
    load_button.pack(pady=3)

    exit_button = ttk.Button(root, text="Exit", command=root.quit)
    exit_button.pack(pady=2)

    funnel_frame = ttk.Frame(root)
    funnel_frame.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    create_app()
