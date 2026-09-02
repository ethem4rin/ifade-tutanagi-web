# -*- coding: utf-8 -*-
"""Kalıcı hafıza: otomatik tamamlama değerleri, kısa unvan öğrenimi, işçi kayıtları.

Veri kullanıcı ana dizininde 'İfadeTutanagi_veri/hafiza.json' altında tutulur
(exe ile paketlendiğinde de yazılabilir bir konum)."""
import json
import os


def veri_dizin() -> str:
    base = os.path.join(os.path.expanduser("~"), "İfadeTutanagi_veri")
    os.makedirs(base, exist_ok=True)
    return base


class Hafiza:
    def __init__(self, yol: str = None):
        self.yol = yol or os.path.join(veri_dizin(), "hafiza.json")
        self.veri = {"alanlar": {}, "unvan_kisa": {}, "adres": {}, "isciler": []}
        self.yukle()

    # -- yükle / kaydet --------------------------------------------------
    def yukle(self):
        if os.path.exists(self.yol):
            try:
                with open(self.yol, "r", encoding="utf-8") as f:
                    d = json.load(f)
                for k in self.veri:
                    if k in d:
                        self.veri[k] = d[k]
            except Exception:
                pass

    def kaydet(self):
        try:
            with open(self.yol, "w", encoding="utf-8") as f:
                json.dump(self.veri, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    # -- otomatik tamamlama ---------------------------------------------
    def oneriler(self, alan: str):
        return sorted(self.veri["alanlar"].get(alan, []), key=lambda s: s.lower())

    def alan_ekle(self, alan: str, deger: str):
        deger = (deger or "").strip()
        if not deger:
            return
        lst = self.veri["alanlar"].setdefault(alan, [])
        if deger not in lst:
            lst.append(deger)

    # -- kısa unvan öğrenimi (ham tam unvan -> seçilen kısa ad) ----------
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
        # aynı işçi daha önce girildiyse kaydını güncelle, kopya biriktirme
        if ad:
            for i, eski in enumerate(self.veri["isciler"]):
                if (eski.get("ad_soyad") or "").strip().lower() == ad.lower():
                    self.veri["isciler"][i] = {**eski, **kayit}
                    break
            else:
                self.veri["isciler"].append(kayit)
        else:
            self.veri["isciler"].append(kayit)
        # tüm alan değerlerini otomatik tamamlamaya işle
        for k, v in kayit.items():
            if isinstance(v, str) and v.strip():
                self.alan_ekle(k, v)

    def isci_bul(self, ad_soyad: str):
        """Daha önce girilmiş işçiyi adından bulur (en son kayıt kazanır)."""
        ad = (ad_soyad or "").strip().lower()
        if not ad:
            return None
        for kayit in reversed(self.veri["isciler"]):
            if (kayit.get("ad_soyad") or "").strip().lower() == ad:
                return kayit
        return None

    def isci_adlari(self):
        """Kayıtlı tüm işçi adları."""
        adlar = []
        for k in self.veri["isciler"]:
            ad = (k.get("ad_soyad") or "").strip()
            if ad and ad not in adlar:
                adlar.append(ad)
        return sorted(adlar, key=lambda s: s.lower())
