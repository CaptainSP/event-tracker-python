from flask import request, redirect, jsonify
from flask_restful import Api, Resource

from services.auth_service import AuthService
from services.mails_service import MailsService
from flask import send_from_directory


def initialize_routes(app,redis_conn,pg_conn):
    api = Api(app)
    
    auth_service = AuthService(pg_conn)
    mails_service = MailsService(app,redis_conn,pg_conn)
    
    class AuthController(Resource):
        def get(self, action):
            if action == 'login':
                return redirect(auth_service.sign_in().get('url'), code=302)
            elif action == 'callback':
                code = request.args.get('code')
                token, user, access_token = auth_service.callback(code)
                mails_service.fetch_emails(access_token=access_token,user=user)
                return redirect(f'http://localhost:4200/login?token={token}', code=302)
            return jsonify({'error': 'Action not recognized'})

    class EmailController(Resource):
        def get(self):
            headers = request.headers
            jwt = headers.get('Authorization')
            if not jwt:
                return jsonify({'error': 'Unauthorized'})
            jwt_token = jwt.split(' ')[1]
            parsed_jwt = auth_service.decode_jwt(jwt_token)
            sub = parsed_jwt.get('sub')
            cursor = pg_conn.cursor()
            cursor.execute(f"SELECT * FROM users WHERE id = '{sub}'")
            user = cursor.fetchone()
            cursor.close()
            if not user:
                return jsonify({'error': 'Unauthorized'})
            access_token = user[2]
            print(user[1])
            return jsonify(mails_service.fetch_emails(access_token=access_token,user=user))
        
    class EventsController(Resource):
        def get(self):
                headers = request.headers
                jwt = headers.get('Authorization')
                if not jwt:
                    return jsonify({'error': 'Unauthorized'})
                jwt_token = jwt.split(' ')[1]
                parsed_jwt = auth_service.decode_jwt(jwt_token)
                sub = parsed_jwt.get('sub')
                cursor = pg_conn.cursor()
                cursor.execute('''SELECT * FROM "user" WHERE "id" = %s''', (sub,))
                user = cursor.fetchone()
                cursor.close()
                if not user:
                    return jsonify({'error': 'Unauthorized'})
                return jsonify(mails_service.fetch_events_from_db(user[0]))
     
    class TagsController(Resource):
        def get(self):
            cursor = pg_conn.cursor()
            cursor.execute('SELECT * FROM tag')
            tags = cursor.fetchall()
            cursor.close()
            return jsonify(tags)     
        
    class ServeAngularApp(Resource):
        def get(self):
            return send_from_directory('public', 'index.html')
    
    class ServeAngularPages(Resource):
        def get(self, page):
            should_serve_file = page.endswith('.js') or page.endswith('.css') or page.endswith('.ico') or page.endswith('.json')
            if should_serve_file:
                return send_from_directory('public', page)
            return send_from_directory('public', 'index.html')        
    api.add_resource(AuthController, '/auth/<string:action>')
    api.add_resource(EmailController, '/emails')
    api.add_resource(EventsController, '/events')
    api.add_resource(TagsController, '/tags')
    api.add_resource(ServeAngularApp, '/')
    api.add_resource(ServeAngularPages, '/<string:page>')