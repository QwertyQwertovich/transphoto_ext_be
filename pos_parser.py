import os
import requests
import time
import threading
import json
import csv
from collections import defaultdict
from zipfile import ZipFile

GTFS_URL = 'https://transport.orgp.spb.ru/Portal/transport/internalapi/gtfs/feed.zip'
VEHICLE_POSITIONS_URL = 'https://portal.gpt.adc.spb.ru/Portal/transport/internalapi/vehicles/positions/?transports=bus%2Ctrolley%2Ctram%2Cship&bbox=28.00%2C59.00%2C33.00%2C61.00'
LOCAL_ZIP_PATH = 'path/to/download/feed.zip'
EXTRACT_PATH = 'gtfs'
ROUTES_FILE = os.path.join(EXTRACT_PATH, 'routes.txt')
VEHICLE_POSITIONS_FILE = 'vehicle_positions.json'

def download_and_extract_gtfs():
    try:
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(LOCAL_ZIP_PATH), exist_ok=True)

        # Скачиваем файл с игнорированием проверки сертификата
        response = requests.get(GTFS_URL, verify=False)
        response.raise_for_status()  # Проверяем успешность запроса
        with open(LOCAL_ZIP_PATH, 'wb') as file:
            file.write(response.content)

        # Распаковываем файл
        with ZipFile(LOCAL_ZIP_PATH, 'r') as zip_ref:
            os.makedirs(EXTRACT_PATH, exist_ok=True)
            zip_ref.extractall(EXTRACT_PATH)

        print(f'GTFS data downloaded and extracted to {EXTRACT_PATH}')
    except requests.exceptions.RequestException as e:
        print(f'Failed to download GTFS data: {e}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
    finally:
        # Удаляем скачанный zip-файл, если он существует
        if os.path.exists(LOCAL_ZIP_PATH):
            os.remove(LOCAL_ZIP_PATH)

def load_routes():
    routes = {}
    try:
        with open(ROUTES_FILE, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                routes[row['route_id']] = row
        print('Routes data loaded successfully.')
    except FileNotFoundError:
        print(f'File {ROUTES_FILE} not found.')
    except Exception as e:
        print(f'An unexpected error occurred while loading routes: {e}')
    return routes

def download_vehicle_positions(routes, previous_positions):
    try:
        # Скачиваем данные с игнорированием проверки сертификата
        response = requests.get(VEHICLE_POSITIONS_URL, verify=False)
        response.raise_for_status()  # Проверяем успешность запроса

        current_positions = response.json()['result']

        # Объединяем новые данные с предыдущими
        updated_positions = {vehicle['vehicleId']: vehicle for vehicle in previous_positions.values()}
        for vehicle in current_positions:
            vehicle_id = vehicle['vehicleId']
            updated_positions[vehicle_id] = vehicle

            # Добавляем данные о маршруте
            route_id = vehicle['routeId']
            if route_id in routes:
                vehicle['routeInfo'] = routes[route_id]

        # Сохраняем данные в файл
        with open(VEHICLE_POSITIONS_FILE, 'w', encoding='utf-8') as file:
            json.dump(list(updated_positions.values()), file, ensure_ascii=False, indent=4)

        print(f'Vehicle positions data updated and saved to {VEHICLE_POSITIONS_FILE}')
        return updated_positions
    except requests.exceptions.RequestException as e:
        print(f'Failed to download vehicle positions data: {e}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
    return previous_positions

def schedule_task(interval, task, *args):
    def wrapper():
        while True:
            task(*args)
            time.sleep(interval)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()

# Инициализируем предыдущие позиции
previous_positions = {}

# Планируем задачу каждые 10 секунд
schedule_task(20, download_vehicle_positions, load_routes(), previous_positions)

# Планируем задачу каждый час (3600 секунд) для скачивания и распаковки GTFS
schedule_task(3600, download_and_extract_gtfs)

print('Scheduler started. Waiting for the next run...')

# Запускаем бесконечный цикл для поддержания основной программы
while True:
    time.sleep(1)
