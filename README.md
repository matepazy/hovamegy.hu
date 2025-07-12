# HovaMegy.hu - valós idejű járatkövetés

> Ez az program nem hivatalos és nem áll kapcsolatban a MÁV Csoporttal. A fejlesztő semmilyen felelősséget nem vállal az oldal használatából eredő következményekért. A megjelenített információk csak tájékoztató jellegűek, a fejlesztő nem garantálja azok pontosságát, teljességét vagy időszerűségét.

## A projekt célja
A MÁV Csoport 2025. június 21-én leállította a vonatinfót. Ezt a már meglévő EMMA rendszerrel pótolták, aminek a funkcionalitása a vonatinfóhoz képest hiányos.
Célom ezzel az, hogy a vonatinfóhoz hasonló felhasználói felületet és funkciókat biztosítsak a felhasználók számára.

## Funkciók
- valós idejű járatkövetés*

**az adatok körübelül 1-3 percenként frissülnek*
- részletes menetrend megtekintése
- szűrés járatokra/járműtípusokra
- útvonaltervezés



## Helyi futtatás
### Futtatás Pythonnal
1. Klónozd a repót
```
git clone https://github.com/matepazy/hovamegy.hu.git
cd hovamegy.hu
```
2. Telepítsd a függőségeket
```
pip install -r requirements.txt
```

3. Futtasd a programot
```
python hovamegy.py
```

A felület a `localhost:8000` címen érhető el.


### Futtatás Dockerrel
1. Klónozd a repót
```
git clone https://github.com/matepazy/hovamegy.hu.git
cd hovamegy.hu
```

**Helyi használatra**

2. Töröld a `docker-compose.yml` fájl 22-31 sorait és a `.env.example`


3. Futtast a containert
```
docker compose up -d
```

**Nyílvános használatra**

2. Nevezd át a `.env.example` fájlt `.env`-re

3. Szerezd meg a Cloudflare tunneled tokenjét és illeszd be a `CLOUDFLARE_TUNNEL_TOKEN` változóba

4. Futtast a containereket
```
docker compose up -d
```

A felület a `localhost:8000` címen érhető el.


Kiindulásként a [holavonatot](https://gitlab.com/holavonat1/holavonat-web) használtam, ezt fejlesztettem tovább.

## API Használata
API Base URL: `https://hovamegy.hu`
##

**`GET`** `/live_data.json`

Megadja az összes járat valós idejű helyzetét. *(jobb ha a hivatalos EMMA API-t használod erre)*
##

**`POST`** `/plan`

Utazástervező API endpoint. JSON formátumban várja a következő paramétereket:
- `from`: Indulási pont koordinátái (`{"lat": szélességi_fok, "lon": hosszúsági_fok}`)
- `to`: Érkezési pont koordinátái (`{"lat": szélességi_fok, "lon": hosszúsági_fok}`)
- `dateTime`: Utazás dátuma és időpontja (ISO 8601 formátumban, pl. `"2025-07-12T22:00"`)
- `arriveBy`: `false` ha indulási időpont, `true` ha érkezési időpont
- `numItineraries`: Visszaadandó útvonalak száma (opcionális, alapértelmezett: 3)

Válasz formátuma: JSON objektum az útvonal részleteivel, menetidőkkel és átszállási információkkal.