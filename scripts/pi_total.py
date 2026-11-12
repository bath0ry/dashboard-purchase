import sys,re,openpyxl,xlrd,os
def rows(f):
    if f.endswith('.xls'):
        b=xlrd.open_workbook(f)
        for s in b.sheets():
            for r in range(s.nrows): yield s.name,r,[s.cell_value(r,c) for c in range(s.ncols)]
    else:
        wb=openpyxl.load_workbook(f,data_only=True,read_only=True)
        for ws in wb.worksheets:
            for i,row in enumerate(ws.iter_rows(values_only=True)): yield ws.title,i,list(row)
for f in sys.argv[1:]:
    print("===",f)
    n=0
    for s,i,r in rows(f):
        txt=" ".join(str(x) for x in r if x not in (None,""))
        if re.search(r'total|合计|总计|amount',txt,re.I) and re.search(r'\d',txt):
            print(s,i,txt[:200]); n+=1
            if n>8: break
