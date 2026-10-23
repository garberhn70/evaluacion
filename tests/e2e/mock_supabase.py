"""Supabase simulado para pruebas de navegador.

Reproduce lo que el cliente necesita: Auth (contraseña, usuario, salida),
PostgREST sobre app_records con aislamiento por usuario (simula RLS) y la RPC
activate_device_license con la misma lógica del schema.sql. NO es el Supabase real:
sirve para probar el código del navegador, no las políticas reales de la base.
"""
import base64, json, time, urllib.parse, uuid

U = 'https://hpowcgmaqqbmijnuktpj.supabase.co'


def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip('=')


def jwt(uid, email):
    now = int(time.time())
    return b64({'alg': 'HS256', 'typ': 'JWT'}) + '.' + b64({'sub': uid, 'email': email, 'role': 'authenticated', 'aud': 'authenticated', 'exp': now + 3600, 'iat': now}) + '.firma-de-prueba'


class MockSupabase:
    def __init__(self):
        self.users = {
            'prueba1@example.com': {'password': 'Clave-Prueba-1', 'id': str(uuid.UUID(int=1))},
            'prueba2@example.com': {'password': 'Clave-Prueba-2', 'id': str(uuid.UUID(int=2))},
        }
        self.tokens = {}
        self.rows = {}  # (user_id, collection, record_id) -> data
        self.licenses = {
            'LIC-PRUEBA-VALIDA-2026': {'status': 'active', 'expires': time.time() + 86400 * 365, 'owner': None, 'max': {'desktop': 1, 'mobile': 1}},
            'LIC-PRUEBA-VENCIDA': {'status': 'active', 'expires': time.time() - 86400, 'owner': None, 'max': {'desktop': 1, 'mobile': 1}},
        }
        self.devices = []  # dicts license, user, device_id, type, revoked
        self.fail = set()  # 'select', 'upsert', 'delete', 'rpc', 'all'
        self.log = []

    # ---------- utilidades ----------
    def user_from(self, req):
        h = req.headers.get('authorization', '')
        tok = h.split(' ', 1)[1] if h.lower().startswith('bearer ') else ''
        return self.tokens.get(tok)

    def session(self, email):
        u = self.users[email]
        tok = jwt(u['id'], email)
        self.tokens[tok] = {'id': u['id'], 'email': email}
        user = {'id': u['id'], 'email': email, 'aud': 'authenticated', 'role': 'authenticated', 'app_metadata': {}, 'user_metadata': {}, 'created_at': '2026-10-23T00:00:00Z'}
        return {'access_token': tok, 'token_type': 'bearer', 'expires_in': 3600, 'expires_at': int(time.time()) + 3600, 'refresh_token': 'r-' + u['id'], 'user': user}

    @staticmethod
    def reply(route, status, body=None):
        route.fulfill(status=status, content_type='application/json',
                      headers={'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*',
                               'access-control-expose-headers': 'content-range'},
                      body='' if body is None else json.dumps(body))

    def user_rows(self, uid):
        return [{'user_id': k[0], 'collection': k[1], 'record_id': k[2], 'data': v} for k, v in self.rows.items() if k[0] == uid]

    # ---------- enrutador ----------
    def handle(self, route, req):
        if req.method == 'OPTIONS':
            return self.reply(route, 200, {})
        if 'all' in self.fail:
            return route.abort('internetdisconnected')
        url = urllib.parse.urlparse(req.url)
        path, q = url.path, urllib.parse.parse_qs(url.query)
        self.log.append((req.method, path, url.query[:120]))
        body = {}
        if req.post_data:
            try:
                body = json.loads(req.post_data)
            except Exception:
                body = {}
        # ---- Auth ----
        if path == '/auth/v1/token':
            gt = q.get('grant_type', [''])[0]
            if gt == 'password':
                u = self.users.get(body.get('email', ''))
                if not u or u['password'] != body.get('password'):
                    return self.reply(route, 400, {'code': 'invalid_credentials', 'error': 'invalid_grant', 'error_description': 'Invalid login credentials', 'msg': 'Invalid login credentials'})
                return self.reply(route, 200, self.session(body['email']))
            if gt == 'refresh_token':
                rt = body.get('refresh_token', '')
                for email, u in self.users.items():
                    if rt == 'r-' + u['id']:
                        return self.reply(route, 200, self.session(email))
                return self.reply(route, 400, {'error': 'invalid_grant', 'msg': 'Invalid Refresh Token'})
        if path == '/auth/v1/user':
            u = self.user_from(req)
            if not u:
                return self.reply(route, 401, {'msg': 'invalid JWT'})
            return self.reply(route, 200, {'id': u['id'], 'email': u['email'], 'aud': 'authenticated', 'role': 'authenticated'})
        if path == '/auth/v1/logout':
            return route.fulfill(status=204, headers={'access-control-allow-origin': '*'}, body='')
        if path in ('/auth/v1/signup', '/auth/v1/recover'):
            return self.reply(route, 200, {})
        # ---- RPC ----
        if path == '/rest/v1/rpc/activate_device_license':
            if 'rpc' in self.fail:
                return self.reply(route, 500, {'message': 'Error interno simulado'})
            u = self.user_from(req)
            if not u:
                return self.reply(route, 401, {'message': 'permission denied for function activate_device_license'})
            code, dev, typ = body.get('p_license_code'), body.get('p_device_id') or '', body.get('p_device_type')
            if typ not in ('desktop', 'mobile') or len(dev) < 12:
                return self.reply(route, 200, {'ok': False, 'message': 'Dispositivo inválido.'})
            lic = self.licenses.get(code)
            if not lic:
                return self.reply(route, 200, {'ok': False, 'message': 'Código de licencia no válido.'})
            if lic['status'] not in ('active', 'grace_period'):
                return self.reply(route, 200, {'ok': False, 'message': 'Licencia suspendida o no activa.'})
            if lic['expires'] < time.time():
                return self.reply(route, 200, {'ok': False, 'message': 'Licencia vencida o fuera de vigencia.'})
            if lic['owner'] and lic['owner'] != u['id']:
                return self.reply(route, 200, {'ok': False, 'message': 'La licencia pertenece a otra cuenta.'})
            lic['owner'] = lic['owner'] or u['id']
            n = sum(1 for d in self.devices if d['license'] == code and d['user'] == u['id'] and d['type'] == typ and not d['revoked'] and d['device_id'] != dev)
            if n >= lic['max'][typ]:
                return self.reply(route, 200, {'ok': False, 'message': 'Ya se alcanzó el límite de dispositivos de este tipo. Libera uno o contacta al administrador.'})
            if not any(d['license'] == code and d['device_id'] == dev for d in self.devices):
                self.devices.append({'license': code, 'user': u['id'], 'device_id': dev, 'type': typ, 'revoked': False})
            return self.reply(route, 200, {'ok': True, 'status': lic['status']})
        # ---- app_records ----
        if path == '/rest/v1/app_records':
            u = self.user_from(req)
            uid = u['id'] if u else None
            filt = {k: v[0][3:] for k, v in q.items() if v and v[0].startswith('eq.')}
            likes = {k: v[0][5:] for k, v in q.items() if v and v[0].startswith('like.')}
            import fnmatch
            def match(k):
                d = {'user_id': k[0], 'collection': k[1], 'record_id': k[2]}
                return k[0] == uid and all(d[f] == val for f, val in filt.items() if f in d) and all(fnmatch.fnmatch(d[f], val.replace('%', '*')) for f, val in likes.items() if f in d)
            if req.method == 'GET':
                if 'select' in self.fail:
                    return self.reply(route, 500, {'message': 'Error interno simulado al leer'})
                out = [r for r in self.user_rows(uid) if match((r['user_id'], r['collection'], r['record_id']))]
                return self.reply(route, 200, out)
            if req.method == 'POST':
                if 'upsert' in self.fail:
                    return route.abort('internetdisconnected')
                rows = body if isinstance(body, list) else [body]
                for r in rows:
                    if not uid or r.get('user_id') != uid:
                        return self.reply(route, 403, {'code': '42501', 'message': 'new row violates row-level security policy for table "app_records"'})
                for r in rows:
                    if r.get('collection') not in ('atletas', 'pruebas', 'evaluaciones', 'config'):
                        return self.reply(route, 400, {'code': '23514', 'message': 'violates check constraint'})
                for r in rows:
                    self.rows[(r['user_id'], r['collection'], r['record_id'])] = r['data']
                return route.fulfill(status=201, headers={'access-control-allow-origin': '*'}, body='')
            if req.method == 'PATCH':
                for k in [k for k in self.rows if match(k)]:
                    self.rows[k] = body.get('data', self.rows[k])
                return route.fulfill(status=204, headers={'access-control-allow-origin': '*'}, body='')
            if req.method == 'DELETE':
                if 'delete' in self.fail:
                    return route.abort('internetdisconnected')
                for k in [k for k in self.rows if match(k)]:
                    del self.rows[k]
                return route.fulfill(status=204, headers={'access-control-allow-origin': '*'}, body='')
        if path in ('/rest/v1/licenses', '/rest/v1/license_devices'):
            return self.reply(route, 200, [])
        return self.reply(route, 404, {'message': 'ruta no simulada ' + path})
