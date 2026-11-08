# Real-Time Screen OCR Translator (Windows Overlay)

Python tabanlı, GPU hızlandırmalı EasyOCR ve Windows Win32 API kullanarak ekrandaki / oyunlardaki metinleri gerçek zamanlı yakalayıp şeffaf katmanda (overlay) Türkçe çeviriye dönüştüren masaüstü aracı.

## Özellikler
- **Şeffaf & Tıklamayı Engellemeyen Katman:** Win32 API (`WS_EX_TRANSPARENT`, `WS_EX_LAYERED`) entegrasyonu sayesinde oyun ve pencereleri engellemeden en üstte çalışır.
- **DPI Kalibrasyonu:** Windows ekran ölçeklendirme (%125, %150 vb.) kaynaklı koordinat kaymalarını otomatik düzeltir.
- **Önbellek (Caching):** Aynı metinler için gereksiz çeviri isteklerini önler.
- **Kısayol Desteği:** `F4` tuşu ile canlı döngüyü arka planda açıp kapatma.

## Kullanılan Teknolojiler
- Python 3
- EasyOCR & PyTorch
- OpenCV & Pillow
- Win32 API (pywin32)
- Tkinter & Threading
