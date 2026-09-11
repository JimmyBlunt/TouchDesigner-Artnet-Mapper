# Naechster Diagnoseschritt nach dem Scanvideo

Read-only Controller-Messung waehrend capture-8c0c9f32-bf7c-42cb-a7e5-81823fb7d73b: In 9,047 Sekunden stiegen packets um 1509, framesComplete/outputFrames um 42, framesIncomplete um 106 und timeouts um 1. droppedPackets und sequenceErrors blieben unveraendert. Der Controller meldete 5-7 FPS in den drei Stichproben, zuvor 4 FPS. Rohwerte: controller-scan-throughput.json.

Damit werden nur rund 4,6 LED-Ausgaben/s im betrachteten Intervall gemeldet. Die gemessenen langen Kamera-Lesephasen koennen daher auch Folge verzoegert sichtbarer Schaltzustaende sein; sie beweisen keinen Kameradefekt oder langsame Bildverarbeitung.

Der Scanplan enthaelt alle 13 Universen U120-U132 lueckenlos. Schwarze Restplaetze an den Panelenden sind korrekt. 20 komplette Bloecke/s wuerden 260 Pakete/s bedeuten; tatsaechlich empfangene rund 167 Pakete/s duerfen ohne gemessene Senderzahl nicht pauschal als Paketverlust gewertet werden. Die 20 Hz im Worker sind eine Obergrenze, keine garantierte Ist-Rate.

Controller-Firmware ist im Workspace nicht vorhanden. Die WebUI nennt framesComplete 'Vollstaendige Sammlungen' und outputFrames 'LED-Ausgaben'; die exakte interne Definition von framesIncomplete ist unbekannt. droppedPackets=0 schliesst Verluste vor dem Firmwarehandler nicht aus. Sequenzfehler sind bei der derzeit verwendeten Art-Net-Sequenznummer 0 wenig aussagekraeftig.

## Geplanter Vergleich nach Abschluss der laufenden Aufnahme

1. Aktuelle Ansicht abschliessen und sichern; kein Eingriff waehrend der Aufnahme.
2. Etwa 20 gut sichtbare LEDs fuer einen separaten kurzen Diagnosetest auswaehlen. Die produktiven Ansichten und ihr voller Umfang bleiben erhalten.
3. Tatsachlich gesendete Pakete/Bloecke und Controllerzaehler ueber denselben Zeitraum erfassen. Erst daraus unterscheiden, ob der Sender selbst seltener sendet oder nach dem Senden Pakete/Frames fehlen.
4. Kleine Abstaende zwischen den 13 Universe-Paketen als einzelne Testvariable pruefen. Alle Universen, Helligkeit, Kamera und maximale Blockrate dabei gleich lassen. Noch keine Behauptung, dass diese Aenderung hilft.
5. Vollstaendige LED-Ausgaben, Zeit pro LED, Erkennungsquote und sichtbare Blitzfolge vergleichen. Falls der Empfang vollstaendig ist und die Verzoegerung bleibt, Kamera-/Controllerlatenz mit gezielten Ein-/Aus-Schritten weiter trennen.

In diesem Schritt wurden nur Messungen und ein Vergleichsplan erstellt. Kein neuer Scan, Testmuster, Controller-Schreibzugriff oder geaendertes Sendetiming gestartet. Noch kein Kurztestprofil in die Dialoge uebernommen.
