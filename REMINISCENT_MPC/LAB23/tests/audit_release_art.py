#!/usr/bin/env python3
"""Visual provenance gate, no audio or plugin changes. No network. Exit 1 on unknown graphics/components."""
import sys,json,zipfile,hashlib,fnmatch,pathlib
manifest=json.loads(pathlib.Path(__file__).with_name('art_gate_manifest.json').read_text())
archive=pathlib.Path(sys.argv[1]); z=zipfile.ZipFile(archive)
root='Yeti Fingers - VST - REminiSCENT/Plugin Skins/'
tui=json.loads(z.read(root+'TUI.json'))
comps=tui['pageData']['tabs'][0]['componentDefinition']['componentsData']
images={path[len(root):]:path for path in z.namelist() if path.startswith(root) and path.lower().endswith(('.png','.jpg','.jpeg'))}
errors=[];review=[]
for name,sha in manifest['base_image_sha256'].items():
 if name not in images:errors.append('FALTA FONDO LAB10: '+name)
 elif hashlib.sha256(z.read(images[name])).hexdigest()!=sha:errors.append('FONDO LAB10 MODIFICADO: '+name)
for path in images:
 if any(pattern.lower() in path.lower() for pattern in manifest['disallowed_patterns']):errors.append('ARTE RECHAZADO: '+path)
 if path not in manifest['base_image_sha256'] and path!='lab10_touch_hit.png':review.append('OVERLAY NO COTEJADO CON HTML LAB10: '+path)
for c in comps:
 typ=c['componentData']['type'];name=c['componentData'].get('name','')
 if typ not in manifest['allowed_sdk_types']:errors.append('CONTROL NO NATIVO DEL SDK: '+name+' ('+typ+')')
 if 'solaris' in name.lower():errors.append('COMPONENTE INTRO RECHAZADO: '+name)
 if typ=='Image':
  key=c['componentData']['data'].get('image')
  if key not in images:errors.append('REFERENCIA A IMAGEN AUSENTE: '+str(key))
# overlays are flagged explicitly, not a declaration of approval
report={'archive':archive.name,'base_images_verified':len(manifest['base_image_sha256']),'graphics_total':len(images),'components':len(comps),'errors':errors,'requires_visual_approval':review,'release_gate':'BLOCK' if errors or review else 'PASS'}
print(json.dumps(report,indent=2,ensure_ascii=False))
sys.exit(bool(errors or review))