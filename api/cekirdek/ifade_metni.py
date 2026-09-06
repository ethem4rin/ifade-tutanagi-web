# -*- coding: utf-8 -*-
"""İfade gövde metni: yeşil (seçilir) + kırmızı (elle doldurulur) alanlar.

`ALANLAR` arayüzün soracağı alanların şemasını verir.
`govde(v)` bir değer sözlüğü alıp paragraf metinlerini üretir.

Alan tipleri:
  metin    -> serbest yazı (kırmızı/X boşluk)
  secim    -> 'olumlu'/'olumsuz' iki durumlu yeşil geçiş
  kosul    -> True/False; bağlı cümle bloğunu açar/kapatır
  secenek  -> `secenekler` listesinden biri seçilir

Kapsam:
  isci    -> her işçi için ayrı sorulur
  isyeri  -> işyeri seçildikten sonra bir kez sorulur, tüm işçiler için aynı kalır
"""

VARDIYA_YOK = "Bulunmamaktadır"          # yıllık izin seçeneği
IZIN_SECENEKLERI = [VARDIYA_YOK, "14", "20", "26"]


def _a(anahtar, etiket, tip, varsayilan, kapsam="isci", secenekler=None):
    d = {"anahtar": anahtar, "etiket": etiket, "tip": tip,
         "varsayilan": varsayilan, "kapsam": kapsam}
    if secenekler:
        d["secenekler"] = secenekler
    return d


# ---------------------------------------------------------------------------
# Alan şeması — arayüz bunu okuyup formu üretir
# ---------------------------------------------------------------------------
ALANLAR = [
    # ---- işyeri geneli: bir kez sorulur, tüm işçilerde aynı ----
    _a("takip_araci", "İşyerinde çalışma sürelerinin takibi (PDKS/kart/imza föyü...)",
       "metin", "", kapsam="isyeri"),
    _a("ucret_ifadesi", "Ücret ödeme günü ve bankası (örn: ilgili ayın 10.günü Ziraat Bankasından)",
       "metin", "", kapsam="isyeri"),

    # ---- işçiye özel ----
    _a("ise_baslama", "İşe başlama (yaklaşık yıl/tarih)", "metin", "2017"),
    _a("bolum", "Bölüm (örn: muhasebe)", "metin", ""),
    _a("unvan", "Unvan (örn: işçi / müdür yardımcısı)", "metin", ""),
    _a("gorev_tanimi", "Yaptığı işler (görev tanımı)", "metin", ""),

    _a("giris_cikis", "İşe giriş-çıkış yaptı mı", "kosul", False),
    _a("cikis_yili", "Çıkış yılı (giriş-çıkış = Evet ise)", "metin", ""),
    _a("giris_yili", "Tekrar giriş yılı (giriş-çıkış = Evet ise)", "metin", ""),

    _a("sozlesme", "İş sözleşmesi imzaladı ve nüsha aldı", "secim", "olumlu"),
    _a("ucret_son_ay", "Son ay alınan ücret (TL)", "metin", ""),
    _a("ek_ucret", "Ücrete ek kalemler (yoksa boş)", "metin", ""),
    _a("elden_odeme", "Elden ücret ödemesi", "secim", "olumsuz"),
    _a("yabanci", "İşyerinde yabancı çalışan", "secim", "olumsuz"),

    _a("vardiya", "Vardiyalı çalışıyor", "kosul", False),
    # vardiya varsa:
    _a("v_gun", "Vardiya: haftada kaç gün", "metin", ""),
    _a("v_saat", "Vardiya saat aralıkları / ara dinlenmeleri", "metin", ""),
    _a("v_hafta_tatili", "Vardiya: haftada kaç gün hafta tatili", "metin", ""),
    # vardiya yoksa:
    _a("n_gun", "Normal: haftada kaç gün çalışıyor", "metin", ""),
    _a("n_saat", "Normal: saat aralığı + ara dinlenmesi", "metin", ""),
    _a("n_tatil_gun", "Normal: hangi günler hafta tatili", "metin", ""),

    _a("fazla_mesai", "Yoğun dönemde fazla çalışma oluyor", "secim", "olumlu"),
    _a("fm_odeme", "Fazla çalışma ödemesi alıyor", "secim", "olumlu"),
    _a("ubgt", "UBGT günlerinde çalışma oluyor", "secim", "olumlu"),
    _a("ubgt_odeme", "UBGT için ilave ücret ödeniyor", "secim", "olumlu"),

    _a("izin_gun", "Yıllık izin hakkı", "secenek", "14", secenekler=IZIN_SECENEKLERI),
    _a("bakiye_izin", "Birikmiş bakiye yıllık izin", "secim", "olumsuz"),
    _a("izin_parcali", "İzinleri parçalı (10 günden az) kullandı", "secim", "olumlu"),

    _a("ifade_tarihi", "İfade tarihi (gg/aa/yyyy)", "metin", ""),
]

VARSAYILAN = {a["anahtar"]: a["varsayilan"] for a in ALANLAR}

# İşyeri seçilince bir kez sorulan alanlar
ISYERI_ALANLARI = [a["anahtar"] for a in ALANLAR if a["kapsam"] == "isyeri"]


def _olumlu(v, key):
    return str(v.get(key, "olumlu")).strip().lower().startswith("oluml") or v.get(key) is True


def _acik(v, key):
    """kosul tipi alan açık mı (True / 'olumlu')."""
    return v.get(key) in (True, "olumlu", "True", "true")


def _bos_temizle(metin: str) -> str:
    """Doldurulmamış alanlardan kalan çift boşlukları toparlar."""
    return " ".join(metin.split())


def govde(v: dict):
    """Değer sözlüğünden paragraf metinleri listesi üretir."""
    g = {**VARSAYILAN, **(v or {})}
    P = []

    # --- 1. paragraf: kimlik + görev + sözleşme ---
    if _acik(g, "giris_cikis"):
        cikis = str(g.get("cikis_yili", "")).strip()
        giris = str(g.get("giris_yili", "")).strip()
        if cikis and giris:
            gc = f"{cikis} yılında çıktım, {giris} yılında girdim."
        elif cikis:
            gc = f"{cikis} yılında çıktım."
        else:
            gc = "Daha önce işe giriş çıkış yaptım."
    else:
        gc = "Daha önce işe giriş çıkış yapmadım. Kesintisiz olarak çalışıyorum."

    sozlesme = ("İşe girerken iş sözleşmesi imzaladım ve bir nüshasını aldım."
                if _olumlu(g, "sozlesme") else "İşe girerken iş sözleşmesi imzalamadım.")

    P.append(_bos_temizle(
        f"Adı geçen; {g.get('ad_soyad','')} isimli işçi; “Ben yaklaşık {g['ise_baslama']} "
        f"tarihinden itibaren işyerinde çalışıyorum. Hâlihazırda {g['bolum']} bölümünde "
        f"{g['unvan']} olarak görev yapmaktayım. {gc} Ben işyerinde {g['gorev_tanimi']} "
        f"görevlerini yerine getiriyorum. {sozlesme}"
    ))

    # --- 2. paragraf: ücret ---
    ek = (f" Ücretime ek olarak {g['ek_ucret']} kalemlerinde ücret alıyorum."
          if str(g["ek_ucret"]).strip() else "")
    elden = "Elden ücret ödemesi yoktur." if not _olumlu(g, "elden_odeme") else "Elden ücret ödemesi vardır."
    yabanci = ("Ben işyerinde yabancı çalışana rastlamadım."
               if not _olumlu(g, "yabanci") else "Ben işyerinde yabancı çalışana rastladım.")
    P.append(_bos_temizle(
        f"Ben son ay yaklaşık {g['ucret_son_ay']} tl ücret aldım.{ek} "
        f"Ücretim {g['ucret_ifadesi']} yatırılmaktadır. "
        f"İşyerinden ücret alacağım bulunmamaktadır. {elden} "
        f"Ücret hesap pusulaları düzenli olarak tarafımla paylaşılmaktadır. {yabanci}"
    ))

    # --- 3. paragraf: çalışma sürelerinin takibi + çalışma düzeni ---
    if _acik(g, "vardiya"):
        P.append(_bos_temizle(
            f"İşyerine giriş çıkış saatlerimiz {g['takip_araci']} aracılığı ile takip edilmektedir. "
            f"İşyerimizde vardiyalı çalışma vardır. Ben de vardiyalı olarak çalışıyorum. "
            f"Ben haftanın {g['v_gun']} günü {g['v_saat']} şeklinde dönüşümlü olarak çalışmaktayım. "
            f"Bu çalışma düzeninde haftanın {g['v_hafta_tatili']} günü kadar hafta tatili kullanmaktayım. "
            f"Vardiyalarımız dönüşümlü olarak düzenlenmektedir. Daimi gece çalışması (2 haftayı aşacak "
            f"şekilde gece çalışması) yapmıyorum. 7 gün üst üste olacak şekilde yani hafta tatili "
            f"kullanmaksızın çalıştığım olmadı."
        ))
    else:
        # "İşyerimizde vardiyalı çalışma yoktur." ibaresi kaldırıldı
        P.append(_bos_temizle(
            f"İşyerine giriş çıkış saatlerimiz {g['takip_araci']} aracılığı ile takip edilmektedir. "
            f"Ben haftanın {g['n_gun']} günü {g['n_saat']} şekilde çalışıyorum. {g['n_tatil_gun']} "
            f"günlerini hafta tatili kullanıyorum. 7 gün üst üste olacak şekilde yani hafta tatili "
            f"kullanmaksızın çalıştığım olmadı."
        ))

    # --- fazla çalışma ---
    if _olumlu(g, "fazla_mesai"):
        fm = "İşlerin yoğun olduğu dönemde normal çalışma sürelerimin üzerinde çalıştığım olmaktadır."
        if _olumlu(g, "fm_odeme"):
            fm += " Bu çalışmalarım karşılığında fazla çalışma ödemesi almaktayım."
        P.append(fm)
    else:
        P.append("İşlerin yoğun olduğu dönemde normal çalışma sürelerimin üzerinde çalıştığım olmamaktadır.")

    # --- UBGT ---
    if _olumlu(g, "ubgt"):
        ub = "Ulusal bayram ve genel tatil günlerinde genellikle bir çalışma olmaktadır."
        if _olumlu(g, "ubgt_odeme"):
            ub += " Çalıştığımız bu günler için ilave bir ücret ödemesi yapılmaktadır."
        P.append(ub)
    else:
        P.append("Ulusal bayram ve genel tatil günlerinde genellikle bir çalışma olmamaktadır.")

    # --- yıllık izin ---
    izin = str(g.get("izin_gun", "")).strip()
    if not izin or izin.lower() == VARDIYA_YOK.lower():
        izin_cumlesi = "Benim kıdemimden ötürü yıllık izin hakkım bulunmamaktadır."
    else:
        izin_cumlesi = f"Benim kıdemimden ötürü yıllık izin hakkım {izin} gündür."
    bakiye = ("İçerde birikmiş bakiye yıllık iznim bulunmamaktadır."
              if not _olumlu(g, "bakiye_izin") else "İçerde birikmiş bakiye yıllık iznim bulunmaktadır.")
    parcali = (" Ben geçtiğimiz dönem yıllık izinlerimi 10 günden aşağı olacak şekilde "
               "parçalar halinde kullandım." if _olumlu(g, "izin_parcali") else "")
    P.append(_bos_temizle(
        f"{izin_cumlesi} {bakiye} "
        f"Yıllık izin dönemine ait ücretleri peşin veya avans olarak ödenmemektedir.{parcali} ” dedi."
    ))

    return P


def kapanis(v: dict):
    tarih = (v or {}).get("ifade_tarihi", "")
    return ("Bu konuda başka bir diyeceği olmadığını ifade ettiğinden, işbu tutanak alınan ifadeye "
            f"göre işyerinde düzenlendi. İfade sahibince okundu, doğruluğu kabul edilerek imzalandı. {tarih}")


def dosya_adi(sira, ad_soyad: str) -> str:
    """Örn: 'İfade 1 Ethem Arın İsimli İşçinin İfade Tutanağı.docx'"""
    ad = " ".join(str(ad_soyad or "").split()) or "İsimsiz"
    for c in '<>:"/\\|?*':
        ad = ad.replace(c, " ")
    ad = " ".join(ad.split())
    return f"İfade {sira} {ad} İsimli İşçinin İfade Tutanağı.docx"
