# -*- coding: utf-8 -*-
"""Kullanıcı hesapları ve oturum yönetimi.

Şifreler PBKDF2-HMAC-SHA256 ile (rastgele tuz + 200.000 tur) saklanır;
düz metin şifre hiçbir yerde tutulmaz. Veriler `depo` katmanına yazılır
(Supabase tanımlıysa Supabase, değilse yerel JSON).
"""
import hashlib
import hmac
import secrets
import time
import unicodedata

import depo

_TUR = 200_000
_OTURUM_SURESI = 60 * 60 * 12          # 12 saat


def kullanici_adi_normalize(ad: str) -> str:
    """Büyük/küçük ve boşluk farkı hesap ayrımı yaratmasın."""
    return unicodedata.normalize("NFKC", (ad or "").strip()).casefold()


def _sifre_hashle(sifre: str, tuz: bytes = None):
    tuz = tuz or secrets.token_bytes(16)
    ozet = hashlib.pbkdf2_hmac("sha256", (sifre or "").encode("utf-8"), tuz, _TUR)
    return tuz.hex(), ozet.hex()


# ---------------------------------------------------------------------------
def kayit_ol(ad: str, sifre: str, tam_ad: str = "") -> dict:
    """Yeni hesap açar. Hata durumunda ValueError fırlatır."""
    anahtar = kullanici_adi_normalize(ad)
    if len(anahtar) < 3:
        raise ValueError("Kullanıcı adı en az 3 karakter olmalı.")
    if len(sifre or "") < 6:
        raise ValueError("Şifre en az 6 karakter olmalı.")
    if depo.kullanici_getir(anahtar):
        raise ValueError("Bu kullanıcı adı zaten alınmış.")
    tuz, ozet = _sifre_hashle(sifre)
    tam = (tam_ad or ad).strip()
    depo.kullanici_kaydet(anahtar, {
        "ad": ad.strip(),
        "tam_ad": tam,
        "tuz": tuz,
        "ozet": ozet,
        "olusturma": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    return {"ad": ad.strip(), "tam_ad": tam}


def dogrula(ad: str, sifre: str):
    """Şifre doğruysa kullanıcı bilgisini döndürür, değilse None."""
    anahtar = kullanici_adi_normalize(ad)
    kullanici = depo.kullanici_getir(anahtar)
    if not kullanici:
        return None
    _, ozet = _sifre_hashle(sifre, bytes.fromhex(kullanici["tuz"]))
    if not hmac.compare_digest(ozet, kullanici["ozet"]):
        return None
    return {"anahtar": anahtar, "ad": kullanici["ad"],
            "tam_ad": kullanici.get("tam_ad", kullanici["ad"])}


def sifre_degistir(anahtar: str, eski: str, yeni: str):
    kullanici = depo.kullanici_getir(anahtar)
    if not kullanici:
        raise ValueError("Kullanıcı bulunamadı.")
    _, ozet = _sifre_hashle(eski, bytes.fromhex(kullanici["tuz"]))
    if not hmac.compare_digest(ozet, kullanici["ozet"]):
        raise ValueError("Mevcut şifre yanlış.")
    if len(yeni or "") < 6:
        raise ValueError("Yeni şifre en az 6 karakter olmalı.")
    tuz, yeni_ozet = _sifre_hashle(yeni)
    kullanici["tuz"], kullanici["ozet"] = tuz, yeni_ozet
    kullanici.pop("anahtar", None)
    depo.kullanici_kaydet(anahtar, kullanici)


# ---------------------------------------------------------------------------
def oturum_ac(anahtar: str) -> str:
    jeton = secrets.token_urlsafe(32)
    depo.oturum_kaydet(jeton, anahtar, time.time() + _OTURUM_SURESI)
    return jeton


def oturum_kapat(jeton: str):
    if jeton:
        depo.oturum_sil(jeton)


def oturum_kullanici(jeton: str):
    """Geçerli oturumun kullanıcı anahtarını döndürür, yoksa None."""
    if not jeton:
        return None
    kayit = depo.oturum_getir(jeton)
    if not kayit:
        return None
    try:
        bitis = float(kayit.get("bitis", 0))
    except (TypeError, ValueError):
        return None
    if bitis < time.time():
        depo.oturum_sil(jeton)
        return None
    return kayit.get("kullanici")
