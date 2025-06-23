#!/usr/bin/env python3

from flask import Flask, request, session, jsonify
from flask_restful import Migrate
from sqlalchemy.exc import Int
from sqlalchemy.orm import validates
from config import app, db, api
from models import User, Recipe
class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return {'errors': ['Username and password are required']}, 422

        try:
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            new_user.password_hash = password
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id

            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username must be unique"]}, 422
        except ValueError as ve:
            return {"errors": [str(ve)]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio
                }, 200
        return {}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }, 200

        return {"errors": ["Invalid username or password"]}, 401

class Logout(Resource):
    def delete(self):
        session.pop("user_id", None)
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"errors": ["Unauthorized"]}, 401

        try:
            user = User.query.get(user_id)
            if user:
                return [recipe.to_dict() for recipe in user.recipes], 200
            else:
                return {"errors": ["User not found"]}, 404
        except Exception as e:
            return {"errors": [str(e)]}, 500

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"errors": ["Unauthorized"]}, 401

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes = data.get("minutes_to_complete")

        try:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes,
                user_id=user_id
            )

            db.session.add(new_recipe)
            db.session.commit()
            return new_recipe.to_dict(), 201
        except ValueError as ve:
            return {"errors": [str(ve)]}, 422
        except Exception as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 500

# Register routes
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
    