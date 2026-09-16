#include "frame_assembler.h"
#include "apa_frame.h"
#include <assert.h>
#include <stdio.h>
#include <time.h>
using namespace artframe;
struct Packet {
  uint8_t bytes[530]; size_t length;
  uint8_t* data() { return bytes; }
  size_t size() const { return length; }
  void pop_back() { --length; }
  uint8_t& operator[](size_t i) { return bytes[i]; }
};
Packet packet(uint16_t universe, uint8_t seq=1, size_t bytes=510, uint8_t value=1) {
  Packet p{}; p.length=18+bytes; memset(p.bytes,value,p.length);
  memcpy(p.data(),"Art-Net\0",8); p[8]=0;p[9]=0x50;p[10]=0;p[11]=14;
  p[12]=seq;p[13]=0;p[14]=universe&255;p[15]=universe>>8;p[16]=bytes>>8;p[17]=bytes&255;
  return p;
}
template<size_t N> Result send(Assembler<N>& a, uint16_t u, uint8_t s=1, size_t bytes=510, uint8_t value=1, uint32_t now=1) {
  auto p=packet(u,s,bytes,value); return a.accept(p.data(),p.size(),now);
}
int main() {
  unsigned cases=0;
  {
    uint8_t rgb[]={255,0,128,0,255,0}, encoded[apaFrameBytes<2>()+1];
    memset(encoded,0x55,sizeof(encoded)); encodeApa102<2>(rgb,encoded,16);
    for(unsigned i=0;i<4;++i)assert(encoded[i]==0);
    assert(encoded[4]==255 && encoded[5]==8 && encoded[6]==0 && encoded[7]==16);
    assert(encoded[8]==255 && encoded[9]==0 && encoded[10]==16 && encoded[11]==0);
    assert(encoded[12]==255 && encoded[13]==0x55);
    static_assert(apaFrameBytes<512>()==2084,"APA end clocks required");++cases;
  }
  {
    Assembler<203> a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,1,512,7)==Result::Accepted);assert(send(a,121,1,100,8)==Result::Complete);
    for(size_t i=0;i<510;++i)assert(a.rgb[i]==7);
    for(size_t i=510;i<609;++i)assert(a.rgb[i]==8);
    assert(a.counters.completed==1);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,121,1,98)==Result::Ignored);assert(a.counters.malformed==1);
    auto p=packet(120);p.pop_back();assert(a.accept(p.data(),p.size(),1)==Result::Ignored);
    p=packet(120,1,511);assert(a.accept(p.data(),p.size(),1)==Result::Ignored);
    p=packet(120);p[11]=13;assert(a.accept(p.data(),p.size(),1)==Result::Ignored);
    p=packet(120);p[9]=0x20;assert(a.accept(p.data(),p.size(),1)==Result::Ignored);
    p=packet(120);p[15]=128;assert(a.accept(p.data(),p.size(),1)==Result::Ignored);
    assert(send(a,999)==Result::Ignored);assert(a.counters.unrelated==1);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,1)==Result::Accepted);assert(send(a,120,1)==Result::Ignored);
    assert(send(a,121,1)==Result::Complete);assert(send(a,121,1)==Result::Ignored);
    assert(a.counters.completed==1 && a.counters.duplicate==2);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,8)==Result::Accepted);assert(send(a,121,9)==Result::Accepted);
    assert(send(a,121,8)==Result::Ignored);assert(send(a,120,9)==Result::Complete);
    assert(a.counters.incomplete==1 && a.counters.late==1);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    uint8_t sequences[]={254,255,1,2};
    for(uint8_t s:sequences) {
      assert(send(a,121,s)==Result::Accepted);assert(send(a,120,s)==Result::Complete);
    }
    assert(a.counters.completed==4);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,0)==Result::Accepted);assert(send(a,120,0)==Result::Accepted);
    assert(send(a,121,0)==Result::Complete);assert(a.counters.incomplete==1);
    assert(send(a,121,0)==Result::Accepted);assert(send(a,120,0)==Result::Complete);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,200,510,1,0xffffff00)==Result::Accepted);
    a.expire(0x20000);assert(a.counters.incomplete==1);
    assert(send(a,121,1,510,1,2000000)==Result::Accepted);
    assert(send(a,120,1,510,1,2000001)==Result::Complete);++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,3)==Result::Accepted);assert(send(a,121,0)==Result::Accepted);
    assert(send(a,120,0)==Result::Complete);assert(a.counters.incomplete==1);++cases;
  }
  {
    Assembler<203>a;Route good[]={{120,203,0}},bad[]={{120,204,0}};
    assert(a.configure(good,1));assert(!a.configure(bad,1));assert(send(a,120)==Result::Ignored);
    Route overlap[]={{120,100,0},{122,100,50}};assert(!a.configure(overlap,2));
    Route sameU[]={{120,100,0},{120,100,100}};assert(!a.configure(sameU,2));
    Route overflow[]={{32767,203,0}};assert(!a.configure(overflow,1));++cases;
  }
  {
    Assembler<203>a;Route r[]={{120,203,0}};assert(a.configure(r,1));
    assert(send(a,120,5)==Result::Accepted);a.resetCandidate();
    assert(send(a,121,5)==Result::Accepted);assert(a.counters.completed==0);
    assert(send(a,120,5)==Result::Complete);assert(a.counters.completed==1);++cases;
  }
  {
    Assembler<4105>a;Route r[]={{120,203,0},{122,738,203},{127,880,941},{133,810,1821},{139,352,2631},{142,1122,2983}};
    assert(a.configure(r,6));assert(a.universes()==28);
    clock_t start=clock();
    for(unsigned frame=0;frame<10000;++frame) {
      uint8_t seq=frame%255+1;unsigned completed=0;
      for(const auto& route:r)for(unsigned p=0;p<route.pixels;p+=170)
        completed += send(a,route.universe+p/170,seq,512,uint8_t(route.offset/3),frame*33334)==Result::Complete;
      assert(completed==1);
    }
    double elapsed=double(clock()-start)/CLOCKS_PER_SEC;
    printf("Host-only parser throughput: %.0f frames/s, 28 universes, 10000 frames (not ESP/network/output FPS)\n",10000/elapsed);
    assert(a.counters.completed==10000 && a.counters.incomplete==0);++cases;
  }
  printf("PASS: %u C++ test groups\n",cases);
}
