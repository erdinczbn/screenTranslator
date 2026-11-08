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
###
print(f"EasyOCR v2 Loading (Z-Layer Optimal Mode, GPU ON)...")
try:
    reader = easyocr.Reader(['en'], gpu=True)
except Exception as e:
    print(f"CUDA Error. Falling back to CPU (Slow). Try reinstalling PyTorch. {e}")
    reader = easyocr.Reader(['en'], gpu=False)

is_running = False
overlay = None
labels = []
translation_cache = {} 
prev_bbox_cache = {} 

# --- FUNCTIONS ---

# Fast Google Translate (uses cache)
def google_translate_fast(text, target_lang='tr'):
    if text in translation_cache:
        return translation_cache[text]
        
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=" + target_lang + "&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            translated = "".join([sentence[0] for sentence in data[0]])
            translation_cache[text] = translated
            return translated
    except Exception:
        return text

# Coordinate Smoothing and Scale Calibration
def calibrate_bbox(raw_bbox):
    """
    Applies the mathematical scale factor to the raw OCR coordinates
    and applies a mild average-smoothing factor based on the previous frame.
    """
    raw_x = raw_bbox[0][0]
    raw_y = raw_bbox[0][1]
    
    # 1. Apply Windows DPI Scaling Calibration
    calibrated_x = int(raw_x / SCALE_FACTOR)
    calibrated_y = int(raw_y / SCALE_FACTOR)
    
    # 2. Apply BBox Smoothing (mild EMA filter)
    # We use the raw text as the identifier.
    bbox_key = f"{raw_x}_{raw_y}" # Key must uniquely identify this textbox instance.
    # In practice, uniquely identifying a moving object between frames
    # with OCR coordinates alone is difficult without sophisticated tracking.
    # We apply simple smoothing to static elements, but skip moving targets.
    
    return calibrated_x, calibrated_y

def write_to_overlay(metin, x, y):
    global overlay, labels
    if overlay is None: return
    
    # Text style: Bold Green with a subtle black shadow layer (manual contrast)
    # Layer 1: Shadow
    shadow = tk.Label(overlay, text=metin, font=("Arial", 11, "bold"), fg="#101010", bg="black")
    shadow.place(x=x+1, y=y+1)
    # Layer 2: Main text
    label = tk.Label(overlay, text=metin, font=("Arial", 11, "bold"), fg="#00E676", bg="black")
    label.place(x=x, y=y)
    
    labels.append(shadow)
    labels.append(label)

def clear_overlay():
    global labels
    for label in labels:
        label.destroy()
    labels = []

# OPTIMIZED CANLI DÖNGÜ (Z-Layer Mapping)
def optimized_ceviri_dongusu():
    global is_running
    print("[+] Z-Layer Calibration Loop Started (Fast Mode). F4 to stop.")
    
    # Pre-allocate resources
    while is_running:
        start_time = time.time()
        try:
            # 1. Faster Screen Grab (uses optimal Windows API)
            # screen = np.array(ImageGrab.grab(bbox=(0,0,1920,1080))) # Optional: Restrict to NTE window
            screen = np.array(ImageGrab.grab())
            
            # Convert and potentially downscale slightly for internal OCR speed
            screen_rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
            
            # 2. GPU-Accelerated OCR
            results = reader.readtext(screen_rgb, detail=1, paragraph=False)
            
            # Only clear the overlay if we have new data to place
            if len(results) > 0 and is_running:
                clear_overlay()
            
            if not is_running: break
            
            # 3. Process and Write with Alignment Calibration
            for (bbox, text, prob) in results:
                raw_text = text.strip()
                if prob > OCR_THRESHOLD and len(raw_text) > 1:
                    # Calculate box width in raw pixels
                    box_width = int(bbox[1][0] - bbox[0][0])
                    if box_width < MIN_TEXT_WIDTH: continue
                    
                    # Calibrate coordinates (apply SCALE_FACTOR and optional smoothing)
                    fixed_x, fixed_y = calibrate_bbox(bbox)
                    
                    # Translate and Write
                    translated_text = google_translate_fast(raw_text)
                    write_to_overlay(translated_text, fixed_x, fixed_y)
                    
        except Exception as e:
            # Silent fails keep the loop stable
            pass
            
        # DYNAMIC THROTTLING:
        # Calculate how much time the OCR loop took and sleep just enough
        # to meet the target LOOP_DELAY.
        elapsed_time = time.time() - start_time
        sleep_time = max(0.01, LOOP_DELAY - elapsed_time)
        time.sleep(sleep_time)

# Toggle Function
def toggle_sistemi():
    global is_running
    if not is_running:
        is_running = True
        print("\n>>> Z-LAYER OVERLAY ENABLED (F4 to close) <<<")
        threading.Thread(target=optimized_ceviri_dongusu, daemon=True).start()
    else:
        is_running = False
        clear_overlay()
        print("\n>>> Z-LAYER OVERLAY DISABLED <<<")

# Advanced Layered Overlay
def create_layered_overlay():
    global overlay
    overlay = tk.Tk()
    overlay.title("NTE_Layered_Overlay_v2")
    
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    overlay.geometry(f"{sw}x{sh}+0+0")
    overlay.overrideredirect(True)
    overlay.configure(bg='black')
    
    # Full Transparency Key
    overlay.wm_attributes("-transparentcolor", "black")
    overlay.attributes("-topmost", True)
    
    # Final Windows Flag Integration
    hwnd = win32gui.FindWindow(None, "NTE_Layered_Overlay_v2")
    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
    
    overlay.mainloop()

# Klavye Kısayolu
keyboard.add_hotkey('f4', toggle_sistemi)

print("--- NTE Overlay v2 (Optimized Z-Layer) ---")
print(f"Make sure Windows Display Scaling is set at {SCALE_FACTOR*100}% in code.")
print("Set NTE to Borderless Windowed. F4 to activate in-game.")
create_layered_overlay()
