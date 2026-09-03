/* İşçi İfade Tutanağı — web arayüz mantığı */
"use strict";

// [anahtar, etiket, otomatikTamamlama]
// Hafızada yalnızca ad ve soyad tutulur; diğer alanlar her seferinde elle girilir.
const KIMLIK = [
  ["ad", "Adı", true],
  ["soyad", "Soyadı", true],
  ["dogum_yeri_yili", "Doğum Yeri/Yılı", false],
  ["baba_ana", "Baba/Ana Adı", false],
  ["gorevi", "Görevi", false],
  ["tc", "T.C. Kimlik No", false],
  ["telefon", "Telefon No", false],
  ["ikametgah", "İkametgahı", false],
];

let jeton = localStorage.getItem("jeton") || "";
let veri = null;          // parse edilmiş PDF
let secili = null;        // seçili işyeri
let alanSemasi = [];      // ifade alanları
let paketListe = [];      // toplu ZIP için biriken işçiler
let siraSayaci = 1;       // tutanak numarası — her indirme/eklemede artar

const $ = (s) => document.querySelector(s);
const el = (t, c) => { const e = document.createElement(t); if (c) e.className = c; return e; };

/* ---------------- API ---------------- */
async function api(yol, secenek = {}) {
  const bas = secenek.headers || {};
  if (jeton) bas["Authorization"] = "Bearer " + jeton;
  if (secenek.json !== undefined) {
    bas["Content-Type"] = "application/json";
    secenek.body = JSON.stringify(secenek.json);
    secenek.method = secenek.method || "POST";
  }
  const y = await fetch("/api" + yol, { ...secenek, headers: bas });
  // 401 giriş/kayıt uçlarında "hatalı şifre" demektir; oturum düştü sanıp
  // kullanıcıyı yanıltmayalım — gerçek hata mesajı aşağıda okunur.
  const kimlikUcu = yol.startsWith("/giris") || yol.startsWith("/kayit");
  if (y.status === 401 && !kimlikUcu) {
    cikisYap();
    throw new Error("Oturum sona erdi, tekrar giriş yapın.");
  }
  if (!y.ok) {
    let m = "İşlem başarısız.";
    try { m = (await y.json()).detail || m; } catch (e) {}
    throw new Error(m);
  }
  return y;
}
const apiJson = async (y, s) => (await api(y, s)).json();

async function apiIndir(yol, govde, varsayilanAd) {
  const y = await api(yol, { json: govde });
  const blob = await y.blob();
  let ad = varsayilanAd;
  const cd = y.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename\*=UTF-8''(.+)$/);
  if (m) { try { ad = decodeURIComponent(m[1]); } catch (e) {} }
  const url = URL.createObjectURL(blob);
  const a = el("a"); a.href = url; a.download = ad;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function bildir(mesaj, hatali) {
  const b = $("#bildirim");
  b.textContent = mesaj;
  b.className = "bildirim" + (hatali ? " hatali" : "");
  clearTimeout(b._z);
  b._z = setTimeout(() => b.classList.add("gizli"), 4200);
}

/* ---------------- giriş ---------------- */
document.querySelectorAll(".sekme").forEach((s) => {
  s.onclick = () => {
    document.querySelectorAll(".sekme").forEach((x) => x.classList.remove("aktif"));
    s.classList.add("aktif");
    const kayit = s.dataset.sekme === "kayit";
    $("#girisForm").classList.toggle("gizli", kayit);
    $("#kayitForm").classList.toggle("gizli", !kayit);
    $("#girisHata").classList.add("gizli");
  };
});

function girisHata(mesaj) {
  const h = $("#girisHata");
  h.textContent = mesaj;
  h.classList.remove("gizli");
}

["#gAd", "#gSifre", "#kAd", "#kSifre"].forEach((sec) => {
  $(sec).addEventListener("input", () => $("#girisHata").classList.add("gizli"));
});

$("#girisForm").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const c = await apiJson("/giris", { json: { ad: $("#gAd").value, sifre: $("#gSifre").value } });
    jeton = c.jeton; localStorage.setItem("jeton", jeton);
    baslat(c.kullanici.tam_ad || c.kullanici.ad);
  } catch (err) { girisHata(err.message); }
};

$("#kayitForm").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const c = await apiJson("/kayit", {
      json: { ad: $("#kAd").value, sifre: $("#kSifre").value, tam_ad: $("#kTamAd").value },
    });
    jeton = c.jeton; localStorage.setItem("jeton", jeton);
    baslat(c.kullanici.tam_ad || c.kullanici.ad);
  } catch (err) { girisHata(err.message); }
};

$("#cikisBtn").onclick = async () => {
  try { await api("/cikis", { method: "POST" }); } catch (e) {}
  cikisYap();
};

function cikisYap() {
  jeton = ""; localStorage.removeItem("jeton");
  $("#uygulama").classList.add("gizli");
  $("#girisEkran").classList.remove("gizli");
}

async function baslat(adi) {
  const h = $("#girisHata");
  h.textContent = ""; h.classList.add("gizli");   // eski hata kalmasın
  $("#gSifre").value = ""; $("#kSifre").value = "";
  $("#girisEkran").classList.add("gizli");
  $("#uygulama").classList.remove("gizli");
  $("#kullaniciEtiket").textContent = "👤 " + adi;
  const s = await apiJson("/alanlar");
  alanSemasi = s.alanlar;
  kimlikKur();
  ifadeKur();
}

/* ---------------- otomatik tamamlama ---------------- */
function otoTamamla(girdi, alan, secilince) {
  const sarmal = el("div", "oto-sarmal");
  girdi.parentNode.insertBefore(sarmal, girdi);
  sarmal.appendChild(girdi);
  let liste = null, oneriler = [], indeks = -1;

  const kapat = () => { if (liste) { liste.remove(); liste = null; indeks = -1; } };

  const goster = (secenekler) => {
    kapat();
    if (!secenekler.length) return;
    liste = el("div", "oneri-liste");
    secenekler.forEach((deger, i) => {
      const d = el("div");
      d.textContent = deger;
      d.onmousedown = (e) => { e.preventDefault(); sec(deger); };
      liste.appendChild(d);
    });
    sarmal.appendChild(liste);
    oneriler = secenekler;
  };

  const sec = (deger) => {
    girdi.value = deger;
    kapat();
    if (secilince) secilince(deger);
  };

  girdi.addEventListener("input", async () => {
    const yazi = girdi.value.trim().toLowerCase();
    if (!yazi) return kapat();
    let tum = [];
    try { tum = (await apiJson("/oneriler?alan=" + encodeURIComponent(alan))).oneriler; }
    catch (e) { return; }
    const esl = tum.filter((s) => s.toLowerCase().includes(yazi))
      .sort((a, b) => (a.toLowerCase().startsWith(yazi) ? 0 : 1) - (b.toLowerCase().startsWith(yazi) ? 0 : 1))
      .slice(0, 8);
    if (esl.length === 1 && esl[0].toLowerCase() === yazi) return kapat();
    goster(esl);
  });

  girdi.addEventListener("keydown", (e) => {
    if (!liste) return;
    const ogeler = [...liste.children];
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      indeks += e.key === "ArrowDown" ? 1 : -1;
      if (indeks < 0) indeks = ogeler.length - 1;
      if (indeks >= ogeler.length) indeks = 0;
      ogeler.forEach((o, i) => o.classList.toggle("secili", i === indeks));
    } else if (e.key === "Enter" && indeks >= 0) {
      e.preventDefault(); sec(oneriler[indeks]);
    } else if (e.key === "Escape") kapat();
  });

  girdi.addEventListener("blur", () => setTimeout(kapat, 160));
}

/* ---------------- kimlik bölümü ---------------- */
function kimlikKur() {
  const izgara = $("#kimlikIzgara");
  izgara.innerHTML = "";
  KIMLIK.forEach(([anahtar, etiket, oto]) => {
    const l = el("label"); l.textContent = etiket;
    const g = el("input"); g.type = "text"; g.id = "k_" + anahtar;
    izgara.appendChild(l); izgara.appendChild(g);
    if (oto) otoTamamla(g, anahtar, null);
  });
}

/* ---------------- ifade bölümü ---------------- */
function ifadeKur() {
  const kap = $("#ifadeAlanlar");
  kap.innerHTML = "";
  alanSemasi.forEach((a) => {
    const satir = el("div", "ifade-satir");
    const soru = el("div", "soru");
    const nokta = el("span", "nokta " + (a.tip === "metin" ? "kirmizi" : "yesil"));
    soru.appendChild(nokta);
    soru.appendChild(document.createTextNode(a.etiket));
    satir.appendChild(soru);

    if (a.tip === "metin") {
      const g = el("input"); g.type = "text"; g.id = "f_" + a.anahtar;
      if (a.varsayilan) g.value = a.varsayilan;
      satir.appendChild(g);
      otoTamamla(g, a.anahtar, null);
    } else {
      const etiket = el("label", "anahtar");
      const g = el("input"); g.type = "checkbox"; g.id = "f_" + a.anahtar;
      const acik = a.varsayilan === true ||
        String(a.varsayilan).toLowerCase().startsWith("oluml");
      g.checked = acik;
      const kaydirak = el("span", "kaydirak");
      const metin = el("span", "metin"); metin.textContent = acik ? "Evet" : "Hayır";
      g.onchange = () => { metin.textContent = g.checked ? "Evet" : "Hayır"; };
      etiket.appendChild(g); etiket.appendChild(kaydirak); etiket.appendChild(metin);
      satir.appendChild(etiket);
    }
    kap.appendChild(satir);
  });
}

/* ---------------- PDF ---------------- */
$("#pdfGirdi").onchange = async (e) => {
  const dosya = e.target.files[0];
  if (!dosya) return;
  const fd = new FormData(); fd.append("dosya", dosya);
  $("#pdfDurum").textContent = "okunuyor…";
  try {
    veri = await (await api("/pdf", { method: "POST", body: fd })).json();
  } catch (err) {
    $("#pdfDurum").textContent = "hata";
    return bildir(err.message, true);
  }
  const n = veri.isyerleri.length;
  const d = $("#pdfDurum");
  d.textContent = "✓ " + n + " işyeri bulundu";
  d.className = "durum ok";
  const s = $("#isyeriSecim");
  s.innerHTML = "";
  veri.isyerleri.forEach((k, i) => {
    const o = el("option"); o.value = i; o.textContent = k.sira + ". " + k.unvan_kisa;
    s.appendChild(o);
  });
  $("#isyeriSatir").style.display = "";
  isyeriSec(0);
  ["#isyeriKart", "#kimlikKart", "#ifadeKart", "#onizlemeKart", "#kaydetKart"]
    .forEach((x) => $(x).classList.remove("gizli"));
};

$("#isyeriSecim").onchange = (e) => isyeriSec(+e.target.value);

function isyeriSec(i) {
  secili = veri.isyerleri[i];
  // yeni işyeri -> tutanak numaralandırması baştan başlar
  siraSayaci = 1;
  paketListe = [];
  listeYenile();
  siraGoster();
  $("#iSicil").value = secili.sicil;
  $("#iUnvan").value = secili.unvan_kisa;
  $("#iIsveren").value = secili.isveren;
  $("#iAdres").value = secili.adres;
}

/* ---------------- veri toplama ---------------- */
function isyeriTopla() {
  return {
    sicil: $("#iSicil").value.trim(),
    unvan_kisa: $("#iUnvan").value.trim(),
    isveren: $("#iIsveren").value.trim(),
    adres: $("#iAdres").value.trim(),
    gorev_no: secili ? secili.gorev_no : "",
    unvan_tam: secili ? secili.unvan_tam : "",
    adres_ham: secili ? secili.adres_ham : "",
  };
}

function isciTopla() {
  const d = {};
  KIMLIK.forEach(([a]) => { d[a] = $("#k_" + a).value.trim(); });
  // belge ve dosya adı için tam ad
  d.ad_soyad = [d.ad, d.soyad].filter(Boolean).join(" ");
  alanSemasi.forEach((a) => {
    const g = document.getElementById("f_" + a.anahtar);
    if (!g) return;
    d[a.anahtar] = a.tip === "metin" ? g.value.trim() : g.checked;
  });
  return d;
}

function onizlemeParagraflar() {
  const ham = $("#onizlemeMetin").value.trim();
  if (!ham) return [null, null];
  const bloklar = ham.split(/\n\s*\n/).map((b) => b.replace(/\s*\n\s*/g, " ").trim()).filter(Boolean);
  if (!bloklar.length) return [null, null];
  return [bloklar.slice(0, -1), bloklar[bloklar.length - 1]];
}

/* ---------------- önizleme ---------------- */
$("#onizlemeBtn").onclick = async () => {
  try {
    const c = await apiJson("/onizleme", { json: { isci: isciTopla() } });
    $("#onizlemeMetin").value = c.paragraflar.concat([c.kapanis]).join("\n\n");
  } catch (err) { bildir(err.message, true); }
};

/* ---------------- indirme ---------------- */
function govdeKur(sira) {
  const [paragraflar, kapanis] = onizlemeParagraflar();
  return {
    isyeri: isyeriTopla(), baslik: veri.baslik, isci: isciTopla(),
    sira: sira, paragraflar: paragraflar, kapanis: kapanis,
  };
}

$("#indirBtn").onclick = async () => {
  const ad = [$("#k_ad").value.trim(), $("#k_soyad").value.trim()].filter(Boolean).join(" ");
  if (!$("#k_ad").value.trim() || !$("#k_soyad").value.trim())
    return bildir("Adı ve Soyadı boş olamaz.", true);
  try {
    await apiIndir("/tutanak", govdeKur(siraSayaci), "İfade Tutanağı.docx");
    bildir("İfade " + siraSayaci + " — " + ad + " indirildi ve hafızaya kaydedildi.");
    siraSayaci++;                 // sonraki işçi 2, 3, 4 ... diye devam etsin
    siraGoster();
    formTemizle();
  } catch (err) { bildir(err.message, true); }
};

function siraGoster() {
  const e = document.querySelector("#siraEtiket");
  if (e) e.textContent = "Sıradaki tutanak no: " + siraSayaci;
}

$("#listeyeBtn").onclick = () => {
  const ad = [$("#k_ad").value.trim(), $("#k_soyad").value.trim()].filter(Boolean).join(" ");
  if (!$("#k_ad").value.trim() || !$("#k_soyad").value.trim())
    return bildir("Adı ve Soyadı boş olamaz.", true);
  const [paragraflar, kapanis] = onizlemeParagraflar();
  paketListe.push({ isci: isciTopla(), paragraflar, kapanis, sira: siraSayaci });
  bildir("İfade " + siraSayaci + " — " + ad + " pakete eklendi.");
  siraSayaci++;
  siraGoster();
  listeYenile();
  formTemizle();
};

function listeYenile() {
  $("#listeDurum").classList.toggle("gizli", !paketListe.length);
  $("#listeSayi").textContent = paketListe.length;
  const u = $("#listeUl"); u.innerHTML = "";
  paketListe.forEach((k, i) => {
    const li = el("li");
    li.textContent = "İfade " + (k.sira || i + 1) + " — " + (k.isci.ad_soyad || "(isimsiz)");
    u.appendChild(li);
  });
}

$("#paketBtn").onclick = async () => {
  try {
    await apiIndir("/paket",
      { isyeri: isyeriTopla(), baslik: veri.baslik, isciler: paketListe },
      "ekler dizimi.zip");
    bildir("ZIP indirildi — masaüstüne çıkarabilirsiniz.");
    paketListe = []; listeYenile(); siraGoster();
  } catch (err) { bildir(err.message, true); }
};

/* ---------------- işveren formu ---------------- */
$("#formOlusturBtn").onclick = async () => {
  try {
    await apiIndir("/form", { isyeri: isyeriTopla(), satir: 30 }, "İşçi Bilgi Formu.xlsx");
    bildir("Boş form indirildi — işverene gönderebilirsiniz.");
  } catch (err) { bildir(err.message, true); }
};

$("#formGirdi").onchange = async (e) => {
  const dosya = e.target.files[0];
  if (!dosya) return;
  const fd = new FormData(); fd.append("dosya", dosya);
  let isciler;
  try { isciler = (await (await api("/form-oku", { method: "POST", body: fd })).json()).isciler; }
  catch (err) { return bildir(err.message, true); }
  if (!isciler.length) return bildir("Formda işçi bulunamadı.", true);
  const s = $("#formIsciSecim");
  s.innerHTML = "";
  isciler.forEach((k, i) => {
    const o = el("option"); o.value = i; o.textContent = (i + 1) + ". " + k.ad_soyad;
    s.appendChild(o);
  });
  s.style.display = "";
  s._isciler = isciler;
  s.onchange = () => formIsciSec(+s.value);
  formIsciSec(0);
  bildir(isciler.length + " işçi yüklendi — listeden seçip ifade bilgilerini girin.");
};

function formIsciSec(i) {
  const isc = $("#formIsciSecim")._isciler[i];
  KIMLIK.forEach(([a]) => { if (isc[a] !== undefined) $("#k_" + a).value = isc[a] || ""; });
  // Excel'de tek sütun "Adı Soyadı" varsa ad/soyad olarak böl
  if (isc.ad === undefined && isc.ad_soyad) {
    const p = isc.ad_soyad.trim().split(/\s+/);
    $("#k_soyad").value = p.length > 1 ? p.pop() : "";
    $("#k_ad").value = p.join(" ");
  }
}

/* ---------------- temizle ---------------- */
$("#yeniBtn").onclick = formTemizle;

function formTemizle() {
  KIMLIK.forEach(([a]) => { $("#k_" + a).value = ""; });
  alanSemasi.forEach((a) => {
    const g = document.getElementById("f_" + a.anahtar);
    if (g && a.tip === "metin") g.value = a.varsayilan || "";
  });
  $("#onizlemeMetin").value = "";
}

/* ---------------- açılış ---------------- */
(async function () {
  if (!jeton) return;
  try {
    const c = await apiJson("/ben");
    await baslat(c.kullanici);
  } catch (e) { cikisYap(); }
})();
