# TouchDesigner: lesende Hotspot-Stichprobe bei ausgeschalteter Ausgabe

12. September 2026. Zwei Leseproben über die bestehende TD-HTTP-Bridge;
kein Cook erzwungen, kein Parameter verändert, kein Sender gestartet.
Der Sender war bei beiden Proben nachweislich ausgeschaltet.

Die relevante Stichprobe liegt in `native-hotspots-off-active.json`.
Zwischen den Zählerständen liegen 6,283 Sekunden. 26 TOP-/CHOP-/Execute-Nodes
hatten zusätzliche Cooks. Die folgende Liste enthält die 15 aktiven Nodes
mit den höchsten **zuletzt** gemeldeten CPU-Cookzeiten; diese Zeiten sind
keine Mittelwerte und dürfen nicht als CPU-Profil summiert werden.

| Node unter `/project1/` | letzter CPU-Cook ms | Cooks/s im Fenster |
|---|---:|---:|
| pixelblaze_mapper/preview3d/instance_data | 17,540 | 3,18 |
| topto1 | 7,609 | 12,89 |
| legacy_source_mask | 4,755 | 12,41 |
| moviefilein1 | 1,184 | 12,41 |
| script4 | 0,959 | 30,72 |
| layout_scene_editor/scene_render | 0,568 | 12,41 |
| chopexec1 | 0,557 | 12,41 |
| madmapper_material_player | 0,212 | 12,89 |
| material_gradient_player | 0,125 | 12,89 |
| math3 | 0,118 | 12,89 |
| lookup1 | 0,102 | 12,41 |
| math1 | 0,088 | 12,41 |
| res1 | 0,083 | 12,89 |
| merge3 | 0,050 | 12,89 |
| lfo1 | 0,039 | 12,41 |

Die zuerst aufgezeichnete Datei `native-hotspots-off.json` enthält absichtlich
auch den ungefilterten Überblick. Dort erscheinen historische Einzelcooks wie
`layout_scene_editor/instances` mit 4285 ms, aber nur 38 Cooks insgesamt.
Dieser Node cookte im anschließenden Messfenster nicht erneut. Solche Werte
sind **keine laufende Dauerlast** und sollen nicht als aktueller Engpass
missverstanden werden. Gleiches gilt für einmalige Shaderkompilierungen.

Das Projekt hat Zielrate 60. Kein Performance-CHOP war vorhanden. Die globale
tatsächliche Bildrate wurde hier deshalb nicht zuverlässig ermittelt;
`absTime.frame / absTime.seconds` wäre wegen möglicher übersprungener Frames
keine geeignete Messung. Die obigen Zahlen beschreiben individuelle Cookraten
bei Ausgabe AUS, nicht die spätere aktive Produktrate. HTTP-/Inventarzugriff
und wechselnde Sichtbarkeit können die Stichprobe beeinflussen.

## Priorisierte Folgerungen

1. `topto1` ist als GPU-zu-CPU-Übergang ein vorrangiger Kandidat: aktuelle
   Parameter für Readback/Download, tatsächliche Auflösung, Samplemenge und
   mögliche Synchronisation untersuchen. Das aktuelle Mapping darf dabei
   keine Frame- oder Pixelverschiebung erhalten. Der Messwert allein beweist
   noch keine bestimmte GPU-Synchronisationsursache.
2. `legacy_source_mask` kostet in dieser Stichprobe mehrere Millisekunden
   regelmäßig. Callback auf Python-Schleifen, unnötige Kopien und wiederholtes
   Parsen derselben Maske prüfen. Vektorisierung bzw. gecachte Masken sind
   sinnvolle Kandidaten, sofern Tests die schwarzen Slots exakt erhalten.
3. `preview3d/instance_data` ist teuer, läuft aber nur etwa dreimal pro Sekunde.
   Geometrie und statische Attribute sollten nur bei Layoutänderung neu
   berechnet werden; bewegte Farben getrennt aktualisieren. Eine weitere
   Drosselung beeinflusst Vorschau, nicht notwendigerweise die LED-Ausgabe.
4. Die aktiven GLSL-Materialnodes selbst melden hier nur etwa 0,1–0,2 ms CPU.
   Daraus folgt keine GPU-Zeitmessung, aber kein vorrangiger Hinweis, die
   Animation vereinfachen zu müssen. Zunächst Readback, Maskierung und
   Vorschau-Callback untersuchen.
5. Ein belastbarer Vorher-/Nachhervergleich muss bei derselben aktiven Ausgabe,
   denselben sichtbaren Dialogen und identischem Material die Producerzählung,
   Pack-/Übergabezeiten sowie Empfänger-Ausgaben zusammen auswerten. Die bereits
   beobachteten etwa 20,64 Producer-FPS, 18,93 ms Senderzeit und 9,30 ms Packzeit
   sind im Senderzustand der ersten Datei erhalten; der Senderzustand war dabei
   ein gespeicherter Wert des zuvor gestoppten Laufs, keine neue aktive Messung.
