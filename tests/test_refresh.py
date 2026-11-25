import csv,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import parse_table,refresh,META,CATEGORY,ROOT

def source(value='1200',status='',extra=None):
 row={k:'' for k in META};row.update(REF_DATE='2023',GEO='Canada',Statistic='Average expenditure per household',UOM='Dollars',SCALAR_FACTOR='units',VALUE=value,STATUS=status,VECTOR='v1');row[CATEGORY]='Food expenditures'
 if extra:row.update(extra)
 text=io.StringIO();w=csv.DictWriter(text,fieldnames=list(row));w.writeheader();w.writerow(row);b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:z.writestr('11100222.csv',text.getvalue())
 return b.getvalue()
TABLE={'id':'11100222','mode':'geography','dimension':None}
CATS=[{'id':'food','source':'Food expenditures'}]
class RefreshTests(unittest.TestCase):
 def test_published_flag_is_not_zero(self):
  p=parse_table(source('', 'F'),TABLE,CATS)[0];self.assertIsNone(p['values']['food']['annual']);self.assertEqual(p['values']['food']['status'],'F')
 def test_refyear_separate_from_check_date(self):
  p=parse_table(source(),TABLE,CATS)[0];self.assertEqual(p['year'],'2023');self.assertEqual(p['values']['food']['annual'],1200)
 def test_unit_change_and_unexpected_dimension_fail(self):
  for extra in [{'UOM':'Percent'},{'New dimension':'All'}]:
   with self.assertRaises(ValueError):parse_table(source(extra=extra),TABLE,CATS)
 def test_missing_category_fails(self):
  with self.assertRaises(ValueError):parse_table(source(),TABLE,CATS+[{'id':'rent','source':'Shelter'}])
 def test_partial_failure_leaves_old_snapshot(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);cfg=p/'config.json';out=p/'data.json';out.write_text('old good snapshot');cfg.write_text(json.dumps({'tables':[TABLE,{**TABLE,'id':'11100223'}],'categories':CATS}))
   with patch('refresh.download',side_effect=[source(),RuntimeError('source unavailable')]):
    with self.assertRaises(RuntimeError):refresh(cfg,out)
   self.assertEqual(out.read_text(),'old good snapshot')
 def test_seeded_data_provenance_and_real_available_dimensions(self):
  data=json.loads((ROOT/'web/data/benchmarks.json').read_text());self.assertTrue(data['checked_at'].endswith('Z'));self.assertEqual(len(data['sources']),1)
  for src in data['sources']:self.assertEqual(len(src['sha256']),64)
  for p in data['profiles']:
   if p['mode'] in ['tenure','household']:self.assertEqual(p['geography'],'Canada')
  self.assertTrue(any(p['geography']=='British Columbia' for p in data['profiles']))
  self.assertTrue(any(p['geography']=='Nova Scotia' and p['mode']=='geography' for p in data['profiles']))
if __name__=='__main__':unittest.main()
