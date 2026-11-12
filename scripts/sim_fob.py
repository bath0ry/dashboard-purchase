import sys, openpyxl, glob, os, re
for f in sorted(sys.argv[1:]):
    try:
        wb=openpyxl.load_workbook(f,data_only=True,read_only=True)
    except Exception as e:
        print(os.path.basename(f),"ERR",e); continue
    out=[]
    for name in wb.sheetnames:
        ws=wb[name]
        if not re.search(r'CONVENCIONAL|COMPRA|CONTA',name,re.I): continue
        for row in ws.iter_rows(max_row=20,max_col=4):
            for c in row:
                if isinstance(c.value,str) and c.value.strip().upper().startswith('VALOR FOB'):
                    v=ws.cell(row=c.row,column=c.column+1).value
                    out.append((name,v))
                if isinstance(c.value,str) and c.value.strip().upper()=='CLIENTE':
                    out.append(('cli',ws.cell(row=c.row,column=c.column+1).value))
                if isinstance(c.value,str) and c.value.strip().upper()=='DATA':
                    out.append(('data',str(ws.cell(row=c.row,column=c.column+1).value)[:10]))
        if out: break
    print(os.path.basename(f), out[:4])
