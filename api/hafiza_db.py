# -*- coding: utf-8 -*-
"""Kullanıcı hafızası — Supabase/JSON deposu üzerinden.

Masaüstü sürümündeki `cekirdek.hafiza.Hafiza` ile aynı arayüzü sunar;
fark: veriyi dosya yerine `depo` katmanına yazar (sunucusuz ortamda çalışır).
"""
import depo


class Hafiza:
    def __init__(self, kullanici: str):
        self.kullanici = kullanici
        self.veri = depo.hafiza_getir(kullanici)

    def kaydet(self):
        depo.hafiza_kaydet(self.kullanici, self.veri)

    # -- otomatik tamamlama ---------------------------------------------
    def oneriler(self, alan: str):
        return sorted(self.veri["alanlar"].get(alan, []), key=lambda s: s.lower())

    def alan_ekle(self, alan: str, deger: str):
        deger = (deger or "").strip()
        if not deger:
            return
        liste = self.veri["alanlar"].setdefault(alan, [])
        if deger not in liste:
            liste.append(deger)

    # -- işyeri öğrenimi -------------------------------------------------
    def unvan_kisa_getir(self, ham: str):
        return self.veri["unvan_kisa"].get((ham or "").strip())

    def unvan_kisa_kaydet(self, ham: str, kisa: str):
        if (ham or "").strip():
            self.veri["unvan_kisa"][ham.strip()] = (kisa or "").strip()

    def adres_getir(self, ham: str):
        return self.veri["adres"].get((ham or "").strip())

    def adres_kaydet(self, ham: str, adres: str):
        if (ham or "").strip():
            self.veri["adres"][ham.strip()] = (adres or "").strip()

    # -- işçi kaydı ------------------------------------------------------
    def isci_ekle(self, kayit: dict):
        ad = (kayit.get("ad_soyad") or "").strip()
        if ad:
            for i, eski in enumerate(self.veri["isciler"]):
                if (eski.get("ad_soyad") or "").strip().lower() == ad.lower():
                    self.veri["isciler"][i] = {**eski, **kayit}
                    break
            else:
                self.veri["isciler"].append(kayit)
        else:
            self.veri["isciler"].append(kayit)
        for k, v in kayit.items():
            if isinstance(v, str) and v.strip():
                self.alan_ekle(k, v)

    def isci_bul(self, ad_soyad: str):
        ad = (ad_soyad or "").strip().lower()
        if not ad:
            return None
        for kayit in reversed(self.veri["isciler"]):
            if (kayit.get("ad_soyad") or "").strip().lower() == ad:
                return kayit
        return None

    def isci_adlari(self):
        adlar = []
        for k in self.veri["isciler"]:
            ad = (k.get("ad_soyad") or "").strip()
            if ad and ad not in adlar:
                adlar.append(ad)
        return sorted(adlar, key=lambda s: s.lower())
