"""Pruebas de navegador de la rama supabase-integration-prep (Supabase simulado).
Uso: python3 run_tests.py <etiqueta-version>
"""
import json, os, re, subprocess, sys, time, traceback, datetime
from common import *
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVD = os.path.join(HERE, 'evidencia'); os.makedirs(EVD, exist_ok=True)
VERSION = sys.argv[1] if len(sys.argv) > 1 else 'sin-version'
RESULTS = []
U1 = ('prueba1@example.com', 'Clave-Prueba-1')
U2 = ('prueba2@example.com', 'Clave-Prueba-2')
LIC = 'LIC-PRUEBA-VALIDA-2026'
UID1, UID2 = '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002'

# Imágenes de prueba
small = os.path.join(EVD, 'foto_pequena.png'); Image.new('RGB', (300, 360), (40, 120, 200)).save(small)
big = os.path.join(EVD, 'foto_grande.jpg'); Image.new('RGB', (4000, 3000), (200, 80, 40)).save(big, quality=95)
txt = os.path.join(EVD, 'no_es_imagen.txt'); open(txt, 'w').write('texto')
bad = os.path.join(EVD, 'corrupta.png'); open(bad, 'wb').write(b'\x89PNG\r\n\x1a\nbasura' * 10)


def rec(tid, area, funcion, pasos, esperado, fn):
    t0 = time.time()
    try:
        estado, obtenido, evid = fn()
    except Exception as e:
        estado, obtenido, evid = 'Fallida', 'Excepción en la prueba: ' + (str(e).split('\n')[0])[:300], ''
        traceback.print_exc()
    RESULTS.append({'id': tid, 'area': area, 'funcion': funcion, 'pasos': pasos, 'esperado': esperado, 'obtenido': obtenido,
                    'estado': estado, 'evidencia': evid, 'fecha': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'version': VERSION,
                    'tipo': 'Automática (navegador Chromium, Supabase simulado)'})
    print(f'[{estado:9}] {tid} {funcion} — {obtenido[:140]}')


def blocked(tid, area, funcion, motivo, necesita):
    RESULTS.append({'id': tid, 'area': area, 'funcion': funcion, 'pasos': '—', 'esperado': '—', 'obtenido': motivo, 'estado': 'Bloqueada',
                    'evidencia': necesita, 'fecha': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'version': VERSION, 'tipo': 'Requiere Supabase real'})
    print(f'[Bloqueada] {tid} {funcion}')


def shot(pg, name):
    path = os.path.join(EVD, name + '.png'); pg.screenshot(path=path, full_page=False); return 'evidencia/' + name + '.png'


def ok(cond, si, no):
    return ('Aprobada', si, '') if cond else ('Fallida', no, '')


def fill_eval(pg, nombre, mom='pre', temp='2026', vals=None):
    pg.click('#t-evaluar')
    pg.select_option('#e-atleta', '__new'); pg.wait_for_timeout(150)
    pg.fill('#e-nombre', nombre); pg.select_option('#e-sexo', 'F'); pg.select_option('#e-pos', 'Punta')
    pg.fill('#e-nac', '2008-05-10'); pg.fill('#e-temp', temp); pg.select_option('#e-mom', mom); pg.wait_for_timeout(150)
    pg.fill('#e-nombre', nombre)
    v = vals or {}
    for k, val in {'a-peso': '60', 'a-talla': '170', 'a-alc1': '220', 'a-alc2': '215'}.items():
        pg.fill('#' + k, v.get(k, val))
    data = {'bloqueo': ['260', '265', '262'], 'ataque': ['280', '285', '283'], 'horizontal': ['180', '190', ''], 's5': ['1.20', '1.15', '1.18'],
            's10': ['2.00', '1.95', ''], 'ttest': ['11.2', '11.0'], 'balon': ['6.0', '6.5', ''], 'plancha': ['90'], 'burpees': ['20']}
    data.update(v.get('t', {}))
    for k, arr in data.items():
        for i, x in enumerate(arr):
            if pg.locator(f'#in-{k}-{i}').count():
                pg.fill(f'#in-{k}-{i}', x)
    pg.fill('#in-sentadilla-carga', v.get('carga', '60')); pg.fill('#in-sentadilla-reps', v.get('reps', '5')); pg.fill('#in-balon-kg', '3')
    pg.wait_for_timeout(200)


def show_all(pg):
    # la app oculta las pruebas ya registradas al continuar una evaluación (casilla «solo las que faltan»)
    if pg.locator('#selHide').count() and pg.is_checked('#selHide'):
        pg.uncheck('#selHide'); pg.wait_for_timeout(200)


def save(pg):
    pg.click('#e-save'); pg.wait_for_timeout(900)
    return pg.text_content('#e-toast') or ''


def dialogs(pg, answers):
    """answers: lista de valores para confirm/prompt en orden (True/False o texto; None = cancelar)."""
    q = list(answers)
    def h(d):
        a = q.pop(0) if q else False
        if d.type == 'prompt':
            d.accept(a) if isinstance(a, str) else d.dismiss()
        else:
            d.accept() if a else d.dismiss()
    pg.on('dialog', h)
    return q


def db_rows(m, uid, col=None):
    return {k[2]: v for k, v in m.rows.items() if k[0] == uid and (col is None or k[1] == col)}


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= A. Inicio de sesión y licencia =================
    m = MockSupabase()
    ctx = setup_context(browser, m); errs = []; pg = open_page(ctx, errs)

    def a1():
        gate0 = pg.is_visible('#cloudAuthGate')
        login(pg, *U1, LIC)
        return ('Aprobada' if gate0 and not pg.is_visible('#cloudAuthGate') and 'Conectado' in pg.text_content('#storeNote') else 'Fallida',
                f"Puerta visible al abrir: {gate0}. Tras iniciar: puerta visible={pg.is_visible('#cloudAuthGate')}, estado='{pg.text_content('#storeNote')}'. Corrección aplicada antes: lectura del código de licencia.", shot(pg, 'A1_login_valido'))
    rec('A1', 'A. Sesión y licencia', 'Inicio de sesión válido con licencia válida', 'Correo, contraseña y licencia de prueba → Iniciar sesión', 'Entra a la app, estado «Conectado a la base de datos centralizada»', a1)

    def a2():
        return ok(pg.is_visible('#cloudAuthTop') and 'Conectado' in pg.text_content('#storeNote') and not pg.is_visible('#cloudAuthGate') if (pg.reload(), pg.wait_for_timeout(1500)) else False,
                  'Tras recargar sigue conectado sin volver a pedir datos', 'Tras recargar volvió a pedir la sesión: ' + pg.text_content('#storeNote'))
    rec('A2', 'A. Sesión y licencia', 'Persistencia de sesión al recargar', 'Recargar la página con sesión activa', 'Sigue conectado', a2)

    def a3():
        pg.click('#cloudSignOut'); pg.wait_for_timeout(1500)
        lic = pg.evaluate("localStorage.getItem('vb-license-code')")
        return ok(pg.is_visible('#cloudAuthGate') and lic is None, 'Vuelve la pantalla de acceso; el código de licencia guardado se borra', f'Puerta={pg.is_visible("#cloudAuthGate")}, licencia guardada={lic}')
    rec('A3', 'A. Sesión y licencia', 'Cierre de sesión', 'Cerrar sesión', 'Vuelve a la pantalla de acceso', a3)

    def a4():
        login(pg, U1[0], 'Contraseña-incorrecta', LIC)
        msg = pg.text_content('#cloudAuthMessage')
        return ok(pg.is_visible('#cloudAuthGate') and 'incorrectos' in msg, f"Rechazada con mensaje: «{msg}»", f'No se rechazó correctamente: {msg}')
    rec('A4', 'A. Sesión y licencia', 'Rechazo de credenciales incorrectas', 'Contraseña incorrecta', 'Mensaje de error, no entra', a4)

    def a5():
        login(pg, *U1, 'CODIGO-INVENTADO')
        msg = pg.text_content('#cloudAuthMessage')
        return ok(pg.is_visible('#cloudAuthGate') and 'no válido' in msg, f'Rechazada: «{msg}»', f'Mensaje: {msg}')
    rec('A5', 'A. Sesión y licencia', 'Rechazo de licencia inválida', 'Credenciales válidas + código de licencia inexistente', 'No entra; «Código de licencia no válido.»', a5)

    def a6():
        pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1200)
        login(pg, *U1, 'LIC-PRUEBA-VENCIDA')
        msg = pg.text_content('#cloudAuthMessage')
        return ok('vencida' in msg, f'Rechazada: «{msg}»', f'Mensaje: {msg}')
    rec('A6', 'A. Sesión y licencia', 'Licencia vencida', 'Código de licencia vencido', 'No entra; mensaje de vigencia', a6)

    def a7():
        login(pg, *U1, LIC)  # este equipo ya ocupa el cupo de computadora (A1 usó otro id de equipo)
        msg = pg.text_content('#cloudAuthMessage')
        ctx2 = setup_context(browser, m); pg2 = open_page(ctx2); login(pg2, *U1, LIC, 'mobile'); mob = 'Conectado' in pg2.text_content('#storeNote'); ctx2.close()
        return ('Aprobada' if 'límite' in msg and mob else 'Fallida',
                f'Segunda computadora: «{msg}». Un celular con la misma licencia: {"entra" if mob else "no entra"} (cupo 1 computadora + 1 celular).', shot(pg, 'A7_limite_dispositivos'))
    rec('A7', 'A. Sesión y licencia', 'Límite de dispositivos', 'Misma licencia en una 2.ª computadora (localStorage borrado = equipo nuevo) y en un celular', '2.ª computadora rechazada; celular aceptado', a7)

    def a8():
        c3 = setup_context(browser, m); p3 = open_page(c3); login(p3, *U2, LIC); msg = p3.text_content('#cloudAuthMessage'); c3.close()
        return ok('otra cuenta' in msg, f'Rechazada: «{msg}»', f'Mensaje: {msg}')
    rec('A8', 'A. Sesión y licencia', 'Licencia de otra cuenta', 'Usuario 2 intenta usar la licencia ya asignada al usuario 1', 'Rechazo «pertenece a otra cuenta»', a8)

    def a9():
        c4 = setup_context(browser, m); p4 = open_page(c4)
        m.fail.add('rpc'); login(p4, *U1, LIC, 'mobile'); msg = p4.text_content('#cloudAuthMessage'); note = p4.text_content('#storeNote'); m.fail.discard('rpc')
        s = shot(p4, 'A9_error_servidor'); c4.close()
        return ok(p4 and 'Licencia no validada' in note and msg, f'Error 500 del servidor: queda en la pantalla de acceso con «{msg}» y estado «{note}»; no se muestra como éxito.', f'Estado: {note} / {msg}')[:2] + (s,)
    rec('A9', 'A. Sesión y licencia', 'Error del servidor al validar licencia', 'La RPC responde 500', 'No entra y muestra el error', a9)
    ctx.close()

    def a10():
        mm = MockSupabase(); mm.fail.add('all'); c5 = setup_context(browser, mm); p5 = open_page(c5)
        login(p5, *U1, LIC); gate = p5.is_visible('#cloudAuthGate'); msg = p5.text_content('#cloudAuthMessage'); s = shot(p5, 'A10_primer_uso_sin_internet'); c5.close()
        return ('Aprobada' if gate and 'conexión a internet' in msg else 'Fallida', f'Primer uso sin internet (sin copia previa): sigue la pantalla de acceso con el mensaje «{msg}». Es lo esperado: la primera vez hay que validar la cuenta y la licencia con conexión.', s)
    rec('A10', 'A. Sesión y licencia', 'Primer uso sin internet', 'Equipo nuevo, sin conexión, intenta iniciar sesión', 'No entra y explica el motivo', a10)

    # ================= B, C, D, E con usuario 1 conectado =================
    m = MockSupabase()
    ctx = setup_context(browser, m); errs = []; pg = open_page(ctx, errs); login(pg, *U1, LIC)

    def b1():
        pg.click('#t-evaluar'); pg.select_option('#e-atleta', '__new'); pg.fill('#e-nombre', ''); pg.click('#e-save'); pg.wait_for_timeout(400)
        t = pg.text_content('#e-toast'); n = len(db_rows(m, UID1, 'atletas'))
        return ok('Escriba el nombre' in t and n == 0, f'Sin nombre: «{t}»; no se creó ningún registro', f'Toast «{t}», registros {n}')
    rec('B1', 'B. Atletas', 'Campo obligatorio: nombre', 'Guardar atleta nuevo sin nombre', 'Mensaje y nada guardado', b1)

    def b2():
        fill_eval(pg, 'Atleta Ficticia Uno')
        pg.click('#e-save'); pg.click('#e-save', force=True, no_wait_after=True, timeout=2000) if pg.locator('#e-save').is_enabled() else None
        pg.wait_for_timeout(1200)
        ath = db_rows(m, UID1, 'atletas'); ev = db_rows(m, UID1, 'evaluaciones')
        return ok(len(ath) == 1 and len(ev) == 1, f'1 atleta y 1 evaluación en la base simulada tras doble toque en Guardar; mensaje «{pg.text_content("#e-toast")}»',
                  f'Atletas {len(ath)}, evaluaciones {len(ev)}')
    rec('B2', 'B. Atletas', 'Crear atleta y guardar sin duplicados', 'Llenar ficha completa y tocar Guardar dos veces seguidas', 'Un solo atleta y una sola evaluación', b2)

    def c1():
        # la app usa el formato numérico es-HN (punto decimal)
        exp = {'bloqueo': '50 cm', 'ataque': '65 cm', 'horizontal': '190 cm', 's5': '1.15 s', 's10': '1.95 s', 'ttest': '11.00 s', 'sentadilla': '68 kg', 'balon': '6.50 m', 'plancha': '90 s', 'burpees': '20 rep'}
        aid = list(db_rows(m, UID1, 'atletas'))[0]
        pg.select_option('#e-atleta', aid); pg.wait_for_timeout(400); show_all(pg)
        got = {k: (pg.text_content('#res-' + k) or '').strip() for k in exp}
        bad = {k: (got[k], e) for k, e in exp.items() if not got[k].startswith(e)}
        calc = pg.text_content('#anthroCalc')
        imc_ok = '20.8' in calc or '20,8' in calc
        pot = '3.698' in got['bloqueo'] or '3,698' in got['bloqueo'] or '3698' in got['bloqueo']
        s = shot(pg, 'C1_resultados')
        return ('Aprobada' if not bad and imc_ok and pot else 'Fallida',
                ('Todos los resultados coinciden con el cálculo manual: bloqueo 265−215=50 cm (potencia 60,7·50+45,3·60−2055=3.698 W), ataque 285−220=65 cm, sentadilla Brzycki 60·36/(37−5)=67,5→68 kg, IMC 60/1,7²=20,8.' if not bad and imc_ok and pot else f'Diferencias: {bad}; IMC en pantalla: {imc_ok}; potencia: {pot}'), s)
    rec('C1', 'C. Pruebas físicas', 'Fórmulas con valores conocidos', 'Abrir la evaluación guardada y comparar cada resultado', 'Coinciden con el cálculo manual', c1)

    def c2():
        show_all(pg); pg.fill('#in-bloqueo-0', '200'); pg.fill('#in-bloqueo-1', ''); pg.fill('#in-bloqueo-2', ''); pg.fill('#in-sentadilla-reps', '12'); pg.fill('#a-peso', 'abc'); pg.wait_for_timeout(200)
        rb = pg.text_content('#res-bloqueo'); rs = pg.text_content('#res-sentadilla'); calc = pg.text_content('#anthroCalc')
        cond = 'mayor que el alcance' in rb and '10 repeticiones' in rs and 'Escriba peso y talla' in calc
        pg.select_option('#e-atleta', list(db_rows(m, UID1, 'atletas'))[0]); pg.wait_for_timeout(300)
        return ok(cond, 'Valores incorrectos se marcan: salto menor que el alcance, más de 10 repeticiones y peso no numérico (IMC no se calcula)', f'Bloqueo «{rb}», sentadilla «{rs}», antropometría «{calc[:80]}»')
    rec('C2', 'C. Pruebas físicas', 'Valores incorrectos e incompletos', 'Escribir salto < alcance, 12 repeticiones, peso «abc»', 'Mensajes de error, sin resultados falsos', c2)

    def b3():
        aid = list(db_rows(m, UID1, 'atletas'))[0]
        pg.select_option('#e-atleta', aid); pg.wait_for_timeout(300); show_all(pg); pg.select_option('#e-pos', 'Central'); pg.fill('#a-peso', '61'); save(pg)
        pg.reload(); pg.wait_for_timeout(1800); pg.click('#t-evaluar'); pg.select_option('#e-atleta', aid); pg.wait_for_timeout(300); show_all(pg)
        pos = pg.input_value('#e-pos'); peso = pg.input_value('#a-peso'); dbp = db_rows(m, UID1, 'atletas')[aid].get('posicion')
        return ok(pos == 'Central' and peso == '61' and dbp == 'Central', 'Edición guardada en la base y recuperada tras recargar (posición Central, peso 61)', f'Pantalla pos={pos} peso={peso}; base pos={dbp}')
    rec('B3', 'B. Atletas', 'Editar y recuperar tras recargar', 'Cambiar posición y peso, guardar, recargar', 'Se ven los datos nuevos', b3)

    # ---- D. Fotografías ----
    def d1():
        pg.click('#t-evaluar'); aid = list(db_rows(m, UID1, 'atletas'))[0]; pg.select_option('#e-atleta', aid); pg.wait_for_timeout(300)
        pg.set_input_files('#athletePhotoUpload', small); pg.wait_for_timeout(700)
        vis = pg.is_visible('#athletePhotoPreview'); src = pg.get_attribute('#athletePhotoPreview', 'src') or ''
        pg.click('#athletePhotoRemove'); pg.wait_for_timeout(200); gone = not pg.is_visible('#athletePhotoPreview')
        return ok(vis and src.startswith('data:image/jpeg') and gone, 'Vista previa en JPEG comprimido; «Quitar fotografía» la retira antes de guardar', f'vista={vis}, tipo={src[:22]}, retirada={gone}')
    rec('D1', 'D. Fotografías', 'Elegir imagen, vista previa y quitar', 'Subir PNG 300×360, luego Quitar', 'Vista previa y retiro correcto', d1)

    def d2():
        aid = list(db_rows(m, UID1, 'atletas'))[0]
        pg.set_input_files('#athletePhotoUpload', big); pg.wait_for_timeout(1500); save(pg)
        foto = db_rows(m, UID1, 'atletas')[aid].get('foto', '')
        kb = round(len(foto) * 3 / 4 / 1024)
        import base64, io
        w, h = Image.open(io.BytesIO(base64.b64decode(foto.split(',')[1]))).size if foto else (0, 0)
        pg.reload(); pg.wait_for_timeout(1800); pg.click('#t-evaluar'); pg.select_option('#e-atleta', aid); pg.wait_for_timeout(400)
        back = pg.is_visible('#athletePhotoPreview'); s = shot(pg, 'D2_foto_recuperada')
        return ('Aprobada' if foto and max(w, h) <= 480 and back else 'Fallida', f'Foto de 4000×3000 guardada como {w}×{h} ({kb} KB) y recuperada tras recargar: {back}', s)
    rec('D2', 'D. Fotografías', 'Imagen grande: compresión, guardado y recuperación', 'Subir JPG 4000×3000, guardar, recargar', 'Se reduce (≤480 px) y reaparece', d2)

    def d3():
        pg.set_input_files('#athletePhotoUpload', txt); pg.wait_for_timeout(300); m1 = pg.text_content('#athletePhotoNote')
        pg.set_input_files('#athletePhotoUpload', bad); pg.wait_for_timeout(800); m2 = pg.text_content('#athletePhotoNote')
        return ok('archivo de imagen' in m1 and 'No se pudo' in m2, f'Texto: «{m1}». PNG dañado: «{m2}»', f'{m1} / {m2}')
    rec('D3', 'D. Fotografías', 'Formatos no válidos', 'Subir un .txt y un PNG dañado', 'Mensajes claros, sin romper la ficha', d3)

    def d4():
        cap = pg.get_attribute('#athletePhotoUpload', 'capture')
        return ('Fallida' if cap else 'Aprobada', f'El selector de archivos tiene capture="{cap}": en iPad y celulares abre directo la cámara y no deja elegir una foto de la galería, aunque el botón dice «Elegir fotografía».' if cap else 'Sin atributo capture', '')
    rec('D4', 'D. Fotografías', '«Elegir fotografía» en celular/iPad', 'Revisar el selector de archivo', 'Permite elegir de la galería', d4)

    def d5():
        pg.click('#t-evaluar'); pg.select_option('#e-atleta', '__new'); pg.wait_for_timeout(200); pg.fill('#e-nombre', 'Atleta Foto Nueva')
        pg.set_input_files('#athletePhotoUpload', small); pg.wait_for_timeout(600)
        pg.select_option('#e-mom', 'mitad'); pg.wait_for_timeout(400)
        kept = pg.is_visible('#athletePhotoPreview')
        return ('Aprobada' if kept else 'Fallida', 'La foto se conserva al cambiar el momento' if kept else 'La foto tomada a un atleta nuevo se pierde al cambiar el momento, la temporada o el atleta antes de guardar (loadEvalForm la reinicia).', '')
    rec('D5', 'D. Fotografías', 'Foto de atleta nuevo al cambiar momento', 'Atleta nuevo + foto, luego cambiar el momento antes de guardar', 'La foto se mantiene', d5)

    # ---- E. Supabase (simulado) ----
    def e1():
        aid = list(db_rows(m, UID1, 'atletas'))[0]
        pg.click('#t-atletas'); pg.wait_for_timeout(300)
        if not pg.evaluate(f"document.querySelector('details.ath[data-aid=\"{aid}\"]').open"):
            pg.locator(f'details.ath[data-aid="{aid}"] > summary').first.click(); pg.wait_for_timeout(300)
        pg.locator(f'[data-delath="{aid}"]').first.click(); pg.wait_for_timeout(300); pg.locator(f'[data-delath="{aid}"]').first.click(); pg.wait_for_timeout(1200)
        left = [k for k in db_rows(m, UID1) if aid in k]
        pg.reload(); pg.wait_for_timeout(1800)
        vis = pg.locator(f'details.ath[data-aid="{aid}"]').count()
        return ok(not left and vis == 0, 'Atleta y sus evaluaciones borrados de la base; no reaparecen al recargar', f'Quedan en base: {left}; visible tras recargar: {vis}')
    rec('B4', 'B. Atletas', 'Eliminar atleta de prueba', 'Borrar atleta (doble toque de confirmación), recargar', 'Desaparece de la base y de la pantalla', e1)

    def e2():
        fill_eval(pg, 'Atleta Sin Red'); m.fail.add('upsert'); t = save(pg); m.fail.discard('upsert')
        n = len([1 for a in db_rows(m, UID1, 'atletas').values() if a.get('nombre') == 'Atleta Sin Red'])
        q = pg.evaluate('window.vbPendingCount()'); note = pg.text_content('#storeNote'); s = shot(pg, 'E2_guardado_sin_red')
        return ('Aprobada' if 'se subirá' in t and n == 0 and q >= 1 and 'Sin conexión' in note else 'Fallida',
                f'Con la conexión cortada al guardar: «{t}». Pendientes en la cola: {q}. Estado: «{note}». Nada llegó a la nube todavía ({n}).', s)
    rec('E2', 'E. Supabase', 'Corte de conexión al guardar', 'Cortar la red justo al guardar', 'Se guarda en este equipo, queda en cola y se avisa', e2)

    def e3():
        pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(3500)
        n = len([1 for a in db_rows(m, UID1, 'atletas').values() if a.get('nombre') == 'Atleta Sin Red'])
        q = pg.evaluate('window.vbPendingCount()'); note = pg.text_content('#storeNote')
        return ok(n == 1 and q == 0 and 'Conectado' in note, f'Al volver la conexión se subió solo: en la nube {n}, en cola {q}, estado «{note}»', f'nube {n}, cola {q}, estado {note}')
    rec('E3', 'E. Supabase', 'Sincronización al volver la conexión', 'Volver a tener internet', 'La cola se sube sola', e3)

    def e4():
        c2_ = setup_context(browser, m); p2 = open_page(c2_)
        p2.evaluate("([d])=>localStorage.setItem('vb-device-id',d)", [pg.evaluate("localStorage.getItem('vb-device-id')")])  # mismo equipo autorizado
        login(p2, *U1, LIC)
        fill_eval(p2, 'Atleta Otra Sesion'); save(p2); p2.wait_for_timeout(500)
        pg.reload(); pg.wait_for_timeout(1800)
        seen = 'Atleta Otra Sesion' in pg.inner_text('#e-atleta')
        c2_.close()
        return ok(seen, 'Un cambio hecho en otra sesión aparece al recargar (Realtime en vivo no se puede simular aquí)', 'No apareció')
    rec('E4', 'E. Supabase', 'Cambios de otra sesión', 'Segunda sesión crea atleta; la primera recarga', 'Aparece', e4)

    def o1():
        m.fail.add('all'); pg.reload(); pg.wait_for_timeout(2500)
        note = pg.text_content('#storeNote'); gate = pg.is_visible('#cloudAuthGate'); opts = pg.inner_text('#e-atleta')
        s = shot(pg, 'O1_abrir_sin_internet')
        return ('Aprobada' if not gate and 'Atleta Sin Red' in opts and 'Sin conexión' in note else 'Fallida',
                f'Sin internet al abrir: pantalla de acceso visible={gate}; estado «{note}»; atletas de la nube disponibles: {"sí" if "Atleta Sin Red" in opts else "no"}', s)
    rec('O1', 'O. Sin conexión', 'Abrir la app sin internet tras trabajar en la nube', 'Trabajar conectado, cortar internet y recargar', 'Abre con la copia de este equipo', o1)

    def o2():
        fill_eval(pg, 'Atleta Offline'); t = save(pg); q = pg.evaluate('window.vbPendingCount()')
        n = len([1 for a in db_rows(m, UID1, 'atletas').values() if a.get('nombre') == 'Atleta Offline'])
        return ok('se subirá' in t and q >= 1 and n == 0, f'Evaluación nueva sin internet: «{t}»; en cola {q}', f'{t} / cola {q} / nube {n}')
    rec('O2', 'O. Sin conexión', 'Registrar sin internet', 'Crear atleta y evaluación sin conexión', 'Se guarda en el equipo y queda en cola', o2)

    def o3():
        aid = [k for k, a in db_rows(m, UID1, 'atletas').items() if a.get('nombre') == 'Atleta Sin Red'][0]
        pg.click('#t-atletas'); pg.wait_for_timeout(300)
        if not pg.evaluate(f"document.querySelector('details.ath[data-aid=\"{aid}\"]').open"):
            pg.locator(f'details.ath[data-aid="{aid}"] > summary').first.click(); pg.wait_for_timeout(300)
        pg.locator(f'[data-delath="{aid}"]').first.click(); pg.wait_for_timeout(300); pg.locator(f'[data-delath="{aid}"]').first.click(); pg.wait_for_timeout(800)
        gone = pg.locator(f'details.ath[data-aid="{aid}"]').count() == 0; still = aid in db_rows(m, UID1, 'atletas')
        return ok(gone and still, 'Borrado sin internet: desaparece en el equipo y queda en cola (la nube aún lo tiene)', f'pantalla {gone}, nube {still}')
    rec('O3', 'O. Sin conexión', 'Borrar sin internet', 'Borrar un atleta sin conexión', 'Se borra en el equipo y queda en cola', o3)

    def o4():
        pg.click('#t-atletas'); pg.wait_for_timeout(200); pg.click('#resetAllData'); pg.wait_for_timeout(400); t = pg.text_content('#resetAllToast')
        return ok('necesita conexión' in t, f'«{t}»', t)
    rec('O4', 'O. Sin conexión', 'Restablecer sin internet', 'Tocar Restablecer sin conexión', 'No se permite', o4)

    def o5():
        q0 = pg.evaluate('window.vbPendingCount()'); pg.click('#cloudSignOut'); pg.wait_for_timeout(800)
        still = not pg.is_visible('#cloudAuthGate') and pg.evaluate('window.vbPendingCount()') == q0
        return ok(still and q0 > 0, f'Con {q0} cambios sin subir, «Cerrar sesión» pide confirmación; al cancelar sigue dentro y no se pierde nada', f'cola {q0}, sigue dentro {still}')
    rec('O5', 'O. Sin conexión', 'Cerrar sesión con cambios sin subir', 'Cerrar sesión y cancelar el aviso', 'Avisa y no pierde cambios', o5)

    def o6():
        m.fail.discard('all'); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(4000)
        names = [a.get('nombre') for a in db_rows(m, UID1, 'atletas').values()]
        q = pg.evaluate('window.vbPendingCount()'); note = pg.text_content('#storeNote')
        cond = 'Atleta Offline' in names and 'Atleta Sin Red' not in names and q == 0 and 'Conectado' in note
        pg.reload(); pg.wait_for_timeout(1800); opts = pg.inner_text('#e-atleta')
        cond = cond and 'Atleta Offline' in opts and 'Atleta Sin Red' not in opts
        return ('Aprobada' if cond else 'Fallida', f'Al volver internet: se subió el atleta nuevo y se aplicó el borrado; cola {q}; estado «{note}»; tras recargar coincide: {cond}', shot(pg, 'O6_sincronizado'))
    rec('O6', 'O. Sin conexión', 'Subir lo hecho sin internet', 'Volver a tener conexión', 'Altas y borrados llegan a la nube', o6)

    def o7():
        pg.evaluate("(()=>{const o=JSON.parse(localStorage.getItem('vb-offline-user'));o.licOk=Date.now()-31*864e5;localStorage.setItem('vb-offline-user',JSON.stringify(o))})()")
        m.fail.add('all'); pg.reload(); pg.wait_for_timeout(2500); gate = pg.is_visible('#cloudAuthGate'); m.fail.discard('all')
        return ok(gate, 'Con la última validación de licencia de hace 31 días, sin internet no deja entrar (límite: 30 días)', 'Entró con la licencia vencida en modo sin conexión')
    rec('O7', 'O. Sin conexión', 'Límite de días sin conexión', 'Última validación hace 31 días y sin internet', 'Pide conexión', o7)

    def o8():
        pg.evaluate("(()=>{const o=JSON.parse(localStorage.getItem('vb-offline-user'));o.licOk=Date.now();localStorage.setItem('vb-offline-user',JSON.stringify(o))})()")
        ctx.route('**/supabase-js@2.118.0/dist/umd/supabase.js', lambda r: r.abort('internetdisconnected'))
        m.fail.add('all'); pg.reload(); pg.wait_for_timeout(2500)
        gate = pg.is_visible('#cloudAuthGate'); note = pg.text_content('#storeNote'); opts = pg.inner_text('#e-atleta')
        m.fail.discard('all'); ctx.unroute('**/supabase-js@2.118.0/dist/umd/supabase.js')
        ctx.route('**/supabase-js@2.118.0/dist/umd/supabase.js', lambda r: r.fulfill(path=SBJS, content_type='application/javascript', headers={'access-control-allow-origin': '*'}))
        return ok(not gate and 'Sin conexión' in note and 'Atleta Offline' in opts, f'Sin internet y sin poder cargar la librería: entra con la copia del equipo («{note[:60]}…»)', f'puerta {gate}, estado {note}')
    rec('O8', 'O. Sin conexión', 'Sin internet ni librería en caché', 'Cortar internet y la CDN; recargar', 'Abre con la copia del equipo', o8)

    blocked('E6', 'E. Supabase', 'Aislamiento real entre cuentas (RLS)', 'Necesita dos cuentas de prueba en el Supabase real. Desde aquí no tengo permiso para conectarme a su proyecto.',
            'Ejecutar tests/integracion-supabase.html con dos cuentas de prueba')
    blocked('E7', 'E. Supabase', 'Permisos de licencias y license_devices', 'Necesita el Supabase real (políticas y función activate_device_license).', 'Ejecutar tests/integracion-supabase.html')
    ctx.close()

    # ================= F. Informes PDF (datos sembrados) =================
    m = MockSupabase(); ctx = setup_context(browser, m); pg = open_page(ctx); login(pg, *U1, LIC)
    fill_eval(pg, 'Ana Ficticia', 'pre', vals={'t': {'bloqueo': ['265', '', '']}}); pg.set_input_files('#athletePhotoUpload', small); pg.wait_for_timeout(600); save(pg)
    fill_eval(pg, 'Bea Ficticia', 'pre', vals={'t': {'bloqueo': ['255', '', '']}}); save(pg)
    for nom, blo in [('Ana Ficticia', '270'), ('Bea Ficticia', '257')]:
        aid = [k for k, a in db_rows(m, UID1, 'atletas').items() if a['nombre'] == nom][0]
        pg.click('#t-evaluar'); pg.select_option('#e-atleta', aid); pg.select_option('#e-mom', 'fin'); pg.wait_for_timeout(300); show_all(pg)
        pg.fill('#a-alc2', '215'); pg.fill('#a-alc1', '220'); pg.fill('#in-bloqueo-0', blo); save(pg)

    def pdf_of(click):
        with pg.expect_download(timeout=15000) as d:
            click(); pg.wait_for_timeout(800); pg.click('#ofShare')
        path = os.path.join(EVD, d.value.suggested_filename); d.value.save_as(path); pg.click('#ofClose'); return path

    def pages(path):
        out = subprocess.run(['pdfinfo', path], capture_output=True, text=True).stdout
        return int(re.search(r'Pages:\s+(\d+)', out).group(1))

    def txt_of(path):
        return subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout

    def imgs(path):
        out = subprocess.run(['pdfimages', '-list', path], capture_output=True, text=True).stdout
        return max(0, len(out.strip().split('\n')) - 2)

    def f1():
        pg.click('#t-atletas'); pg.wait_for_timeout(400)
        path = pdf_of(lambda: pg.locator('.qpdf [data-pdf]').first.click())
        t = txt_of(path); n = pages(path); im = imgs(path)
        cond = 'Ana Ficticia' in t and '50 cm' in t and '55 cm' in t and '+10' in t and im >= 1
        return ('Aprobada' if cond else 'Fallida', f'{os.path.basename(path)}: {n} página(s), {im} imagen(es). Bloqueo pre 50 cm, fin 55 cm y cambio +10 % presentes: {cond}', 'evidencia/' + os.path.basename(path))
    rec('F1', 'F. PDF', 'Ficha individual con foto', 'Ficha PDF de una atleta con foto y dos etapas', 'Nombre, foto, valores y % correctos', f1)

    def f2():
        pg.select_option('#d-mom', 'fin')
        path = pdf_of(lambda: pg.click('#pdfTeam'))
        t = txt_of(path); n = pages(path); im = imgs(path)
        pg_blo = [b for b in t.split('\f') if 'COMPARATIVO POR ETAPAS' in b and 'Salto de bloqueo' in b]
        blo = pg_blo[0] if pg_blo else ''
        avg_ok = ('45.0 cm' in blo or '45,0 cm' in blo) and ('48.5 cm' in blo or '48,5 cm' in blo) and ('+7,8' in blo or '+7.8' in blo)
        ana_ok = '+10.0%' in blo or '+10,0%' in blo
        bea_ok = '+5.0%' in blo or '+5,0%' in blo
        cond = n == 13 and avg_ok and ana_ok and bea_ok
        return ('Aprobada' if cond else 'Fallida',
                f'{n} páginas (resumen + 12 pruebas), {im} imágenes. Bloqueo: Ana 50→55 (+10 %): {ana_ok}; Bea 40→42 (+5 %): {bea_ok}; promedio 45→48,5 (+7,8 %): {avg_ok}', 'evidencia/' + os.path.basename(path))
    rec('F2', 'F. PDF', 'Informe del equipo y comparativo por etapas', 'Resumen del equipo (fin de temporada) con 2 atletas en pre y fin', '1 página resumen + 1 por prueba; promedios y % correctos', f2)

    def f3():
        path = pdf_of(lambda: pg.locator('.qpdf [data-informe]').nth(1).click())
        t = txt_of(path); cond = 'Bea Ficticia' in t and 'Sin foto' in t
        return ok(cond, f'Atleta sin foto: el informe se genera y muestra «Sin foto» ({pages(path)} páginas)', 'No se generó correctamente')[:2] + ('evidencia/' + os.path.basename(path),)
    rec('F3', 'F. PDF', 'Informe de atleta sin foto', 'Informe y plan de la atleta sin foto', 'Se genera sin error', f3)
    ctx.close()

    # ================= G. Restablecimiento =================
    m = MockSupabase(); ctx = setup_context(browser, m); pg = open_page(ctx); login(pg, *U1, LIC)
    for i in range(3):
        fill_eval(pg, f'Atleta Borrable {i+1}'); save(pg)
    m.rows[(UID2, 'atletas', 'ajeno-1')] = {'nombre': 'Atleta de otra cuenta'}
    before = len(db_rows(m, UID1))

    ANS = []
    def _h(d):
        a = ANS.pop(0) if ANS else False
        if d.type == 'prompt':
            d.accept(a) if isinstance(a, str) else d.dismiss()
        else:
            d.accept() if a else d.dismiss()
    pg.on('dialog', _h)
    def g_click(answers):
        ANS[:] = answers; pg.click('#t-atletas'); pg.wait_for_timeout(300); pg.click('#resetAllData'); pg.wait_for_timeout(1500)
        return pg.text_content('#resetAllToast') or ''

    def g1():
        t = g_click([False]); n = len(db_rows(m, UID1))
        return ok(n == before, f'Cancelado en la 1.ª confirmación: {n} registros intactos', f'Registros {before}→{n}')
    rec('G1', 'G. Restablecer', 'Cancelar la primera confirmación', 'Tocar el botón y Cancelar', 'Nada se borra', g1)

    def g2():
        pg2 = pg
        t = g_click([True, 'borrar']); n = len(db_rows(m, UID1))
        return ok(n == before and 'cancelada' in t, f'Palabra incorrecta («borrar»): «{t}», {n} registros intactos', f'{t} / {n}')
    rec('G2', 'G. Restablecer', 'Palabra de confirmación incorrecta', 'Aceptar y escribir «borrar» en minúsculas', 'Nada se borra', g2)

    def g3():
        m.fail.add('delete'); t = g_click([True, 'BORRAR']); m.fail.discard('delete'); n = len(db_rows(m, UID1))
        opts = pg.inner_text('#e-atleta')
        return ok('No se pudo completar' in t and n == before and 'Atleta Borrable 1' in opts, f'Con la red cortada: «{t[:90]}…»; base y pantalla intactas', f'{t} / {n}')
    rec('G3', 'G. Restablecer', 'Fallo de conexión durante el borrado', 'Confirmar con BORRAR con la red cortada', 'Error visible, sin borrado parcial ni falso éxito', g3)

    def g4():
        t = g_click([True, 'BORRAR']); n1 = len(db_rows(m, UID1)); n2 = len(db_rows(m, UID2))
        pg.reload(); pg.wait_for_timeout(1800)
        opts = pg.inner_text('#e-atleta'); lic = pg.evaluate("localStorage.getItem('vb-license-code')"); conn = 'Conectado' in pg.text_content('#storeNote')
        s = shot(pg, 'G4_tras_borrar')
        cond = n1 == 0 and n2 == 1 and 'Borrable' not in opts and lic and conn
        return ('Aprobada' if cond else 'Fallida', f'«{t}». Registros del usuario: {before}→{n1}; los de otra cuenta se conservan ({n2}). Tras recargar no reaparecen; sesión y licencia conservadas: {bool(lic) and conn}.', s)
    rec('G4', 'G. Restablecer', 'Borrado confirmado con BORRAR', 'Aceptar y escribir BORRAR; recargar', 'Se borran solo los datos de la cuenta; sesión y licencia siguen', g4)
    ctx.close()

    # ================= D (cámara) =================
    cam = p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
    mc = MockSupabase(); cctx = setup_context(cam, mc, permissions=['camera']); cp = open_page(cctx); login(cp, *U1, LIC)

    def d6():
        cp.click('#t-evaluar'); cp.click('#athleteCameraStart'); cp.wait_for_timeout(1500)
        live = cp.is_visible('#athleteCameraVideo'); cp.click('#athleteCameraCapture'); cp.wait_for_timeout(500)
        prev = cp.is_visible('#athletePhotoPreview'); src = cp.get_attribute('#athletePhotoPreview', 'src') or ''
        s = shot(cp, 'D6_camara')
        return ('Aprobada' if live and prev and src.startswith('data:image/jpeg') else 'Fallida', f'Cámara simulada: video visible {live}; foto capturada {prev}', s)
    rec('D6', 'D. Fotografías', 'Capturar con la cámara', 'Tomar fotografía → Capturar foto', 'Vista previa con la foto', d6)
    cctx.close(); cam.close()

    deny = p.chromium.launch(args=['--deny-permission-prompts'])
    md = MockSupabase(); dctx = setup_context(deny, md); dp = open_page(dctx); login(dp, *U1, LIC)

    def d7():
        dp.click('#t-evaluar'); dp.click('#athleteCameraStart'); dp.wait_for_timeout(1500); msg = dp.text_content('#athletePhotoNote')
        return ok(bool(msg) and not dp.is_visible('#athleteCameraVideo'), f'Permiso de cámara negado: «{msg}»', f'Mensaje: {msg}')
    rec('D7', 'D. Fotografías', 'Permiso de cámara denegado', 'Negar el permiso de cámara', 'Mensaje claro', d7)
    dctx.close(); deny.close()

    # ================= N. Normas internacionales por edad y sexo =================
    m = MockSupabase(); ctx = setup_context(browser, m); nerr = []; pg = open_page(ctx, nerr); login(pg, *U1, LIC)
    T_N = {'horizontal': ['190', '', ''], 'cmj': ['33.0', '', ''], 's10': ['1.95', '', ''], 'ttest': ['11.0', '']}

    def nueva(nombre, nac, sexo='F'):
        fill_eval(pg, nombre, vals={'t': T_N}); pg.select_option('#e-sexo', sexo); pg.fill('#e-nac', nac); pg.wait_for_timeout(300)

    def nivel_txt(nombre):
        aid = [k for k, a in db_rows(m, UID1, 'atletas').items() if a['nombre'] == nombre][0]
        pg.click('#t-atletas'); pg.wait_for_timeout(400)
        d = pg.locator(f'details[data-sub="{aid}-lvl"]')
        par = d.locator('xpath=ancestor::details[1]')
        if par.count() and not par.evaluate('e=>e.open'): par.locator('summary').first.click(); pg.wait_for_timeout(400)
        d = pg.locator(f'details[data-sub="{aid}-lvl"]')
        if not d.evaluate('e=>e.open'): d.locator('summary').first.click(); pg.wait_for_timeout(500)
        return pg.locator(f'details[data-sub="{aid}-lvl"]').inner_text()

    def n1():
        pg.click('#t-evaluar'); pg.wait_for_timeout(200); show_all(pg)
        has = pg.locator('#in-cmj-0').count() == 1 and pg.locator('#in-cmj-2').count() == 1
        body = pg.inner_text('body')
        return ok(has and 'Salto vertical CMJ' in body and not nerr, 'La ficha tiene el Salto vertical CMJ con 3 intentos y sin errores de página', f'campos {has}, errores {nerr[:2]}')
    rec('N1', 'N. Normas', 'Prueba nueva: salto vertical CMJ', 'Abrir la ficha', 'Aparece el CMJ con 3 intentos', n1)

    def n2():
        nueva('Nora Mayor', '2008-05-10'); save(pg); t = nivel_txt('Nora Mayor')
        exp = ['Salto horizontal: 190 cm (Bueno · FitBack 2023)', 'Salto vertical CMJ: 32,5 cm' if False else 'Salto vertical CMJ: 33', '(Medio · Voleibol juvenil élite)', 'Sprint 10 m: 1.95 s (Medio · Voleibol femenino de club)', 'T-Test de agilidad: 11.00 s (Bueno · T-test adultos)']
        miss = [e for e in exp if e not in t and e.replace('.', ',') not in t]
        return ok(not miss, '18 años, rama femenina: horizontal 190 = Bueno (FitBack), CMJ 33 = Medio, 10 m 1,95 = Medio, T-test 11,0 = Bueno, cada uno con su fuente', f'faltan {miss}; texto: {t[:400]}')
    rec('N2', 'N. Normas', 'Nivel con norma por edad (18 años)', 'Atleta F nacida en 2008 con horizontal 190, CMJ 33, 10 m 1,95, T-test 11,0', 'Niveles de la norma de 18 años con la fuente', n2)

    def n3():
        nueva('Nina Juvenil', '2012-03-01')
        imc = pg.inner_text('body').lower(); imc_ok = 'imc para la edad (oms) z +0.3: normal' in imc or 'imc para la edad (oms) z +0,3: normal' in imc
        save(pg); t = nivel_txt('Nina Juvenil')
        exp = ['Salto horizontal: 190 cm (Bueno · FitBack 2023)', 'Sprint 10 m: 1.95 s (Bueno · Voleibol femenino de club)', 'T-Test de agilidad: 11.00 s (Medio)']
        miss = [e for e in exp if e not in t and e.replace('.', ',') not in t]
        return ok(not miss and imc_ok, '14 años: horizontal = Bueno (tabla de 14), 10 m = Bueno (Sub-13 a Sub-16), T-test sin norma usa la referencia interna (Medio); IMC 20,8 → z +0,3 normal (OMS)', f'faltan {miss}; IMC OMS {imc_ok}; texto: {t[:300]}')
    rec('N3', 'N. Normas', 'Norma según la edad (14 años) e IMC OMS', 'Atleta F nacida en 2012 con los mismos valores; peso 60, talla 170', 'Tabla de 14 años; T-test con referencia interna; z de IMC +0,3', n3)

    def n4():
        pg.click('#t-atletas'); pg.wait_for_timeout(300)
        box = pg.locator('details.box', has_text='Referencias de nivel físico')
        if not box.evaluate('e=>e.open'): box.locator('summary').first.click(); pg.wait_for_timeout(300)
        tabla = box.inner_text(); fuentes = all(x in tabla for x in ['FitBack 2023', 'Voleibol juvenil élite', 'Voleibol femenino de club', 'T-test adultos', 'OMS'])
        pg.uncheck('#normon-horizontal'); pg.wait_for_timeout(900)
        t = nivel_txt('Nora Mayor'); interno = 'Salto horizontal: 190 cm (Medio)' in t
        cfg = db_rows(m, UID1, 'config').get('umbrales', {}); guardado = cfg.get('normOn', {}).get('horizontal') is False
        pg.reload(); pg.wait_for_timeout(2500); pg.click('#t-atletas'); pg.wait_for_timeout(300)
        box = pg.locator('details.box', has_text='Referencias de nivel físico'); box.locator('summary').first.click(); pg.wait_for_timeout(300)
        sigue = not pg.is_checked('#normon-horizontal')
        pg.check('#normon-horizontal'); pg.wait_for_timeout(600)
        return ok(fuentes and interno and guardado and sigue, 'Las 4 normas se ven con su fuente; al desmarcar la de salto horizontal se usa la referencia interna (190 = Medio), se guarda en la cuenta y sigue así al recargar', f'fuentes {fuentes}, interno {interno}, guardado {guardado}, tras recargar {sigue}')
    rec('N4', 'N. Normas', 'Desactivar una norma', 'Referencias de nivel físico: desmarcar Salto horizontal; recargar', 'Vuelve a la referencia interna y se recuerda', n4)

    def n5():
        nueva('Olga Adulta', '1998-01-15'); b = pg.inner_text('body').lower()
        return ok('normal' in b and 'imc para la edad (oms)' not in b and not nerr, 'Adulta de 28 años: IMC con categorías de adulto (Normal), sin puntaje OMS; sin errores de página', f'errores {nerr[:2]}')
    rec('N5', 'N. Normas', 'IMC de adulto', 'Atleta nacida en 1998, peso 60, talla 170', 'Categoría de adulto', n5)
    ctx.close()
    browser.close()

json.dump(RESULTS, open(os.path.join(HERE, 'resultados.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
from collections import Counter
print(Counter(r['estado'] for r in RESULTS))
