#include "ui41_approved_visual_math.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
using namespace reminisc_visual;
static void ok(bool b,const char* msg){if(!b){std::fprintf(stderr,"FAIL: %s\n",msg);std::exit(1);}}
static bool diff(float a,float b){return std::fabs(a-b)>1.e-4f;}
int main(){
 // Exactly the dependencies authored in LAB10, not a substitute DSP function.
 auto base=radar(64,64,64,64);
 auto body=radar(127,64,64,64);
 ok(diff(base.bassX,body.bassX)&&diff(base.bassY,body.bassY)&&diff(base.peakY,body.peakY),"radar BODY positions");
 auto decay=radar(64,127,64,64);
 ok(diff(base.ringOpacity,decay.ringOpacity)&&diff(base.bassDuration,decay.bassDuration),"radar DECAY persistence/time");
 auto excite=radar(64,64,127,64);
 ok(diff(base.midX,excite.midX)&&diff(base.peakStrength,excite.peakStrength),"radar EXCITE");
 auto mix=radar(64,64,64,127);
 ok(diff(base.bassOpacity,mix.bassOpacity)&&diff(base.midOpacity,mix.midOpacity),"radar MIX");
 auto low=molecule(64,0,64,64),high=molecule(64,127,64,64);
 ok(low.count==11&&high.count==29,"granular density node count LAB10");
 auto seed=molecule(64,64,64,64);
 auto big=molecule(127,64,64,64);
 ok(diff(seed.nodes[0].r,big.nodes[0].r)&&seed.count==big.count,"granular SIZE radius only");
 auto shifted=molecule(64,64,127,64);
 ok(diff(seed.nodes[0].x,shifted.nodes[0].x),"granular POSITION x");
 auto wetter=molecule(64,64,64,127);
 ok(diff(seed.nodes[3].y1,wetter.nodes[3].y1)&&diff(seed.nodes[3].y2,wetter.nodes[3].y2),"granular MIX amplitude");
 for(int i=0;i<seed.count;i++)ok(seed.nodes[i].y1+seed.nodes[i].y2>293.99f&&seed.nodes[i].y1+seed.nodes[i].y2<294.01f,"symmetric DNA");
 std::puts("PASS: exact LAB10 radar and molecular geometry, all four parameters independently reactive");
 return 0;
}
