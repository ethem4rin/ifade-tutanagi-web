# -*- coding: utf-8 -*-
"""Veri deposu: Supabase (Postgres) veya yerel JSON.

Vercel gibi sunucusuz ortamlarda dosya sistemi kalıcı değildir; orada
SUPABASE_URL + SUPABASE_KEY ortam değişkenleri tanımlanınca Supabase kullanılır.
Bu değişkenler yoksa (yerel geliştirme) `veri/` altındaki JSON dosyalarına düşer.

Tablolar için `supabase_kurulum.sql` dosyasına bakın.
"""
import json
import os
import time

_SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
_SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or ""

SUPABASE_AKTIF = bool(_SUPABASE_URL and _SUPABASE_KEY)


# ===========================================================================
# Supabase REST (PostgREST) — ek bağımlılık yok, urllib yeterli
# ===========================================================================
def _istek(yontem: str, yol: str, govde=None, basliklar=None):
    import urllib.error
    import urllib.request

    url = "%s/rest/v1/%s" % (_SUPABASE_URL, yol)
    bas = {
        "apikey": _SUPABASE_KEY,
        "Authorization": "Bearer " + _SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    if basliklar:
        bas.update(basliklar)
    veri = json.dumps(govde).encode("utf-8") if govde is not None else None
    istek = urllib.request.Request(url, data=veri, headers=bas, method=yontem)
    try:
        with urllib.request.urlopen(istek, timeout=15) as y:
            ham = y.read().decode("utf-8")
            return json.loads(ham) if ham.strip() else []
    except urllib.error.HTTPError as e:
        detay = e.read().decode("utf-8", "replace")
        raise RuntimeError("Supabase hatası (%s): %s" % (e.code, detay[:300]))


def _d(deger: str) -> str:
    """Filtre değerini URL için kodlar (Türkçe karakter, boşluk, / + gibi)."""
    from urllib.parse import quote
    return quote(str(deger), safe="")


def _sec(tablo, filtre, tek=True):
    sonuc = _istek("GET", "%s?%s&select=*" % (tablo, filtre))
    if tek:
        return sonuc[0] if sonuc else None
    return sonuc


def _yaz(tablo, kayit, catisma="id"):
    """upsert — varsa günceller, yoksa ekler."""
    _istek("POST", "%s?on_conflict=%s" % (tablo, catisma), [kayit],
           {"Prefer": "resolution=merge-duplicates,return=minimal"})


def _sil(tablo, filtre):
    _istek("DELETE", "%s?%s" % (tablo, filtre), None, {"Prefer": "return=minimal"})


# ===========================================================================
# Yerel JSON yedeği
# ===========================================================================
def _dosya_adi(kullanici: str) -> str:
    """Kullanıcı adını güvenli dosya adına çevirir (yol ayıracı, Türkçe karakter vb.)."""
    import hashlib
    return "hafiza_%s.json" % hashlib.sha256(kullanici.encode("utf-8")).hexdigest()[:16]


def _yerel_kok():
    kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri")
    os.makedirs(kok, exist_ok=True)
    return kok


def _yerel_oku(ad, varsayilan):
    yol = os.path.join(_yerel_kok(), ad)
    if os.path.exists(yol):
        try:
            with open(yol, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return varsayilan


def _yerel_yaz(ad, veri):
    yol = os.path.join(_yerel_kok(), ad)
    gecici = yol + ".tmp"
    with open(gecici, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
    os.replace(gecici, yol)


# ===========================================================================
# Ortak arayüz — auth.py ve hafıza bunu kullanır
# ===========================================================================
def kullanici_getir(anahtar: str):
    if SUPABASE_AKTIF:
        return _sec("kullanicilar", "anahtar=eq.%s" % _d(anahtar))
    return _yerel_oku("kullanicilar.json", {}).get(anahtar)


def kullanici_kaydet(anahtar: str, kayit: dict):
    if SUPABASE_AKTIF:
        _yaz("kullanicilar", {**kayit, "anahtar": anahtar}, "anahtar")
        return
    tum = _yerel_oku("kullanicilar.json", {})
    tum[anahtar] = kayit
    _yerel_yaz("kullanicilar.json", tum)


def oturum_getir(jeton: str):
    if SUPABASE_AKTIF:
        return _sec("oturumlar", "jeton=eq.%s" % _d(jeton))
    return _yerel_oku("oturumlar.json", {}).get(jeton)


def oturum_kaydet(jeton: str, kullanici: str, bitis: float):
    if SUPABASE_AKTIF:
        _yaz("oturumlar", {"jeton": jeton, "kullanici": kullanici, "bitis": bitis}, "jeton")
        return
    tum = _yerel_oku("oturumlar.json", {})
    tum[jeton] = {"kullanici": kullanici, "bitis": bitis}
    # süresi geçenleri temizle
    simdi = time.time()
    tum = {j: k for j, k in tum.items() if k.get("bitis", 0) >= simdi}
    _yerel_yaz("oturumlar.json", tum)


def oturum_sil(jeton: str):
    if SUPABASE_AKTIF:
        _sil("oturumlar", "jeton=eq.%s" % _d(jeton))
        return
    tum = _yerel_oku("oturumlar.json", {})
    tum.pop(jeton, None)
    _yerel_yaz("oturumlar.json", tum)


def hafiza_getir(kullanici: str) -> dict:
    bos = {"alanlar": {}, "unvan_kisa": {}, "adres": {}, "isciler": []}
    if SUPABASE_AKTIF:
        satir = _sec("hafiza", "kullanici=eq.%s" % _d(kullanici))
        if satir and isinstance(satir.get("veri"), dict):
            return {**bos, **satir["veri"]}
        return bos
    return {**bos, **_yerel_oku(_dosya_adi(kullanici), {})}


def hafiza_kaydet(kullanici: str, veri: dict):
    if SUPABASE_AKTIF:
        _yaz("hafiza", {"kullanici": kullanici, "veri": veri,
                        "guncelleme": time.strftime("%Y-%m-%dT%H:%M:%S")}, "kullanici")
        return
    _yerel_yaz(_dosya_adi(kullanici), veri)


def durum() -> dict:
    return {"supabase": SUPABASE_AKTIF,
            "depo": "Supabase" if SUPABASE_AKTIF else "yerel JSON"}
