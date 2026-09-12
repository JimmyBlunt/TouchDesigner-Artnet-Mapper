#include <Arduino.h>
#include <QNEthernet.h>
#include "receiver_core.h"

#ifndef PINOUT_CONFIRMED
#define PINOUT_CONFIRMED 0
#endif
#if PINOUT_CONFIRMED || defined(PINOUT_COMPILE_FIXTURE)
#include <FastLED.h>
#else
struct CRGB { uint8_t r,g,b; }; // Safe image has no LED driver dependency.
#endif
#if PINOUT_CONFIRMED
#include "third_party/object_fled/src/ObjectFLEDDmaManager.h"
#endif
#if defined(PINOUT_COMPILE_FIXTURE) || defined(BENCH_UNWIRED_PINS)
#define LED_PIN_1 2
#define LED_PIN_2 3
#define LED_PIN_3 4
#define LED_PIN_4 5
#define LED_PIN_5 6
#define LED_PIN_6 7
#define LED_PIN_7 8
#elif PINOUT_CONFIRMED
#include "hardware_pins.h"
#endif

using namespace qindesign::network;
EthernetUDP udp(96); // More than three complete 28-packet frames; inspect drops.
artnet::Receiver receiver;
CRGB leds[artnet::kPixels];
static_assert(sizeof(CRGB)==3,"ArtDmx copies require packed RGB pixels");
constexpr uint32_t kPeriodUs=33334; // <=30 FPS, no catch-up output bursts.
constexpr uint32_t kWireGuardUs=880*30+300;
static_assert(kWireGuardUs<kPeriodUs,"Longest chain exceeds the 30 FPS budget");
bool armed=false, black=true, networkStarted=false;
uint32_t showStart=0, lastReport=0, submitted=0, blackoutCount=0;
uint32_t showUs=0, maxShowUs=0, maxLoopUs=0, foreignPackets=0, telemetrySkipped=0;
uint32_t previousSubmitted=0, previousComplete=0, maxQueue=0;
uint32_t armedAt=0;
#ifdef BENCH_UNWIRED_PINS
constexpr bool kUnwiredBench=true;
#else
constexpr bool kUnwiredBench=false;
#endif
uint32_t dmaCompleted=0, dmaUs=0, dmaBusyDeferrals=0;
bool dmaPending=false;
void clearLeds() { ::memset(static_cast<void*>(leds),0,sizeof(leds)); }
bool dmaReady() {
#if PINOUT_CONFIRMED
  // Pinned FastLED internal API: avoid rewriting its shared DMA framebuffer
  // while the previous transfer is still active, without blocking UDP drainage.
  const bool busy=fl::ObjectFLEDDmaManager::getInstance().isBusy();
  if(!busy && dmaPending) { ++dmaCompleted; dmaUs=micros()-showStart; dmaPending=false; }
  return !busy;
#else
  return true;
#endif
}

void registerOutputs() {
#if PINOUT_CONFIRMED || defined(PINOUT_COMPILE_FIXTURE)
  // Incoming ArtDmx is RGB; only the physical output swaps to GRB.
  FastLED.addLeds<WS2812B,LED_PIN_1,GRB>(leds+0,203);
  FastLED.addLeds<WS2812B,LED_PIN_2,GRB>(leds+203,738);
  FastLED.addLeds<WS2812B,LED_PIN_3,GRB>(leds+941,880);
  FastLED.addLeds<WS2812B,LED_PIN_4,GRB>(leds+1821,810);
  FastLED.addLeds<WS2812B,LED_PIN_5,GRB>(leds+2631,352);
  FastLED.addLeds<WS2812B,LED_PIN_6,GRB>(leds+2983,680);
  FastLED.addLeds<WS2812B,LED_PIN_7,GRB>(leds+3663,442);
#endif
}
void showFrame(bool isBlack) {
#if PINOUT_CONFIRMED
  const uint32_t started=micros();
  FastLED.show();
  showUs=micros()-started;
  if(showUs>maxShowUs) maxShowUs=showUs;
  showStart=started;
  dmaPending=true;
  if(isBlack) ++blackoutCount; else ++submitted;
#endif
  black=isBlack;
}
void stopOutput() {
  armed=false; receiver.clear();
  // The loop issues blackout after the prior DMA wire guard has elapsed.
}
void report() {
  const uint32_t now=millis(), dt=now-lastReport;
  if(!dt) return;
  const auto& c=receiver.counts;
  char line[1400];
  const auto ip=Ethernet.localIP();
  const int n=snprintf(line,sizeof(line),
    "{\"firmware\":\"teensy41-artnet-0.1\",\"pinout_confirmed\":%s,"
    "\"unwired_bench\":%s,\"armed\":%s,\"black\":%s,\"ip\":\"%u.%u.%u.%u\",\"link\":%s,"
    "\"packets\":%lu,\"udp_received\":%lu,\"udp_queue_drops\":%lu,"
    "\"queue_peak\":%lu,\"rejected\":%lu,\"foreign\":%lu,\"ignored\":%lu,"
    "\"complete\":%lu,\"incomplete\":%lu,\"stale\":%lu,\"duplicates\":%lu,"
    "\"overwritten\":%lu,\"submitted\":%lu,\"blackouts\":%lu,"
    "\"complete_fps\":%.3f,\"submit_fps\":%.3f,"
    "\"show_call_us\":%lu,\"max_show_call_us\":%lu,\"max_loop_us\":%lu,"
    "\"telemetry_skipped\":%lu,\"dma_completed\":%lu,\"dma_elapsed_us\":%lu,"
    "\"dma_busy_deferrals\":%lu,\"physical_fps_verified\":false}\n",
    PINOUT_CONFIRMED?"true":"false",kUnwiredBench?"true":"false",armed?"true":"false",black?"true":"false",
    ip[0],ip[1],ip[2],ip[3],Ethernet.linkState()?"true":"false",
    c.packets,udp.totalReceiveCount(),udp.droppedReceiveCount(),maxQueue,
    c.rejected,foreignPackets,c.ignored,c.complete,c.incomplete,c.stale,c.duplicate,
    c.overwritten,submitted,blackoutCount,
    double(c.complete-previousComplete)*1000/dt,double(submitted-previousSubmitted)*1000/dt,
    showUs,maxShowUs,maxLoopUs,telemetrySkipped,dmaCompleted,dmaUs,dmaBusyDeferrals);
  if(Serial && n>0 && n<int(sizeof(line)) && Serial.availableForWrite()>=n)
    Serial.write(reinterpret_cast<const uint8_t*>(line),n);
  else ++telemetrySkipped;
  previousComplete=c.complete; previousSubmitted=submitted; lastReport=now;
}
void serialCommands() {
  static char command[48]; static unsigned pos=0; static bool overflow=false;
  for(unsigned i=0;i<64 && Serial.available();++i) {
    const char c=Serial.read();
    if(c=='\n' || c=='\r') {
      command[pos]=0;
      if(!overflow) {
        if(!strcmp(command,"STOP")) stopOutput();
        else if(!strcmp(command,"STATUS")) report();
        else if(!strcmp(command,"ARM") && PINOUT_CONFIRMED) {
          receiver.clear(); armed=true; armedAt=millis();
        }
      }
      pos=0; overflow=false;
    } else if(pos+1<sizeof(command) && !overflow) command[pos++]=c;
    else overflow=true;
  }
}
void setup() {
  Serial.begin(115200); // Never wait for USB: networking remains responsive.
#if PINOUT_CONFIRMED
  registerOutputs();
  FastLED.setBrightness(16); // Initial bench brightness cap; do not apply live settings.
  FastLED.setDither(0);
  clearLeds();
  showFrame(true);
#endif
  Ethernet.setHostname("teensy-artnet-test");
  Ethernet.begin(); // DHCP: no guessed static address and no collision with ESP .151.
  networkStarted=udp.begin(6454);
}
void loop() {
  const uint32_t loopStart=micros();
  Ethernet.loop();
  if(!networkStarted) networkStarted=udp.begin(6454);
  serialCommands();
  // Work is bounded under floods, but drains several complete frames each iteration.
  for(unsigned i=0;i<128;++i) {
    const auto queued=udp.receiveQueueSize(); if(queued>maxQueue) maxQueue=queued;
    const int n=udp.parsePacket(); if(n<0) break;
    if(!n) continue;
    if(udp.remoteIP()!=IPAddress(10,0,0,125)) { ++foreignPackets; continue; }
    receiver.ingest(udp.data(),udp.size(),udp.receivedTimestamp());
  }
  const uint32_t now=millis(); receiver.expire(now);
  if(armed && (!Ethernet.linkState() ||
      (uint32_t(now-armedAt)>1000 && uint32_t(now-receiver.lastComplete())>1000)))
    stopOutput();
  const uint32_t since=micros()-showStart;
  const bool available=dmaReady();
  if(!available && since>=kPeriodUs) ++dmaBusyDeferrals;
  if(available && !armed && !black && since>=kWireGuardUs) {
    clearLeds();
    showFrame(true);
  } else if(available && armed && since>=kPeriodUs && receiver.take(reinterpret_cast<uint8_t*>(leds))) {
    showFrame(false);
  }
  const uint32_t loopUs=micros()-loopStart; if(loopUs>maxLoopUs) maxLoopUs=loopUs;
  if(uint32_t(now-lastReport)>=1000) report();
}
