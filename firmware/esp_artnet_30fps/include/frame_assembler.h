#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

namespace artframe {
struct Route { uint16_t universe; uint16_t pixels; uint16_t offset; };
struct Counters {
  uint32_t packets = 0, malformed = 0, unrelated = 0, accepted = 0;
  uint32_t completed = 0, incomplete = 0, duplicate = 0, late = 0;
};
enum class Result { Ignored, Accepted, Complete };

// One sender only; nonzero ArtDmx sequences must identify the whole frame.
// Sequence zero is supported, but cannot prove absence of cross-frame mixing
// after packet loss: use nonzero sequences for defensible measurements.
template<size_t Pixels, size_t MaxUniverses = 32>
class Assembler {
 public:
  uint8_t rgb[Pixels * 3] = {};
  Counters counters;
  bool configure(const Route* routes, size_t count) {
    configured_ = false; used_ = 0; all_ = seen_ = 0;
    haveSeq_ = completedSequence_ = false;
    for (size_t i = 0; i < count; ++i) {
      if (!routes[i].pixels || size_t(routes[i].offset) + routes[i].pixels > Pixels) return false;
      for (size_t j = 0; j < i; ++j)
        if (routes[i].offset < size_t(routes[j].offset) + routes[j].pixels &&
            routes[j].offset < size_t(routes[i].offset) + routes[i].pixels) return false;
      for (size_t p = 0; p < routes[i].pixels; p += 170) {
        if (used_ == MaxUniverses || used_ == 32) return false;
        uint16_t u = routes[i].universe + p / 170;
        if (u > 32767) return false;
        for (size_t j = 0; j < used_; ++j) if (universes_[j] == u) return false;
        universes_[used_] = u;
        offsets_[used_] = (routes[i].offset + p) * 3;
        size_t left = routes[i].pixels - p;
        lengths_[used_] = (left < 170 ? left : 170) * 3;
        all_ |= uint32_t(1) << used_++;
      }
    }
    configured_ = used_ != 0;
    return configured_;
  }
  void expire(uint32_t now, uint32_t timeout = 100000) {
    if (seen_ && uint32_t(now - began_) > timeout) {
      ++counters.incomplete; seen_ = 0;
    }
    // Permit a sender restart after a quiet period (including sequence reset).
    if (haveSeq_ && uint32_t(now - lastAccepted_) > 1000000) haveSeq_ = false;
  }
  Result accept(const uint8_t* p, size_t n, uint32_t now) {
    ++counters.packets;
    expire(now);
    if (!configured_ || n < 18 || memcmp(p, "Art-Net\0", 8) || p[8] != 0 || p[9] != 0x50 ||
        ((uint16_t(p[10]) << 8) | p[11]) < 14) return malformed();
    size_t len = (size_t(p[16]) << 8) | p[17];
    if (len < 2 || len > 512 || (len & 1) || n < 18 + len || (p[15] & 0x80)) return malformed();
    const uint16_t universe = uint16_t(p[14]) | (uint16_t(p[15]) << 8);
    size_t index = 0;
    while (index < used_ && universes_[index] != universe) ++index;
    if (index == used_) { ++counters.unrelated; return Result::Ignored; }
    if (len < lengths_[index]) return malformed();
    uint8_t seq = p[12];
    if (seq && haveSeq_) {
      if (seq != sequence_) {
        // Sequence wraps 255 -> 1, zero is reserved.
        unsigned distance = (unsigned(seq) + 255 - sequence_) % 255;
        if (distance > 127) { ++counters.late; return Result::Ignored; }
        abandon();
      } else if (completedSequence_) { ++counters.duplicate; return Result::Ignored; }
    } else if (haveSeq_ != (seq != 0)) abandon();
    if (!seen_) { began_ = now; completedSequence_ = false; }
    haveSeq_ = seq != 0; sequence_ = seq;
    uint32_t bit = uint32_t(1) << index;
    if (seen_ & bit) {
      ++counters.duplicate;
      if (seq) return Result::Ignored;
      abandon(); began_ = now;
    }
    // Slots 511/512 are padding; RGB universe stride remains 170 pixels.
    memcpy(rgb + offsets_[index], p + 18, lengths_[index]);
    seen_ |= bit; lastAccepted_ = now; ++counters.accepted;
    if (seen_ == all_) {
      seen_ = 0; completedSequence_ = seq != 0; ++counters.completed;
      return Result::Complete;
    }
    return Result::Accepted;
  }
  size_t universes() const { return used_; }
  void resetCandidate() {
    abandon(); haveSeq_ = false; sequence_ = 0; lastAccepted_ = 0;
  }
 private:
  uint16_t universes_[MaxUniverses] = {}, offsets_[MaxUniverses] = {}, lengths_[MaxUniverses] = {};
  size_t used_ = 0;
  uint32_t seen_ = 0, all_ = 0, began_ = 0, lastAccepted_ = 0;
  uint8_t sequence_ = 0;
  bool haveSeq_ = false, completedSequence_ = false, configured_ = false;
  Result malformed() { ++counters.malformed; return Result::Ignored; }
  void abandon() { if (seen_) ++counters.incomplete; seen_ = 0; completedSequence_ = false; }
};
}
