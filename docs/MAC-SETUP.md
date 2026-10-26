---
source: ai
ai_generated: "(C)"
---
# Mac-klargøring fra v0.1

**Kørbar lokal prototype — ikke verificeret på en fysisk iPhone eller i Hinge.**
Python-kernen, HTTP-driveren og kontrolpanelets API er implementeret og testet.
Ingen Hinge-knapnavne er opfundet: knapperne skal kalibreres fra din egen app.
Hvis de nødvendige stabile, navngivne knapper ikke findes, stopper v1 og kræver
en lokal tilpasning. En bestået demo er ikke bevis for Hinge-kompatibilitet.

## Hvad den gør

Du åbner Hinge på din iPhone og starter selv en afgrænset session fra Mac'en.
V1 gentager **almindeligt hjerte → Send Like → bekræftet ny profil**, uden at
vurdere personer. Der er start/stop, kontrol uden klik, tæller og tidsgrænse.
Standard: 5 send-forsøg og højst 120 sekunder. Grænser: 1–25 forsøg, 1–600 sekunder.
Send-forsøg er ikke det samme som serverbekræftede likes.

Ingen AI-model, API-nøgle, Hinge-password, private Hinge-API'er, cloudtjeneste,
roser, beskeder, køb eller omgåelse af appens grænser. Ukendte skærme stopper
forløbet. Den accepterer ikke automatisk popups eller systemtilladelser.

**Hinge forbyder denne automatisering. Brug kan medføre udelukkelse; Hinge
skriver også, at oprettelse/distribution af sådanne værktøjer fører til ban.**
Læs [Hinges egen besked](https://help.hinge.co/hc/en-us/articles/49657802257683-Note-on-Third-Party-Automated-Tools).
Ingen session er startet på din konto af denne leverance.

## 1. Prøv kontrolpanelet uden telefon

Åbn Terminal i denne projektmappe. Python 3.11+ er påkrævet; der er ingen
Python-pakker, du skal installere for at køre programmet.

```bash
bash start.sh --demo
```

Browseren åbner `http://127.0.0.1:8765`. I demoen er alle skærme kunstige,
og ingen rigtige likes sendes. Tryk **Kontrollér uden klik**, vælg fx 2 forsøg,
markér bekræftelsen og start. Demoen er tydeligt mærket og kan ikke kobles til
en rigtig telefon. Ctrl+C i Terminal lukker programmet.

## 2. Opsæt den rigtige iPhone-driver på din Mac

Det er denne del, der kræver opsætning — USB-tillid alene giver ikke adgang til
at trykke i apps. Denne v1 bruger Appium 3, XCUITest og WebDriverAgent (WDA).

Forudsætninger: macOS, en fuld Xcode-version som understøtter din iOS-version,
Python 3.11+, Node i Appium 3's understøttede interval (`^20.19.0 || ^22.12.0 ||
>=24.0.0`) og npm 10+. En nyere kompatibel LTS-version af Node er det letteste.
Installer og åbn Xcode én gang; acceptér eventuelle vilkår og platformdownloads.

På iPhone: tilslut USB, tryk **Godkend denne computer**, slå **Udviklertilstand**
til under Indstillinger → Anonymitet & sikkerhed, genstart og bekræft.
Slå **Enable UI Automation** til under Udvikler-indstillinger, hvis vist.
Indstillingsnavne afhænger af sprog/version. Detaljer findes i [Appiums
klargøring](https://appium.github.io/appium-xcuitest-driver/latest/preparation/real-device-config/)
og [Apples guide](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device).

Kør:

```bash
bash setup-mac.sh
bash open-wda.sh
```

Installationen er projektlokal i `.tools/` og `.appium/`; der installeres ikke
globale npm-pakker. Scriptet starter ingen live-session. Appium/driveren
installeres fra npm; den løste Appium-version låses lokalt af npm.

### Signér WDA én gang i Xcode

Tilføj din Apple-konto i Xcode → Settings → Apple Accounts. I WDA-projektet:
vælg **WebDriverAgentRunner** som target/scheme, din tilsluttede iPhone som
destination og dit team under **Signing & Capabilities**. Brug et unikt
bundle-id, som dit team kan signere. Vælg **Product → Test** for at bygge og
installere runneren. Godkend udviklerappen på telefonen, hvis iOS beder om det.
Stop Xcode-testen efter vellykket opsætning, inden du starter en ny driversession.

Et gratis Apple Personal Team kan bruges, men signeringen kan kræve de manuelle
trin i [Appiums provisioning-guide](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/provisioning-profile/).
Ved fejl om provisioning profile: brug Basic Manual Configuration i guiden;
opret et lille iOS-projekt med et unikt bundle-id og dit team for at få en profil.
Gratis profiler udløber og skal genopbygges; se [Apples kontobeskrivelse](https://developer.apple.com/help/account/basics/about-your-developer-account).

Kopiér din iPhones **Identifier/UDID** fra Xcode → Window → Devices and
Simulators. Team ID er en 10-tegns værdi i udviklersigneringen; se din konto
eller signeringscertifikatet lokalt. WDA bundle-id er det, du netop valgte.
**Del aldrig dit Apple-password, signeringscertifikat eller enhedslogs i repoet.**

## 3. Forbind, kalibrér, start

```bash
bash start.sh
```

Scriptet starter Appium på `127.0.0.1:4723` og kontrolpanelet på
`127.0.0.1:8765`. Det afviser optagede porte frem for at overtage andre sessioner.
Begge processer afsluttes via Ctrl+C. Åbn panelet på Mac'en — det er bevidst
ikke tilgængeligt fra andre enheder på netværket.

Indtast UDID og de to signeringsværdier i kontrolpanelet. Team ID og WDA
bundle-id kan være tomme, hvis WDA-projektet allerede er korrekt signeret.
**Forbind telefon** opretter kun en driversession; det sender ingen likes.
Åbn derefter Hinge manuelt på din ulåste iPhone.

På Discover-profilsiden: **Aflæs den åbne skærm**, vælg Discover-markøren og
et almindeligt hjerte i listerne og tryk **Gem profilside**. Tryk derefter selv
på et hjerte på telefonen, men send ikke. Ryd en eventuel kommentar, aflæs
skærmen igen, vælg **Send Like**, bekræft tomt kommentarfelt og gem send-knappen.
Luk dialogen manuelt og gå tilbage til Discover.

Start altid med **Kontrollér uden klik**. Det skal genkende `feed`. Prøv derefter
**1 forsøg**, mens du ser på telefonen. Først efter en korrekt, overvåget
rigtig test giver en længere session mening. V1 er ikke lovet stabil uden opsyn.
Mac og iPhone skal være vågne, appen skal være i forgrunden, og du må ikke
bruge telefonen samtidig. Der er ingen stemmestyring eller automatisk genstart.

## Stop og grænser

Stopknappen sætter stopflaget uden at vente på driverens netværkslås. Flag og
tidsgrænse kontrolleres igen lige før et klik afsendes. Et klik, der allerede
er afsendt, kan ikke tilbagekaldes. Et fejlet/usikkert send-forsøg gentages aldrig.

Appskift, lås, alerts, nye knapper, ændrede inputfelter, manglende skærmskift
eller uændret profil får sessionen til at stoppe. Det er forsigtigt, ikke en
fuldstændig forståelse af enhver mulig popup: layouts, der ligner de indlærte,
kan ikke garanteres genkendt korrekt. V1 bruger ikke OCR, AI eller koordinater.

## Privatliv

Kun lokal adgang; Host-, Origin- og sessionstokenkontrol. Ingen indgående
fjernstyring. Skærmtekst behandles i hukommelsen. Et sessionssaltet fingeraftryk
bruges til at skelne profilskift og gemmes ikke. Der gemmes ikke screenshots,
profilarkiver eller fulde skærmtræer af programmet.

`.local/device.local.json` og `.local/selectors.local.json` indeholder
enhedsopsætning og knap-/inputkalibrering. **Knapnavne kan selv indeholde
personoplysninger, så disse filer er private og Git-ignorerede.** Lokale
filer oprettes med begrænsede rettigheder. Xcode og tredjepartsdriveren kan
stadig have egne lokale diagnosticeringsdata; upload dem ikke.

## Test og projektstruktur

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile core.py bridge.py demo.py app.py
node --check dashboard.js
bash -n setup-mac.sh start.sh open-wda.sh
```

`core.py`: knapgenkendelse og sessionsforløb. `bridge.py`: rigtig lokal
Appium/W3C-klient. `app.py`: HTTP-kontrolpanel og kalibrering. `demo.py`: eksplicit
offline-demo. `dashboard.*`/`style.css`: brugerflade. `tests/`: unit-, API- og
HTTP-kontrakttests. `VERIFICATION.md`: hvad der faktisk er afprøvet.

Den valgfri `tests/browser_smoke.py` kræver Playwright/Chromium og må kun køre
mod sine egne syntetiske skærme. Den indgår ikke i standardbibliotekssuiten.
