import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
db = setup_db(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# CORS Headers 
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response

db_drop_and_create_all()


## ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    """Retrieve the entire list of drinks in the database
    No Authorization required
    Keyword arguments:
    """
    drinks = Drink.query.order_by(Drink.id).all()
    data = {
      'success': True,
      'drinks': [drink.short() for drink in drinks]
    }
    return jsonify(data), 200

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    """Retrieve the entire list of drinks in the database
    Authorization required 'get:drinks-detail'
    Keyword arguments:
    """
    drinks = Drink.query.order_by(Drink.id).all()
    data = {
      'success': True,
      'drinks': [drink.long() for drink in drinks]
    }
    return jsonify(data), 200

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(payload):
    """Retrieve the entire list of drinks in the database
    Authorization required 'post:drinks'
    Keyword arguments:
    """
    body = request.get_json()
    title = body.get('title',None)
    recipe = body.get('recipe',None)
    if title is None or recipe is None:
        abort(422)
    error = False
    result=None
    try:
        drink = Drink(title=title, recipe=json.dumps(recipe))
        result = drink.long()
        drink.insert()
    except:
        print("error")
        db.session.rollback()
        error=True
    finally:
        db.session.close()    
    if error:
        abort(500)
    return jsonify({'success':True,'drinks': [result]}),200    

@app.route('/drinks/<int:id>',methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_question(payload,id):
    """Patch the drink
    Authorization required 'patch:drinks'
    Keyword arguments:
    id -- the integer id of the drink to delete
    """
    drink = Drink.query.get(id)
    if drink is None:
      abort(404)
    body = request.get_json()
    title = body.get('title',None)
    recipe = body.get('recipe',None)
    if title is None and recipe is None:
        abort(422)
    error = False
    result = None
    if title is not None:
        drink.title = title
    if recipe is not None:
        drink.recipe = json.dumps(recipe)
    try:
        drink.update()
        result = drink.long()
    except:
        db.session.rollback()
        error=True
    finally:
        db.session.close()    
    if error:
        abort(500)
    return jsonify({'success':True,'drinks': [result]}),200   
    
@app.route('/drinks/<int:id>',methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_question(payload,id):
    """Delete the drink
    Authorization required 'delete:drinks'
    Keyword arguments:
    id -- the integer id of the drink to delete
    """
    drink = Drink.query.get(id)
    if drink is None:
      abort(404)
    error=False
    try:
        drink.delete()
    except:
        db.session.rollback()
        error=True
    finally:
        db.session.close()
    if error:
        abort(500)
    data = {
        'success':True,
        'delete': id
        }
    return jsonify(data),200


## Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

@app.errorhandler(500)
def server_error(error):
    data = {
      'success':False,
      'error': 500,
      'message': 'Internal Server Error'
    }
    return jsonify(data), 500


@app.errorhandler(AuthError)
def auth_error(e):
    print(e)
    data = {
      'success':False,
      'error': e.status_code,
      'message': e.error['code']
    }
    return jsonify(data), e.status_code


