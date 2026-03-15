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

# Отключаем внутренние логи Vosk, чтобы не нагружать систему записью
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

def messagebox(title, text):
    ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)

def обратный_вызов_аудио(данные, кадры, время, статус):
    if статус:
        logging.error(f"Ошибка аудио: {статус}")
    ОЧЕРЕДЬ.put(bytes(данные))

if __name__ == "__main__":
    полный_путь_модели = r"D:\VoskModels\vosk-model-ru-0.22"

    if not os.path.exists(полный_путь_модели):
        messagebox("Ошибка Vosk", f"Модель не найдена: {полный_путь_модели}")
        sys.exit(1)

    try:
        logging.info("Загрузка модели...")
        модель = Model(полный_путь_модели)
        # Оптимизация: распознаватель создается один раз
        распознаватель = KaldiRecognizer(модель, ЧАСТОТА)

        айди_микрофона = 12 

        with sd.RawInputStream(samplerate=ЧАСТОТА, blocksize=4000, # Уменьшил блок для плавности
                               device=айди_микрофона, dtype='int16', 
                               channels=1, callback=обратный_вызов_аудио):
            
            logging.info("Система активна (CPU Mode)")

            while True:
                данные = ОЧЕРЕДЬ.get()
                if распознаватель.AcceptWaveform(данные):
                    результат = json.loads(распознаватель.Result())
                    текст = результат.get("text", "")
                    
                    if текст:
                        if "выход" in текст.lower():
                            break
                        
                        # Пишем текст
                        keyboard.write(текст + " ")
                        # Небольшая пауза для стабильности клавиатурного ввода
                        time.sleep(0.05)

    except Exception as ошибка:
        logging.critical(f"Ошибка: {ошибка}")
        messagebox("Ошибка", str(ошибка))
        sys.exit(1)