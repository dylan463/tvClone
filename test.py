import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import mplfinance as mpf

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gold/USD Trading Chart")
        self.root.geometry("1200x700")
        
        # Create frame for header
        header_frame = tk.Frame(root, bg="#f0f0f0", height=50)
        header_frame.pack(fill=tk.X)
        
        # Trading pair info
        pair_label = tk.Label(header_frame, text="Or / Dollar Américain • 15 • OANDA", font=("Arial", 12, "bold"), bg="#f0f0f0")
        pair_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Price info
        price_info = tk.Label(header_frame, 
                             text="O 2,905.410  H 2,906.145  B 2,904.945  C 2,904.970  -0.495 (-0.02%)", 
                             font=("Arial", 11), bg="#f0f0f0")
        price_info.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Create trade buttons frame
        buttons_frame = tk.Frame(root, bg="white", height=40)
        buttons_frame.pack(fill=tk.X)
        
        # Sell button
        sell_button = tk.Button(buttons_frame, text="SELL\n2,904.750", bg="#ff4d4d", fg="white", 
                               font=("Arial", 10, "bold"), width=12, height=2)
        sell_button.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Buy button
        buy_button = tk.Button(buttons_frame, text="BUY\n2,905.210", bg="#4d79ff", fg="white", 
                              font=("Arial", 10, "bold"), width=12, height=2)
        buy_button.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Session info
        session_frame = tk.Frame(root, bg="white")
        session_frame.pack(fill=tk.X)
        
        session_label1 = tk.Label(session_frame, text="KZ Boxes 0330-0545 0830-1045 5", bg="white")
        session_label1.pack(anchor=tk.W, padx=10, pady=2)
        
        session_label2 = tk.Label(session_frame, text="AsiaSessionHighLowMidLines 1800-0200 sol 1 sol 1", bg="white")
        session_label2.pack(anchor=tk.W, padx=10, pady=2)
        
        # Create main chart
        self.create_chart()
        
        # Create bottom time labels
        time_frame = tk.Frame(root)
        time_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        times = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", 
                "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00", 
                "7", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00"]
        
        for t in times:
            time_label = tk.Label(time_frame, text=t, width=4)
            time_label.pack(side=tk.LEFT)
            
        # Add TradingView logo
        logo_label = tk.Label(time_frame, text="TradingView", font=("Arial", 10, "bold"))
        logo_label.pack(side=tk.LEFT, padx=20)
    
    def create_chart(self):
        # Create frame for chart
        chart_frame = tk.Frame(self.root)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create matplotlib figure for the candlestick chart
        fig, ax = plt.subplots(figsize=(12, 5), dpi=100)
        
        # Generate sample price data
        np.random.seed(42)  # For reproducible results
        dates = pd.date_range(start="2023-01-01", periods=100, freq="15min")
        
        # Starting price around 2900
        base_price = 2900
        price_range = 50
        
        opens = [base_price + np.random.normal(0, price_range/10)]
        highs = [opens[0] + abs(np.random.normal(0, price_range/15))]
        lows = [opens[0] - abs(np.random.normal(0, price_range/15))]
        closes = [opens[0] + np.random.normal(0, price_range/10)]
        
        # Generate rest of the prices with some trend and volatility
        for i in range(1, len(dates)):
            prev_close = closes[i-1]
            price_change = np.random.normal(0, price_range/20)
            if i % 20 < 10:  # Create some trend
                price_change += 0.5
            else:
                price_change -= 0.5
                
            open_price = prev_close
            close_price = open_price + price_change
            high_price = max(open_price, close_price) + abs(np.random.normal(0, price_range/30))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, price_range/30))
            
            opens.append(open_price)
            highs.append(high_price)
            lows.append(low_price)
            closes.append(close_price)
        
        # Create DataFrame for mplfinance
        ohlc_data = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes
        }, index=dates)
        
        # Plot with mplfinance
        mpf.plot(ohlc_data, type='candle', style='yahoo', ax=ax, 
                volume=False, show_nontrading=False,
                uptick_color='white', downtick_color='black',
                edgecolor='black')
        
        # Customize the chart
        ax.grid(True, alpha=0.3)
        ax.set_ylabel('Price')
        ax.get_xaxis().set_visible(False)  # Hide x-axis dates (we'll add our own)
        
        # Add price axis on the right
        price_labels = np.arange(2850, 2951, 10)
        ax2 = ax.twinx()
        ax2.set_ylim(ax.get_ylim())
        ax2.set_yticks(price_labels)
        ax2.set_yticklabels([f"{p:,.0f}" for p in price_labels])
        
        # Add current price indicator
        current_price = 2904.97
        ax.axhline(y=current_price, color='r', linestyle='-', alpha=0.5)
        
        # Add current price label
        ax.text(len(dates) - 5, current_price, f"2,904.970\n11:26", 
                color='white', fontweight='bold', 
                bbox=dict(facecolor='red', alpha=0.8, boxstyle='round,pad=0.5'))
        
        # Embed the matplotlib figure in tkinter
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()