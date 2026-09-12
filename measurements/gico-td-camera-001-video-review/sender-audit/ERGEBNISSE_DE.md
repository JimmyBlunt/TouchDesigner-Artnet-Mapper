# Offline-Prüfung der TD-Produktion – GICO-Kameratest 001

Die Protokolle enthalten bereits vor der eigentlichen Netzwerkausgabe fehlende Bild-IDs. Insbesondere wurden im Abschnitt mit 30 neuen Inhalten pro Sekunde nur **1.712 von 1.800 geplanten IDs** eingereicht. Der Worker-Mittelwert von 29,77 gesendeten Paketsätzen pro Sekunde ist deshalb kein Beleg für 29,77 unterschiedliche sichtbare Bilder pro Sekunde.

| Geplanter Inhalt | Native Einreichungen / 60 s | Unterschiedliche IDs | Fehlende IDs | Wiederholte Einreichungen derselben ID | Eingereichte unterschiedliche IDs / 60 s |
|---|---:|---:|---:|---:|---:|
| 15 pro Sekunde | 2.628 | 896 / 900 | 4 (0,44 %) | 1.732 | 14,933 pro Sekunde |
| 25 pro Sekunde | 2.641 | 1.477 / 1.500 | 23 (1,53 %) | 1.164 | 24,617 pro Sekunde |
| 30 pro Sekunde | 2.662 | 1.712 / 1.800 | 88 (4,89 %) | 950 | 28,533 pro Sekunde |

Dies sind Produzentenwerte, keine optische Messung. Die gesamten erwarteten ID-Bereiche einschließlich Anfang und Ende wurden geprüft: 0–899, 0–1499 beziehungsweise 0–1799. Alle Lücken liegen innerhalb dieser Bereiche. Der feste Transport-Sollwert betrug in allen Abschnitten 30 Paketsätze pro Sekunde. Die native TD-Seite reichte häufiger ein; der Worker verwirft im vorgesehenen Verfahren ältere wartende Paketsätze zugunsten des aktuellen Inhalts. Eine vorhandene ID muss deshalb nicht tatsächlich gesendet oder sichtbar geworden sein.

## Zeitverhalten vor dem Worker

| Abschnitt | Median Abstand zwischen protokollierten Einreichungen | 95. Perzentil | Maximum | Median Zeit bis zur ersten Einreichung einer anderen ID | Maximum dieser Zeit |
|---|---:|---:|---:|---:|---:|
| 15 | 20,859 ms | 40,504 ms | 155,871 ms | 66,657 ms | 167,856 ms |
| 25 | 21,105 ms | 40,051 ms | 129,234 ms | 39,899 ms | 142,408 ms |
| 30 | 20,895 ms | 40,452 ms | 138,114 ms | 32,990 ms | 148,552 ms |

Die Zeitstempel werden zu Beginn des Fixture-Schritts erfasst, **vor** Source-Cook, Packen und Übergabe. Die Tabellen zeigen somit Abstände zwischen den Startzeitpunkten später erfolgreich eingereichter Schritte, keine exakten Queue-, Socket-, elektrischen oder optischen Zeitstempel. Die Haltezeiten beziehen sich ausschließlich auf die im Produzentenlog enthaltenen IDs.

Über den gesamten Lauf fallen **17 Lücken größer als 90 ms** auf, die ungefähr alle **12,8 Sekunden** auftreten: Beginn bei 4,024 s, 16,815 s, 29,609 s, 42,435 s bis 208,814 s. Die Unterbrechungen dauern 92,743–155,871 ms. Die Ursache ist mit diesen Protokollen nicht bestimmbar; ein periodischer Vorgang auf der TD-/Hostseite ist ein gezielt zu prüfender Ansatz. Im 30er-Abschnitt erklären vier dieser langen Lücken elf der 88 fehlenden IDs. Die übrigen ID-Ausfälle entstehen an kürzeren Lücken im Produzentenlog.

## Native Zähler und tatsächliche Worker-Zähler

Über den vollständigen Test inklusive Kalibrierung, Warm-up und Schwarzpausen:

- 9.681 protokollierte Einreichungen; dies stimmt mit dem nativen `send_count` und dem finalen Worker-`submitted_batches` überein.
- 6.541 vollständig gesendete Paketsätze und 156.984 Datenpakete: exakt 24 Universen pro Paketsatz.
- 3.139 überholte Paketsätze; 0 zurückgewiesene Paketsätze und 0 gemeldete Socket-Sendefehler.
- Ein Paketsatz bleibt in der Differenz zwischen eingereicht, gesendet, überholt und zurückgewiesen beim angeforderten Stopp unklassifiziert. Daraus ist kein Netzwerkverlust abzuleiten.
- Final 48 Blackout-Pakete, Worker geschlossen, Wiederherstellungsprüfungen erfolgreich.
- Worker-Mittelwert **29,7731 Paketsätze/s**, berechnet als `(sent_batches − 1) / active_seconds` über 219,6613 Sekunden zwischen erster und letzter vollständiger Sendung. Keine Aufteilung dieses Sendewerts nach Messphase möglich.
- Die früher gelesene native Transport-Statuskopie enthält 6.533 gesendete Paketsätze; für die Gesamtsumme gilt der nach dem Stopp gelesene finale Worker-Stand 6.541.
- Native Packzeit im letzten Status: Mittel 8,107 ms, Maximum 19,877 ms; gesamte native Sendefunktion Mittel 8,641 ms, Maximum 20,805 ms. Worker-Zeit je vollständiger Sendung maximal 3,319 ms. Diese Zähler verwenden unterschiedliche Zeitfenster und dürfen nicht addiert oder als vollständiges Profil interpretiert werden.

## Abgleich mit dem Video

`sender-audit.json` enthält pro Messphase alle fehlenden IDs sowie den vollständigen Verlauf jeder eingereichten ID mit erster/letzter Einreichung und Wiederholungszahl. Bei der Videoauswertung sind mindestens drei Kategorien zu trennen:

1. ID bereits im Produzentenlog fehlend: diese Fixture hat sie nicht eingereicht; daraus folgt keine Controller-Schwäche.
2. ID eingereicht, optisch nicht nachgewiesen: Worker-Ersetzung, weiterer Übertragungs-/Ausgabeweg und optische Nichterkennung bleiben ohne zusätzliche Daten mögliche Ursachen.
3. ID optisch sicher erkannt: tatsächlicher sichtbarer Inhalt, einschließlich der getrennt ausgewiesenen Decoder-Sicherheitsstufe.

Der Test ersetzt die eigentliche Effektquelle durch einen temporären Script CHOP. Die Laufzeit beliebiger produktiver Effekte ist damit nicht gemessen. Die Zeitlücken belegen einen Optimierungsbedarf in diesem konkreten TD-Testpfad; sie bestimmen weder ein allgemeines GICO-Limit noch die maximal mögliche Leistung nach einer Optimierung.

Zusätzlich werden die zeitbasiert auf 15/25/30 Hz quantisierten IDs zunächst von der ungefähr 44-Hz-TD-Produktion und danach vom unabhängigen 30-Hz-Worker abgetastet. Schon diese nicht synchronisierte Auswahl kann eingereichte IDs ersetzen oder vorhandene Inhalte wiederholen. Ein bei jeder nativen Berechnung veränderter Effekt hat andere Eigenschaften. Der Architekturhinweis und die gesonderte Prüfung der 12,8-s-Periodik stehen in `PERIODIK_CODE_REVIEW_DE.md`; die optische Rate dieser Testquelle ist kein allgemeines FPS-Limit der Produktionspipeline.

Reproduktion ab Repository-Ordner:

```powershell
& 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' measurements/gico-td-camera-001-video-review/sender-audit/analyze_sender.py --run measurements/gico-td-camera-001 --output measurements/gico-td-camera-001-video-review/sender-audit
```

Das Skript prüft monotone Zeit/IDs, alle `accepted`-Flags, die exakte zeitbasierte ID-Formel und die Phasensummen. SHA-256 der Eingangsdateien und des Skripts stehen im JSON. Es liest ausschließlich lokale Dateien und verändert weder TouchDesigner noch Hardware.
