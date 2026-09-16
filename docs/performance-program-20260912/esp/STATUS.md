# ESP: Abschluss des verfügbaren Hardwaretests

Aktuell installiert: physical768-raw-v2, COM5, 10.0.0.151, MAC E8-68-E7-0D-38-A4. WS2812: 256 Pixel, GPIO14, U0–1. APA102: 512 Pixel, DATA18/CLOCK19, U2–5. Ausgabe nach Abschluss disarmed bestätigt.

Firmware-SHA256: `cfee468ab700cbcb732e0ea221cc02933afd329f62d05ef299ad00d7dfc027be`.

| Profil / Empfang | Gesendete Bilder | Empfangene Bilder | Beide Ausgänge abgeschlossen | Pakete empfangen / gesendet |
|---|---:|---:|---:|---:|
| Physical768, Socket, 30 s |900|900|900|5400/5400|
| Virtual1755, Socket, 30,022 s |898|16|16|5588/10776|
| Virtual1755, Raw64, 60,000 s |1800|1800|1799|21600/21600|
| Physical768, Raw64, 120,002 s |3599|3599|3599|21594/21594|

Endmessung: 29,991 FPS, keine unvollständigen Bilder, keine Mailboxüberschreibungen, keine Raw-Queue-Drops oder gemeldeten Fehler. Ein Hostoverrun erklärt, warum der Sender 3.599 statt 3.600 Bilder erzeugte. Beim virtuellen Profil wurde ein wartendes Bild ersetzt; Ausgangsrate 29,983 FPS. Es waren keine 1.755 physischen LEDs angeschlossen.

Die sechs Datagrammslots des SDK-Socketpfades wurden durch einen Raw-UDP-Callback mit begrenzter 64er-Queue umgangen. Quelle ist weiterhin auf 10.0.0.125 begrenzt; alte ARM-Generationen werden verworfen. Hardware-Regression für malformed/oversize, ARM mit altem Teilbild, neues vollständiges Bild und STOP bestanden (`raw64-ingress-hardware-regression.json`). Beide Profile gebaut und auf dem verifizierten Gerät getestet; abschließend korrektes physisches Profil wieder installiert.

Die Originalfirmware ist zweimal bytegleich privat gesichert. Nichtgeheime Firmwareabschnitte, Quellen, Build-/Flashlogs und SHA256 liegen in den versionierten Paketen und Manifesten. Kein NVS- oder WLAN-Geheimnis wird veröffentlicht. Produktivcontroller .248 und GICO .244 wurden nicht geflasht.

Optische Bildnummern-/Dauertestabnahme bleibt offen. Dies ist experimentelle Messfirmware, kein vollständiger Ersatz aller Funktionen der alten Controlleroberfläche. Frühere Messungen und Zwischenstände bleiben in `STATUS_ZWISCHENSTAND_SOCKET.md` und den Rohdateien erhalten. Gesamtbewertung: `../ERGEBNISSE_DE.md`.
