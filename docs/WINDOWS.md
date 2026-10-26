# Windows + iPhone — første prototype

Denne udgave er en teknisk prototype. Et samlet forløb er ikke afprøvet på en fysisk
iPhone eller med den aktuelle Hinge-app. Demoen kræver ingen telefon.

## 1. Prøv demoen

Installer Python 3.11+ med Python Launcher fra python.org. Udpak eller klon
projektet. Dobbeltklik `demo-windows.cmd`. Browseren åbner et lokalt panel.
Demoen arbejder udelukkende med kunstige profiler og sender ingen likes.

## 2. Klargør telefonen

Der kræves iOS 18+, USB-tillid, udviklertilstand og UI Automation, hvor
indstillingen vises. Installér Apples Mobile Device-drivere på Windows.
Appiums guide anbefaler Apples selvstændige iTunes-installationspakke.

En korrekt signeret WebDriverAgentRunner skal allerede være installeret.
På Windows kan den offentlige Appium-pakke pakkes og signeres med Sideloadly;
se [Windows-signering](WINDOWS-SIGNING.md). Alternativt bruges en Mac med kompatibel Xcode
til at signere og installere runneren til netop din iPhone. Se
[Mac-klargøring](MAC-SETUP.md). Brug det bundle-id, der blev signeret;
kopiér det fra din egen opsætning, ikke fra eksemplerne.
Signeringen kan udløbe og kræve ny installation fra Mac.

## 3. Installér driveren på Windows

Installer Node.js 22.12+ eller 24 LTS og npm 10+. Kør:

```bat
setup-windows.cmd
```

Scriptet installerer Appium 3.8.0 og XCUITest 12.20.0 lokalt.
Windows-understøttelse kræver en driver med understøttelse af non-macOS
hosts og appium-ios-remotexpc 5.1+. Den præcise løste version gemmes lokalt
i `.tools/package-lock.json` og `.appium`.
Scriptet installerer ikke WDA på telefonen og starter ingen session.
Ved gentagen opsætning genbruges den allerede installerede XCUITest-driver.
Den kontrolleres før opsætningen meldes færdig: Windows kræver i denne
udgave mindst 12.20.0 i 12.x-serien. Ældre eller ukendte hovedversioner giver
en fejl og bevares. Opdatér den projektlokale driver til den angivne version,
før du forsøger telefonforbindelsen; opsætningen udskifter den ikke automatisk.
Kør `doctor-windows.cmd` for at kontrollere lokal software og USB-registrering.
Kontrollen viser ingen enheds-id'er, opretter ingen telefonsession og bekræfter
ikke WDA-signering eller en aktiv tunnel. `--software-only` kontrollerer kun
installationen og kræver ingen tilsluttet telefon.

Appiums generelle `driver doctor xcuitest` kræver fejlagtigt Xcode ved denne
Windows-opsætning. Derfor bruger Windows-startfilerne projektets egen,
afgrænsede kontrol. Xcode bruges fortsat til WDA-signering på en Mac.

Hvis USB-kommunikationen mangler, skal **Apple Mobile Device Support** være
installeret og tjenesten køre. Den officielle Apple-pakke findes også som
`Apple.AppleMobileDeviceSupport` i Microsofts WinGet-katalog. Godkend derefter
computeren på din ulåste iPhone. USB-registrering alene beviser ikke, at
telefonen har godkendt computeren eller er klar til automatisering.

## 4. Start tre terminaler

Hold følgende åbne hver for sig, fra projektmappen:

```bat
tunnel-windows.cmd
```

```bat
start-windows.cmd
```

```bat
panel-windows.cmd
```

Tunnelværktøjet kan kræve en administratorterminal til netværksinterfacet.
Der foretages ingen automatisk elevation eller ændring af Windows' politikker.
Tunnelprocessen skal blive kørende. Appium og kontrolpanelet bindes kun til
127.0.0.1. Hvis en port er optaget, luk din gamle lokale proces først.
Ctrl+C i hver terminal afslutter den tilhørende proces.

I panelet vælger du **Windows · installeret WebDriverAgent**, indtaster UDID,
iOS-version og WDA bundle-id. Team ID bruges kun med Mac-forbindelsen.
Tryk **Forbind telefon**. Dette opretter en driversession uden at like.

## 5. Kalibrér og afprøv én handling

Åbn Hinge manuelt. Brug **Aflæs den åbne skærm** til at vælge Discover-markør
og almindeligt hjerte. Gem profilsiden. Åbn selv like-dialogen, ryd eventuelle
kommentarer, aflæs og gem den almindelige send-knap. Gå tilbage til Discover.

Vælg **Kontrollér uden klik**, og afprøv derefter højst ét send-forsøg, mens du
ser på telefonen. Manglende stabile knapnavne kræver en lokal tilpasning.
Skærmbilleder er ikke tilstrækkelige til at udlede accessibility-navne.

På de viste billeder står der “Send prioriteret synes godt…”. Prototypen
afviser `priorit…`, roser og køb som klikmål. Den aktuelle version tester kun
almindelige likes. Hvis denne knap er den eneste mulighed, stopper prototypen.

## Kilder til driveropsætningen

- [Appium: Windows/Linux](https://appium.github.io/appium-xcuitest-driver/latest/guides/non-macos-hosts/)
- [Appium: RemoteXPC](https://appium.github.io/appium-xcuitest-driver/latest/guides/remotexpc-tunnels-real-devices/)
- [Appium: iPhone-klargøring](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/device-setup/)

Der er ingen tiltag til at skjule automatisering, omgå udfordringer eller
udvide appens like-grænser. Hinge kan spærre konti ved automatisering.
