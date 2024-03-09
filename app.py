from flask import Flask , request
from flask_restx import Api, Resource, fields
from werkzeug.middleware.proxy_fix import ProxyFix
import bcrypt
from datetime import datetime, timedelta
import jwt
SECRET_KEY = 'ClaveSuperSecreta'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='Delivery Service',
    description='A simple Delivery Service API',
)
UsersNS = api.namespace('users', description='userInfo operations')
CardsNS = api.namespace('cars', description='trajectory information')


users = api.model('Users', {
    'username': fields.String(required=True, description=''),
    'password': fields.String(required=True, description=''),

})

cards = api.model('Cards', {
    'number': fields.String(required=True, description=''),
    'cvv': fields.String(required=True, description=''),
    'date': fields.Date(required=True, description='',dt_format='rfc822'),

})


def encrypt_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def generate_jwt_token(user_name):
    # Fecha y hora de expiración del token (puedes ajustar el tiempo según tus necesidades)
    expiration = datetime.utcnow() + timedelta(days=1)  # Token válido por 1 día

    # Crear payload del token con la información del usuario
    payload = {
        'user_name': user_name,
        'exp': expiration
    }

    # Generar token JWT
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return token

def verify_jwt_token(token):
    try:
        # Verificar y decodificar el token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # Token expirado
        return None
    except jwt.InvalidTokenError:
        # Token inválido
        return None

#CustomerService
class usersDAO(object):
    def __init__(self):
        self.counter = 0
        self.users = [
            {
                'username': 'admin',
                'password': encrypt_password('admin')
            }
        ]

    def create(self,data):
        user = data
        new_user = {
            'username':user['username'],
            'password': encrypt_password(user['password']),
        }
        for userRegistered in self.users:
            if userRegistered['username'] == user['username']:
                api.abort(400,"Ya existe el usuario {}".format(user['username']))

        self.users.append(new_user)
        return new_user 

    def login(self,data):
        user = data
        for userRegistered in self.users:
            print(userRegistered)
            if userRegistered['username'] == user['username']:
                password = check_password(user['password'],userRegistered['password'])
                token = generate_jwt_token(userRegistered['username'])  
                print(token)
                return {'token': token}, 200
        return {'mensaje': 'Credenciales inválidas'}, 401    


DAOUSER = usersDAO()

@UsersNS.route('/')
class UsersService(Resource):
    '''Shows a list of all customers'''
    @UsersNS.doc('list customers info')
    @UsersNS.marshal_list_with(users)
    def get(self):
        '''List customer information'''
        return DAOUSER.users

    @UsersNS.doc('create_customer')
    @UsersNS.expect(users)
    @UsersNS.marshal_with(users, code=200)
    def post(self):
        '''Create customer information'''
        return DAOUSER.create(api.payload), 200

@UsersNS.route('/login')
class usersService(Resource):
    @UsersNS.doc('login')
    @UsersNS.expect(users)
    def post(self):
        '''Loguear usuario'''
        user = api.payload
        token, status_code = DAOUSER.login(user)
        return {'token': token}, status_code

if __name__ == '__main__':
    app.run(debug=True)

