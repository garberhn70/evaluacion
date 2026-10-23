import json, sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from mock_supabase import MockSupabase, U
BASE=os.environ.get('VB_BASE','http://127.0.0.1:8787/index.html')
SBJS=os.environ.get('VB_SUPABASE_JS',os.path.join(os.path.dirname(__file__),'node_modules','@supabase','supabase-js','dist','umd','supabase.js'))
EVAL_INIT="try{localStorage.setItem('yoyo-evaluador',JSON.stringify({nombre:'Evaluador',apellido:'De Prueba',cargo:'Entrenador'}))}catch(e){}"
def setup_context(browser, mock, sbjs=True, **kw):
    ctx=browser.new_context(viewport={'width':1100,'height':900}, accept_downloads=True, **kw)
    ctx.add_init_script(EVAL_INIT)
    if sbjs: ctx.route('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2', lambda r: r.fulfill(path=SBJS, content_type='application/javascript'))
    else: ctx.route('https://cdn.jsdelivr.net/**', lambda r: r.abort('internetdisconnected'))
    ctx.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    ctx.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    ctx.route('https://script.google.com/**', lambda r: r.abort())
    ctx.route(U+'/**', mock.handle)
    return ctx
def open_page(ctx, errs=None):
    pg=ctx.new_page()
    if errs is not None:
        pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE); pg.wait_for_timeout(1200)
    return pg
def login(pg, email, pw, lic, dev='desktop'):
    pg.fill('#cloudEmail', email); pg.fill('#cloudPassword', pw); pg.fill('#cloudLicense', lic)
    pg.select_option('#cloudDeviceType', dev)
    pg.click('#cloudSignIn'); pg.wait_for_timeout(2500)
