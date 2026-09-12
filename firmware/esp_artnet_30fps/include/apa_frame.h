#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
namespace artframe {
template<size_t Count> constexpr size_t apaFrameBytes() { return 4 + Count * 4 + (Count + 15) / 16; }
template<size_t Count>
void encodeApa102(const uint8_t* rgb, uint8_t* output, uint8_t brightnessLimit = 16) {
  memset(output,0,4);
  for(size_t i=0;i<Count;++i) {
    size_t p=4+i*4;
    output[p]=0xff;
    output[p+1]=uint16_t(rgb[i*3+2])*brightnessLimit/255;
    output[p+2]=uint16_t(rgb[i*3+1])*brightnessLimit/255;
    output[p+3]=uint16_t(rgb[i*3])*brightnessLimit/255;
  }
  memset(output+4+Count*4,0xff,(Count+15)/16);
}
}
