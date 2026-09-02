# -*- coding: utf-8 -*-
"""İşçi İfade Tutanağı — Web sürümü (FastAPI).

Masaüstü sürümüyle aynı çekirdeği kullanır; fark: kullanıcı girişi ve
kullanıcı başına ayrı hafıza, çıktılar ZIP/docx olarak indirilir.
"""
import io
import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Header
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles

BURADA = Path(__file__).resolve().parent
sys.path.insert(0, str(BURADA))

import auth                                    # noqa: E402
import depo                                    # noqa: E402
import paket                                   # noqa: E402
from cekirdek import gorev_listesi as G        # noqa: E402
from cekirdek import tutanak_uretici as T      # noqa: E402
from cekirdek import ifade_metni as IM         # noqa: E402
from cekirdek import excel_form as X           # noqa: E402
from hafiza_db import Hafiza                   # noqa: E402

app = FastAPI(title="İşçi İfade Tutanağı")

ONYUZ = BURADA.parent / "public"


# ---------------------------------------------------------------------------
# yardımcılar
# ---------------------------------------------------------------------------
def _kullanici(jeton: str):
    anahtar = auth.oturum_kullanici(jeton)
    if not anahtar:
        raise HTTPException(status_code=401, detail="Oturum geçersiz, tekrar giriş yapın.")
    return anahtar


def _hafiza(anahtar: str) -> Hafiza:
    return Hafiza(anahtar)


def _jeton(authorization: str = Header(default="")) -> str:
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return authorization.strip()


# ---------------------------------------------------------------------------
# hesap
# ---------------------------------------------------------------------------
@app.post("/api/kayit")
def kayit(govde: dict = Body(...)):
    try:
        kullanici = auth.kayit_ol(govde.get("ad", ""), govde.get("sifre", ""),
                                  govde.get("tam_ad", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    dogrulanan = auth.dogrula(govde.get("ad", ""), govde.get("sifre", ""))
    return {"jeton": auth.oturum_ac(dogrulanan["anahtar"]), "kullanici": kullanici}


@app.post("/api/giris")
def giris(govde: dict = Body(...)):
    kullanici = auth.dogrula(govde.get("ad", ""), govde.get("sifre", ""))
    if not kullanici:
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı.")
    return {"jeton": auth.oturum_ac(kullanici["anahtar"]),
            "kullanici": {"ad": kullanici["ad"], "tam_ad": kullanici["tam_ad"]}}


@app.post("/api/cikis")
def cikis(authorization: str = Header(default="")):
    auth.oturum_kapat(_jeton(authorization))
    return {"ok": True}


@app.get("/api/ben")
def ben(authorization: str = Header(default="")):
    anahtar = _kullanici(_jeton(authorization))
    h = _hafiza(anahtar)
    return {"kullanici": anahtar, "kayitli_isci": len(h.isci_adlari())}


@app.post("/api/sifre")
def sifre(govde: dict = Body(...), authorization: str = Header(default="")):
    anahtar = _kullanici(_jeton(authorization))
    try:
        auth.sifre_degistir(anahtar, govde.get("eski", ""), govde.get("yeni", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


# ---------------------------------------------------------------------------
# görev listesi PDF
# ---------------------------------------------------------------------------
@app.post("/api/pdf")
async def pdf_yukle(dosya: UploadFile = File(...), authorization: str = Header(default="")):
    anahtar = _kullanici(_jeton(authorization))
    icerik = await dosya.read()
    gecici = os.path.join(tempfile.gettempdir(), "gl_%s.pdf" % os.getpid())
    with open(gecici, "wb") as f:
        f.write(icerik)
    try:
        veri = G.parse(gecici)
    except Exception as e:
        raise HTTPException(status_code=400, detail="PDF okunamadı: %s" % e)
    finally:
        try:
            os.remove(gecici)
        except OSError:
            pass
    if not veri["isyerleri"]:
        raise HTTPException(status_code=400, detail="PDF'te işyeri bulunamadı. Doğru Görev Listesi mi?")
    # öğrenilmiş kısa unvan/adres varsa uygula
    h = _hafiza(anahtar)
    for k in veri["isyerleri"]:
        ogr = h.unvan_kisa_getir(k["unvan_tam"])
        if ogr:
            k["unvan_kisa"] = ogr
        adr = h.adres_getir(k["adres_ham"])
        if adr:
            k["adres"] = adr
    return veri


# ---------------------------------------------------------------------------
# alan şeması + hafıza
# ---------------------------------------------------------------------------
@app.get("/api/alanlar")
def alanlar():
    return {"alanlar": [{"anahtar": a, "etiket": e, "tip": t, "varsayilan": v}
                        for a, e, t, v in IM.ALANLAR]}


@app.get("/api/oneriler")
def oneriler(alan: str, authorization: str = Header(default="")):
    anahtar = _kullanici(_jeton(authorization))
    return {"oneriler": _hafiza(anahtar).oneriler(alan)}


@app.get("/api/isci")
def isci(ad: str, authorization: str = Header(default="")):
    anahtar = _kullanici(_jeton(authorization))
    kayit = _hafiza(anahtar).isci_bul(ad)
    if not kayit:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    return {"isci": kayit}


@app.get("/api/isciler")
def isciler(authorization: str = Header(default="")):
    anahtar = _kullanici(_jeton(authorization))
    return {"adlar": _hafiza(anahtar).isci_adlari()}


@app.post("/api/onizleme")
def onizleme(govde: dict = Body(...), authorization: str = Header(default="")):
    _kullanici(_jeton(authorization))
    isci_veri = govde.get("isci", {})
    return {"paragraflar": IM.govde(isci_veri), "kapanis": IM.kapanis(isci_veri)}


# ---------------------------------------------------------------------------
# tutanak üretimi
# ---------------------------------------------------------------------------
def _docx_uret(govde: dict) -> tuple:
    isyeri = govde.get("isyeri", {})
    baslik = govde.get("baslik", {})
    isci_veri = govde.get("isci", {})
    sira = int(govde.get("sira", 1))
    paragraflar = govde.get("paragraflar")
    kapanis = govde.get("kapanis")
    gecici = os.path.join(tempfile.gettempdir(), "tutanak_%s_%s.docx" % (os.getpid(), sira))
    T.uret(isyeri, baslik, isci_veri, sira, gecici,
           govde_list=paragraflar, kapanis_metni=kapanis)
    with open(gecici, "rb") as f:
        icerik = f.read()
    try:
        os.remove(gecici)
    except OSError:
        pass
    return "İfade Tutanağı %d.docx" % sira, icerik


@app.post("/api/tutanak")
def tutanak(govde: dict = Body(...), authorization: str = Header(default="")):
    """Tek işçi için .docx üretir ve indirir; hafızayı günceller."""
    anahtar = _kullanici(_jeton(authorization))
    ad, icerik = _docx_uret(govde)

    h = _hafiza(anahtar)
    isci_veri = govde.get("isci", {})
    if (isci_veri.get("ad_soyad") or "").strip():
        h.isci_ekle(isci_veri)
    isyeri = govde.get("isyeri", {})
    if isyeri.get("unvan_tam"):
        h.unvan_kisa_kaydet(isyeri["unvan_tam"], isyeri.get("unvan_kisa", ""))
    if isyeri.get("adres_ham"):
        h.adres_kaydet(isyeri["adres_ham"], isyeri.get("adres", ""))
    h.kaydet()

    return Response(
        content=icerik,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%s" %
                 _url_ad(ad)})


@app.post("/api/paket")
def paket_indir(govde: dict = Body(...), authorization: str = Header(default="")):
    """Birden çok işçinin tutanağını 'ekler dizimi' klasör yapısıyla ZIP olarak verir."""
    anahtar = _kullanici(_jeton(authorization))
    isyeri = govde.get("isyeri", {})
    baslik = govde.get("baslik", {})
    kayitlar = govde.get("isciler", [])
    if not kayitlar:
        raise HTTPException(status_code=400, detail="Paketlenecek işçi yok.")

    h = _hafiza(anahtar)
    tutanaklar = []
    for i, kayit in enumerate(kayitlar, 1):
        isci_veri = kayit.get("isci", {})
        ad, icerik = _docx_uret({
            "isyeri": isyeri, "baslik": baslik, "isci": isci_veri, "sira": i,
            "paragraflar": kayit.get("paragraflar"), "kapanis": kayit.get("kapanis"),
        })
        tutanaklar.append((ad, icerik))
        if (isci_veri.get("ad_soyad") or "").strip():
            h.isci_ekle(isci_veri)
    h.kaydet()

    arsiv = paket.zip_olustur(isyeri.get("unvan_kisa", "isyeri"), tutanaklar)
    dosya_adi = "ekler dizimi (%s).zip" % isyeri.get("unvan_kisa", "isyeri")
    return Response(content=arsiv, media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename*=UTF-8''%s" %
                             _url_ad(dosya_adi)})


# ---------------------------------------------------------------------------
# işveren Excel formu
# ---------------------------------------------------------------------------
@app.post("/api/form")
def form_olustur(govde: dict = Body(...), authorization: str = Header(default="")):
    _kullanici(_jeton(authorization))
    isyeri = govde.get("isyeri", {})
    gecici = os.path.join(tempfile.gettempdir(), "form_%s.xlsx" % os.getpid())
    X.form_olustur(isyeri, gecici, satir_sayisi=int(govde.get("satir", 30)))
    with open(gecici, "rb") as f:
        icerik = f.read()
    try:
        os.remove(gecici)
    except OSError:
        pass
    return Response(
        content=icerik,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%s" %
                 _url_ad("İşçi Bilgi Formu.xlsx")})


@app.post("/api/form-oku")
async def form_oku(dosya: UploadFile = File(...), authorization: str = Header(default="")):
    _kullanici(_jeton(authorization))
    icerik = await dosya.read()
    gecici = os.path.join(tempfile.gettempdir(), "dolu_%s.xlsx" % os.getpid())
    with open(gecici, "wb") as f:
        f.write(icerik)
    try:
        isciler = X.form_oku(gecici)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Form okunamadı: %s" % e)
    finally:
        try:
            os.remove(gecici)
        except OSError:
            pass
    return {"isciler": isciler}


# ---------------------------------------------------------------------------
def _url_ad(ad: str) -> str:
    from urllib.parse import quote
    return quote(ad)


@app.get("/api/saglik")
def saglik():
    return {"ok": True, **depo.durum()}


# ön yüz (en sonda: /api yollarını gölgelemesin)
if ONYUZ.is_dir():
    app.mount("/", StaticFiles(directory=str(ONYUZ), html=True), name="onyuz")
