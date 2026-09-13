"""Export confirmed, human/agent-adjudicated records to Markdown and PDF."""
import argparse,collections,json,re,shutil
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Spacer,KeepTogether,PageBreak

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('records',type=Path);ap.add_argument('output',type=Path)
 ap.add_argument('--font-dir',type=Path,default=Path('C:/Windows/Fonts'))
 ap.add_argument('--formats',choices=['md','pdf','both'],default='both')
 args=ap.parse_args();d=json.loads(args.records.read_text('utf8'));records=d['errors'];ids=set()
 scope=d.get('scope_pages',[])
 if not scope or any(type(p)!=int or p<1 for p in scope) or len(scope)!=len(set(scope)):raise ValueError('scope_pages must list the requested PDF pages explicitly')
 complete=d.get('coverage_complete',False)
 if type(complete)!=bool:raise ValueError('coverage_complete must be boolean')
 if complete:
  coverage=d.get('coverage',[])
  if len(coverage)!=len(scope) or set(c['page'] for c in coverage)!=set(scope):raise ValueError('Coverage ledger does not match requested scope_pages')
  for c in coverage:
   if c.get('status')!='complete' or c.get('unresolved')!=[] or c.get('visual_reviewed') is not True or any(c.get('regions',{}).get(k) not in ['complete','not_applicable'] for k in ['text','formulas','figures']):raise ValueError('Complete coverage requires visual and region review without unresolved gaps')
 previous=(0,0)
 styles={'upright':'TR','italic':'TI','bold-italic':'TBI'}
 for e in records:
  if e['id'] in ids:raise ValueError('Duplicate error id: '+e['id'])
  ids.add(e['id'])
  if not isinstance(e['page'],int) or e['page']<1:raise ValueError('Invalid source page')
  if e['page'] not in scope:raise ValueError('Error page outside requested scope')
  if type(e.get('reading_order'))!=int or e['reading_order']<1:raise ValueError('reading_order must be a positive integer')
  current=(e['page'],e['reading_order'])
  if current<=previous:raise ValueError('Errors must be strictly ordered by page and reading_order')
  previous=current
  if not isinstance(e['count'],int) or e['count']<1:raise ValueError('Invalid count')
  for field in ['category','original','reason','correct_latex']:
   if not e[field]:raise ValueError('Empty field: '+field)
  if '$' in e['correct_latex']:raise ValueError('correct_latex must not include dollar delimiters')
  for r in e['correct_runs']:
   if r['style'] not in styles or r.get('position','normal') not in ['normal','sub','super']:raise ValueError('Unsupported mathematical run')
  if not e['correct_runs']:raise ValueError('Missing PDF mathematical runs')
  image=Path(e['image']);image=image if image.is_absolute() else args.records.parent/image
  if not image.is_file():raise ValueError('Missing evidence image: '+str(image))
  e['_image']=image
 args.output.mkdir(parents=True,exist_ok=True)
 if any((args.output/x).exists() for x in ['review.md','review.pdf']):raise ValueError('Use a fresh output directory; report already exists')
 assets=args.output/'assets';assets.mkdir(exist_ok=True)
 for i,e in enumerate(records,1):
  e['_asset']=f'assets/error-{i:04}.png'
  with PILImage.open(e['_image']) as im:im.convert('RGB').save(args.output/e['_asset'])
 state='已完成指定范围' if complete else '未完成；不能据此声称全稿无遗漏'
 intro=[d['scope'],'指定 PDF 页码：'+', '.join(map(str,sorted(scope))),f'覆盖状态：{state}。',f'确认错误 {len(records)} 条，涉及 {sum(e["count"] for e in records)} 个位置。',d['basis'],'按原稿页码和阅读顺序排列；正确字形与所列错误一一对应。原文截图中的其他内容不属于该条修改范围。']+d.get('notes',[])
 def cell(s):return str(s).replace('|','&#124;').replace('\n','<br>')
 if args.formats in ['md','both']:
  md=['---','type: manuscript-review','status: draft','---','',f'# {d["title"]}','']+intro+['','| 页码 | 原文 | 标量／矢量等类别 | 正确格式 |','| --- | --- | --- | --- |']
  for e in records:
   page=f'第 {e["page"]} 页'+(f'（书内 {e["printed_page"]}）' if e.get('printed_page') else '')
   md.append(f'| {cell(page)}，{cell(e["id"])} | ![原文局部]({e["_asset"]})<br>{cell(e["original"])} | {cell(e["category"])} | ${cell(e["correct_latex"])}$<br>{cell(e["reason"])} |')
  (args.output/'review.md').write_text('\n'.join(md)+'\n','utf8')
 if args.formats in ['pdf','both']:
  for name,file in [('CN','simsun.ttc'),('TR','times.ttf'),('TI','timesi.ttf'),('TBI','timesbi.ttf')]:
   pdfmetrics.registerFont(TTFont(name,str(args.font_dir/file),**({'subfontIndex':0} if name=='CN' else {})))
  for e in records:
   for run in e['correct_runs']:
    font=pdfmetrics.getFont(styles[run['style']])
    if any(ord(c) not in font.face.charToGlyph for c in run['text']):raise ValueError('Missing math font glyph; use a verified formula renderer instead: '+run['text'])
  base=ParagraphStyle('body',fontName='CN',fontSize=10,leading=16,wordWrap='CJK',spaceAfter=7)
  heading=ParagraphStyle('heading',parent=base,fontSize=17,leading=25,spaceAfter=15)
  def P(s,style=base):return Paragraph(s,style)
  def footer(c,doc):
   c.setFont('CN',8);c.drawString(38,23,'审校草稿');c.drawRightString(A4[0]-38,23,f'清单第 {doc.page} 页')
  class Doc(SimpleDocTemplate):
   def afterFlowable(self,f):
    if hasattr(f,'bookmark'):
     self.canv.bookmarkPage(f.bookmark);self.canv.addOutlineEntry(f.getPlainText(),f.bookmark,0,False)
  story=[P(escape(d['title']),heading)]+[P(escape(s)) for s in intro];last=None
  for e in records:
   if last!=e['page']:
    story.append(PageBreak());h=P(f'原稿第 {e["page"]} 页',heading);h.bookmark=f'p{e["page"]}';story.append(h);last=e['page']
   iw,ih=PILImage.open(args.output/e['_asset']).size;scale=min((A4[0]-76)/iw,210/ih)
   runs=[]
   for r in e['correct_runs']:
    text=f'<font name="{styles[r["style"]]}" size="14">{escape(r["text"])}</font>'
    pos=r.get('position','normal')
    runs.append(f'<{pos}>{text}</{pos}>' if pos!='normal' else text)
   label=f'第 {e["page"]} 页'+(f'（书内 {e["printed_page"]}）' if e.get('printed_page') else '')
   story.append(KeepTogether([P(escape(label+' · '+e['id']+' · '+e['category'])),Image(str(args.output/e['_asset']),width=iw*scale,height=ih*scale,hAlign='LEFT'),Spacer(1,4),P('原文：'+escape(e['original'])),P('正确格式：'+''.join(runs)),P(escape(e['reason'])),Spacer(1,10)]))
  Doc(str(args.output/'review.pdf'),pagesize=A4,leftMargin=38,rightMargin=38,topMargin=38,bottomMargin=48,title=d['title']).build(story,onFirstPage=footer,onLaterPages=footer)
 print(f'Exported {len(records)} errors to {args.output}; visual QA still required')

if __name__=='__main__':main()
