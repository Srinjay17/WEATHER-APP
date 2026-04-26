import customtkinter as ctk
import requests
import threading
import webbrowser
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

WEATHER_API = "06c921750b9a82d8f5d1294e1586276f"
NEWS_API = "2f82869df03a479b8266787db397c87b"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class WeatherPulseEliteUltra(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WeatherPulse Pro Dashboard")
        self.geometry("1400x900")
        self.configure(fg_color="#0b1120")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===== SIDEBAR =====
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#020617")
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(self.sidebar, text="⚡ WEATHERPULSE",
                     font=("Arial", 18, "bold"), text_color="#38bdf8").pack(pady=20)

        self.city_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Enter City...", height=40)
        self.city_entry.pack(padx=15, pady=10, fill="x")
        self.city_entry.bind("<Return>", lambda e: self.start_data_fetch())

        self.sync_btn = ctk.CTkButton(self.sidebar, text="🚀 Fetch Data",
                                     command=self.start_data_fetch, fg_color="#2563eb")
        self.sync_btn.pack(padx=15, pady=10, fill="x")

        self.map_btn = ctk.CTkButton(self.sidebar, text="🌍 Live Weather Map",
                                    command=self.open_weather_map, fg_color="#0ea5e9")
        self.map_btn.pack(padx=15, pady=5, fill="x")

        self.map3d_btn = ctk.CTkButton(self.sidebar, text="🌐 3D location",
                                      command=self.open_earth_3d, fg_color="#22c55e")
        self.map3d_btn.pack(padx=15, pady=5, fill="x")

        # ===== MAIN =====
        self.main = ctk.CTkFrame(self, fg_color="#0b1120")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure((0, 1, 2), weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        def create_card(parent, title):
            frame = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=15)
            ctk.CTkLabel(frame, text=title, text_color="#94a3b8").pack(pady=(10, 0))
            value = ctk.CTkLabel(frame, text="--", font=("Arial", 28, "bold"))
            value.pack(pady=(5, 10))
            return frame, value

        self.card_temp, self.temp_main = create_card(self.main, "🌡 Temperature")
        self.card_temp.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.card_weather, self.weather_lbl = create_card(self.main, "☁ Condition")
        self.card_weather.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.card_humidity, self.humidity_lbl = create_card(self.main, "💧 Humidity")
        self.card_humidity.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # ===== INFO BAR =====
        self.info_bar = ctk.CTkFrame(self.main, fg_color="#111827")
        self.info_bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10)

        self.dt_lbl = ctk.CTkLabel(self.info_bar, text="--")
        self.dt_lbl.pack(pady=2)

        self.sun_lbl = ctk.CTkLabel(self.info_bar, text="", text_color="#fbbf24")
        self.sun_lbl.pack(pady=2)

        # ===== LEFT PANEL =====
        self.left_panel = ctk.CTkFrame(self.main, fg_color="#020617")
        self.left_panel.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.left_panel, text="👔 Outfit Advice", text_color="#38bdf8").pack(pady=10)
        self.wardrobe_lbl = ctk.CTkLabel(self.left_panel, text="--", justify="left")
        self.wardrobe_lbl.pack()

        ctk.CTkLabel(self.left_panel, text="🧳 Carry Essentials", text_color="#38bdf8").pack(pady=10)
        self.pack_lbl = ctk.CTkLabel(self.left_panel, text="--", justify="left")
        self.pack_lbl.pack()

        # AIR POLLUTION HEADING
        ctk.CTkLabel(self.left_panel, text="🌫 Air Pollution", text_color="#22c55e").pack(pady=10)

        self.aqi_bar = ctk.CTkProgressBar(self.left_panel, width=180)
        self.aqi_bar.pack()

        self.aqi_label = ctk.CTkLabel(self.left_panel, text="--")
        self.aqi_label.pack()

        self.aqi_quality = ctk.CTkLabel(self.left_panel, text="")
        self.aqi_quality.pack()

        # ===== MIDDLE PANEL =====
        self.middle_panel = ctk.CTkFrame(self.main, fg_color="#020617")
        self.middle_panel.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.middle_panel, text="📈 Temperature Trend", text_color="#22c55e").pack(pady=10)

        self.graph_frame = ctk.CTkFrame(self.middle_panel, fg_color="#111827")
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== RIGHT PANEL =====
        self.right_panel = ctk.CTkScrollableFrame(self.main, label_text="📍 Explore & News", fg_color="#020617")
        self.right_panel.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

    # =========================
    def start_data_fetch(self):
        city = self.city_entry.get().strip() or "Kolkata"
        self.sync_btn.configure(state="disabled", text="Loading...")
        threading.Thread(target=self.fetch_all_data, args=(city,), daemon=True).start()

    def fetch_all_data(self, city):
        try:
            w = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API}&units=metric", timeout=10).json()
            f = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API}&units=metric", timeout=10).json()

            lat, lon = w['coord']['lat'], w['coord']['lon']

            aqi = requests.get(f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_API}", timeout=10).json()

            n = requests.get(f"https://newsapi.org/v2/everything?q={city}&pageSize=5&apiKey={NEWS_API}", timeout=10).json()

            self.after(0, lambda: self.update_ui(w, f, aqi, n, city))

        except Exception as e:
            print("ERROR:", e)

        finally:
            self.after(0, lambda: self.sync_btn.configure(state="normal", text="🚀 Fetch Data"))

    # =========================
    def update_ui(self, w, f, aqi, n, city):

        self.temp_main.configure(text=f"{int(w['main']['temp'])}°C")
        self.weather_lbl.configure(text=w['weather'][0]['main'])
        self.humidity_lbl.configure(text=f"{w['main']['humidity']}%")
        self.dt_lbl.configure(text=datetime.now().strftime('%A, %b %d %Y'))

        # OUTFIT FIX
        temp = w['main']['temp']
        cond = w['weather'][0]['main']

        clothes = []
        if temp > 32:
            clothes = ["Light T-shirt", "Shorts", "Cap", "Sunglasses"]
        elif temp > 25:
            clothes = ["Cotton Shirt", "Jeans", "Sneakers"]
        elif temp > 18:
            clothes = ["Full Shirt", "Light Jacket"]
        else:
            clothes = ["Sweater", "Warm Jacket", "Boots"]

        items = ["Phone", "Wallet", "Charger"]
        if "Rain" in cond:
            items.append("Umbrella")

        self.wardrobe_lbl.configure(text="\n".join(f"• {i}" for i in clothes))
        self.pack_lbl.configure(text="\n".join(f"• {i}" for i in items))

        # AQI FIX
        aqi_val = aqi['list'][0]['main']['aqi']
        self.aqi_bar.set(aqi_val / 5)

        quality_map = {
            1: "Good 😃",
            2: "Fair 🙂",
            3: "Moderate 😐",
            4: "Poor 😷",
            5: "Very Poor ☠️"
        }

        self.aqi_label.configure(text=f"AQI Level: {aqi_val}/5")
        self.aqi_quality.configure(text=quality_map.get(aqi_val, ""))

        # GOLDEN + BLUE HOUR FIX (timezone)
        tz = w['timezone']
        sunrise = datetime.utcfromtimestamp(w['sys']['sunrise'] + tz)
        sunset = datetime.utcfromtimestamp(w['sys']['sunset'] + tz)

        blue_morning = sunrise - timedelta(minutes=30)
        golden_morning = sunrise + timedelta(minutes=30)

        golden_evening = sunset - timedelta(minutes=30)
        blue_evening = sunset + timedelta(minutes=30)

        self.sun_lbl.configure(
            text=f"🌅 Golden: {sunrise.strftime('%H:%M')}–{golden_morning.strftime('%H:%M')} | "
                 f"{golden_evening.strftime('%H:%M')}–{sunset.strftime('%H:%M')}   "
                 f"🔵 Blue: {blue_morning.strftime('%H:%M')}–{sunrise.strftime('%H:%M')} | "
                 f"{sunset.strftime('%H:%M')}–{blue_evening.strftime('%H:%M')}"
        )

        # RIGHT PANEL FIX
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.right_panel, text="📍 Explore Popular Places", text_color="#22c55e").pack(pady=5)

        categories = ["parks", "museums", "temples", "restaurants", "hotels", "tourist places"]

        for cat in categories:
            ctk.CTkButton(
                self.right_panel,
                text=f"{cat.title()} ({city})",
                anchor="w",
                fg_color="#1f2937",
                command=lambda c=cat: webbrowser.open(f"https://www.google.com/search?q=best+{c}+in+{city}")
            ).pack(fill="x", pady=3)

        ctk.CTkLabel(self.right_panel, text="📰 Latest News", text_color="#38bdf8").pack(pady=10)

        for art in n.get("articles", [])[:5]:
            title = art.get("title", "News")
            url = art.get("url")
            if url:
                ctk.CTkButton(
                    self.right_panel,
                    text=title,
                    anchor="w",
                    fg_color="transparent",
                    command=lambda u=url: webbrowser.open(u)
                ).pack(fill="x", pady=2)

        self.draw_graph(f)

    # =========================
    def draw_graph(self, f_data):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        temps = [x['main']['temp'] for x in f_data['list'][:8]]
        times = [x['dt_txt'][11:16] for x in f_data['list'][:8]]

        fig, ax = plt.subplots(figsize=(5, 2))
        ax.plot(times, temps, marker='o')

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def open_weather_map(self):
        city = self.city_entry.get() or "Kolkata"
        webbrowser.open(f"https://www.windy.com/{city}")

    def open_earth_3d(self):
        city = self.city_entry.get() or "Kolkata"
        webbrowser.open(f"https://www.google.com/maps/search/{city}/?hl=en&t=k")


if __name__ == "__main__":
    app = WeatherPulseEliteUltra()
    app.mainloop()