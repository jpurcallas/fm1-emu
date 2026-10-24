/* REminiSCENT Solaris v09: clean mathematical water ripples, fixed orbital plane.
   Cut f67: outer contour r=1.0 == station orbital ring exactly.
   At f<=66 the composite contains ONLY the untouched station bitmap.
   3 wave events, no precomputed wave frames. 240x240 native intensity mask. */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#define W 240
#define H 240
#define PI 3.14159265358979323846
static const double CX=120.25338579, CY=129.86907726;
static const double A=64.47929454, B=22.62433963;
static const double ANG=17.69680325*PI/180.;
static inline double clip(double v){return v<0?0:(v>1?1:v);}
static inline double sm(double a,double b,double v){double q=clip((v-a)/(b-a));return q*q*(3-2*q);}
static inline double line_at(double distance,double core,double edge){return 1.0-sm(core,edge,distance);}
static double wave_value(int f,int x,int y){
    const double c=cos(ANG),s=sin(ANG);
    const double dx=x-CX,dy=y-CY;
    const double u=(c*dx+s*dy)/A;
    const double v=(-s*dx+c*dy)/B;
    const double r=hypot(u,v);
    /* Gradient of elliptical radius maps normalized radius to pixel distance.
       No change of inclination or center over time. */
    double g=hypot((c*u-s*v)/A,(s*u+c*v)/B);
    if(g<1e-6)g=.045;
    static const int births[3]={67,94,121};
    static const double bases[4]={1.0,.78,.58,.21};
    static const double moves[4]={1.0,.84,.67,.42};
    static const double alphas[4]={1.0,.80,.64,.38};
    double cover=0;
    for(int p=0;p<3;p++){
        const int age=f-births[p];
        if(age<0||age>38)continue;
        const double birth=(p==0&&age==0)?1.0:sm(-1.,3.,(double)age);
        const double fade=1.-sm(17.,39.,(double)age);
        const double gain=birth*fade;
        for(int k=0;k<4;k++){
            if(k==3&&age>=17)continue;
            /* At f67 k0 is mathematically identical to the station ellipse.
               After the cut all rings expand continuously. */
            const double rr=bases[k]+(double)age*(.0163*moves[k]);
            const double dist=fabs(r-rr)/g;
            const double thickness=(k==0)? .64:.54;
            const double stroke=line_at(dist,thickness*.60,thickness*1.45);
            const double opacity=clip(gain*alphas[k]*stroke*.82);
            cover=1.-(1.-cover)*(1.-opacity);
        }
    }
    /* No water over lower typography. */
    cover*=1.-.98*sm(171.,192.,(double)y);
    return clip(cover);
}
int main(int argc,char **argv){
    if(argc!=3){fprintf(stderr,"usage: %s frame output.raw\n",argv[0]);return 2;}
    int f=atoi(argv[1]);if(f<0||f>=150)return 2;
    FILE *p=fopen(argv[2],"wb");if(!p){perror("open");return 2;}
    uint8_t buf[W*H];
    for(int y=0;y<H;y++)for(int x=0;x<W;x++){
       buf[y*W+x]=(uint8_t)lrint(wave_value(f,x,y)*210.);
    }
    size_t n=fwrite(buf,1,sizeof(buf),p);fclose(p);
    return n==sizeof(buf)?0:1;
}
