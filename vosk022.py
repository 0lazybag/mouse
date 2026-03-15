import os
import sys
import queue
import sounddevice as sd
import json
import keyboard
import time
import logging
import ctypes
from vosk import Model, KaldiRecognizer, SetLogLevel

# Отключаем внутренние логи Vosk
SetLogLevel(-1)

# НАСТРОЙКИ
ИМЯ_МОДЕЛИ = "vosk-model-ru-0.22"
ЧАСТОТА = 16000
ОЧЕРЕДЬ = queue.Queue()

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk_log.txt")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)

def скрыть_консоль():
    """Скрывает окно терминала."""
    окно = ctypes.windll.kernel32.GetConsoleWindow()
    if окно != 0:
        ctypes.windll.user32.ShowWindow(окно, 0)

def messagebox(заголовок, текст):
    ctypes.windll.user32.MessageBoxW(0, текст, заголовок, 0x10)

def выбрать_устройство():
    """Выводит список и просит ввести ID."""
    список_устройств = sd.query_devices()
    print("\n--- ДОСТУПНЫЕ УСТРОЙСТВА ВВОДА ---")
    
    допустимые_айди = []
    for индекс, устройство in enumerate(список_устройств):
        if устройство['max_input_channels'] > 0:
            допустимые_айди.append(индекс)
            метка = "[Bluetooth/Гарнитура]" if any(к in устройство['name'].lower() for к in ["bluetooth", "bowie", "головной"]) else ""
            print(f"ID: {индекс} | {устройство['name']} {метка}")
    
    while True:
        выбор = input("\nВведите ID нужного микрофона: ").strip()
        if выбор.isdigit() and int(выбор) in допустимые_айди:
            return int(выбор)
        print("Ошибка: Введите корректный ID из списка выше.")

def обратный_вызов_аудио(данные, кадры, время, статус):
    if статус:
        logging.error(f"Ошибка аудио: {статус}")
    ОЧЕРЕДЬ.put(bytes(данные))

if __name__ == "__main__":
    # Сначала выбираем устройство, пока консоль видна
    айди_микрофона = выбрать_устройство()
    
    полный_путь_модели = r"D:\VoskModels\vosk-model-ru-0.22"

    if not os.path.exists(полный_путь_модели):
        messagebox("Ошибка Vosk", f"Модель не найдена: {полный_путь_модели}")
        sys.exit(1)

    try:
        print("Загрузка модели... Подождите.")
        модель = Model(полный_путь_модели)
        распознаватель = KaldiRecognizer(модель, ЧАСТОТА)

        # Подключаемся к потоку
        стрим = sd.RawInputStream(samplerate=ЧАСТОТА, blocksize=4000, 
                                  device=айди_микрофона, dtype='int16', 
                                  channels=1, callback=обратный_вызов_аудио)
        
        with стрим:
            logging.info(f"Старт записи с устройства {айди_микрофона}")
            print(f"Подключено к ID {айди_микрофона}. Консоль скрывается...")
            time.sleep(1) # Даем секунду прочитать сообщение
            
            скрыть_консоль()

            while True:
                данные = ОЧЕРЕДЬ.get()
                if распознаватель.AcceptWaveform(данные):
                    результат = json.loads(распознаватель.Result())
                    текст = результат.get("text", "")
                    
                    if текст:
                        if "выход" in текст.lower():
                            break
                        
                        keyboard.write(текст + " ")
                        time.sleep(0.05)

    except Exception as ошибка:
        logging.critical(f"Ошибка: {ошибка}")
        # Если консоль скрыта, выводим ошибку через MessageBox
        messagebox("Критическая ошибка", str(ошибка))
        sys.exit(1)