// UI41: geometry ported from the author-approved LAB10 HTML renderer.
// Visual-only mathematics. No filtering, sample changes, or DSP coupling.
// Coordinates/relations deliberately match radarGraphic(V)/moleculeGraphic(V).
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
namespace reminisc_visual {
inline float u(int raw) {return std::clamp(raw,0,127)/127.0f;}
struct Radar {
 float ringOpacity, bassX,bassY,bassStrength,bassDuration,bassOpacity;
 float midX,midY,midStrength,midDuration,midOpacity;
 float peakX,peakY,peakStrength,peakDuration,peakOpacity;
 float persistence;
};
inline Radar radar(int bodyRaw,int decayRaw,int exciteRaw,int mixRaw){
 const float body=u(bodyRaw),decay=u(decayRaw),excite=u(exciteRaw),mix=u(mixRaw);
 return {
  .35f+decay*.55f,
  19.f+body*29.f, 51.f-body*24.f, .38f+.6f*mix, 2.8f+decay*4.2f,.38f+.62f*mix,
  54.f+excite*18.f, 19.f, .3f+excite*.7f,3.4f+decay*3.f,.4f+.6f*mix,
  69.f, 51.f+body*14.f,.36f+excite*.6f,2.3f+decay*3.f,.3f+.7f*excite,
  decay
 };
}
struct GrainNode {
 float x,y1,y2,r; // paired cyan/gold nodes
 float looseX,looseY,looseRadius;
 bool loose;
};
struct Molecule {
 int count=0;
 std::array<GrainNode,29> nodes{};
};
inline Molecule molecule(int sizeRaw,int densityRaw,int positionRaw,int mixRaw){
 const float s=u(sizeRaw),d=u(densityRaw),pos=u(positionRaw),mix=u(mixRaw);
 Molecule result;
 result.count=11+int(std::lround(d*18.f));
 const float startX=15.f+pos*46.f;
 constexpr float pi=3.14159265358979323846f;
 for(int i=0;i<result.count;++i){
  const float q=float(i)/float(result.count-1);
  const float t=q*pi*(2.6f+d*2.2f);
  const float x=startX+q*515.f;
  const float offset=std::sin(t)*(47.f+30.f*mix);
  const float y1=147.f+offset;
  const float y2=147.f-offset;
  const float split=(.1f+d)*34.f;
  result.nodes[static_cast<size_t>(i)]={x,y1,y2,2.8f+s*5.f,
   x+split,y1-11.f-d*27.f,1.8f+d*3.f,(i%3)==0};
 }
 return result;
}
} // namespace reminisc_visual
