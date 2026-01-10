# Rakendus Wi-Fi leviala kaardistamiseks

Projekt on bakalaureusetöö raames loodud Pythonil põhinev rakendus, millega on võimalik kaardistada Wi-Fi leviala siseruumides ruumiplaani alusel ning visualiseerida Wi-Fi signaali tugevust soojuskaardina.
Rakendus on mõeldud kasutamiseks Windowsi operatsioonisüsteemis.

## Nõuded

Rakenduse käivitamiseks on vajalik:

- **Windowsi operatsioonisüsteem**
- **Python 3.11+**

Pythonit on võimalik alla laadida aadressilt:
https://www.python.org/downloads/

## Projekti struktuur

- `main.py` - Põhiprogramm
- `map_scale.py` - Ruumiplaani mõõtkava määraminse loogika dialoogaknas
- `run.bat` - Rakenduse käivitusskript Windowsis
- `pyproject.toml` - Projekti konfiguratsioonifail
- `uv.lock` - Lukustatud sõltuvuste versioonid
- `wifi_UI.ui` `SetMapScale.ui` - Kasutajaliidese failid
- `resources.rcc`  Qt ressursifail (kasutajaliidese ikoonid)
