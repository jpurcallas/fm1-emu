#!/usr/bin/env python3
"""Emulator-only bounded LCD rendering patch. Does not change DSP/seq/MIDI queues."""
from pathlib import Path
import sys
sdk=Path(sys.argv[1]); display=sdk/"app/biomech/display.c"; hdr=sdk/"app/biomech/biomech_display.h"; ui=sdk/"app/biomech/biomech_sdk_port.c"
s=display.read_text()
anchor="void br_display_render(const BRPanel *p,const BRUiView *v,BRDisplayScratch *scratch,"
assert s.count(anchor)==1
s=s.replace(anchor,"""void br_display_render_tile(const BRPanel *p,const BRUiView *v,BRDisplayScratch *scratch,
                            BRDisplayFlush flush,void *ctx,unsigned tile){
 if(!p||!v||!scratch||!flush||tile>=BR_LCD_H||tile%BR_LCD_TILE_H)return;
 draw_page(p,v,scratch,(int)tile);
 flush(ctx,tile,BR_LCD_TILE_H,scratch->pix);
}
"""+anchor,1);display.write_text(s)
h=hdr.read_text()
assert h.count("void br_display_render(")==1
h=h.replace("void br_display_render(","""void br_display_render_tile(const BRPanel *p,const BRUiView *view,
                            BRDisplayScratch *scratch,BRDisplayFlush flush,void *ctx,unsigned tile);
void br_display_render(""",1);hdr.write_text(h)
u=ui.read_text()
# Replace existing full-screen paint call, even in the v0.8 boot hook, with one bounded tile.
old="""    br_display_render(&shadow_panel,&view,&pixels,lcd_flush,0);"""
assert u.count(old)==1
u=u.replace(old,"""    br_display_render_tile(&shadow_panel,&view,&pixels,lcd_flush,0,lcd_scan_y);
    lcd_scan_y=(lcd_scan_y+BR_LCD_TILE_H)%BR_LCD_H;""",1)
anchor="static uint32_t last_paint;"
assert u.count(anchor)==1
u=u.replace(anchor,anchor+"\nstatic unsigned lcd_scan_y;",1)
# Never let a full paint occur in the control function. Prefer one tile per invocation.
old="""    if(fm1_millis()-last_paint>=90U){
        paint_screen();
        last_paint=fm1_millis();
    }"""
assert u.count(old)==1
u=u.replace(old,"""    /* One tile per control task tick: bounded service time. Audio remains owner
       of BRFM1Runtime; painting is purely UI and never steals a DSP render. */
    if(fm1_millis()-last_paint>=8U){
        paint_screen();
        last_paint=fm1_millis();
    }""",1)
ui.write_text(u)
print("BR3_V09_BOUNDED_LCD_PATCH: 1 of 30 tiles per control service, all BR3 DSP unchanged")
