"""Exercise the actual application at a project subpath in Chromium (CI)."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil,tempfile,threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass

def main():
 screenshots=ROOT/'browser-checks';screenshots.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as temporary:
  shutil.copytree(ROOT/'dist',Path(temporary)/'example-tool')
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=temporary))
  threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();page=browser.new_page(viewport={'width':1280,'height':1000})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.route('**/assets/tool-metrics.js',lambda route:route.fulfill(status=200,body=''))
    page.goto(f'http://127.0.0.1:{server.server_port}/example-tool/')
    page.locator('#current-pay').wait_for();page.locator('#example').click()
    assert 'Illustrative' in page.locator('#example-note').inner_text()
    assert 'Comparison ready' in page.locator('#status').inner_text()
    assert '$70,000' in page.locator('#breakdown').inner_text()
    amounts=page.locator('input[type=number]').evaluate_all('(nodes)=>Object.fromEntries(nodes.map(n=>[n.id,n.value]))')
    page.select_option('#place-pair','halifax-vancouver');page.click('#apply-pair')
    assert page.locator('#current-place').input_value()=='Halifax, NS'
    assert page.locator('#current-region').input_value()=='Nova Scotia'
    assert page.locator('#proposed-region').input_value()=='British Columbia'
    assert page.locator('input[type=number]').evaluate_all('(nodes)=>Object.fromEntries(nodes.map(n=>[n.id,n.value]))')==amounts
    assert page.locator('#research-links a').count()==5
    assert 'no BC pump-price coverage' in page.locator('#research-links').inner_text()
    for link in page.locator('#research-links a').all():
     assert link.get_attribute('href').startswith('https://coolcode.ca/')
     assert '?' not in link.get_attribute('href')
     assert link.get_attribute('rel')=='noopener noreferrer'
    page.locator('#research-check-0').check()
    assert page.locator('#research-check-0').is_checked()
    page.locator('#current-place').fill('<img src=x onerror=alert(1)>')
    assert page.locator('#current-label').inner_text()=='<img src=x onerror=alert(1)>'
    assert page.locator('img').count()==0
    page.locator('#save').click();page.locator('#reset').click()
    assert page.locator('#current-pay').input_value()==''
    page.locator('#load').click();assert float(page.locator('#current-pay').input_value())==80000
    page.locator('#proposed-period').select_option('hourly')
    page.locator('#proposed-hours').fill('0');assert 'positive' in page.locator('#status').inner_text()
    page.locator('#proposed-period').select_option('annual');page.locator('#proposed-hours').fill('40')
    with page.expect_download() as download:page.locator('#csv').click()
    assert download.value.suggested_filename=='movebench-comparison.csv'
    page.locator('#forget').click();assert 'deleted' in page.locator('#save-status').inner_text()
    page.locator('#example').click()
    page.screenshot(path=str(screenshots/'desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(screenshots/'mobile.png'),full_page=True)
    assert not errors,errors
    browser.close()
   print('Browser flow, safe rendering, storage and mobile layout passed')
  finally:server.shutdown()
if __name__=='__main__':main()
