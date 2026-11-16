import argparse, os, json
from pathlib import Path
from datetime import date, datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, text
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

DEFAULT = {
 "pnl":"dw.metric_pnl_monthly",
 "expenses":"dw.metric_expense_category",
 "vendors":"dw.metric_vendor_expense",
 "departments":"dw.metric_phase3_department_month",
 "scorecard":"dw.metric_phase3_executive_scorecard"
}
def ident(v):
 p=v.split(".")
 if len(p)!=2 or not all(x.replace("_","").isalnum() for x in p):
  raise ValueError("Unsafe SQL identifier: "+v)
 return ".".join('"'+x+'"' for x in p)
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--month",required=True,help="YYYY-MM")
 ap.add_argument("--format",choices=["pdf","xlsx","both"],default="both")
 ap.add_argument("--output-dir",default="reports/monthly")
 a=ap.parse_args()
 start=date.fromisoformat(a.month+"-01")
 end=date(start.year+(start.month==12),start.month%12+1,1)
 url=os.getenv("DATABASE_URL")
 if not url: raise SystemExit("Set DATABASE_URL using a secret or environment variable.")
 views={**DEFAULT,**json.loads(os.getenv("PULSEIQ_REPORT_VIEWS","{}"))}
 engine=create_engine(url,pool_pre_ping=True)
 frames={}
 with engine.connect() as c:
  for name,view in views.items():
   schema,table=view.split(".")
   cols=c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema=:s AND table_name=:t"),
                  {"s":schema,"t":table}).scalars().all()
   if not cols: raise RuntimeError(f"View {view} not found. Confirm the actual Phase 3 view name.")
   dc=next((x for x in ["month_start","month","month_date","period_month"] if x in cols),None)
   q=f"SELECT * FROM {ident(view)}"
   params={}
   if dc:
    q+=f' WHERE "{dc}" >= :lo AND "{dc}" < :hi'
    params={"lo":start,"hi":end}
   frames[name]=pd.read_sql_query(text(q),c,params=params)
 engine.dispose()
 cutoff=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
 stem=f"PulseIQ_Monthly_Report_{a.month}"
 if a.format in ["xlsx","both"]:
  p=out/(stem+".xlsx")
  with pd.ExcelWriter(p,engine="openpyxl") as w:
   pd.DataFrame([{"report_month":a.month,"period_start":start,"period_end_exclusive":end,"data_cutoff":cutoff}]).to_excel(w,sheet_name="Cover",index=False)
   for k,df in frames.items(): df.to_excel(w,sheet_name=k[:31],index=False)
  print(p)
 if a.format in ["pdf","both"]:
  p=out/(stem+".pdf"); st=getSampleStyleSheet()
  story=[Paragraph("PulseIQ Monthly Management Pack",st["Title"]),
   Paragraph(f"Reporting month: {a.month}",st["Normal"]),
   Paragraph(f"Period: {start} to {end} (end exclusive)",st["Normal"]),
   Paragraph(f"Data cutoff: {cutoff}",st["Normal"]),Spacer(1,14)]
  for k,df in frames.items():
   story.append(Paragraph(k.replace("_"," ").title(),st["Heading2"]))
   if df.empty: story.append(Paragraph("No records for this period.",st["BodyText"])); continue
   view=df.head(25).fillna("")
   rows=[list(map(str,view.columns))]+view.astype(str).values.tolist()
   t=Table(rows,repeatRows=1)
   t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),
    ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.25,colors.grey),
    ("FONTSIZE",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"TOP")]))
   story.extend([t,Spacer(1,10)])
  SimpleDocTemplate(str(p),pagesize=landscape(A4)).build(story); print(p)
if __name__=="__main__": main()
