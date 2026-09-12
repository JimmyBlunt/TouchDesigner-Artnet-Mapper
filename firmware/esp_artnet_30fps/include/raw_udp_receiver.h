#pragma once
// Bypass the SDK's six-datagram socket mailbox. The lwIP callback copies each
// bounded packet into a 64-entry FreeRTOS queue and immediately frees its pbuf.
// All PCB operations run on the TCP/IP thread, matching Arduino AsyncUDP's API.
#include <Arduino.h>
#include <atomic>
#include <lwip/udp.h>
#include <lwip/pbuf.h>
#include <lwip/priv/tcpip_priv.h>
#include <freertos/queue.h>

namespace rawudp {
constexpr unsigned CAPACITY=64;
struct Packet { uint32_t epoch, stamp; uint16_t length; uint8_t data[531]; };
QueueHandle_t queue=nullptr;
udp_pcb* pcb=nullptr;
std::atomic<uint32_t> epoch{0}, datagrams{0}, dropped{0}, peak{0}, oversized{0}, foreign{0}, stale{0};

void receive(void*,udp_pcb*,pbuf* buffer,const ip_addr_t* source,u16_t) {
  if(!buffer)return;
  ++datagrams;
  if(!IP_IS_V4(source) || ip4_addr_get_u32(ip_2_ip4(source))!=PP_HTONL(0x0a00007d)) {
    ++foreign; pbuf_free(buffer); return;
  }
  Packet packet;
  if(buffer->tot_len>sizeof(packet.data)) {++oversized;pbuf_free(buffer);return;}
  packet.epoch=epoch.load(); packet.stamp=micros(); packet.length=buffer->tot_len;
  const auto copied=pbuf_copy_partial(buffer,packet.data,packet.length,0);
  pbuf_free(buffer);
  if(copied!=packet.length) {++oversized;return;}
  if(xQueueSend(queue,&packet,0)!=pdTRUE) {++dropped;return;}
  const auto count=uxQueueMessagesWaiting(queue);
  if(count>peak.load())peak=count;
}

err_t bindOnTcpipThread(tcpip_api_call_data*) {
  pcb=udp_new_ip_type(IPADDR_TYPE_V4);
  if(!pcb)return ERR_MEM;
  const err_t error=udp_bind(pcb,IP_ADDR_ANY,6454);
  if(error!=ERR_OK) {udp_remove(pcb);pcb=nullptr;return error;}
  udp_recv(pcb,receive,nullptr);
  return ERR_OK;
}

bool begin() {
  queue=xQueueCreate(CAPACITY,sizeof(Packet));
  if(!queue)return false;
  tcpip_api_call_data call{};
  return tcpip_api_call(bindOnTcpipThread,&call)==ERR_OK;
}
} // namespace rawudp
