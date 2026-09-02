# -*- coding: utf-8 -*-
"""Masaüstünde 'ekler dizimi (işyeriadı)' klasör yapısını oluşturur."""
import os

# Referans RAR'daki EK klasörleri + üreteceğimiz EK 4
EK_KLASORLER = [
    "EK 4 İŞÇİ İFADE TUTANAKLARI",
    "EK 5 FAALİYET KONUSU BELGELERİ",
    "EK 6 İŞÇİ LİSTESİ",
    "EK 7 ÖZLÜK DOSYASI VE İŞ SÖZLEŞMESİ ÖRNEKLERİ",
    "EK 8 İŞÇİ ÇALIŞMA SAATLERİ KAYITLARI",
    "EK 9 BANKA ONAYLI ÜCRET ÖDEME KAYITLARI",
    "EK 10 ÜCRET BORDROLARI (ÜCRET HESAP PUSULALARI)",
    "EK 11 ÜCRETLİ YILLIK İZİN KAYITLARI",
]
IFADE_KLASOR = EK_KLASORLER[0]  # EK 4


def masaustu() -> str:
    """Gerçek masaüstü yolu. OneDrive'a yönlendirilmiş masaüstlerini de bulur."""
    # 1) Windows kayıt defteri (en güvenilir - OneDrive yönlendirmesini bilir)
    try:
        import winreg
        anahtar = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, anahtar) as k:
            ham, _ = winreg.QueryValueEx(k, "Desktop")
        yol = os.path.expandvars(ham)
        if os.path.isdir(yol):
            return yol
    except Exception:
        pass

    # 2) OneDrive altındaki masaüstü (TR/EN)
    ev = os.path.expanduser("~")
    onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
    adaylar = []
    if onedrive:
        adaylar += [os.path.join(onedrive, "Masaüstü"), os.path.join(onedrive, "Desktop")]
    adaylar += [
        os.path.join(ev, "OneDrive", "Masaüstü"),
        os.path.join(ev, "OneDrive", "Desktop"),
        os.path.join(ev, "Masaüstü"),
        os.path.join(ev, "Desktop"),
    ]
    for a in adaylar:
        if os.path.isdir(a):
            return a

    # 3) son çare
    son = os.path.join(ev, "Desktop")
    os.makedirs(son, exist_ok=True)
    return son


def _guvenli(ad: str) -> str:
    for c in '<>:"/\\|?*':
        ad = ad.replace(c, " ")
    return " ".join(ad.split()).strip()


def olustur(isyeri_adi: str, taban: str = None) -> dict:
    """'ekler dizimi (isyeri)' ve alt EK klasörlerini oluşturur.
    Döndürür: {'kok':..., 'ifade':...(EK 4 yolu)}"""
    taban = taban or masaustu()
    kok = os.path.join(taban, f"ekler dizimi ({_guvenli(isyeri_adi)})")
    for ek in EK_KLASORLER:
        os.makedirs(os.path.join(kok, ek), exist_ok=True)
    return {"kok": kok, "ifade": os.path.join(kok, IFADE_KLASOR)}
