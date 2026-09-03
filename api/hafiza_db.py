# -*- coding: utf-8 -*-
"""Kullanıcı hafızası — Supabase/JSON deposu üzerinden.

Hafızada YALNIZCA işçilerin adı ve soyadı tutulur (otomatik tamamlama için).
T.C. kimlik no, adres, telefon, anne-baba adı gibi bilgiler saklanmaz.
İşyeri düzeltmeleri (kısa unvan / adres) ayrıca öğrenilir — bunlar kişisel
veri değil, PDF'ten gelen işyeri bilgisinin düzeltilmiş hâlidir.
"""
import depo

# Hafızada tutulmasına izin verilen alanlar
IZINLI_ALANLAR = ("ad", "soyad")


class Hafiza:
    def __init__(self, kullanici: str):
        self.kullanici = kullanici
        self.veri = depo.hafiza_getir(kullanici)
        self._temizle()

    def _temizle(self):
        """Eski sürümlerden kalan kişisel verileri hafızadan düşürür."""
        self.veri.pop("isciler", None)
        alanlar = self.veri.get("alanlar", {})
        self.veri["alanlar"] = {k: v for k, v in alanlar.items() if k in IZINLI_ALANLAR}

    def kaydet(self):
        self._temizle()
        depo.hafiza_kaydet(self.kullanici, self.veri)

    # -- otomatik tamamlama (yalnızca ad / soyad) ------------------------
    def oneriler(self, alan: str):
        if alan not in IZINLI_ALANLAR:
            return []
        return sorted(self.veri["alanlar"].get(alan, []), key=lambda s: s.lower())

    def alan_ekle(self, alan: str, deger: str):
        if alan not in IZINLI_ALANLAR:
            return
        deger = " ".join(str(deger or "").split())
        if not deger:
            return
        liste = self.veri["alanlar"].setdefault(alan, [])
        # aynı değeri büyük/küçük harf farkıyla tekrar eklemeyelim
        if not any(m.lower() == deger.lower() for m in liste):
            liste.append(deger)

    def ad_soyad_ekle(self, ad: str, soyad: str):
        self.alan_ekle("ad", ad)
        self.alan_ekle("soyad", soyad)

    def kayitli_sayisi(self) -> int:
        a = len(self.veri["alanlar"].get("ad", []))
        s = len(self.veri["alanlar"].get("soyad", []))
        return a + s

    # -- işyeri öğrenimi (kişisel veri değil) -----------------------------
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
