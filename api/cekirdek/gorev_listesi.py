# -*- coding: utf-8 -*-
"""Görev Listesi PDF'ini parçalayıp yapılandırılmış kayıt üretir."""
import re
from pypdf import PdfReader

from . import bicimlendirme as B

# Satır gürültüsü (sayfa başlıkları vb.)
_GURULTU = re.compile(
    r"^(T\.C\.|ÇALIŞMA VE SOSYAL|İstanbul Rehberlik|Konu\s*:|"
    r"S\.\s*$|No Sicil|\d+\s*/\s*\d+\s*$)", re.IGNORECASE)

_GOREV_NO = re.compile(r"(S\d{6,})\s*$")
_SICIL = re.compile(r"\b(\d{20,})\b")
_ILCE_IL = re.compile(r"^[A-ZÇĞİÖŞÜ ]+/\s*[A-ZÇĞİÖŞÜ ]+$")
_SAYI = re.compile(r"Sayı\s*:\s*([\d\-]+)\s+(\d{2}/\d{2}/\d{4})")
_MUFETTIS = re.compile(r"Say[ıi]n\s+(.+?)\s*\(İş Müfettişi\)")
_DONEM = re.compile(r"Yılı\s*/\s*Dönemi\s*:\s*(.+)")


def _metin(pdf_yolu: str) -> str:
    r = PdfReader(pdf_yolu)
    return "\n".join((pg.extract_text() or "") for pg in r.pages)


def parse(pdf_yolu: str) -> dict:
    ham = _metin(pdf_yolu)
    satirlar = [s.rstrip() for s in ham.splitlines()]

    # --- başlık bilgileri ---
    sayi, tarih, donem = "", "", ""
    mufettisler = []
    for s in satirlar:
        m = _SAYI.search(s)
        if m and not sayi:
            sayi, tarih = m.group(1), m.group(2)
        m = _MUFETTIS.search(s)
        if m:
            ad = m.group(1).strip()
            if ad not in mufettisler:
                mufettisler.append(ad)
        m = _DONEM.search(s)
        if m and not donem:
            donem = m.group(1).strip()

    sayi_son = sayi.split("-")[-1] if sayi else ""
    # Görev listesinde: 1. isim kıdemsiz, 2. isim kıdemli (kullanıcı kuralı)
    kidemsiz = mufettisler[0] if len(mufettisler) > 0 else ""
    kidemli = mufettisler[1] if len(mufettisler) > 1 else ""

    baslik = {
        "sayi": sayi, "sayi_son": sayi_son, "tarih": tarih, "donem": donem,
        "mufettisler": mufettisler, "kidemsiz": kidemsiz, "kidemli": kidemli,
    }

    # --- işyeri kayıtları ---
    isyerleri = []
    blok = []
    for s in satirlar:
        if _GURULTU.match(s.strip()):
            continue
        blok.append(s)
        if _GOREV_NO.search(s):                 # kayıt bitti
            kayit = _blok_coz(blok)
            if kayit:
                isyerleri.append(kayit)
            blok = []

    # sıra numarası ata
    for i, k in enumerate(isyerleri, 1):
        k["sira"] = i

    return {"baslik": baslik, "isyerleri": isyerleri}


def _blok_coz(blok):
    """Bir işyeri bloğundaki satırları alanlara ayır."""
    metin_satir = [s for s in blok if s.strip()]
    if not metin_satir:
        return None

    # görev no + teftiş türü (son satır)
    gorev_no = ""
    teftis = ""
    for s in metin_satir:
        m = _GOREV_NO.search(s)
        if m:
            gorev_no = m.group(1)
            teftis = s[:m.start()].strip()

    # sicil
    ham_sicil = ""
    for s in metin_satir:
        m = _SICIL.search(s)
        if m:
            ham_sicil = m.group(1)
            break
    if not (ham_sicil and gorev_no):
        return None

    # unvan: "Unvan:" satırından "Adres:" satırına kadar
    # adres: "Adres:" satırından ilçe/il ya da görev-no satırına kadar
    unvan_parcalar, adres_parcalar, ilce_il = [], [], ""
    mod = None
    for s in metin_satir:
        st = s.strip()
        if st.startswith("Unvan:"):
            mod = "unvan"
            unvan_parcalar.append(st[len("Unvan:"):].strip())
            continue
        if st.startswith("Adres:"):
            mod = "adres"
            adres_parcalar.append(st[len("Adres:"):].strip())
            continue
        if _ILCE_IL.match(st):
            ilce_il = st
            mod = None
            continue
        if _GOREV_NO.search(st) or _SICIL.search(st):
            mod = None
            continue
        if mod == "unvan":
            unvan_parcalar.append(st)
        elif mod == "adres":
            adres_parcalar.append(st)

    tam_unvan = re.sub(r"\s+", " ", " ".join(unvan_parcalar)).strip()
    ham_adres = re.sub(r"\s+", " ", " ".join(adres_parcalar)).strip()

    return {
        "sira": 0,
        "sicil_ham": ham_sicil,
        "sicil": B.sicil_formatla(ham_sicil),
        "unvan_tam": tam_unvan,
        "unvan_kisa": B.kisa_unvan(tam_unvan),
        "isveren": B.unvan_duzelt(tam_unvan),
        "adres_ham": ham_adres,
        "ilce_il": ilce_il,
        "adres": B.adres_temizle(ham_adres, ilce_il),
        "teftis_turu": teftis,
        "gorev_no": gorev_no,
    }


if __name__ == "__main__":
    import sys, json
    d = parse(sys.argv[1])
    print(json.dumps(d, ensure_ascii=False, indent=2))
