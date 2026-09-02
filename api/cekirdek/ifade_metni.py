# -*- coding: utf-8 -*-
"""İfade gövde metni: yeşil (olumlu/olumsuz seçilir) + kırmızı (elle doldurulur) alanlar.

`alanlar()` arayüzün soracağı alanların şemasını verir.
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
    ("bolum_gorev",   "Bölüm + unvan (örn: operasyon bölümünde müdür yardımcısı unvanı)", "metin", ""),
    ("gorev_tanimi",  "Yaptığı işler (görev tanımı)", "metin", ""),
    ("kesintisiz",    "Kesintisiz çalışıyor (giriş-çıkış yok)", "kosul", True),

    ("sozlesme",      "İş sözleşmesi imzaladı ve nüsha aldı", "secim", "olumlu"),
    ("ucret_son_ay",  "Son ay alınan ücret (TL)", "metin", ""),
    ("ek_ucret",      "Ücrete ek kalemler (yoksa boş)", "metin", ""),
    ("ucret_gunu",    "Ücret ödeme günü", "metin", "10"),
    ("banka",         "Ücretin yatırıldığı banka", "metin", ""),
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


def govde(v: dict):
    """Değer sözlüğünden paragraf metinleri listesi üretir."""
    g = {**VARSAYILAN, **(v or {})}
    P = []

    # --- 1. paragraf ---
    if g["kesintisiz"] in (True, "olumlu", "olumlu"):
        gc = "Daha önce işe giriş çıkış yapmadım. Kesintisiz olarak çalışıyorum."
    else:
        gc = "Daha önce işe giriş çıkış yaptım."
    # iş sözleşmesi cümlesi 1. paragrafın sonuna eklenir
    if _olumlu(g, "sozlesme"):
        sozlesme = "İşe girerken iş sözleşmesi imzaladım ve bir nüshasını aldım."
    else:
        sozlesme = "İşe girerken iş sözleşmesi imzalamadım."
    P.append(
        f"Adı geçen; {g.get('ad_soyad','')} isimli işçi; “Ben yaklaşık {g['ise_baslama']} "
        f"tarihinden itibaren işyerinde çalışıyorum. Hâlihazırda {g['bolum_gorev']} ile görev "
        f"yapmaktayım. {gc} Ben işyerinde {g['gorev_tanimi']} görevlerini yerine getiriyorum. "
        f"{sozlesme}"
    )

    # --- 2. paragraf: ücret (son ay ücreti giriş cümlesi) ---
    ek = f" Ücretime ek olarak {g['ek_ucret']} kalemlerinde ücret alıyorum." if g["ek_ucret"].strip() else ""
    elden = "Elden ücret ödemesi yoktur." if not _olumlu(g, "elden_odeme") else "Elden ücret ödemesi vardır."
    yabanci = ("Ben işyerinde yabancı çalışana rastlamadım."
               if not _olumlu(g, "yabanci") else "Ben işyerinde yabancı çalışana rastladım.")
    P.append(
        f"Ben son ay yaklaşık {g['ucret_son_ay']} tl ücret aldım.{ek} "
        f"Ücretim ilgili ayı takip eden ayın {g['ucret_gunu']}.günü {g['banka']}ndan yatırılmaktadır. "
        f"İşyerinden ücret alacağım bulunmamaktadır. {elden} Ücret hesap pusulalarımız işverenliğin "
        f"sistemi üzerinden tarafımızla paylaşılmaktadır. {yabanci}"
    )

    # --- 4. paragraf: giriş-çıkış + vardiya ---
    if g["vardiya"] in (True, "olumlu"):
        P.append(
            f"İşyerine giriş çıkış saatlerimiz {g['takip_araci']} aracılığı ile takip edilmektedir. "
            f"İşyerimizde vardiyalı çalışma vardır. Ben de vardiyalı olarak çalışıyorum. "
            f"Ben haftanın {g['v_gun']} günü {g['v_saat']} şeklinde dönüşümlü olarak çalışmaktayım. "
            f"Bu çalışma düzeninde haftanın {g['v_hafta_tatili']} günü kadar hafta tatili kullanmaktayım. "
            f"Vardiyalarımız dönüşümlü olarak düzenlenmektedir. Daimi gece çalışması (2 haftayı aşacak "
            f"şekilde gece çalışması) yapmıyorum. 7 gün üst üste olacak şekilde yani hafta tatili "
            f"kullanmaksızın çalıştığım olmadı."
        )
    else:
        P.append(
            f"İşyerine giriş çıkış saatlerimiz {g['takip_araci']} aracılığı ile takip edilmektedir. "
            f"İşyerimizde vardiyalı çalışma yoktur. "
            f"Ben haftanın {g['n_gun']} günü {g['n_saat']} şekilde çalışıyorum. {g['n_tatil_gun']} "
            f"günlerini hafta tatili kullanıyorum. 7 gün üst üste olacak şekilde yani hafta tatili "
            f"kullanmaksızın çalıştığım olmadı."
        )

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
    P.append(
        f"Benim kıdemimden ötürü {g['izin_gun']} gün kadar yıllık izin hakkım vardır. {bakiye} "
        f"Yıllık izin dönemine ait ücretleri peşin veya avans olarak ödenmemektedir.{parcali} ” dedi."
    )

    return P


def kapanis(v: dict):
    tarih = (v or {}).get("ifade_tarihi", "")
    return ("Bu konuda başka bir diyeceği olmadığını ifade ettiğinden, işbu tutanak alınan ifadeye "
            f"göre işyerinde düzenlendi. İfade sahibince okundu, doğruluğu kabul edilerek imzalandı. {tarih}")
