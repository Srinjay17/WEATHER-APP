import os
import sys
import requests
import threading
import webbrowser
import matplotlib.pyplot as plt
import numpy as np
import customtkinter as ctk
import tkintermapview
from datetime import datetime
from PIL import Image, ImageTk
from io import BytesIO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURATION ---
WEATHER_API = "06c921750b9a82d8f5d1294e1586276f"
NEWS_API = "2f82869df03a479b8266787db397c87b"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AQIPulseUltra(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WeatherPulse Elite Ultra | Global Travel & Safety Dashboard")
        self.geometry("1500x950")

        # UI Grid Layout
        self.grid_columnconfigure(0, weight=1)  # Weather & AQI
        self.grid_columnconfigure(1, weight=3)  # Interactive Map
        self.grid_columnconfigure(2, weight=1)  # News & Places
        self.grid_rowconfigure(1, weight=1)

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#111")
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.city_entry = ctk.CTkEntry(self.header, placeholder_text="Enter City Name...", width=300)
        self.city_entry.pack(side="left", padx=20, pady=20)
        self.city_entry.bind("<Return>", lambda e: self.start_data_fetch())

        self.sync_btn = ctk.CTkButton(self.header, text="EXPLORE CITY", fg_color="#2ecc71",
                                      command=self.start_data_fetch)
        self.sync_btn.pack(side="left", padx=10)

        self.dt_lbl = ctk.CTkLabel(self.header, text="-- | --", font=("Arial", 16, "bold"))
        self.dt_lbl.pack(side="right", padx=30)

        # --- LEFT PANEL: WEATHER & AQI ---
        self.left_col = ctk.CTkScrollableFrame(self, label_text="Live Atmosphere")
        self.left_col.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Current Temp Section
        self.temp_icon = ctk.CTkLabel(self.left_col, text="")
        self.temp_icon.pack(pady=5)
        self.temp_lbl = ctk.CTkLabel(self.left_col, text="--°C", font=("Arial", 40, "bold"))
        self.temp_lbl.pack()

        self.aqi_circle = ctk.CTkLabel(self.left_col, text="--", font=("Arial", 60, "bold"))
        self.aqi_circle.pack(pady=10)

        self.status_lbl = ctk.CTkLabel(self.left_col, text="AWAITING SCAN", font=("Arial", 14, "bold"))
        self.status_lbl.pack()

        # 5-Day Forecast Frame
        ctk.CTkLabel(self.left_col, text="5-DAY FORECAST", font=("Arial", 13, "bold"), text_color="#3498db").pack(
            pady=(20, 10))
        self.forecast_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.forecast_frame.pack(fill="x")

        # --- MIDDLE PANEL: INTERACTIVE MAP ---
        self.map_frame = ctk.CTkFrame(self)
        self.map_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=10)

        # Map Widget
        self.map_widget = tkintermapview.TkinterMapView(self.map_frame, corner_radius=15)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga",
                                        max_zoom=22)  # Google Normal

        # Map Controls
        self.map_ctrl = ctk.CTkFrame(self.map_frame, fg_color="#1a1a1a")
        self.map_ctrl.place(relx=0.5, rely=0.05, anchor="n")
        ctk.CTkButton(self.map_ctrl, text="Satellite", width=80, command=lambda: self.map_widget.set_tile_server(
            "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga")).pack(side="left", padx=5)
        ctk.CTkButton(self.map_ctrl, text="Street", width=80, command=lambda: self.map_widget.set_tile_server(
            "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga")).pack(side="left", padx=5)

        # --- RIGHT PANEL: NEWS & PLACES ---
        self.right_col = ctk.CTkScrollableFrame(self, label_text="City Insights")
        self.right_col.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)

        self.news_scroll = ctk.CTkScrollableFrame(self.right_col, height=300, label_text="Top Headlines")
        self.news_scroll.pack(fill="x", pady=10)

        ctk.CTkLabel(self.right_col, text=" DIRECTIONS & PLACES", font=("Arial", 13, "bold"),
                     text_color="#2ecc71").pack(pady=5)
        self.places_frame = ctk.CTkFrame(self.right_col, fg_color="transparent")
        self.places_frame.pack(fill="both", expand=True)

    def start_data_fetch(self):
        city = self.city_entry.get().strip() or "Kolkata"
        self.sync_btn.configure(state="disabled", text="EXPLORING...")
        threading.Thread(target=self.fetch_all_data, args=(city,), daemon=True).start()

    def fetch_all_data(self, city):
        try:
            # 1. Current Weather & Coords
            geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={WEATHER_API}"
            geo = requests.get(geo_url).json()
            if geo.get('cod') != 200: return
            lat, lon = geo['coord']['lat'], geo['coord']['lon']

            # 2. AQI Data
            aqi_res = requests.get(
                f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_API}").json()

            # 3. 5-Day Forecast
            forecast_res = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={WEATHER_API}").json()

            # 4. Local News
            news_res = requests.get(
                f"https://newsapi.org/v2/everything?q={city}&sortBy=publishedAt&pageSize=8&apiKey={NEWS_API}").json()

            self.after(0, lambda: self.update_ui(geo, aqi_res, forecast_res, news_res, city))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.after(0, lambda: self.sync_btn.configure(state="normal", text="EXPLORE CITY"))

    def update_ui(self, weather_data, aqi_data, forecast_data, news_data, city):
        # Update Map
        lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(12)
        self.map_widget.set_marker(lat, lon, text=f"Current Location: {city}")

        # Update Current Temp
        temp = weather_data['main']['temp']
        icon_code = weather_data['weather'][0]['icon']
        self.temp_lbl.configure(text=f"{round(temp)}°C")
        self.set_weather_icon(self.temp_icon, icon_code, size=(80, 80))

        # Update AQI
        aqi_val = aqi_data['list'][0]['main']['aqi']
        aqi_colors = {1: "#2ecc71", 2: "#f1c40f", 3: "#e67e22", 4: "#e74c3c", 5: "#8e44ad"}
        self.aqi_circle.configure(text=str(aqi_val), text_color=aqi_colors.get(aqi_val, "white"))

        # Update Forecast
        self.update_forecast_ui(forecast_data)

        # Update News & Places
        self.refresh_news(news_data)
        self.refresh_places(city, lat, lon)

    def update_forecast_ui(self, data):
        for w in self.forecast_frame.winfo_children(): w.destroy()
        # Filter for mid-day readings (12:00:00)
        daily_data = [item for item in data['list'] if "12:00:00" in item['dt_txt']][:5]

        for day in daily_data:
            f_date = datetime.strptime(day['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%a")
            f_temp = round(day['main']['temp'])
            f_icon = day['weather'][0]['icon']

            row = ctk.CTkFrame(self.forecast_frame, fg_color="#222", corner_radius=8)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f_date, width=50).pack(side="left", padx=10)
            icon_lbl = ctk.CTkLabel(row, text="")
            icon_lbl.pack(side="left")
            self.set_weather_icon(icon_lbl, f_icon, size=(30, 30))
            ctk.CTkLabel(row, text=f"{f_temp}°C", font=("Arial", 12, "bold")).pack(side="right", padx=15)

    def set_weather_icon(self, label_widget, icon_code, size=(50, 50)):
        def download():
            url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
            response = requests.get(url)
            img_data = Image.open(BytesIO(response.content)).resize(size)
            photo = ImageTk.PhotoImage(img_data)
            label_widget.configure(image=photo)
            label_widget.image = photo

        threading.Thread(target=download).start()

    def refresh_news(self, n_data):
        for w in self.news_scroll.winfo_children(): w.destroy()
        for art in n_data.get('articles', []):
            btn = ctk.CTkButton(self.news_scroll, text=f"• {art['title'][:60]}...",
                                anchor="w", fg_color="transparent", font=("Arial", 11),
                                command=lambda u=art['url']: webbrowser.open(u))
            btn.pack(fill="x", pady=1)

    def refresh_places(self, city, lat, lon):
        for w in self.places_frame.winfo_children(): w.destroy()
        categories = ["Restaurants", "Gas Stations", "Hotels", "Hospitals"]

        for cat in categories:
            btn = ctk.CTkButton(self.places_frame, text=f" Find {cat}",
                                fg_color="#27ae60", hover_color="#2ecc71",
                                command=lambda c=cat: self.find_on_map(c, city))
            btn.pack(fill="x", pady=5)

        # "Get Directions" Button
        ctk.CTkButton(self.places_frame, text=" GET DIRECTIONS (Google Maps)",
                      fg_color="#3498db", command=lambda: webbrowser.open(
                f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}")).pack(fill="x", pady=20)

    def find_on_map(self, query, city):
        # In a real app, you'd use a Places API to add markers. Here we open the web view.
        webbrowser.open(f"https://www.google.com/maps/search/{query}+in+{city}")


if __name__ == "__main__":
    app = AQIPulseUltra()
    app.mainloop()