from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from models import db, User
from flask_restful import Api, Resource
from werkzeug.exceptions import NotFound

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db,render_as_batch=True)
db.init_app(app)
api = Api(app)

class Home(Resource):
    def get(self):
        header = '<h1>This is the first page</h1>'
        return make_response(header, 200)

api.add_resource(Home, '/')

class Users(Resource):
    def get(self):
        users = [user.to_dict() for user in User.query.all()]
        return make_response(jsonify(users), 200)

    def post(self):
        name = request.form.get('name')
        if not name:
            return make_response(
                {"error": "Name is required to create a user"}, 400
            )
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return make_response(new_user.to_dict(), 201)

api.add_resource(Users, '/users')

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
