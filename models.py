from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import Bcrypt


# Consistent metadata usage


bcrypt = Bcrypt()
metadata = MetaData(naming_convention={'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s'})
db = SQLAlchemy(metadata=metadata)

# Association table for many-to-many relationship
user_lifts = db.Table(
    'user_lifts',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('lift_id', db.Integer, db.ForeignKey('lifts.id'), primary_key=True)
)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules = ('-product.user', '-lift.users')
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    user_name = db.Column(db.String,nullable=True, unique=True)
    _password_hash = db.Column(db.String, nullable=False)
    product = db.relationship('Product', back_populates='user')
    lift = db.relationship('Lift', secondary=user_lifts, back_populates='users')

    @validates('name')
    def validate_name(self,key,value):
        if len(value) < 3:
            ValueError('name must be 3 characters and above')
        return value

    @validates('user_name')
    def validate_username(self,key,value):
        if '_' not in value:
            ValueError("username must include a _")
        return value


    @hybrid_property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode("utf-8")

    def authenticate(self,password):
        return bcrypt.check_password_hash(self._password_hash,password.encode('utf-8'))



class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'
    serialize_rules = ('-user.product',)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Integer,db.CheckConstraint('price >= 30'), nullable=False)
    discount_price = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='product')

    __table_args__ = (db.CheckConstraint('(discount_price is NULL) or (discount_price < price)'),)

class Lift(db.Model, SerializerMixin):
    __tablename__ = 'lifts'
    serialize_rules = ('-users.lift',)
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer)
    users = db.relationship('User', secondary=user_lifts, back_populates='lift')
