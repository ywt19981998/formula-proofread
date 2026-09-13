"""Extract evidence and render pages; this script does not adjudicate errors."""
import argparse, hashlib, json, math
from pathlib import Path
import pdfplumber, pdfplumber.page, pdfminer.converter
import pypdfium2

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('pdf',type=Path);ap.add_argument('output',type=Path)
 ap.add_argument('--scale',type=float,default=2)
 args=ap.parse_args()
 if args.scale<=0:ap.error('scale must be positive')
 args.output.mkdir(parents=True,exist_ok=True)
 if (args.output/'inventory.json').exists():ap.error('Use a fresh output directory; inventory already exists')
 cls=pdfminer.converter.PDFLayoutAnalyzer
 original_string,original_char=cls.render_string,cls.render_char
 def render_string(self,textstate,seq,ncs,graphicstate):
  self._proof_render=textstate.render
  return original_string(self,textstate,seq,ncs,graphicstate)
 def render_char(self,*a,**kw):
  result=original_char(self,*a,**kw)
  char=self.cur_item._objs[-1]
  char.proof_render=self._proof_render
  char.proof_stroke=a[-1].linewidth
  return result
 cls.render_string,cls.render_char=render_string,render_char
 pdfplumber.page.ALL_ATTRS=pdfplumber.page.ALL_ATTRS.union({'proof_render','proof_stroke'})
 pages=[]
 with pdfplumber.open(args.pdf) as pdf:
  rendered=pypdfium2.PdfDocument(str(args.pdf))
  for n,p in enumerate(pdf.pages,1):
   chars=[]
   for i,c in enumerate(p.chars):
    a,b,cc,d,_,_=c['matrix'];den=math.hypot(a,b)*math.hypot(cc,d)
    shear=(a*cc+b*d)/den if den else 0
    chars.append(dict(id=f'p{n}-g{i}',text=c['text'],bbox=[c['x0'],c['top'],c['x1'],c['bottom']],font=c['fontname'],size=c['size'],matrix=list(c['matrix']),render_mode=c['proof_render'],stroke_width=c['proof_stroke'],named_bold=('bold' in c['fontname'].lower()),named_italic=any(x in c['fontname'].lower() for x in ['italic','oblique']),shear_candidate=abs(shear)>.08,stroke_bold_candidate=c['proof_render'] in [1,2,5,6] and c['proof_stroke']>0))
   image_name=f'page-{n:03}.png'
   rendered[n-1].render(scale=args.scale).to_pil().save(args.output/image_name)
   pages.append(dict(page=n,width=p.width,height=p.height,render=image_name,chars=chars,images=[dict(bbox=[i['x0'],i['top'],i['x1'],i['bottom']]) for i in p.images],text=p.extract_text(),review_status='pending',unresolved_regions=[]))
  rendered.close()
 data=dict(source=str(args.pdf.resolve()),source_sha256=hashlib.sha256(args.pdf.read_bytes()).hexdigest(),page_count=len(pages),note='Glyph styling fields are evidence candidates, not semantic verdicts. Raw text may contain private-use glyph codes.',pages=pages)
 (args.output/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
 print(f'Rendered {len(pages)} pages; review status is pending: {args.output}')

if __name__=='__main__':main()
