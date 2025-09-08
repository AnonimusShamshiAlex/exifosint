import subprocess
import re
import requests
import webbrowser
from tkinter import Tk, Button, Label, filedialog, messagebox
from PIL import Image

def convert_to_decimal(line):
    match = re.search(r': ([0-9.]+) deg ([0-9.]+)\' ([0-9.]+)" ([NSEW])', line)
    if not match:
        return None
    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def get_gps_info(path):
    try:
        output = subprocess.check_output(['exiftool', path]).decode()
        lat, lon = None, None
        for line in output.split('\n'):
            if "GPS Latitude" in line and "Ref" not in line:
                lat = convert_to_decimal(line)
            elif "GPS Longitude" in line and "Ref" not in line:
                lon = convert_to_decimal(line)
        return lat, lon
    except:
        return None, None

def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lon,
            'zoom': 18,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'KaliPhotoGPS/1.0 (your_email@example.com)'  # Nominatim требует user-agent
        }
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        address = data.get("address", {})
        return address
    except Exception as e:
        return None

def show_result(lat, lon, address):
    lines = []
    if "country" in address:
        lines.append(f"🌍 Страна: {address.get('country')}")
    if "state" in address:
        lines.append(f"🏞️ Регион: {address.get('state')}")
    if "city" in address or "town" in address or "village" in address:
        lines.append(f"🏙️ Город: {address.get('city') or address.get('town') or address.get('village')}")
    if "road" in address:
        lines.append(f"🛣️ Улица: {address.get('road')}")

    map_link = f"https://www.google.com/maps?q={lat},{lon}"
    lines.append(f"🗺️ Карта: {map_link}")
    messagebox.showinfo("Адрес", "\n".join(lines))
    webbrowser.open(map_link)

def select_file():
    path = filedialog.askopenfilename(title="Выберите фото", filetypes=[("Images", "*.jpg *.jpeg *.png")])
    if not path:
        return

    try:
        Image.open(path)
    except:
        messagebox.showerror("Ошибка", "Файл не является изображением.")
        return

    lat, lon = get_gps_info(path)
    if not lat or not lon:
        messagebox.showwarning("Нет GPS", "GPS-данные не найдены.")
        return

    address = reverse_geocode(lat, lon)
    if not address:
        messagebox.showwarning("Ошибка", "Не удалось определить адрес.")
        return

    show_result(lat, lon, address)

# --- GUI ---
root = Tk()
root.title("Место по фото")
root.geometry("300x160")

label = Label(root, text="Выберите фото с GPS", font=("Arial", 12))
label.pack(pady=20)

btn = Button(root, text="Открыть фото", command=select_file)
btn.pack()

root.mainloop()
