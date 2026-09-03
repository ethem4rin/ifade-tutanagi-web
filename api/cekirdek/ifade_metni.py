# -*- coding: utf-8 -*-
"""İfade gövde metni: yeşil (olumlu/olumsuz seçilir) + kırmızı (elle doldurulur) alanlar.

`ALANLAR` arayüzün soracağı alanların şemasını verir.
`govde(v)` bir değer sözlüğü alıp paragraf metinlerini üretir.

Alan tipleri:
  metin  -> serbest yazı (kırmızı/X boşluk)
  secim  -> ('olumlu'/'olumsuz') iki durumlu yeşil geçiş
  kosul  -> True/False; bağlı cümle bloğunu açar/kapatır
"""

# ---------------------------------------------------------------------------
# Alan şeması (arayüz bunu okuyup form üretecek). (anahtar, etiket, tip, varsayılan)
# ---------------------------------------------------------------------------
ALANLAR = [
    ("ise_baslama",   "İşe başlama (yaklaşık yıl/tarih)", "metin",  "2017"),
    ("bolum",         "Bölüm (örn: muhasebe)", "metin", ""),
    ("unvan",         "Unvan (örn: işçi / müdür yardımcısı)", "metin", ""),
    ("gorev_tanimi",  "Yaptığı işler (görev tanımı)", "metin", ""),
    ("kesintisiz",    "Kesintisiz çalışıyor (giriş-çıkış yok)", "kosul", True),
    ("giris_cikis_tarihi", "Giriş-çıkış yaptıysa tarihi (Kesintisiz = Hayır ise)", "metin", ""),

    ("sozlesme",      "İş sözleşmesi imzaladı ve nüsha aldı", "secim", "olumlu"),
    ("ucret_son_ay",  "Son ay alınan ücret (TL)", "metin", ""),
    ("ek_ucret",      "Ücrete ek kalemler (yoksa boş)", "metin", ""),
    ("ucret_ifadesi", "Ücret ödemesi (örn: ilgili ayın 10.günü Ziraat Bankasından)", "metin", ""),
    ("elden_odeme",   "Elden ücret ödemesi", "secim", "olumsuz"),
    ("yabanci",       "İşyerinde yabancı çalışan", "secim", "olumsuz"),

    ("takip_araci",   "Giriş-çıkış takip aracı (PDKS/kart/parmak izi...)", "metin", ""),
    ("vardiya",       "Vardiyalı çalışma var", "kosul", False),
    # vardiya varsa:
    ("v_gun",         "Vardiya: haftada kaç gün", "metin", ""),
    ("v_saat",        "Vardiya saat aralıkları / ara dinlenmeleri", "metin", ""),
    ("v_hafta_tatili","Vardiya: haftada kaç gün hafta tatili", "metin", ""),
    # vardiya yoksa:
    ("n_gun",         "Normal: haftada kaç gün çalışıyor", "metin", ""),
    ("n_saat",        "Normal: saat aralığı + ara dinlenmesi", "metin", ""),
    ("n_tatil_gun",   "Normal: hangi günler hafta tatili", "metin", ""),

    ("fazla_mesai",   "Yoğun dönemde fazla çalışma oluyor", "secim", "olumlu"),
    ("fm_odeme",      "Fazla mesai ödemesi alıyor", "secim", "olumlu"),
    ("ubgt",          "UBGT günlerinde çalışma oluyor", "secim", "olumlu"),
    ("ubgt_odeme",    "UBGT için ilave ücret ödeniyor", "secim", "olumlu"),

    ("izin_gun",      "Kıdeme göre yıllık izin hakkı (gün)", "metin", ""),
    ("bakiye_izin",   "Birikmiş bakiye yıllık izin", "secim", "olumsuz"),
    ("izin_parcali",  "İzinleri parçalı (10 günden az) kullandı", "secim", "olumlu"),

    ("ifade_tarihi",  "İfade tarihi (gg/aa/yyyy)", "metin", ""),
]

VARSAYILAN = {a[0]: a[3] for a in ALANLAR}


def _olumlu(v, key):
    return str(v.get(key, "olumlu")).strip().lower().startswith("oluml") or v.get(key) is True


def _bos_temizle(metin: str) -> str:
    """Doldurulmamış alanlardan kalan çift boşlukları toparlar."""
    return " ".join(metin.split())


def govde(v: dict):
    """Değer sözlüğünden paragraf metinleri listesi üretir."""
    g = {**VARSAYILAN, **(v or {})}
    P = []

    # --- 1. paragraf: kimlik + görev + sözleşme ---
    if g["kesintisiz"] in (True, "olumlu"):
        gc = "Daha önce işe giriş çıkış yapmadım. Kesintisiz olarak çalışıyorum."
    else:
        tarih = str(g.get("giris_cikis_tarihi", "")).strip()
        gc = f"{tarih} tarihinde giriş çıkış yaptım." if tarih else "Daha önce işe giriş çıkış yaptım."

    if _olumlu(g, "sozlesme"):
        sozlesme = "İşe girerken iş sözleşmesi imzaladım ve bir nüshasını aldım."
    else:
        sozlesme = "İşe girerken iş sözleşmesi imzalamadım."

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

    # --- 3. paragraf: giriş-çıkış takibi + çalışma düzeni (tek paragraf) ---
    if g["vardiya"] in (True, "olumlu"):
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
        P.append(_bos_temizle(
            f"İşyerine giriş çıkış saatlerimiz {g['takip_araci']} aracılığı ile takip edilmektedir. "
            f"İşyerimizde vardiyalı çalışma yoktur. "
            f"Ben haftanın {g['n_gun']} günü {g['n_saat']} şekilde çalışıyorum. {g['n_tatil_gun']} "
            f"günlerini hafta tatili kullanıyorum. 7 gün üst üste olacak şekilde yani hafta tatili "
            f"kullanmaksızın çalıştığım olmadı."
        ))

    # --- fazla mesai ---
    if _olumlu(g, "fazla_mesai"):
        fm = "İşlerin yoğun olduğu dönemde normal çalışma sürelerimin üzerinde çalıştığım olmaktadır."
        if _olumlu(g, "fm_odeme"):
            fm += " Bu çalışmalarım karşılığında fazla mesai ödemesi almaktayım."
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
    bakiye = ("İçerde birikmiş bakiye yıllık iznim bulunmamaktadır."
              if not _olumlu(g, "bakiye_izin") else "İçerde birikmiş bakiye yıllık iznim bulunmaktadır.")
    parcali = (" Ben geçtiğimiz dönem yıllık izinlerimi 10 günden aşağı olacak şekilde "
               "parçalar halinde kullandım." if _olumlu(g, "izin_parcali") else "")
    P.append(_bos_temizle(
        f"Benim kıdemimden ötürü {g['izin_gun']} gün kadar yıllık izin hakkım vardır. {bakiye} "
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
