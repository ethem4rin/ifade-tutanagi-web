# -*- coding: utf-8 -*-
"""Metin biçimlendirme yardımcıları: Türkçe başlık, sicil formatı, kısa unvan, adres temizleme."""
import re

# ----------------------------------------------------------------------------
# Türkçe büyük/küçük harf
# ----------------------------------------------------------------------------
_UP = {"i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ü": "Ü", "ö": "Ö", "ç": "Ç"}
_LO = {"İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç"}


def tr_upper(s: str) -> str:
    return "".join(_UP.get(c, c) for c in s).upper()


def tr_lower(s: str) -> str:
    return "".join(_LO.get(c, c) for c in s).lower()


def tr_title(s: str) -> str:
    """Türkçe kurallı başlık: her kelimenin ilk harfi büyük, gerisi küçük."""
    parcalar = re.split(r"(\s+)", s)  # boşlukları koru
    out = []
    for p in parcalar:
        if not p.strip():
            out.append(p)
            continue
        # Nokta/eğik çizgi içeren kısımlarda ilk alfabetik harfi büyüt
        low = tr_lower(p)
        yeni = []
        buyut = True
        for ch in low:
            if buyut and ch.isalpha():
                yeni.append(tr_upper(ch))
                buyut = False
            else:
                yeni.append(ch)
        out.append("".join(yeni))
    return "".join(out)


# ----------------------------------------------------------------------------
# Sicil numarası: 26 haneyi 1-4-2-2-7-3-2-2-3 gruplarına noktalı biçimle
#   27020030311107150340530000 -> 2.7020.03.03.1110715.034.05.30.000
# ----------------------------------------------------------------------------
_SICIL_GRUP = [1, 4, 2, 2, 7, 3, 2, 2, 3]


def sicil_formatla(ham: str) -> str:
    rakam = re.sub(r"\D", "", ham or "")
    if len(rakam) != sum(_SICIL_GRUP):  # 26 değilse dokunma
        return ham.strip()
    parcalar, i = [], 0
    for g in _SICIL_GRUP:
        parcalar.append(rakam[i:i + g])
        i += g
    return ".".join(parcalar)


# ----------------------------------------------------------------------------
# Kısa unvan: sondaki jenerik/hukuki kelimeleri at, marka kısmını bırak
#   "GATEWAY MANAGEMENT LOJİSTİK ANONİM ŞİRKETİ" -> "Gateway Management"
#   "DEFACTO PERAKENDE TİCARET ANONİM ŞİRKETİ"   -> "Defacto"
# ----------------------------------------------------------------------------
_JENERIK = {
    "ANONİM", "LİMİTED", "ŞİRKETİ", "ŞTİ", "ŞTİ.", "LTD", "LTD.", "A.Ş", "A.Ş.",
    "AŞ", "TİCARET", "TİC", "TİC.", "SANAYİ", "SAN", "SAN.", "VE",
    "PERAKENDE", "LOJİSTİK", "HİZMETLERİ", "HİZMET", "HİZ", "HİZ.",
    "İTHALAT", "İHRACAT", "İŞLETMELERİ", "İŞLETME", "YÖNETİMİ", "GRUP",
    "PAZARLAMA", "DAĞITIM", "DIŞ", "İÇ", "ORGANİZASYONLARI",
    "TEKNOLOJİ", "TEKNOLOJİLERİ", "SATIŞ", "YAZILIM", "TURİZM",
    "TASARRUF", "FİNANSMAN", "GIDA", "MUTFAK", "DANIŞMANLIK",
    "ÜRETİM", "İNŞAAT", "GAYRİMENKUL", "ENERJİ", "TEKSTİL", "OTOMOTİV",
    "İŞLETİM", "İŞLETMECİLİK",
}

# PDF metin çıkarımında bitişen jenerik ekleri ayır
_YAPISTIK = [
    (r"ANON[İI]MŞ[İI]RKET[İI]", "ANONİM ŞİRKETİ"),
    (r"L[İI]M[İI]TEDŞ[İI]RKET[İI]", "LİMİTED ŞİRKETİ"),
    (r"T[İI]CARETL[İI]M[İI]TED", "TİCARET LİMİTED"),
]


def _yapistik_ayir(s: str) -> str:
    for pat, rep in _YAPISTIK:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    return s


# Noktalı/bitişik kısaltma parçaları (TİC.A.Ş., HİZ.LTD.ŞTİ. gibi)
_KISALT_PARCA = {"TİC", "A", "Ş", "AŞ", "HİZ", "LTD", "ŞTİ", "SAN"}


def _jenerik_mi(token: str) -> bool:
    t = tr_upper(token.rstrip("."))
    if t in _JENERIK:
        return True
    parcalar = [p for p in t.split(".") if p]
    return len(parcalar) >= 2 and all(p in _KISALT_PARCA for p in parcalar)


def kisa_unvan(unvan: str) -> str:
    unvan = _yapistik_ayir(re.sub(r"\s+", " ", (unvan or "").strip()))
    unvan = unvan.rstrip(".")
    tokens = unvan.split(" ")
    while len(tokens) > 1 and _jenerik_mi(tokens[-1]):
        tokens.pop()
    return tr_title(" ".join(tokens))


def unvan_duzelt(unvan: str) -> str:
    """Tam unvanı düzgün başlık biçimine getir (İşveren alanı için)."""
    s = tr_title(_yapistik_ayir(re.sub(r"\s+", " ", (unvan or "").strip())))
    return s.rstrip(" .")


# ----------------------------------------------------------------------------
# Adres temizleme (best-effort): kısaltmaları düzelt, [No:..] at, ilçe/il ekle
# ----------------------------------------------------------------------------
_ADRES_KISALT = [
    (r"\bMAHALLESİ\b", "Mah."), (r"\bMAH\b\.?", "Mah."),
    (r"\bCADDESİ\b", "Cd."), (r"\bCAD\b\.?", "Cd."), (r"\bCD\b\.?", "Cd."),
    (r"\bSOKAK\b", "Sk."), (r"\bSOK\b\.?", "Sk."), (r"\bSK\b\.?", "Sk."),
    (r"\bBULVARI\b", "Bulv."), (r"\bBLV\b\.?", "Bulv."),
    (r"\bAPARTMANI\b", "Apt."), (r"\bAPT\b\.?", "Apt."),
    (r"\bNO\b\.?", "No:"),
]


def adres_temizle(ham_adres: str, ilce_il: str = "") -> str:
    a = re.sub(r"\[No:.*?\]", "", ham_adres or "")   # köşeli parantezli No kısmını at
    a = re.sub(r"\s+", " ", a).strip(" ,")
    a = tr_title(a)
    # kısaltmalar (başlık hâlinde uygula)
    for pat, rep in _ADRES_KISALT:
        a = re.sub(pat, rep, a, flags=re.IGNORECASE)
    a = re.sub(r"\s+", " ", a).strip(" ,")
    # ilçe / il ekle:  "İSTANBUL / BEYOĞLU" -> "Beyoğlu / İstanbul"
    if ilce_il:
        parts = [p.strip() for p in ilce_il.split("/")]
        if len(parts) == 2:
            il, ilce = tr_title(parts[0]), tr_title(parts[1])
            # adresin sonundaki tekrar eden il/ilçe kelimelerini temizle
            tok = a.split(" ")
            while tok and tr_lower(tok[-1].strip(" ,.")) in (tr_lower(il), tr_lower(ilce)):
                tok.pop()
            a = " ".join(tok).strip(" ,")
            a = f"{a} {ilce} / {il}"
    return a.strip()
