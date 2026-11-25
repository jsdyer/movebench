#!/usr/bin/env python3
"""Download and validate official SHS CSVs; publish only after every table succeeds."""
import argparse, csv, hashlib, io, json, math, os, tempfile, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
CATEGORY = 'Household expenditures, summary-level categories'
META = {'REF_DATE','GEO','DGUID','Statistic',CATEGORY,'UOM','UOM_ID','SCALAR_FACTOR','SCALAR_ID','VECTOR','COORDINATE','VALUE','STATUS','SYMBOL','TERMINATED','DECIMALS'}

def parse_table(blob, table, categories):
    needed = {c['source']: c['id'] for c in categories}
    if len(needed) != len(categories): raise ValueError('Category sources must be unique')
    result = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        member = z.getinfo(table['id']+'.csv')
        if member.file_size > 150_000_000: raise ValueError('Source CSV exceeds bound')
        with z.open(member) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig'))
            if not META.issubset(set(reader.fieldnames or [])): raise ValueError('Unexpected CSV schema')
            extra = set(reader.fieldnames)-META
            expected = {table['dimension']} if table['dimension'] else set()
            if extra != expected: raise ValueError('Unexpected comparison dimensions')
            for row in reader:
                name = row[CATEGORY]
                if name not in needed or row['Statistic'] != 'Average expenditure per household': continue
                if row['UOM'] != 'Dollars' or row['SCALAR_FACTOR'] != 'units': raise ValueError('Unexpected amount unit')
                year = row['REF_DATE']
                if len(year)!=4 or not year.isdigit(): raise ValueError('Invalid reference year')
                group = row[table['dimension']] if table['dimension'] else 'All households'
                key = (year,row['GEO'],group)
                entry=result.setdefault(key,{'year':year,'geography':row['GEO'],'group':group,'mode':table['mode'],'table':table['id'],'values':{}})
                value = float(row['VALUE']) if row['VALUE'] else None
                if value is not None and (not math.isfinite(value) or value < 0 or value > 5_000_000): raise ValueError('Invalid household spending value')
                if value is not None and value.is_integer(): value = int(value)
                category=needed[name]
                if category in entry['values']: raise ValueError('Duplicate category within profile')
                entry['values'][category]={'annual':value,'status':row['STATUS'],'vector':row['VECTOR']}
    if not result: raise ValueError('No expenditure profiles found')
    found={k for p in result.values() for k in p['values']}
    if found != set(needed.values()): raise ValueError('Configured categories missing from table')
    latest=max(k[0] for k in result)
    latest_profiles=[p for p in result.values() if p['year']==latest]
    if not any(len(p['values'])==len(categories) for p in latest_profiles): raise ValueError('Latest source year has no complete category profile')
    return sorted(result.values(), key=lambda p:(p['year'],p['geography'],p['group']))

def download(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'CoolCode MoveBench/1.0 (+https://coolcode.ca/movebench/)'}),timeout=60) as response:
                blob=response.read(25_000_001)
                if len(blob)>25_000_000: raise ValueError('Download exceeds bound')
                return blob
        except Exception:
            if attempt==2: raise
            time.sleep(2**attempt)

def refresh(config_path=ROOT/'references.json', output=ROOT/'web/data/benchmarks.json', source_dir=None):
    config=json.loads(Path(config_path).read_text())
    tables=config['tables']; categories=config['categories']
    if not tables or not categories or len({c['id'] for c in categories})!=len(categories): raise ValueError('Invalid configuration')
    records=[]; sources=[]
    checked=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    for table in tables:
        if not str(table['id']).isdigit() or len(table['id'])!=8: raise ValueError('Invalid table ID')
        url=f"https://www150.statcan.gc.ca/n1/tbl/csv/{table['id']}-eng.zip"
        blob=(Path(source_dir)/(table['id']+'-eng.zip')).read_bytes() if source_dir else download(url)
        rows=parse_table(blob,table,categories);records.extend(rows)
        sources.append({'table':table['id'],'url':f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={table['id']}01",'download':url,'sha256':hashlib.sha256(blob).hexdigest(),'mode':table['mode'],'reference_years':sorted({r['year'] for r in rows}),'checked_at':checked})
        print(f"Validated {table['id']}: {len(rows)} profiles through {sources[-1]['reference_years'][-1]}")
    data={'schema_version':1,'checked_at':checked,'publisher':'Statistics Canada','licence_url':'https://www.statcan.gc.ca/en/reference/licence','categories':categories,'sources':sources,'profiles':records}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=output.parent,delete=False,encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,separators=(',',':'));f.write('\n');temp=f.name
    os.replace(temp,output)
    status={'schema_version':1,'checked_at':checked,'profile_count':len(records),'sources':[{'table':s['table'],'latest_reference_year':s['reference_years'][-1]} for s in sources]}
    with tempfile.NamedTemporaryFile('w',dir=output.parent,delete=False,encoding='utf-8') as f:
        json.dump(status,f,ensure_ascii=False,indent=2);f.write('\n');temp=f.name
    os.replace(temp,output.parent/'status.json')
    print(f'Published {len(records)} genuine source profiles to {output}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path);args=p.parse_args()
    refresh(source_dir=args.source_dir)
