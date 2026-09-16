#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <FastLED.h>
#include <SPI.h>
#include <lwip/sockets.h>
#include <fcntl.h>
#include <atomic>
#include "frame_assembler.h"
#include "apa_frame.h"
#include "raw_udp_receiver.h"

// A distinct source-only override avoids SCons reordering -U/-D flags. The
// default environment remains unchanged, so library objects can be reused.
#ifdef EXPERIMENTAL_PROFILE_OVERRIDE
#undef PANEL_PROFILE
#define PANEL_PROFILE EXPERIMENTAL_PROFILE_OVERRIDE
#endif

#if !defined(CONFIG_IDF_TARGET_ESP32)
#error This build is for classic ESP32 only. Validate S3 hardware and driver separately.
#endif
#if PANEL_PROFILE == 768
#define HAS_APA_OUTPUT 1
constexpr size_t PIXELS = 768, WS_COUNT = 256, APA_COUNT = 512;
constexpr artframe::Route ROUTES[] = {{0,256,0},{2,512,256}};
constexpr uint8_t PINS[] = {14,18};
#elif PANEL_PROFILE == 1755
#define HAS_APA_OUTPUT 1
constexpr size_t PIXELS = 1755, WS_COUNT = 731, APA_COUNT = 1024;
constexpr artframe::Route ROUTES[] = {{0,731,0},{5,1024,731}};
constexpr uint8_t PINS[] = {14,18};
#elif PANEL_PROFILE == 731
constexpr size_t PIXELS = 731;
constexpr artframe::Route ROUTES[] = {{0,731,0}};
constexpr uint8_t PINS[] = {14};
#elif PANEL_PROFILE == 1
constexpr size_t PIXELS = 203;
constexpr artframe::Route ROUTES[] = {{120,203,0}};
#elif PANEL_PROFILE == 5
constexpr size_t PIXELS = 2983;
constexpr artframe::Route ROUTES[] = {{120,203,0},{122,738,203},{127,880,941},{133,810,1821},{139,352,2631}};
#elif PANEL_PROFILE == 6
constexpr size_t PIXELS = 4105;
constexpr artframe::Route ROUTES[] = {{120,203,0},{122,738,203},{127,880,941},{133,810,1821},{139,352,2631},{142,1122,2983}};
#else
#error Unsupported PANEL_PROFILE
#endif
constexpr size_t PORTS = sizeof(ROUTES) / sizeof(ROUTES[0]);
#if PANEL_PROFILE != 731 && !defined(HAS_APA_OUTPUT)
constexpr uint8_t PINS[] = {26,27,25,14,19,17};
#endif
// Headroom above the 30 FPS sender avoids phase aliasing between two independent
// 30 Hz schedulers. The physical strip timing still sets the true upper bound.
constexpr uint32_t OUTPUT_PERIOD_US = 16666, FAILSAFE_US = 1000000;
artframe::Assembler<PIXELS> assembler;
CRGB leds[PIXELS];
uint8_t pendingRgb[PIXELS * 3] = {};
SemaphoreHandle_t mailboxMutex, assemblyMutex;
bool pending = false;
uint32_t pendingAt = 0;
std::atomic<bool> armed{false};
std::atomic<uint32_t> outputFrames{0}, supersededFrames{0}, showUs{0}, maxShowUs{0};
std::atomic<uint32_t> firstOutputUs{0}, lastOutputUs{0}, blackouts{0}, socketErrors{0};
std::atomic<uint32_t> socketReceiveBuffer{0}, lastCompleteUs{0};
std::atomic<uint32_t> foreignSourcePackets{0};
std::atomic<uint32_t> wsCompletedTransfers{0}, apaCompletedTransfers{0};
std::atomic<uint32_t> wsTransferUs{0}, apaTransferUs{0};
portMUX_TYPE outputStatsMutex = portMUX_INITIALIZER_UNLOCKED;
WebServer http(80);
Preferences prefs;
void initializeLedDrivers();

#if defined(HAS_APA_OUTPUT)
// Clocked APA102 SPI runs concurrently with the WS2812 I2S transfer. Both
// tasks finish before the shared LED frame can be replaced.
SPIClass apaSpi(VSPI);
TaskHandle_t apaTaskHandle = nullptr;
SemaphoreHandle_t apaDone;
uint8_t apaBytes[artframe::apaFrameBytes<APA_COUNT>()];
void apaTask(void*) {
  bool initialized = false;
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    if (!initialized) { apaSpi.begin(19,-1,18,-1); initialized = true; }
    uint32_t start=micros();
    apaSpi.beginTransaction(SPISettings(4000000,MSBFIRST,SPI_MODE0));
    apaSpi.writeBytes(apaBytes,sizeof(apaBytes));
    apaSpi.endTransaction();
    apaTransferUs=micros()-start; ++apaCompletedTransfers;
    xSemaphoreGive(apaDone);
  }
}
void prepareApa() {
  static_assert(sizeof(CRGB)==3,"RGB source must be packed");
  artframe::encodeApa102<APA_COUNT>(reinterpret_cast<uint8_t*>(leds+WS_COUNT),apaBytes);
}
#endif

void receiverTask(void*) {
  rawudp::Packet packet;
  unsigned drained=0;
  for (;;) {
    if(xQueueReceive(rawudp::queue,&packet,pdMS_TO_TICKS(1))==pdTRUE) {
      xSemaphoreTake(assemblyMutex,portMAX_DELAY);
      // ARM/STOP invalidates packets already queued by the network callback.
      if(packet.epoch!=rawudp::epoch.load()) {
        ++rawudp::stale;
      } else {
        auto result=assembler.accept(packet.data,packet.length,packet.stamp);
        if(result==artframe::Result::Complete) {
          lastCompleteUs=packet.stamp;
          xSemaphoreTake(mailboxMutex,portMAX_DELAY);
          if(pending)++supersededFrames;
          memcpy(pendingRgb,assembler.rgb,sizeof(pendingRgb));
          pending=true;pendingAt=packet.stamp;
          xSemaphoreGive(mailboxMutex);
        }
      }
      xSemaphoreGive(assemblyMutex);
      if(++drained>=128) {drained=0;vTaskDelay(1);}
    } else {
      drained=0;
      xSemaphoreTake(assemblyMutex,portMAX_DELAY);
      assembler.expire(micros());
      xSemaphoreGive(assemblyMutex);
    }
  }
}

void outputTask(void*) {
  uint32_t nextShow = micros();
  bool showingData = false;
  bool driversReady = false;
  for (;;) {
    // A disarmed boot never initializes LED GPIOs: the testboard pin wiring
    // must be verified before the explicit arm command permits any GPIO use.
    if (armed && !driversReady) { initializeLedDrivers(); driversReady = true; }
    uint32_t now = micros();
    bool ready = false;
    if (int32_t(now - nextShow) >= 0) {
      xSemaphoreTake(mailboxMutex, portMAX_DELAY);
      if (armed && pending && uint32_t(now - pendingAt) <= FAILSAFE_US) {
        memcpy(leds, pendingRgb, sizeof(pendingRgb));
        pending = false; ready = true;
      }
      xSemaphoreGive(mailboxMutex);
    }
    bool blank = (!armed || uint32_t(now - lastCompleteUs.load()) > FAILSAFE_US) && showingData;
    if (blank) { memset(leds, 0, sizeof(leds)); ready = false; }
    if (ready || blank) {
      uint32_t start = micros();
#if defined(HAS_APA_OUTPUT)
      prepareApa(); xTaskNotifyGive(apaTaskHandle);
#endif
      uint32_t wsStart=micros(); FastLED.show();
      wsTransferUs=micros()-wsStart; ++wsCompletedTransfers;
#if defined(HAS_APA_OUTPUT)
      xSemaphoreTake(apaDone,portMAX_DELAY);
#endif
      uint32_t duration = micros() - start;
      showUs = duration;
      if (duration > maxShowUs) maxShowUs = duration;
      // Preserve phase through the 1 ms scheduler quantization. If badly late,
      // schedule a fresh period; never replay queued frames to catch up.
      nextShow += OUTPUT_PERIOD_US;
      if (int32_t(start - nextShow) >= 0) nextShow = start + OUTPUT_PERIOD_US;
      if (ready) {
        portENTER_CRITICAL(&outputStatsMutex);
        uint32_t completedAt=micros();
        if (outputFrames.fetch_add(1) == 0) firstOutputUs = completedAt;
        lastOutputUs = completedAt;
        portEXIT_CRITICAL(&outputStatsMutex);
        showingData = true;
      } else { ++blackouts; showingData = false; }
    }
    vTaskDelay(1);
  }
}

String statusJson() {
  xSemaphoreTake(assemblyMutex, portMAX_DELAY);
  auto c = assembler.counters;
  xSemaphoreGive(assemblyMutex);
  portENTER_CRITICAL(&outputStatsMutex);
  uint32_t outputs = outputFrames, span = lastOutputUs.load() - firstOutputUs.load();
  portEXIT_CRITICAL(&outputStatsMutex);
  float fps = outputs > 1 && span ? float(outputs - 1) * 1000000.0f / span : 0;
  String s = "{\"firmware\":\"experimental-esp-artnet-30fps-v1\",\"backend\":\"FastLED-3.9.15-I2S-parallel";
#if defined(HAS_APA_OUTPUT)
  s += "+APA102-hardware-SPI-concurrent";
#endif
  s += "\"";
  s += ",\"armed\":" + String(armed ? "true" : "false");
  s += ",\"ip\":\"" + WiFi.localIP().toString() + "\",\"pixels\":" + String(PIXELS);
  s += ",\"universes\":" + String(assembler.universes());
  s += ",\"receivedPackets\":" + String(c.packets) + ",\"acceptedPackets\":" + String(c.accepted);
  s += ",\"malformedPackets\":" + String(c.malformed) + ",\"unrelatedPackets\":" + String(c.unrelated);
  s += ",\"duplicatePackets\":" + String(c.duplicate) + ",\"latePackets\":" + String(c.late);
  s += ",\"completedFrames\":" + String(c.completed) + ",\"incompleteFrames\":" + String(c.incomplete);
  s += ",\"supersededFrames\":" + String(supersededFrames.load());
  s += ",\"outputFrames\":" + String(outputs) + ",\"outputAverageFps\":" + String(fps,3);
  s += ",\"wsCompletedTransfers\":" + String(wsCompletedTransfers.load());
  s += ",\"apaCompletedTransfers\":" + String(apaCompletedTransfers.load());
  s += ",\"wsTransferUs\":" + String(wsTransferUs.load()) + ",\"apaTransferUs\":" + String(apaTransferUs.load());
  s += ",\"showCallUs\":" + String(showUs.load()) + ",\"maxShowCallUs\":" + String(maxShowUs.load());
  s += ",\"blackoutFrames\":" + String(blackouts.load()) + ",\"socketErrors\":" + String(socketErrors.load());
  s += ",\"socketReceiveBufferBytes\":" + String(socketReceiveBuffer.load());
  s += ",\"receiveMode\":\"raw-udp-queue64\",\"rawUdpDatagrams\":" + String(rawudp::datagrams.load());
  s += ",\"rawUdpQueueDrops\":" + String(rawudp::dropped.load()) + ",\"rawUdpQueuePeak\":" + String(rawudp::peak.load());
  s += ",\"rawUdpOversizePackets\":" + String(rawudp::oversized.load()) + ",\"rawUdpStaleEpochPackets\":" + String(rawudp::stale.load());
  s += ",\"foreignSourcePackets\":" + String(rawudp::foreign.load()) + ",\"allowedSender\":\"10.0.0.125\"";
  s += ",\"freeHeap\":" + String(ESP.getFreeHeap()) + ",\"rssi\":" + String(WiFi.RSSI());
  s += ",\"uptimeMs\":" + String(millis()) + ",\"targetFps\":30,\"outputCeilingFps\":60,\"brightnessLimit255\":16,\"networkDropCounterAvailable\":false}";
  return s;
}

void setArmed(bool value) {
  // Never replay a frame received before an explicit new arm operation.
  xSemaphoreTake(assemblyMutex, portMAX_DELAY);
  xSemaphoreTake(mailboxMutex, portMAX_DELAY);
  assembler.resetCandidate();
  ++rawudp::epoch;
  pending = false; armed = value;
  xSemaphoreGive(mailboxMutex);
  xSemaphoreGive(assemblyMutex);
}

void initializeLedDrivers() {
#if PANEL_PROFILE == 731 || defined(HAS_APA_OUTPUT)
  FastLED.addLeds<WS2812B,14,GRB>(leds,ROUTES[0].pixels);
#else
  FastLED.addLeds<WS2812B,26,GRB>(leds, 203);
#if PANEL_PROFILE == 5 || PANEL_PROFILE == 6
  FastLED.addLeds<WS2812B,27,GRB>(leds + 203, 738);
  FastLED.addLeds<WS2812B,25,GRB>(leds + 941, 880);
  FastLED.addLeds<WS2812B,14,GRB>(leds + 1821, 810);
  FastLED.addLeds<WS2812B,19,GRB>(leds + 2631, 352);
#endif
#if PANEL_PROFILE == 6
  FastLED.addLeds<WS2812B,17,GRB>(leds + 2983, 1122);
#endif
#endif
  FastLED.setBrightness(16); FastLED.setDither(0); FastLED.clear(false);
}

void setup() {
  Serial.begin(115200);
  mailboxMutex = xSemaphoreCreateMutex(); assemblyMutex = xSemaphoreCreateMutex();
  if (!mailboxMutex || !assemblyMutex || !assembler.configure(ROUTES, PORTS)) {
    Serial.println("FATAL: buffer/configuration initialization failed"); while (true) delay(1000);
  }
  prefs.begin("artnet-exp", false);
  WiFi.mode(WIFI_STA); WiFi.setSleep(false);
  IPAddress fixedIp, netmask, gateway;
  if (fixedIp.fromString(prefs.getString("ip", "")) &&
      netmask.fromString(prefs.getString("mask", "")) &&
      gateway.fromString(prefs.getString("gateway", ""))) WiFi.config(fixedIp,gateway,netmask);
  // Credentials are provisioned over USB, kept in a separate NVS namespace,
  // and never returned by status/config or printed to the serial console.
  String ssid = prefs.getString("ssid", ""), password = prefs.getString("password", "");
  if (ssid.length()) WiFi.begin(ssid.c_str(), password.c_str());
  else WiFi.begin(); // Reuse saved Espressif WiFi credentials if available.
  http.on("/api/status", HTTP_GET, [] { http.send(200,"application/json",statusJson()); });
  http.on("/api/config", HTTP_GET, [] {
    String s = "{\"experimental\":true,\"profile\":" + String(PANEL_PROFILE) + ",\"routingMutable\":false,\"outputs\":[";
    for (size_t i=0;i<PORTS;++i) {
      if(i) s += ',';
      s += "{\"pin\":" + String(PINS[i]) + ",\"count\":" + String(ROUTES[i].pixels) + ",\"universe\":" + String(ROUTES[i].universe);
#if defined(HAS_APA_OUTPUT)
      if (i == 1) s += ",\"type\":\"APA102\",\"clockPin\":19,\"spiHz\":4000000,\"colorOrder\":\"BGR\"";
      else
#endif
        s += ",\"type\":\"WS2812B\",\"clockPin\":-1,\"colorOrder\":\"GRB\"";
      s += "}";
    }
    http.send(200,"application/json",s + "]}");
  });
  http.on("/api/arm", HTTP_POST, [] {
    if (http.arg("enabled") != "true" && http.arg("enabled") != "false") { http.send(400,"application/json","{\"error\":\"enabled=true or false required\"}"); return; }
    setArmed(http.arg("enabled") == "true"); http.send(200,"application/json",statusJson());
  });
  if(!rawudp::begin()) {
    Serial.println("FATAL: raw UDP queue/bind initialization failed");while(true)delay(1000);
  }
  http.begin();
#if defined(HAS_APA_OUTPUT)
  apaDone=xSemaphoreCreateBinary();
  if (!apaDone || xTaskCreatePinnedToCore(apaTask,"apa102-spi",3072,nullptr,1,&apaTaskHandle,0) != pdPASS) {
    Serial.println("FATAL: APA102 task allocation failed"); while(true) delay(1000);
  }
#endif
  if (xTaskCreatePinnedToCore(receiverTask,"artnet-rx",4096,nullptr,2,nullptr,0) != pdPASS ||
      xTaskCreatePinnedToCore(outputTask,"led-output",4096,nullptr,1,nullptr,1) != pdPASS) {
    Serial.println("FATAL: task allocation failed"); while (true) delay(1000);
  }
  Serial.println("EXPERIMENTAL READY, GPIOs uninitialized. Commands: status, arm, stop, ip ADDRESS MASK GATEWAY, wifi SSID<TAB>PASSWORD");
}

void loop() {
  http.handleClient();
  static String command;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') {
      if (command.endsWith("\r")) command.remove(command.length()-1);
      if (command == "status") Serial.println(statusJson());
      else if (command == "arm") { setArmed(true); Serial.println("armed"); }
      else if (command == "stop") { setArmed(false); Serial.println("disarmed"); }
      else if (command.startsWith("ip ")) {
        int one=command.indexOf(' ',3), two=command.indexOf(' ',one+1);
        IPAddress ip,mask,gateway;
        if(one>3 && two>one && ip.fromString(command.substring(3,one)) &&
           mask.fromString(command.substring(one+1,two)) && gateway.fromString(command.substring(two+1))) {
          setArmed(false); prefs.putString("ip",ip.toString()); prefs.putString("mask",mask.toString());
          prefs.putString("gateway",gateway.toString()); WiFi.config(ip,gateway,mask);
          Serial.println("Static IP stored and applied");
        } else Serial.println("Invalid IP command");
      }
      else if (command.startsWith("wifi ")) {
        int split = command.indexOf('\t',5);
        if(split > 5 && split-5 <= 32 && command.length()-split-1 <= 63) {
          String ssid = command.substring(5,split), password = command.substring(split+1);
          setArmed(false); prefs.putString("ssid",ssid); prefs.putString("password",password);
          WiFi.begin(ssid.c_str(),password.c_str()); Serial.println("WiFi credentials stored; connecting with DHCP");
        } else Serial.println("Invalid WiFi command format");
      } else Serial.println("Unknown command");
      command = "";
    } else if (command.length() < 128) command += ch;
    else command = "";
  }
  delay(1);
}
