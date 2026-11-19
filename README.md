# SAP Stok Yönetimi (MM) – Python Analiz Aracı

SAP ERP'nin malzeme yönetimi (MM) modülündeki stok sürecini, sentetik bir SQLite veritabanı üzerinde Python ile yeniden kuran öğrenme ve analiz projesidir. Stok bakiyesi, hareket listesi ve yeniden sipariş planlaması üretir; sonuçları terminale, Excel'e ve CSV'ye yazar.

> Bu proje gerçek bir SAP sistemine bağlanmaz. Veri, SAP tablo yapısına benzeyen simülasyon verisidir.

## Neden SAP'de stok yönetimi?

Örnek şirket: **Mavi Pak Plastik A.Ş.**, iki fabrikalı bir plastik ambalaj üreticisi.

Excel ile yönetildiğinde tipik sorunlar:

- Depo kaydı gerçek stokla tutmaz, üretim hattı hammadde bulamaz.
- Aynı malzeme iki depoda durur, kimse fark etmez.
- Muhasebe stok değerini ay sonunda elle hesaplar.
- Sipariş, mal girişi ve fatura birbirine bağlanamaz.

SAP'de her stok hareketi bir malzeme belgesi olarak kaydedilir, muhasebe kaydı otomatik oluşur ve stok miktarı ile değeri tek kaynaktan anlık görülür. Bu proje bu mantığın analiz tarafını gösterir.

## Süreç akışı

| # | Adım | SAP T-code | Projedeki karşılığı |
|---|------|-----------|---------------------|
| 1 | Satın alma talebi | ME51N | `PurchaseRequisitions` |
| 2 | Satın alma siparişi | ME21N | `PurchaseOrderDocuments`, `PurchaseOrderItems` |
| 3 | Mal girişi (101) | MIGO | `MaterialDocuments` |
| 4 | Stok bakiyesi | MMBE, MB52 | `MaterialStocks`, `stock.py` |
| 5 | Mal çıkışı | MIGO | `MaterialDocuments` |
| 6 | Hareket listesi | MB51 | `movements.py` |
| 7 | İhtiyaç planlama | MD04 | `planning.py` |

## Veri seti

**Simulated Inventory Management Database** – Alessandro Berti  
Kaynak: <https://zenodo.org/records/15515788>  
Lisans: CC BY 4.0. Kullanırken yazara atıf vermek zorunludur; tam atıf metnini kayıt sayfasındaki "Cite as" bölümünden alın.

Dosyayı indirip `data/raw/inventory_management.db` olarak kaydedin. Aynı kaydın daha yeni bir sürümü geri çekilmiştir, bu sürüm kullanılmalıdır.

### Tablo eşlemesi

| Veritabanı tablosu | SAP karşılığı |
|--------------------|---------------|
| `Materials` | MARA |
| `MaterialStocks` | MARD |
| `PurchaseRequisitions` | EBAN |
| `PurchaseOrderDocuments` | EKKO |
| `PurchaseOrderItems` | EKPO |
| `GoodsReceiptsAndIssues` | EKBE |
| `MaterialDocuments` | MKPF / MSEG (MATDOC) |
| `SalesOrderDocuments` | VBAK |
| `SalesOrderItems` | VBAP |
| `SalesDocumentFlows` | VBFA |
| `OrderSuggestions` | PLAF |

## Kurulum

Python 3.13 gerekir. Proje klasöründe (Windows PowerShell):

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest
```

macOS / Linux için: `python3.13 -m venv .venv` ve `source .venv/bin/activate`.

## Kullanım

Komutsuz çalıştırınca proje bilgi ekranı açılır:

```powershell
python main.py
```

| Komut | Ne yapar |
|-------|----------|
| `python main.py info` | Proje bilgi ekranı |
| `python main.py schema` | Tablolar, sütunlar, örnek satırlar |
| `python main.py stock` | Fabrika, depo ve malzeme bazında stok, stok değeri |
| `python main.py movements` | Hareket listesi ve aylık özet |
| `python main.py planning` | EOQ, emniyet stoku, yeniden sipariş noktası, durum, sipariş önerisi |
| `python main.py report` | `reports/` altına `stok_raporu.xlsx` ve `planlama.csv` yazar |

Filtreler komut adından sonra yazılır:

```powershell
python main.py movements --material 5 --plant Plant1 --start 2024-03-01 --end 2024-06-30 --limit 10
python main.py planning --limit 10
```

Alternatif çağrı: `python -m sap_stok planning`

## Planlama mantığı

| Büyüklük | Hesap |
|----------|-------|
| Günlük ortalama talep | Satış siparişi kalemlerinden, tüm tarih aralığına yayılmış günlük ortalama |
| Yıllık talep | günlük ortalama × 365 |
| Tedarik süresi | Satın alma talebindeki planlanan teslim süresinin ortalaması; yoksa 14 gün |
| Emniyet stoku | `z × günlük talep standart sapması × √tedarik süresi` (z = 1,65, yaklaşık %95 hizmet seviyesi) |
| Yeniden sipariş noktası | `günlük ortalama talep × tedarik süresi + emniyet stoku` |
| EOQ | `√(2 × yıllık talep × sipariş maliyeti / stok tutma maliyeti)` |
| Sipariş maliyeti | 50 (sabit varsayım) |
| Stok tutma maliyeti | Ortalama satın alma fiyatının %20'si |

Durum etiketleri:

| Durum | Koşul |
|-------|-------|
| `NO_DEMAND` | Günlük ortalama talep 0 |
| `CRITICAL` | Toplam stok ≤ emniyet stoku |
| `REORDER` | Toplam stok ≤ yeniden sipariş noktası |
| `OVERSTOCK` | Toplam stok > emniyet stoku + EOQ |
| `OK` | Diğer durumlar |

`CRITICAL` ve `REORDER` malzemeler için `suggested_order_qty = yukarı yuvarla(yeniden sipariş noktası + EOQ − toplam stok)`.

Varsayımlar `src/sap_stok/config.py` içinde değiştirilebilir.

## Proje yapısı

```
sapstok/
├── main.py
├── pyproject.toml
├── README.md
├── data/
│   ├── raw/                  inventory_management.db
│   └── processed/
├── reports/                  üretilen Excel ve CSV
├── src/sap_stok/
│   ├── about.py              bilgi ekranı
│   ├── cli.py                komut satırı
│   ├── config.py             yollar ve planlama varsayımları
│   ├── db.py                 SQLite bağlantısı
│   ├── inspect_schema.py     şema inceleme
│   ├── loaders.py            tablolar -> DataFrame
│   ├── movements.py          hareket listesi, aylık özet
│   ├── planning.py           EOQ, emniyet stoku, ROP, durum
│   ├── reports.py            Excel ve CSV yazımı
│   ├── sap_mapping.py        tablo ve hareket tipi eşlemesi
│   └── stock.py              stok bakiyesi ve değeri
└── tests/
```

## Testler

```powershell
pytest -q
```

Testler gerçek veritabanına dokunmaz; aynı şemada küçük bir sahte veritabanı üretir.

## Bilinen sınırlamalar

- `MaterialStocks` tablosunda ayrı bir "serbest kullanım" sütunu yoktur. `total_stock`, altı stok sütununun toplamıdır.
- Hareket tipleri yalnızca `Goods Receipt` (101, +) ve `Goods Issue` (201, −) olarak eşlenmiştir; bu bir varsayımdır.
- Veri sentetiktir. Stok, talep ve tedarik süreleri birbiriyle tutarlı olmayabilir; çoğu malzemenin `OVERSTOCK` veya `NO_DEMAND` çıkması beklenir.
- `GoodsReceiptsAndIssues`, `OrderSuggestions` ve `SalesDocumentFlows` tabloları henüz hesaplamalara dahil değildir.

## Atıf

Bu proje, Alessandro Berti'nin CC BY 4.0 lisanslı *Simulated Inventory Management Database* veri setini kullanır: <https://zenodo.org/records/15515788>
