# Video des laufenden Scans

Quelle: WhatsApp Video 2026-09-11 at 10.11.05.mp4, 464 x 832, 1523 dekodierte Bilder, etwa 25,4 Sekunden. Originalpfad und SHA-256 stehen in source-and-method.json. Das Original wurde nicht veraendert.

Das Video wurde bildweise ausgewertet. Die Uebersicht und die Kontaktboegen zeigen die sichtbaren Lichtpunkte. Aus dem blauen Leuchthof wurden zusammenhaengende sichtbare Leuchtphasen anhand der Videobild-Zeitstempel bestimmt (Schwellen und Empfindlichkeitsvergleich siehe source-and-method.json, Rohwerte in per-frame.csv).

Es sind bei den gewaehlten, visuell gegengeprueften Schwellen 33 deutliche Leuchtphasen zu sehen. Ihre gemessenen Dauern liegen ungefaehr zwischen 0,12 und 0,82 Sekunden; Median etwa 0,20 Sekunden. Schwellen fuer die Mindestflaeche von 20, 50 und 100 Pixeln liefern dieselbe Anzahl und dieselben Extremwerte. Das sind optische Videoereignisse, keine zugeordneten Original-LED-IDs.

Beispiele relativ zum Videobeginn:

| Beginn | Ende | Ungefaehre sichtbare Leuchtdauer |
|---|---|---|
| 7,19 s | 7,91 s | 0,72 s |
| 8,66 s | 9,47 s | 0,82 s |
| 11,04 s | 11,67 s | 0,63 s |
| 11,96 s | 12,07 s | 0,12 s |
| 12,51 s | 12,63 s | 0,12 s |
| 12,84 s | 12,98 s | 0,13 s |
| 16,68 s | 17,48 s | 0,80 s |

Damit ist die stark wechselnde sichtbare Leuchtdauer am Panel bestaetigt. Die Abfolge laengerer Leuchtphasen und anschliessender kurzer Blitze ist keine reine Verzoegerung der TouchDesigner-Statusanzeige.

Grenzen: Handybelichtung, Kompression und Bildabtastung begrenzen die Genauigkeit; die Zeiten sind Naeherungen. Ohne zeitgleich zugeordnete Scan-LED-IDs laesst sich aus dem Video allein nicht beweisen, welche LED vollstaendig uebersprungen wurde. Extrem kurze/schwache Blitze koennen im Video fehlen. Ebenso laesst sich die Ursache noch nicht eindeutig zwischen Erkennungswartezeit, Kamerapuffer und Controllerreaktion aufteilen. Die bisherigen gemessenen Kamera-Lesezeiten belegen nicht fuer sich einen Defekt oder langsame Bildverarbeitung.

Kein Scan gestoppt oder neu gestartet; keine Scan-, Kamera- oder Controllerparameter geaendert. In diesem Schritt wurden nur Videoanalyse und Dokumentation erstellt.
