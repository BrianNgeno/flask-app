from flask import Flask, request, make_response, jsonify, session
from flask_migrate import Migrate
from models import db, User
from flask_restful import Api, Resource
from werkzeug.exceptions import NotFound
from flask_cors import CORS
from flask_bcrypt import Bcrypt

app = Flask(__name__)

CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False
app.secret_key='super_secret'

migrate = Migrate(app, db,render_as_batch=True)
bcrypt = Bcrypt(app)
db.init_app(app)
api = Api(app)



@app.before_request
def check_login():
    if not session['user_id'] \
        and request.endpoint != 'login' \
        and request.endpoint != 'home'\
        and request.endpoint != 'users':
        return {"error":"unauthorized"},401

class Login(Resource):
    def post(self):
        username = request.get_json()['user_name']
        user =  User.query.filter(User.user_name==username).first()
        password = request.get_json()['password']
        if user.authenticate(password):
            session['user_id']= user.id
            return user.to_dict(),200
        
        return  {"error":"username or password is incorrect"},401

class Logout(Resource):
    def delete(self):
        session['user_id']=None
        return {"message":'logged out'},204

api.add_resource(Logout,"/logout", endpoint='logout')
api.add_resource(Login,'/login',endpoint='login')

class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()
        if user:
            return user.to_dict()
        else:
            return {"message":"the current user is unauthorized to access"},401

api.add_resource(CheckSession,'/session/check')

class Home(Resource):

    def get(self):
        header = '<h1>This is the first page</h1>'
        session['user'] = 'moringaschool'
        print("the session cookie set for user is", session.get('user'))
        return make_response(header, 200)

api.add_resource(Home, '/',endpoint='home')

class Users(Resource):
    def get(self):
        users = [user.to_dict() for user in User.query.all()]
        return make_response(jsonify(users), 200)

    def post(self):
        name = request.form.get('name')
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        if not name:
            return make_response(
                {"error": "Name is required to create a user"}, 400
            )
        new_user = User(name=name,user_name=user_name,password_hash=password)
        db.session.add(new_user)
        db.session.commit()
        return make_response(new_user.to_dict(), 201)

api.add_resource(Users, '/users', endpoint='users')

class Single(Resource):
    def get(self, id):
        user = User.query.filter_by(id=id).first()
        if user:
            return make_response(user.to_dict(), 200)
        return make_response(
            {"error": f"The user with id {id} does not exist"}, 404
        )

    def delete(self, id):
        user = User.query.filter_by(id=id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return make_response(
                {"message": "User deleted successfully"}, 200
            )
        return make_response(
            {"error": f"The user with id {id} does not exist"}, 404
        )

    def patch(self, id):
        user = User.query.filter_by(id=id).first()
        if not user:
            return make_response(
                {"error": f"The user with id {id} does not exist"}, 404
            )
        for attr in request.form:
            setattr(user, attr, request.form.get(attr))
        db.session.commit()
        return make_response(user.to_dict(), 200)

api.add_resource(Single, '/users/<int:id>')

@app.errorhandler(NotFound)
def handle_not_found(e):
    return make_response(
        "Not Found: The requested resource does not exist.", 404
    )

app.register_error_handler(404, handle_not_found)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
