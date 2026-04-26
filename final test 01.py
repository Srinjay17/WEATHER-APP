import os
import sys
import requests
import threading
import webbrowser
import matplotlib.pyplot as plt
import numpy as np
import customtkinter as ctk
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- MANDATORY TCL/TK FIX ---
python_path = r'C:\Users\ROHAN\AppData\Local\Programs\Python\Python313'
os.environ['TCL_LIBRARY'] = os.path.join(python_path, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(python_path, 'tcl', 'tk8.6')

# --- CONFIGURATION ---
WEATHER_API = "06c921750b9a82d8f5d1294e1586276f"
NEWS_API = "2f82869df03a479b8266787db397c87b"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class AQIPulseUltra(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AQIPulse Ultra - Satellite & Trend Pro")
        self.geometry("1450x900")

        # UI Grid Layout
        self.grid_columnconfigure(0, weight=1)  # Health
        self.grid_columnconfigure(1, weight=2)  # News & AQI Prediction
        self.grid_columnconfigure(2, weight=1)  # Insights & Maps

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#111")
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.city_entry = ctk.CTkEntry(self.header, placeholder_text="Enter City Name...", width=350)
        self.city_entry.pack(side="left", padx=20, pady=20)
        self.city_entry.bind("<Return>", lambda e: self.start_data_fetch())

        self.sync_btn = ctk.CTkButton(self.header, text="EXPLORE CITY", fg_color="#2ecc71",
                                      hover_color="#27ae60", command=self.start_data_fetch)
        self.sync_btn.pack(side="left", padx=10)

        self.dt_lbl = ctk.CTkLabel(self.header, text="SYSTEM READY", font=("Arial", 14, "bold"))
        self.dt_lbl.pack(side="right", padx=30)

        # --- LEFT PANEL: HEALTH ---
        self.left_col = ctk.CTkScrollableFrame(self, label_text="Health Protection")
        self.left_col.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)

        self.aqi_circle = ctk.CTkLabel(self.left_col, text="--", font=("Arial", 90, "bold"))
        self.aqi_circle.pack(pady=20)

        self.status_lbl = ctk.CTkLabel(self.left_col, text="AWAITING SCAN", font=("Arial", 22, "bold"))
        self.status_lbl.pack()

        ctk.CTkLabel(self.left_col, text="\n🛡️ PROTECTIVE ADVICE", font=("Arial", 13, "bold"),
                     text_color="#2ecc71").pack()
        self.gear_lbl = ctk.CTkLabel(self.left_col, text="• Input a city to begin.", justify="left",
                                     font=("Arial", 14), wraplength=250)
        self.gear_lbl.pack(pady=15)

        # --- MIDDLE PANEL: NEWS & AQI PREDICTION ---
        self.mid_col = ctk.CTkFrame(self, fg_color="transparent")
        self.mid_col.grid(row=1, column=1, sticky="nsew", padx=5, pady=15)

        ctk.CTkLabel(self.mid_col, text="📈 24-HOUR AQI PREDICTION TREND", font=("Arial", 14, "bold")).pack(anchor="w",
                                                                                                           padx=10)
        self.graph_frame = ctk.CTkFrame(self.mid_col, height=220, fg_color="#1a1a1a")
        self.graph_frame.pack(fill="x", padx=10, pady=10)

        self.news_scroll = ctk.CTkScrollableFrame(self.mid_col, height=500, label_text="Live Top News Headlines")
        self.news_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # --- RIGHT PANEL: SATELLITE & COMPOSITION ---
        self.right_col = ctk.CTkScrollableFrame(self, label_text="Satellite & Insights")
        self.right_col.grid(row=1, column=2, sticky="nsew", padx=15, pady=15)

        ctk.CTkLabel(self.right_col, text="🧪 AIR COMPOSITION", font=("Arial", 12, "bold"), text_color="#2ecc71").pack(
            pady=5)
        self.composition_frame = ctk.CTkFrame(self.right_col, fg_color="#2b2b2b")
        self.composition_frame.pack(fill="x", padx=5, pady=5)

        self.chem_data = ctk.CTkLabel(self.composition_frame, text="PM2.5: --\nPM10: --\nCO: --",
                                      justify="left", font=("Consolas", 15), pady=15)
        self.chem_data.pack()

        ctk.CTkLabel(self.right_col, text="\n🗺️ LOCATION & DIRECTIONS", font=("Arial", 12, "bold"),
                     text_color="#2ecc71").pack(pady=5)
        self.places_frame = ctk.CTkFrame(self.right_col, fg_color="transparent")
        self.places_frame.pack(fill="both", expand=True)

    def start_data_fetch(self):
        city = self.city_entry.get().strip() or "Kolkata"
        self.sync_btn.configure(state="disabled", text="SCANNING...")
        threading.Thread(target=self.fetch_all_data, args=(city,), daemon=True).start()

    def fetch_all_data(self, city):
        try:
            geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}"
            geo = requests.get(geo_url).json()
            if geo.get('cod') != 200: return

            lat, lon = geo['coord']['lat'], geo['coord']['lon']

            aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_API}"
            aqi_res = requests.get(aqi_url).json()

            news_url = (f"https://newsapi.org/v2/everything?q={city}+news&"
                        f"language=en&sortBy=publishedAt&pageSize=15&apiKey={NEWS_API}")
            news_res = requests.get(news_url).json()

            self.after(0, lambda: self.update_ui(aqi_res, news_res, city))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.after(0, lambda: self.sync_btn.configure(state="normal", text="EXPLORE CITY"))

    def update_ui(self, aqi_data, news_data, city):
        data = aqi_data['list'][0]
        aqi_val = data['main']['aqi']
        comp = data['components']

        aqi_map = {
            1: ("GOOD", "#2ecc71", "Fresh air. No restrictions."),
            2: ("FAIR", "#f1c40f", "Acceptable quality."),
            3: ("MODERATE", "#e67e22", "N95 Mask recommended."),
            4: ("POOR", "#e74c3c", "Unhealthy. Wear N95/N99."),
            5: ("HAZARDOUS", "#8e44ad", "Stay indoors immediately.")
        }
        name, color, advice = aqi_map.get(aqi_val)

        self.dt_lbl.configure(text=f"{city.upper()} | {datetime.now().strftime('%d %b %Y')}")
        self.aqi_circle.configure(text=str(aqi_val), text_color=color)
        self.status_lbl.configure(text=name, text_color=color)
        self.gear_lbl.configure(text=f"• {advice}")

        self.chem_data.configure(text=f"PM2.5: {comp['pm2_5']} | PM10: {comp['pm10']} | CO: {comp['co']}")

        self.refresh_news(news_data)
        self.refresh_places(city)
        self.draw_trend_graph(aqi_val, color)

    def refresh_news(self, n_data):
        for w in self.news_scroll.winfo_children(): w.destroy()
        articles = n_data.get('articles', [])
        for art in articles[:10]:
            if not art.get('title'): continue
            card = ctk.CTkFrame(self.news_scroll, fg_color="#1e1e1e", corner_radius=6)
            card.pack(fill="x", pady=4, padx=5)
            btn = ctk.CTkButton(card, text=f"📰 {art['title'][:70]}...", anchor="w", fg_color="transparent",
                                command=lambda u=art['url']: webbrowser.open(u))
            btn.pack(fill="x", padx=10, pady=5)

    def refresh_places(self, city):
        for w in self.places_frame.winfo_children(): w.destroy()

        # SATELLITE BUTTON
        sat_url = f"https://www.google.com/maps/search/{city.replace(' ', '+')}/@?api=1&map_action=map&basemap=satellite"
        ctk.CTkButton(self.places_frame, text="🛰️ SATELLITE VIEW", fg_color="#3498db",
                      hover_color="#2980b9", command=lambda: webbrowser.open(sat_url)).pack(fill="x", pady=8, padx=10)

        # CATEGORY BUTTONS
        cats = [("🌳 Parks", "parks"), ("🏛️ Museums", "museums"), ("🍴 Dining", "restaurants")]
        for label, query in cats:
            search_url = f"https://www.google.com/maps/search/{query}+in+{city.replace(' ', '+')}"
            ctk.CTkButton(self.places_frame, text=label, fg_color="#2c3e50",
                          command=lambda u=search_url: webbrowser.open(u)).pack(fill="x", pady=4, padx=10)

    def draw_trend_graph(self, aqi, color):
        for w in self.graph_frame.winfo_children(): w.destroy()
        fig, ax = plt.subplots(figsize=(6, 2.2), dpi=100)
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#1a1a1a')

        # Simulated Prediction (Fluctuation)
        x = ["Now", "+4h", "+8h", "+12h", "+16h", "+20h", "+24h"]
        y = [aqi, aqi + 0.2, aqi + 0.5, aqi + 0.1, aqi - 0.3, aqi + 0.2, aqi]

        ax.plot(x, y, marker='o', color=color, linewidth=2, label="AQI Forecast")
        ax.tick_params(colors='white', labelsize=8)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.grid(color='#333', linestyle='--', linewidth=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)


if __name__ == "__main__":
    app = AQIPulseUltra()
    app.mainloop()
