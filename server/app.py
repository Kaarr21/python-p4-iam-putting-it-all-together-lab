from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    # Relationship to recipes - this creates a 'recipes' attribute that returns a list
    recipes = db.relationship("Recipe", backref="user", lazy=True, cascade="all, delete-orphan")

    # Exclude the user data from recipe serialization to prevent circular references
    serialize_rules = ("-recipes.user", "-_password_hash")

    def __init__(self, username, image_url=None, bio=None):
        self.username = username
        self.image_url = image_url
        self.bio = bio

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hash is not readable.")

    @password_hash.setter
    def password_hash(self, password):
        if not password:
            raise ValueError("Password is required.")
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates('username')
    def validate_username(self, key, username):
        if not username or username.strip() == "":
            raise ValueError("Username is required.")
        return username


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Exclude the recipe data from user serialization to prevent circular references
    serialize_rules = ("-user.recipes",)

    def __init__(self, title, instructions, minutes_to_complete, user_id):
        self.title = title
        self.instructions = instructions
        self.minutes_to_complete = minutes_to_complete
        self.user_id = user_id

    @validates('title')
    def validate_title(self, key, title):
        if not title or title.strip() == "":
            raise ValueError("Title is required.")
        return title

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions.strip()) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return instructions
        
    @validates('minutes_to_complete')
    def validate_minutes(self, key, minutes):
        if type(minutes) is not int or minutes <= 0:
            raise ValueError("Minutes to complete must be a positive integer.")
        return minutes
        