# Rakendus Wi-Fi leviala kaardistamiseks

Projekt on bakalaureusetöö raames loodud Pythonil põhinev rakendus, millega on võimalik kaardistada Wi-Fi leviala siseruumides ruumiplaani alusel ning visualiseerida Wi-Fi signaali tugevust soojuskaardina.
Rakendus on mõeldud kasutamiseks Windowsi operatsioonisüsteemis.

## Nõuded

Rakenduse käivitamise eelduseks on vajalik:

- **Windowsi operatsioonisüsteem**
- **Python 3.11+**
- **lswifi**

Pythonit on võimalik alla laadida aadressilt:
https://www.python.org/downloads/

## Rakenduse käivitamine
1. Lae alla ja paki lahti projekti kaust
2. Installi `lswifi` käsuga `python -m pip install -U lswifi`
3. Leia `lswifi.exe` asukoht Pythoni `Scripts` kaustas käsuga `where lswifi`
4. Navigeeri antud asukohta, kopeeri `lswifi.exe` ja pane see `WiFi Heatmap Tool` kausta `WiFi Heatmap Tool.exe` kõrvale

## Projekti struktuur

- `main.py` - Põhiprogramm
- `map_scale.py` - Ruumiplaani mõõtkava määramise loogika dialoogaknas
- `pyproject.toml` - Projekti konfiguratsioonifail
- `uv.lock` - Lukustatud sõltuvuste versioonid
- `wifi_UI.ui` `SetMapScale.ui` - Kasutajaliidese failid
- `icons/` - Rakenduses kasutatavad ikoonid
- `WiFi Heatmap Tool/` - Kaust rakenduse käivitatava failiga
