# Status: GICO-Kameratest

Stand: 12.09.2026. Teilaufgabe 1, Agent `gico_camera_test`.

- Pure Bildnummer-Codierung, 24-Universen-Paketerzeugung und konservative
  Auswertung implementiert.
- Aufnahmeprotokoll 15/25/30 FPS mit Kalibriersequenz vorbereitet.
- Kommando zum Offline-Vorbereiten und expliziten Start implementiert; Start
  prüft TD-Ausgabe aus und verwendet den vorhandenen separaten Senderworker.
- Video-Kalibrierung mit Panel-Rechtecken und nummeriertem Kontrollbild,
  Frame-Zeitstempelauswertung, CRC-/Helligkeitsprüfung und CSV-Nachweis vorhanden.
- Deutsche Bedienungs- und Aufnahmeanleitung: `ANLEITUNG_DE.md`.
- Keine Hardwareausgabe, kein TD-Zugriff, keine Controllerkonfiguration und keine
  Firmwareänderung durch diesen Agenten gestartet.

Validierung abgeschlossen: **16 Tests bestanden in 23,786 Sekunden**.

- Alle 4.096 Bildnummern korrekt hin und zurück codiert; sämtliche 86.016
  möglichen einzelnen Bitfehler einschließlich Referenzbit erkannt.
- Paketadressen, reservierte schwarze Bereiche, ArtDmx-Header und Helligkeits-
  grenzen geprüft.
- Fehlende optische IDs, falsche einzelne Codes, Zählerüberlauf, unerwartete
  Rücksprünge, lange gehaltene Bilder und ungültige Zeitstempel geprüft.
- Vollständiges synthetisches MJPG-Video mit drei Panels und 120 Kamera-FPS
  geschrieben und wieder eingelesen. Automatische Marker-Kalibrierung und
  anschließende Auswertung erkennen die simulierten 15/25/30 FPS innerhalb
  0,25 FPS, ohne fehlende IDs oder unterschiedliche Panelnummern. Dabei werden
  echte Decoder-Präsentationszeitstempel verwendet, keine Frameindex-FPS-Rechnung.
- Sendergrenze isoliert getestet: fehlgeschlagene TD-off-Prüfung konstruiert
  keinen Worker; ein Einreichungsfehler schließt den Worker und protokolliert
  den Fehler. Diese Tests verwenden ausschließlich Mocks.
- Offline-Plan tatsächlich erzeugt: `offline-plan/plan.json`. Kein Socket und
  kein TD-Aufruf bei diesem `prepare`-Kommando.

Testkommando:

```powershell
& 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' -m unittest tests.test_gico_camera_benchmark tests.test_gico_camera_video tests.test_gico_camera_sender
```

Bereitschaft: Software und Aufnahmeablauf sind für einen beaufsichtigten echten
Durchlauf vorbereitet. Live-Erprobung und reale Videokalibrierung bleiben offen.
Offen für die Hardwaremessung: ungeschnittenes Originalvideo eines echten
Durchlaufs mit bekannter Aufnahme-/Zeitlupenzeitbasis. Vorhandene Offline-Tests
können keine realen GICO-Ausgabe-FPS bestätigen.

Headerkorrektur nach Integrationsreview: Der Kamerasender verwendet wie der
bestehende native GICO-Pfad dauerhaft ArtDmx-Sequenz 0. Optische Bildnummern
bleiben im Gray-/CRC-Payload. Der Test prüft zwei aufeinanderfolgende Batches
mit jeweils 24 Sequenz-0-Paketen und den entsprechenden Logeintrag.


## Erster optischer Aufnahmelauf ausgeführt

`measurements/gico-camera-001`: Benutzer filmt das untere Panel mit angegebenen 60 Kamera-FPS. Lauf vollständig beendet, alle 5.030 Batches / 120.720 ArtDmx-Pakete ohne gemeldete Sendefehler oder Worker-Drops gesendet; abschließend 48 Schwarzpakete und Worker beendet. Rohphasen, Einreichungszeitpunkte und Bedienkontext gespeichert. Originalvideo und Identifikation des gefilmten Panels stehen noch aus. 60 Kamera-FPS erlauben bei 30 LED-FPS nur etwa zwei Abtastungen pro Zustand; dies ist zunächst eine orientierende Messung, kein Nachweis stabiler optischer 30 FPS.

WhatsApp-Vorprüfung: 576×1024, knapp 60 FPS, 244,013 s. Kalibrierpunkte erkennbar, aber kurze Decoderstichproben zu 96–100 % uneindeutig; keine belastbare LED-FPS-Zahl. Nach Abgleich zweier Schwarzpausen fehlen in dieser Datei ungefähr 33 s des letzten Messabschnitts. Originaldatei angekündigt; vor erneutem Test zunächst diese prüfen. Belege: `measurements/gico-camera-001-whatsapp-review/BEWERTUNG_DE.md`.

Zweite WhatsApp-Datei geprüft: 289,323 s inklusive schwarzem Testende, aber 464×832 statt 576×1024 Pixel. In drei Decoderstichproben 0/181, 66/180, 0/180 gültige Kameraaufnahmen; weiterhin keine belastbare GICO-FPS-Angabe. Originaldatei abwarten. Belege: `measurements/gico-camera-001-video2-review/BEWERTUNG_DE.md`.


## Originalaufnahme vollständig ausgewertet

`E:/LED Full.mov`, 1080×1920, knapp 60 FPS, 289,323 s. Neue lokale Kalibrierung und begrenzter Erasure-CRC-Decoder getestet. Im 30-FPS-Fenster 1.785 aufeinanderfolgende IDs 8–1.792 mindestens einmal gelesen, keine ID-Lücke: 29,991 beobachtete neue IDs/s. 809 IDs haben mindestens eine vollständig gelesene CRC-Aufnahme, 976 sind nur mit begrenzter Erasure-Rekonstruktion belegt. 593 IDs erscheinen nur in einem Kamerabild. Strenge Zweibildbeobachtung daher 20,209/s, ausdrücklich keine GICO-Leistungsgrenze. Bei 25 FPS 24,987/s (Einbild), bei 15 FPS 14,730/s einschließlich etwa einer Sekunde verworfener Bildregistrierung.

Das ist starke optische Evidenz für nominal 30 FPS am gefilmten Panel im unabhängigen Sendertest. Keine elektrische/all-port/TD-Integrationsabnahme; strengere 120/240-FPS-Aufnahme optional für ursprüngliche Zweibildabnahme. Vollständiger Bericht und Rohbelege: `measurements/gico-camera-001-original-review/ERGEBNISSE_DE.md`. Keine Hardwareausgabe während der Auswertung.

TD→GICO-Test implementiert: nativer Bytevergleich für 25 Muster und lokaler Kurzlauf mit 3.888 geprüften Paketen bestanden. Details in TD_ANLEITUNG_DE.md.

TD→GICO-Hardwarelauf `measurements/gico-td-camera-001` vollständig abgeschlossen: 220,012 s, 6.541 gesendete Batches / 156.984 Datenpakete, keine gemeldeten Sendefehler; Worker-Mittelwert 29,773 Batches/s bei 30 FPS Solltransport. 3.139 ältere Einreichungen durch Latest-Frame-Verhalten verworfen, nicht mit Netzwerkverlusten gleichzusetzen. Inhalt nominell 15/25/30 FPS, Transport durchgehend 30 FPS. Nach 48 Schwarzpaketen regulär beendet; alle Wiederherstellungsprüfungen bestanden und Ausgabe zusätzlich live als aus bestätigt. Benutzer filmt nach Vorbereitung mit iPhone 13 Slo-Mo 240 FPS; Originalaufnahme und tatsächliche Zeitbasis noch ausstehend. Noch keine optische FPS-Aussage dieses TD-Laufs. Details: `measurements/gico-td-camera-001/ERGEBNISSE_DE.md`.

## TD-Originalaufnahme LED2.mov ausgewertet (2026-09-13)

Die unabhängige Prüfung der gemischten Zeitbasis und die optische Auswertung sind abgeschlossen. In den vollständig verlangsamten Fenstern wurden 14,933 / 23,544 / 26,680 unterschiedliche sichtbare IDs pro Sekunde bei Sollinhalt 15 / 25 / 30 FPS erkannt; ausgewertete reale Zeiten 59,5 / 59,5 / 33,875 s. Jede gezählte ID ist mindestens zweimal unmittelbar hintereinander erkannt, einschließlich begrenzter CRC-Erasure-Rekonstruktion. Das normal schnelle Exportende bestätigt ergänzend 26,322 IDs/s über 21 s mit nur einem Kamerabild als Mindestbeleg.

Stabile optische 30 FPS sind für diesen TD-Testpfad nicht nachgewiesen. Bereits vor dem Worker fehlen über die gesamte 30-FPS-Phase 88 von 1.800 geplanten Inhalts-IDs; weitere optische Lücken sind keiner einzelnen nachfolgenden Stufe zugeordnet. Getrennte Inhalts-/TD-/Worker-Zeitgeber sowie Producerpausen ungefähr alle 12,8 s müssen als Nächstes isoliert werden. Das ist keine allgemeine GICO-Grenze: Der unabhängige Sendertest zeigte zuvor nominal 30 FPS am gefilmten Panel.

Bericht, Grafik, Kalibrierung, Rohentscheidungen und Sendervergleich: `measurements/gico-td-camera-001-video-review/ERGEBNISSE_DE.md`. Diese Auswertung erfolgte ausschließlich offline, ohne Änderungen an TD, Firmware oder LED-Ausgabe.
