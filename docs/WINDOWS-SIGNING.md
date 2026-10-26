---
source: ai
ai_generated: "(C)"
---
# WebDriverAgent-signering på Windows

Den offentlige WebDriverAgent fra Appium kan pakkes som IPA og signeres
lokalt med Sideloadly. Windows-forløbet er klargjort; det er først verificeret
på telefonen, når signering, installation og Appium-forbindelse faktisk lykkes.

## Den klargjorte PC

1. Dobbeltklik `sign-windows.cmd` i projektmappen. Den åbner Sideloadly og
   viser `.local/WebDriverAgent.ipa` i Stifinder.
2. Vælg din USB-forbundne iPhone og træk IPA-filen ind i Sideloadly.
3. Indtast selv Apple-id i programmet og gennemfør eventuel Apple-bekræftelse.
   Lad automatisk app-fornyelse være slået fra. Tryk selv Start.
4. Hvis iPhone beder om tillid: Indstillinger → Generelt → VPN og
   enhedsadministration → udviklerappen → godkend.
5. Fortsæt i Windows-guiden. Det faktiske app-id registreres lokalt,
   hvorefter tunnel, forbindelse og kalibrering kan kontrolleres.

Sideloadly er tredjepartssoftware fra [producentens side](https://sideloadly.io/).
Den hentede producentfil er ikke digitalt signeret. Ingen Apple-oplysninger
skal skrives i chatten eller gemmes i projektet. Den medfølgende launcher
installerer ingen baggrundstjeneste. Automatisk fornyelse vælges i Sideloadly.
Gratis signering udløber normalt efter syv dage; se [producentens FAQ](https://sideloadly.io/faq).

## Ny opsætning

Kør `setup-windows.cmd`, derefter `prepare-wda-windows.cmd`. Sidstnævnte henter
den WDA-version, der matcher den installerede XCUITest-driver, og pakker den
med Python-standardbiblioteket. Hent selv Sideloadly fra producenten, hvis det
ikke allerede er klargjort. Tredjepartsprogrammer og IPA medtages ikke i kilde-ZIP.

`prepare_wda.py` overskriver aldrig en eksisterende IPA og accepterer kun en
usigneret iPhone-app uden provisioning-profiler/certifikater. Programfilernes
Unix-eksekveringsbit bevares i IPA-pakken. Pakning er ikke signering.

Teknisk: hvis et fuldt, observeret app-id er gemt med
`wda_bundle_id_exact: true`, tilføjer Windows-forbindelsen ingen `.xctrunner`
suffix. Browserforbindelsen bevarer denne markering for samme telefon/app-id.
Ældre base-id-konfiguration og Mac-signering beholder deres eksisterende adfærd.

[Appiums download/signering](https://appium.github.io/appium-xcuitest-driver/latest/reference/scripts/),
[Appiums Windows-forbindelse](https://appium.github.io/appium-xcuitest-driver/latest/guides/non-macos-hosts/).
