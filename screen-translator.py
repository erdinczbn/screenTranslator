import tkinter as tk
import threading
import time
import keyboard
import win32gui
import win32con
import json
import urllib.request
import urllib.parse
import cv2
import numpy as np
import easyocr
from PIL import ImageGrab

SCALE_FACTOR = 1.25
LOOP_DELAY = 0.2
MIN_TEXT_WIDTH = 40
OCR_THRESHOLD = 0.3

print("[*] EasyOCR Başlatılıyor (GPU / CUDA Modu)...")
try:
    reader = easyocr.Reader(['en'], gpu=True)
    print("[+] GPU (CUDA) hızlandırması başarıyla aktif edildi.")
except Exception as e:
    print(f"[!] GPU hatası alındı, CPU moduna geçiliyor: {e}")
    reader = easyocr.Reader(['en'], gpu=False)

is_running = False
overlay = None
labels = []
translation_cache = {}

def google_translate_fast(text, target_lang='tr'):
    if text in translation_cache:
        return translation_cache[text]
        
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=" + target_lang + "&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            translated = "".join([sentence[0] for sentence in data[0]])
            translation_cache[text] = translated
            return translated
    except Exception:
        return text

def calibrate_bbox(raw_bbox):
    raw_x = raw_bbox[0][0]
    raw_y = raw_bbox[0][1]
    calibrated_x = int(raw_x / SCALE_FACTOR)
    calibrated_y = int(raw_y / SCALE_FACTOR)
    return calibrated_x, calibrated_y

def write_to_overlay(metin, x, y):
    global overlay, labels
    if overlay is None: 
        return

    shadow = tk.Label(overlay, text=metin, font=("Segoe UI", 11, "bold"), fg="#101010", bg="black")
    shadow.place(x=x+1, y=y+1)
    label = tk.Label(overlay, text=metin, font=("Segoe UI", 11, "bold"), fg="#00E676", bg="black")
    label.place(x=x, y=y)
    labels.append(shadow)
    labels.append(label)

def clear_overlay():
    global labels
    for label in labels:
        try:
            label.destroy()
        except Exception:
            pass
    labels = []

def canlı_ceviri_dongusu():
    global is_running
    print("[+] Canlı ekran çevirisi aktif. Durdurmak için F4 tuşuna basın.")
    
    while is_running:
        start_time = time.time()
        try:
            screen = np.array(ImageGrab.grab())
            screen_rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)

            results = reader.readtext(screen_rgb, detail=1, paragraph=False)

            if len(results) > 0 and is_running:
                clear_overlay()

            if not is_running: 
                break

            for (bbox, text, prob) in results:
                raw_text = text.strip()
                if prob > OCR_THRESHOLD and len(raw_text) > 1:
                    box_width = int(bbox[1][0] - bbox[0][0])
                    if box_width < MIN_TEXT_WIDTH: 
                        continue
                    
                    fixed_x, fixed_y = calibrate_bbox(bbox)
                    ceviri = google_translate_fast(raw_text)
                    write_to_overlay(ceviri, fixed_x, fixed_y)

        except Exception:
            pass

        elapsed_time = time.time() - start_time
        sleep_time = max(0.01, LOOP_DELAY - elapsed_time)
        time.sleep(sleep_time)

def toggle_sistemi():
    global is_running
    if not is_running:
        is_running = True
        print("\n>>> CANLI EKRAN ÇEVİRİSİ BAŞLATILDI (Kapatmak için F4) <<<")
        threading.Thread(target=canlı_ceviri_dongusu, daemon=True).start()
    else:
        is_running = False
        clear_overlay()
        print("\n>>> CANLI EKRAN ÇEVİRİSİ DURDURULDU <<<")

def create_layered_overlay():
    global overlay
    overlay = tk.Tk()
    overlay.title("Screen_OCR_Translator_Overlay")
    
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    overlay.geometry(f"{sw}x{sh}+0+0")
    overlay.overrideredirect(True)
    overlay.configure(bg='black')
    overlay.wm_attributes("-transparentcolor", "black")
    overlay.attributes("-topmost", True)
    hwnd = win32gui.FindWindow(None, "Screen_OCR_Translator_Overlay")
    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
    
    overlay.mainloop()

keyboard.add_hotkey('f4', toggle_sistemi)

print("=" * 60)
print("     CANLI EKRAN VE OYUN ÇEVİRİ ARACI (SCREEN OCR)        ")
print("=" * 60)
print(f"[*] Windows Ekran Ölçeği: %{int(SCALE_FACTOR*100)}")
print("[*] Oyunları veya uygulamaları 'Pencereli Tam Ekran (Borderless)' modunda açın.")
print("[*] Çeviriyi başlatmak ve durdurmak için F4 tuşuna basın.")
print("=" * 60)

create_layered_overlay()
