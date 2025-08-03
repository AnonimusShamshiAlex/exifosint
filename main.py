import subprocess
import re
import requests
import webbrowser
import os
import shutil
import time
from tkinter import Tk, Button, Label, filedialog, messagebox
from PIL import Image

def convert_to_decimal(line):
    """Преобразует GPS-координаты из формата 'X deg Y' Z" N/S/E/W' в десятичные."""
    match = re.search(r': ([0-9.]+) deg(?: ([0-9.]+)\')?(?: ([0-9.]+)")? ([NSEW])', line)
    if not match:
        return None
    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees)
    if minutes:
        decimal += float(minutes) / 60
    if seconds:
        decimal += float(seconds) / 3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

def get_gps_info(path):
    """Извлекает GPS-координаты из EXIF-данных изображения."""
    if not shutil.which('exiftool'):
        messagebox.showerror("Ошибка", "exiftool не установлен. Установите его с https://exiftool.org/")
        return None, None

    if not path.lower().endswith(('.jpg', '.jpeg')):
        messagebox.showerror("Ошибка", "Поддерживаются только JPEG-файлы.")
        return None, None

    try:
        output = subprocess.check_output(['exiftool', os.path.normpath(path)], stderr=subprocess.STDOUT).decode()
        lat, lon = None, None
        for line in output.split('\n'):
            if "GPS Latitude" in line and "Ref" not in line:
                lat = convert_to_decimal(line)
            elif "GPS Longitude" in line and "Ref" not in line:
                lon = convert_to_decimal(line)
        if not lat or not lon:
            messagebox.showwarning("Нет GPS", "GPS-данные не найдены в файле.")
            return None, None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            messagebox.showerror("Ошибка", "Некорректные GPS-координаты.")
            return None, None
        return lat, lon
    except subprocess.CalledProcessError:
        messagebox.showerror("Ошибка", "Не удалось извлечь EXIF-данные. Проверьте файл.")
        return None, None
    except FileNotFoundError:
        messagebox.showerror("Ошибка", "exiftool не найден.")
        return None, None
    except UnicodeDecodeError:
        messagebox.showerror("Ошибка", "Ошибка декодирования данных EXIF.")
        return None, None

def reverse_geocode(lat, lon):
    """Получает адрес по GPS-координатам через Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {'format': 'json', 'lat': lat, 'lon': lon, 'zoom': 18, 'addressdetails': 1}
        headers = {'User-Agent': 'KaliPhotoGPS/1.0 (your_email@example.com)'}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        time.sleep(1)  # Задержка для соблюдения лимитов Nominatim
        return response.json().get("address", {})
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}")
        return None
    except ValueError:
        messagebox.showerror("Ошибка", "Не удалось обработать ответ от сервера.")
        return None

def show_result(lat, lon, address):
    """Отображает адрес и открывает карту."""
    lines = []
    if "country" in address:
        lines.append(f"🌍 Страна: {address.get('country')}")
    if "state" in address:
        lines.append(f"🏞️ Регион: {address.get('state')}")
    if "city" in address or "town" in address or "village" in address:
        lines.append(f"🏙️ Город: {address.get('city') or address.get('town') or address.get('village')}")
    if "road" in address:
        lines.append(f"🛣️ Улица: {address.get('road')}")
    if not lines:
        lines.append("ℹ️ Адрес не удалось определить подробно.")
    
    map_link = f"https://www.google.com/maps?q={lat},{lon}"
    lines.append(f"🗺️ Карта: {map_link}")
    messagebox.showinfo("Адрес", "\n".join(lines))
    webbrowser.open(map_link)

def select_file():
    """Открывает диалог выбора файла и обрабатывает его."""
    path = filedialog.askopenfilename(title="Выберите фото", filetypes=[("Images", "*.jpg *.jpeg")])
    if not path:
        return

    try:
        Image.open(path).close()  # Проверяем, что файл — изображение
    except Exception:
        messagebox.showerror("Ошибка", "Файл не является изображением.")
        return

    root.config(cursor="wait")  # Индикатор загрузки
    lat, lon = get_gps_info(path)
    root.config(cursor="")  # Снимаем индикатор
    if not lat or not lon:
        return

    address = reverse_geocode(lat, lon)
    if not address:
        return

    show_result(lat, lon, address)

# --- GUI ---
root = Tk()
root.title("Место по фото")
root.geometry("300x160")
root.minsize(300, 160)  # Минимальный размер окна
root.bind('<Escape>', lambda e: root.quit())  # Закрытие по Esc

label = Label(root, text="Выберите фото с GPS", font=("Arial", 12))
label.pack(pady=20)

btn = Button(root, text="Открыть фото", command=select_file)
btn.pack()

btn_exit = Button(root, text="Выход", command=root.quit)
btn_exit.pack(pady=10)

root.mainloop()
