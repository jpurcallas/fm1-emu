// REminiSCENT: 253-sample FLAC lossless reader, decoding at PREPARE only.
// David Reid's MIT-0/public domain dr_flac is vendored separately in third_party.
// No sample file is written back to disk and NO decoding happens in the audio callback.
// IMPORTANT: PCM is stored uncompressed in RAM (351 MB bank, not mmap). MPC RAM QA is mandatory.
#include "engine.hpp"
#include <algorithm>
#include <cstdint>
#include <limits>
#include <vector>
#define DR_FLAC_IMPLEMENTATION
#include "third_party/dr_flac.h"
namespace rem {
bool Bank::loadFlac(const std::string& path, int root, std::string& err) {
 drflac* f=drflac_open_file(path.c_str(), nullptr);
 if(!f){err="FLAC no se puede abrir: "+path;return false;}
 const int ch=int(f->channels),bits=int(f->bitsPerSample),rate=int(f->sampleRate);
 const uint64_t frames=f->totalPCMFrameCount;
 if((ch!=1 && ch!=2)||(bits!=16 && bits!=24 && bits!=32)||rate<8000||rate>192000||frames==0){
   drflac_close(f);err="FLAC formato no soportado o sin audio: "+path;return false;
 }
 const uint64_t bytes=frames*uint64_t(ch)*uint64_t(bits/8);
 if(bytes>size_t(-1)||frames>size_t(-1)){drflac_close(f);err="FLAC demasiado grande: "+path;return false;}
 Sample s;s.root=root;s.rate=rate;s.channels=ch;s.bits=bits;s.wavFormat=1;s.frames=size_t(frames);
 try{s.pcm.resize(size_t(bytes));}catch(...){drflac_close(f);err="No hay RAM para PCM FLAC: "+path;return false;}
 static constexpr drflac_uint64 BLOCK=1024;
 std::vector<drflac_int32> block(BLOCK*size_t(ch));
 uint64_t cursor=0;
 while(cursor<frames){
   const drflac_uint64 want=std::min<drflac_uint64>(BLOCK,frames-cursor);
   const drflac_uint64 got=drflac_read_pcm_frames_s32(f,want,block.data());
   if(got!=want){drflac_close(f);err="FLAC truncado: "+path;return false;}
   const int bps=bits/8;
   const uint64_t ns=got*uint64_t(ch);
   for(uint64_t i=0;i<ns;i++){
     // dr_flac outputs signed PCM expanded to 32-bit MSB alignment.
     // Copy high 16/24/32 bits in little-endian order, without dithering.
     const uint32_t packed=uint32_t(block[size_t(i)]) >> (32-bits);
     const size_t off=size_t((cursor*uint64_t(ch)+i)*uint64_t(bps));
     for(int byte=0;byte<bps;byte++)s.pcm[off+size_t(byte)]=uint8_t(packed>>(8*byte));
   }
   cursor+=got;
 }
 drflac_close(f);
 layers.push_back(std::move(s));
 return true;
}
} // namespace rem
