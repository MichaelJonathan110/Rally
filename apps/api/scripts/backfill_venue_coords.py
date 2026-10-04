"""Backfill latitude/longitude for venues that lack them, using a city lookup."""
from __future__ import annotations
import random, sqlite3, sys
from pathlib import Path

CITY = {
 'Jakarta':(-6.2088,106.8456),'Bandung':(-6.9175,107.6191),'Surabaya':(-7.2575,112.7521),
 'Medan':(3.5952,98.6722),'Semarang':(-6.9932,110.4203),'Makassar':(-5.1477,119.4327),
 'Palembang':(-2.9761,104.7754),'Tangerang':(-6.1783,106.6319),'Tangerang Selatan':(-6.2886,106.7179),
 'Depok':(-6.4025,106.7942),'Bekasi':(-6.2383,106.9756),'Bogor':(-6.5971,106.8060),
 'Yogyakarta':(-7.7956,110.3695),'Surakarta':(-7.5755,110.8243),'Malang':(-7.9666,112.6326),
 'Denpasar':(-8.6705,115.2126),'Padang':(-0.9471,100.4172),'Padang Panjang':(-0.4644,100.4001),
 'Pekanbaru':(0.5071,101.4478),'Banjarmasin':(-3.3186,114.5944),'Banjarbaru':(-3.4424,114.8325),
 'Pontianak':(-0.0263,109.3425),'Singkawang':(0.9041,108.9851),'Samarinda':(-0.5022,117.1536),
 'Balikpapan':(-1.2379,116.8529),'Bontang':(0.1246,117.4982),'Tarakan':(3.3274,117.5760),
 'Manado':(1.4748,124.8421),'Bitung':(1.4404,125.1214),'Tomohon':(1.3266,124.8406),
 'Kotamobagu':(0.7333,124.3167),'Gorontalo':(0.5435,123.0568),'Jayapura':(-2.5916,140.6690),
 'Ambon':(-3.6954,128.1814),'Tual':(-5.6369,132.7467),'Mataram':(-8.5833,116.1167),
 'Bima':(-8.4601,118.7269),'Kupang':(-10.1772,123.6070),'Batam':(1.0456,104.0305),
 'Tanjungpinang':(0.9186,104.4667),'Pekalongan':(-6.8886,109.6753),'Cirebon':(-6.7320,108.5523),
 'Tasikmalaya':(-7.3274,108.2207),'Serang':(-6.1104,106.1503),'Cilegon':(-6.0027,106.0114),
 'Jambi':(-1.6101,103.6131),'Sungai Penuh':(-2.0634,101.3913),'Bengkulu':(-3.8004,102.2655),
 'Bandar Lampung':(-5.3971,105.2668),'Metro':(-5.1131,105.3067),'Palangka Raya':(-2.2080,113.9165),
 'Pangkalpinang':(-2.1316,106.1169),'Kendari':(-3.9985,122.5130),'Baubau':(-5.4700,122.6000),
 'Palu':(-0.8917,119.8707),'Ternate':(0.7900,127.3800),'Tidore Kepulauan':(0.7400,127.4400),
 'Sorong':(-0.8762,131.2558),'Banda Aceh':(5.5483,95.3238),'Sabang':(5.8933,95.3214),
 'Lhokseumawe':(5.1801,97.1507),'Langsa':(4.4683,97.9683),'Subulussalam':(2.6592,97.8948),
 'Binjai':(3.6001,98.4850),'Pematangsiantar':(2.9595,99.0687),'Tebing Tinggi':(3.3285,99.1625),
 'Sibolga':(1.7427,98.7792),'Padangsidimpuan':(1.3739,99.2683),'Tanjungbalai':(2.9667,99.8000),
 'Gunungsitoli':(1.2890,97.6162),'Bukittinggi':(-0.3055,100.3692),'Payakumbuh':(-0.2297,100.6323),
 'Solok':(-0.7893,100.6543),'Sawahlunto':(-0.6790,100.7776),'Pariaman':(-0.6264,100.1207),
 'Dumai':(1.6667,101.4500),'Prabumulih':(-3.4328,104.2357),'Lubuk Linggau':(-3.2967,102.8617),
 'Pagar Alam':(-4.0217,103.2520),'Palopo':(-3.0000,120.2000),'Parepare':(-4.0135,119.6255),
 'Pasuruan':(-7.6453,112.9075),'Probolinggo':(-7.7543,113.2159),'Mojokerto':(-7.4707,112.4338),
 'Kediri':(-7.8480,112.0178),'Blitar':(-8.0954,112.1610),'Madiun':(-7.6298,111.5239),
 'Magelang':(-7.4698,110.2177),'Salatiga':(-7.3305,110.5084),'Tegal':(-6.8694,109.1402),
 'Sukabumi':(-6.9277,106.9300),'Cimahi':(-6.8732,107.5422),'Banjar':(-7.3667,108.5333),
 'Batu':(-7.8672,112.5239),
}

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    db = root / 'rally_dev.db'
    con = sqlite3.connect(db)
    cur = con.cursor()
    rows = cur.execute('SELECT id, city FROM venues').fetchall()
    before = cur.execute('SELECT COUNT(*) FROM venues WHERE latitude IS NOT NULL AND longitude IS NOT NULL').fetchone()[0]
    rng = random.Random(20261003)
    updated = 0
    unmatched = set()
    for vid, city in rows:
        key = (city or '').strip()
        base = CITY.get(key)
        if not base:
            unmatched.add(key)
            continue
        lat = base[0] + rng.uniform(-0.03, 0.03)
        lng = base[1] + rng.uniform(-0.03, 0.03)
        cur.execute('UPDATE venues SET latitude=?, longitude=? WHERE id=?', (round(lat,6), round(lng,6), vid))
        updated += 1
    con.commit()
    after = cur.execute('SELECT COUNT(*) FROM venues WHERE latitude IS NOT NULL AND longitude IS NOT NULL').fetchone()[0]
    print(f'coords before={before} updated={updated} after={after} total={len(rows)}')
    missing = cur.execute('SELECT COUNT(*) FROM venues WHERE latitude IS NULL').fetchone()[0]
    print(f'still_missing={missing} unmatched_cities={sorted(unmatched)}')
    top = cur.execute('SELECT city, COUNT(*) c FROM venues WHERE latitude IS NOT NULL GROUP BY city ORDER BY c DESC LIMIT 8').fetchall()
    print('top cities:', top)
    con.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
