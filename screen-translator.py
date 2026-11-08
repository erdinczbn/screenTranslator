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

# Ekran olceklendirme orani (Windows Ayarlari: %125 = 1.25)
EKRAN_OLCEGI = 1.25
DONGU_GECIKMESI = 0.2
MIN_METIN_GENISLIGI = 40
OCR_ESIK_DEGERI = 0.3

# EasyOCR GPU ile baslatiliyor
try:
    okuyucu = easyocr.Reader(['en'], gpu=True)
except Exception:
    okuyucu = easyocr.Reader(['en'], gpu=False)

calisiyor = False
pencere = None
etiketler = []
ceviri_hafizasi = {}

def ceviri_yap(metin, hedef_dil='tr'):
    if metin in ceviri_hafizasi:
        return ceviri_hafizasi[metin]
        
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=" + hedef_dil + "&dt=t&q=" + urllib.parse.quote(metin)
        istek = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(istek) as yanit:
            veri = json.loads(yanit.read().decode())
            sonuc = "".join([parca[0] for parca in veri[0]])
            ceviri_hafizasi[metin] = sonuc
            return sonuc
    except Exception:
        return metin

def koordinat_duzelt(kutu):
    ham_x = kutu[0][0]
    ham_y = kutu[0][1]
    duzeltilmis_x = int(ham_x / EKRAN_OLCEGI)
    duzeltilmis_y = int(ham_y / EKRAN_OLCEGI)
    return duzeltilmis_x, duzeltilmis_y

def ekrana_yaz(metin, x, y):
    global pencere, etiketler
    if pencere is None:
        return

    # Golge ve ana metin katmani
    golge = tk.Label(pencere, text=metin, font=("Arial", 11, "bold"), fg="#101010", bg="black")
    golge.place(x=x + 1, y=y + 1)
    yazi = tk.Label(pencere, text=metin, font=("Arial", 11, "bold"), fg="#00E676", bg="black")
    yazi.place(x=x, y=y)
    etiketler.append(golge)
    etiketler.append(yazi)

def ekrani_temizle():
    global etiketler
    for etiket in etiketler:
        etiket.destroy()
    etiketler = []

def ceviri_dongusu():
    global calisiyor
    print("[+] Canli ceviri baslatildi. Durdurmak icin F4.")

    while calisiyor:
        baslangic = time.time()
        try:
            ekran = np.array(ImageGrab.grab())
            ekran_rgb = cv2.cvtColor(ekran, cv2.COLOR_BGR2RGB)
            sonuclar = okuyucu.readtext(ekran_rgb, detail=1, paragraph=False)

            if len(sonuclar) > 0 and calisiyor:
                ekrani_temizle()

            if not calisiyor:
                break

            for (kutu, metin, guvenilirlik) in sonuclar:
                ham_metin = metin.strip()
                if guvenilirlik > OCR_ESIK_DEGERI and len(ham_metin) > 1:
                    genislik = int(kutu[1][0] - kutu[0][0])
                    if genislik < MIN_METIN_GENISLIGI:
                        continue

                    x, y = koordinat_duzelt(kutu)
                    turkce = ceviri_yap(ham_metin)
                    ekrana_yaz(turkce, x, y)

        except Exception:
            pass

        gecen_sure = time.time() - baslangic
        bekleme = max(0.01, DONGU_GECIKMESI - gecen_sure)
        time.sleep(bekleme)

def sistemi_tetikle():
    global calisiyor
    if not calisiyor:
        calisiyor = True
        print("[+] Ceviri katmani aktif.")
        threading.Thread(target=ceviri_dongusu, daemon=True).start()
    else:
        calisiyor = False
        ekrani_temizle()
        print("[-] Ceviri katmani kapatildi.")

def seffaf_pencere_olustur():
    global pencere
    pencere = tk.Tk()
    pencere.title("Ekran_Ceviri_Overlay")
    ekran_g = pencere.winfo_screenwidth()
    ekran_y = pencere.winfo_screenheight()
    pencere.geometry(f"{ekran_g}x{ekran_y}+0+0")
    pencere.overrideredirect(True)
    pencere.configure(bg='black')

    # Saydamlik ve tiklamayi arka plana gecirme (Click-through)
    pencere.wm_attributes("-transparentcolor", "black")
    pencere.attributes("-topmost", True)
    hwnd = win32gui.FindWindow(None, "Ekran_Ceviri_Overlay")
    stil = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, stil | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

    pencere.mainloop()

keyboard.add_hotkey('f4', sistemi_tetikle)

print("[*] Program hazir. 'F4' ile kapatıp açılabilir.")
seffaf_pencere_olustur()
