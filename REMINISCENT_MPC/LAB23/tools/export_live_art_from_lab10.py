#!/usr/bin/env python3
"""Export LAB23 visual FilmStrip overlays from author-approved private LAB10 HTML.

Requires: playwright, Chromium, Pillow. Source HTML must be the exact approved
REminiSCENT_UI_LAB_10_INTEGRATION.html, not a redesign.
Usage: python export_live_art_from_lab10.py <LAB10.html> <LAB23/skins>
No DSP, sample, or parameter changes. Duduk stays excluded from LAB19 bank.
"""
import sys
from pathlib import Path
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright

def image(page, box):
    return Image.open(BytesIO(page.screenshot(clip=box, animations="disabled"))).convert("RGBA")

def save(frames, filename):
    w,h=frames[0].size
    assert all(pic.size==(w,h) for pic in frames)
    out=Image.new("RGBA",(w,h*len(frames)))
    for i,pic in enumerate(frames):out.paste(pic,(0,i*h))
    out.save(filename,optimize=True)

def run(html,skins):
    skins.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,args=["--no-sandbox"])
        p=b.new_page(viewport={"width":1280,"height":800},device_scale_factor=1)
        p.set_content(html.read_text(encoding="utf8"))
        p.get_by_text("SALTAR INTRO").click()
        p.wait_for_timeout(250)
        selector=p.locator("#stage select").nth(0)
        choices=selector.locator("option").all_text_contents()
        assert len(choices)==28 and sum("Duduk" in x for x in choices)==1
        frames=[]
        for i,name in enumerate(choices):
            if "Duduk" in name:continue
            selector.select_option(index=i)
            p.wait_for_timeout(10)
            r=selector.bounding_box()
            assert round(r["width"])==435 and round(r["height"])==48
            frames.append(image(p,{"x":r["x"],"y":r["y"],"width":435,"height":48}))
        assert len(frames)==27
        save(frames,skins/"acoustic_source_lab10_27.png")
        p.locator("#nav button").nth(1).click()
        p.wait_for_timeout(200)
        assert p.locator("#stage button").count()==8
        waves=[]
        for i in range(8):
            p.locator("#stage button").nth(i).click()
            p.wait_for_timeout(40)
            waves.append(image(p,{"x":49,"y":266,"width":780,"height":339}))
        save(waves,skins/"osc_lab10_eight_waves.png")
        b.close()

if __name__=="__main__":
    assert len(sys.argv)==3, "Usage: export_live_art_from_lab10.py LAB10.html LAB23/skins"
    run(Path(sys.argv[1]),Path(sys.argv[2]))
