# 🚂 HolaVonat - Magyar Vonatkövetés

Egy valós idejű vonatkövetési alkalmazás, amely a MÁV EMMA API-ját használja a magyar vasúti járművek pozíciójának megjelenítésére interaktív térképen.

## 📋 Tartalomjegyzék

- [Áttekintés](#áttekintés)
- [Funkciók](#funkciók)
- [Technológiák](#technológiák)
- [Telepítés](#telepítés)
  - [Docker használatával](#docker-használatával)
  - [Helyi futtatás](#helyi-futtatás)
- [Használat](#használat)
- [API Végpontok](#api-végpontok)
- [Konfiguráció](#konfiguráció)
- [Hozzájárulás](#hozzájárulás)
- [Licenc](#licenc)

## 🎯 Áttekintés

A HolaVonat egy modern webes alkalmazás, amely valós időben jeleníti meg a magyar vasúti járművek pozícióját. Az alkalmazás a MÁV hivatalos EMMA API-ját használja az adatok lekéréséhez, és egy gyönyörű, interaktív térképen jeleníti meg azokat.

### Főbb jellemzők:
- 🗺️ Valós idejű vonatpozíciók megjelenítése
- 🚄 Különböző járműtípusok támogatása (vonat, helyettesítő busz, elővárosi vasút, villamosvasút)
- 📍 Részletes útvonal és megálló információk
- 🕐 Késési információk és menetrendi adatok
- 🎨 Modern, reszponzív felhasználói felület
- 🔄 Automatikus adatfrissítés 45 másodpercenként

## ✨ Funkciók

### Térképes megjelenítés
- **Interaktív térkép**: Leaflet.js alapú térkép Magyarország teljes területével
- **Járműmarkerek**: Színkódolt markerek a különböző járműtípusokhoz
- **Irányjelzés**: Háromszög alakú markerek a járművek haladási irányával
- **Klaszterezés**: Automatikus marker csoportosítás nagyobb zoom szinteken

### Járműinformációk
- **Vonatszám és útvonal**: Teljes vonatszám és útvonal megjelenítése
- **Célállomás**: Aktuális célállomás információ
- **Sebesség**: Valós idejű sebességadatok
- **Késések**: Érkezési és indulási késések megjelenítése
- **Megállók**: Teljes útvonal és megállóhelyek listája

### Útvonaltervezés
- **Állomáskeresés**: Intelligens állomásnév keresés
- **Többféle útvonal**: Alternatív útvonalak megjelenítése
- **Menetidő kalkuláció**: Pontos utazási idő becslés
- **Átszállási információk**: Részletes átszállási útmutatás

## 🛠️ Technológiák

### Backend
- **Python 3.11**: Fő programozási nyelv
- **Flask 2.3.3**: Webes keretrendszer
- **Requests 2.31.0**: HTTP kliens könyvtár
- **Threading**: Háttérben futó adatfrissítés
- **Concurrent.futures**: Párhuzamos API hívások optimalizálása

### Frontend
- **HTML5/CSS3**: Modern webes szabványok
- **JavaScript (ES6+)**: Interaktív funkcionalitás
- **Leaflet.js**: Térképes megjelenítés
- **Leaflet.markercluster**: Marker csoportosítás
- **Inter Font**: Modern tipográfia

### DevOps
- **Docker**: Konténerizáció
- **Docker Compose**: Többkonténeres alkalmazás kezelés
- **Cloudflare Tunnel**: Biztonságos külső hozzáférés
- **Health Checks**: Alkalmazás állapot monitorozás

## 🚀 Telepítés

### Docker használatával (Ajánlott)

1. **Repository klónozása**:
```bash
git clone https://github.com/your-username/hovamegy.git
cd hovamegy
```

2. **Környezeti változók beállítása** (opcionális):
```bash
cp .env.example .env
# Szerkeszd a .env fájlt és add meg a Cloudflare Tunnel tokent
```

3. **Alkalmazás indítása**:
```bash
docker-compose up -d
```

4. **Böngészőben megnyitás**:
```
http://localhost:8000
```

### Helyi futtatás

1. **Python 3.11+ telepítése** (ha még nincs telepítve)

2. **Függőségek telepítése**:
```bash
pip install -r requirements.txt
```

3. **Alkalmazás indítása**:
```bash
python hovamegy.py
```

4. **Böngészőben megnyitás**:
```
http://localhost:8000
```

## 📖 Használat

### Főoldal
- Nyisd meg a böngészőben a `http://localhost:8000` címet
- A térkép automatikusan betölti a vonatpozíciókat
- Kattints egy vonatra a részletes információkért
- Használd a zoom gombokat a térkép nagyításához/kicsinyítéséhez

### Útvonaltervezés
- Navigálj a `/trip` oldalra
- Add meg a kiindulási és célállomást
- Válaszd ki a kívánt időpontot
- Tekintsd meg az elérhető útvonalakat


## 🔌 API Végpontok

### Publikus végpontok

#### `GET /`
Főoldal megjelenítése

#### `GET /trip`
Útvonaltervező oldal megjelenítése

#### `GET /train_data.json`
Aktuális vonatadatok JSON formátumban

**Válasz példa**:
```json
{
  "lastUpdated": 1703123456,
  "vehicles": [
    {
      "id": "MAV:Trip:123456",
      "name": "IC 123",
      "headsgn": "Budapest-Keleti",
      "lat": 47.5,
      "lon": 19.0,
      "sp": 120,
      "hd": 45,
      "mode": "RAIL",
      "stops": [...]
    }
  ]
}
```

#### `GET /api/stations?q={keresési_kifejezés}&limit={limit}`
Állomáskeresés

**Paraméterek**:
- `q`: Keresési kifejezés (min. 2 karakter)
- `limit`: Találatok száma (alapértelmezett: 5)

#### `POST /api/plan`
Útvonaltervezés

**Kérés példa**:
```json
{
  "from": {"lat": 47.5, "lon": 19.0},
  "to": {"lat": 47.6, "lon": 19.1},
  "dateTime": "2024-01-01T10:00",
  "arriveBy": false,
  "numItineraries": 3
}
```

## ⚙️ Konfiguráció

### Környezeti változók

| Változó | Leírás | Alapértelmezett |
|---------|--------|-----------------|
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare Tunnel token | - |

### Alkalmazás beállítások

A `hovamegy.py` fájlban módosíthatók:

```python
# Adatfrissítési intervallum (másodperc)
UPDATE_INTERVAL = 45

# Egyidejű API kérések maximális száma
MAX_CONCURRENT_REQUESTS = 10

# Szerver port
PORT = 8000
```

## 🤝 Hozzájárulás

Örülünk minden hozzájárulásnak! Kérjük, kövesd az alábbi lépéseket:

### 1. Fejlesztői környezet beállítása

```bash
# Repository forkolása és klónozása
git clone https://github.com/your-username/hovamegy.git
cd hovamegy

# Virtuális környezet létrehozása
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Függőségek telepítése
pip install -r requirements.txt
```



### 4. Tesztelés

```bash
# Alkalmazás indítása fejlesztői módban
python hovamegy.py

# Böngészőben tesztelés
open http://localhost:8000

# API végpontok tesztelése
curl http://localhost:8000/train_data.json
```

### 5. Hibajelentés

Ha hibát találsz, kérjük nyiss egy **GitHub Issue**-t az alábbi információkkal:

- **Hiba leírása**: Mit vártál és mi történt helyette
- **Reprodukálási lépések**: Hogyan lehet a hibát előidézni
- **Környezet**: Operációs rendszer, Python verzió, böngésző
- **Logok**: Releváns hibaüzenetek vagy logok
- **Képernyőképek**: Ha vizuális hiba, csatolj képernyőképeket

### 6. Funkció kérések

Új funkciók kéréséhez:

1. **Ellenőrizd** a meglévő issue-kat, hátha már van hasonló kérés
2. **Hozz létre** egy új issue-t "Feature Request" címkével
3. **Írd le részletesen** a kívánt funkciót és annak indoklását
4. **Add meg** példákat a használatra

### 7. Kód review

Minden PR-t átnézünk a következő szempontok alapján:

- **Funkcionalitás**: A kód megfelelően működik-e
- **Kódminőség**: Tiszta, olvasható és karbantartható-e
- **Teljesítmény**: Nincs-e negatív hatása a teljesítményre
- **Biztonság**: Nincsenek-e biztonsági problémák
- **Dokumentáció**: Megfelelően dokumentált-e

### 8. Közreműködők

Köszönet minden közreműködőnek! 🙏

<!-- Ide kerülnek majd a közreműködők -->

## 📄 Licenc

Ez a projekt [MIT Licenc](LICENSE) alatt áll. Lásd a LICENSE fájlt a részletekért.

## 🆘 Támogatás

Ha segítségre van szükséged:

1. **Dokumentáció**: Olvasd el ezt a README-t
2. **Issues**: Nézd meg a [GitHub Issues](https://github.com/matepazy/holavonat/issues) oldalt
3. **Discussions**: Csatlakozz a [GitHub Discussions](https://github.com/matepazy/holavonat/discussions) beszélgetésekhez

## 🔗 Hasznos linkek

- [MÁV EMMA](https://emma.mav.hu/) - Hivatalos MÁV utazástervező
- [Leaflet.js](https://leafletjs.com/) - Térképes könyvtár dokumentáció
- [Flask](https://flask.palletsprojects.com/) - Flask keretrendszer dokumentáció
- [Docker](https://docs.docker.com/) - Docker dokumentáció

---

**Készítette**: A HolaVonat fejlesztői csapat  
**Utolsó frissítés**: 2024. január  
**Verzió**: 1.0.0

🚂 Boldog vonatozást! 🚂