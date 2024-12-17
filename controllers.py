from flask import request, redirect, jsonify
from flask_restful import Api, Resource

from services.auth_service import AuthService
from services.mails_service import MailsService

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
                token, access_token = auth_service.callback(code)
                mails_service.fetch_emails(access_token=access_token)
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
            return jsonify(mails_service.fetch_emails(access_token=access_token))
        
    api.add_resource(AuthController, '/auth/<string:action>')
    api.add_resource(EmailController, '/emails')