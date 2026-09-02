# -*- coding: utf-8 -*-
"""'ekler dizimi (işyeri)' klasör yapısını ZIP olarak paketler.

Masaüstü sürümü klasörleri doğrudan oluşturuyordu; web sürümünde aynı yapı
ZIP içinde üretilir, kullanıcı indirip masaüstüne çıkarır.
"""
import io
import os
import zipfile

from cekirdek.klasor import EK_KLASORLER, IFADE_KLASOR, _guvenli


def zip_olustur(isyeri_adi: str, tutanaklar) -> bytes:
    """tutanaklar: [(dosya_adi, docx_bytes), ...] -> ZIP baytları.

    ZIP kökünde 'ekler dizimi (işyeri)' klasörü, altında tüm EK klasörleri;
    tutanaklar 'EK 4 İŞÇİ İFADE TUTANAKLARI' içine yerleşir. Boş klasörler de
    korunur (Windows Gezgini boş klasörleri de çıkarır)."""
    kok = "ekler dizimi ({})".format(_guvenli(isyeri_adi) or "isyeri")
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        for ek in EK_KLASORLER:
            # boş klasör girdisi (sonda / ile)
            z.writestr("{}/{}/".format(kok, ek), "")
        for ad, icerik in tutanaklar:
            z.writestr("{}/{}/{}".format(kok, IFADE_KLASOR, ad), icerik)
    return tampon.getvalue()
