import requests
import numpy as np
import schedule
import time

# ======= API Keys =======
OPENWEATHER_API_KEY = "67fd1958779a651e2031cffc0c5b0de6"
WEATHERAPI_KEY = "bb964397a15b44b692b150529251204"
WEATHERSTACK_KEY = "5a48ff964a1ed5a37b6128d519095b79"

# ======= API Fetch Functions =======
def get_openweather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        return requests.get(url).json()
    except Exception as e:
        print("OpenWeather error:", e)
        return {}

def get_weatherapi(city):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city}"
    try:
        return requests.get(url).json()
    except Exception as e:
        print("WeatherAPI error:", e)
        return {}

def get_weatherstack(city):
    url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_KEY}&query={city}"
    try:
        return requests.get(url).json()
    except Exception as e:
        print("WeatherStack error:", e)
        return {}

# ======= Normalize Temperatures =======
def normalize_data(data_sources):
    temp_values = []
    for data in data_sources:
        try:
            if 'main' in data:
                temp_values.append(data['main']['temp'])  # OpenWeather
            elif 'current' in data and 'temp_c' in data['current']:
                temp_values.append(data['current']['temp_c'])  # WeatherAPI
            elif 'current' in data and 'temperature' in data['current']:
                temp_values.append(data['current']['temperature'])  # WeatherStack
        except:
            continue
    return temp_values

# ======= AI-based Merging (Outlier Filter) =======
def ai_merge_temperature(temp_list):
    if not temp_list:
        return "N/A"
    temp_arr = np.array(temp_list)
    mean = np.mean(temp_arr)
    std = np.std(temp_arr)
    filtered = temp_arr[np.abs(temp_arr - mean) <= 1.5 * std]  # remove outliers
    if len(filtered) == 0:
        return round(mean, 2)
    return round(np.mean(filtered), 2)

# ======= Weather Fetch and Display =======
def fetch_and_display(city="London"):
    data1 = get_openweather(city)
    data2 = get_weatherapi(city)
    data3 = get_weatherstack(city)

    temps = normalize_data([data1, data2, data3])
    merged_temp = ai_merge_temperature(temps)

    print(f"🌦️ Weather in {city}: {merged_temp}°C (merged from {len(temps)} sources)")

# ======= Scheduler (every 10 minutes) =======
def start_scheduler(city="London"):
    fetch_and_display(city)
    schedule.every(10).minutes.do(lambda: fetch_and_display(city))
    while True:
        schedule.run_pending()
        time.sleep(1)

# ======= Optional Streamlit UI =======
# def run_ui():
#     import streamlit as st
#     st.title("🌍 Real-Time Weather Aggregator")
#     city = st.text_input("Enter City", "London")

#     if st.button("Get Weather"):
#         data1 = get_openweather(city)
#         data2 = get_weatherapi(city)
#         data3 = get_weatherstack(city)
#         temps = normalize_data([data1, data2, data3])
#         merged_temp = ai_merge_temperature(temps)
#         st.success(f"🌤 {city}: {merged_temp}°C (from {len(temps)} sources)")
def run_ui():
    import streamlit as st
    import datetime

    st.set_page_config(page_title="🌤️ Weather App", page_icon="🌦️", layout="centered")

    # Dark mode support + white card fix
    st.markdown("""
        <style>
        .main {
            background-color: #0f1117;
            font-family: 'Segoe UI', sans-serif;
        }
        .weather-box {
            background-color: #ffffff;
            border-radius: 20px;
            padding: 30px;
            margin-top: 30px;
            text-align: center;
            box-shadow: 0 0 20px rgba(255,255,255,0.05);
            color: #000000;
        }
        .temperature {
            font-size: 50px;
            font-weight: bold;
            margin: 10px 0;
        }
        .city {
            font-size: 32px;
            font-weight: 600;
        }
        .weather-details {
            font-size: 18px;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🌦️ Real-Time Weather App")

    city = st.text_input("🔍 Enter City Name", "London")

    if st.button("Get Weather"):
        data1 = get_openweather(city)
        data2 = get_weatherapi(city)
        data3 = get_weatherstack(city)

        temps = normalize_data([data1, data2, data3])
        merged_temp = ai_merge_temperature(temps)

        if merged_temp == "N/A":
            st.error("❌ Could not fetch data. Please try again.")
            return

        # Extract more details from OpenWeatherMap (first fallback)
        humidity = wind = "-"
        weather_icon = "🌦️"
        if data1 and data1.get("main"):
            humidity = data1["main"].get("humidity", "-")
            wind = data1["wind"].get("speed", "-")

            main_desc = data1["weather"][0]["main"].lower()
            if "clear" in main_desc:
                weather_icon = "☀️"
            elif "cloud" in main_desc:
                weather_icon = "⛅"
            elif "rain" in main_desc:
                weather_icon = "🌧️"
            elif "snow" in main_desc:
                weather_icon = "❄️"
            elif "storm" in main_desc:
                weather_icon = "⛈️"

        st.markdown(f"""
            <div class="weather-box">
                <div class="city">{city.title()} {weather_icon}</div>
                <div class="temperature">{merged_temp}°C</div>
                <div class="weather-details">
                    💧 Humidity: {humidity}%<br>
                    🌬️ Wind: {wind} m/s<br>
                    📅 {datetime.datetime.now().strftime('%A, %d %B %Y - %I:%M %p')}
                </div>
                <div style="margin-top: 10px; font-size: 14px; color: #444;">
                    Data aggregated from {len(temps)} weather services.
                </div>
            </div>
        """, unsafe_allow_html=True)

# ======= Entry Point =======
if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "cli"

    if mode == "cli":
        city = input("Enter a city: ") or "London"
        start_scheduler(city)
    elif mode == "ui":
        run_ui()
