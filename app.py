# Miguel Angelo Bondad
# Python resource-based REST API using Flask
# Recipe Sharing Platform API

# modules to import
from flask import Flask, render_template
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
import urllib, pyodbc

# init app & api
app = Flask(__name__)
api = Api(app)

# params for app connection to mssql
# change params if necessary
driver_name = "SQL Server"
server_name = "tcp:localhost,1433" # default
database_name = "TempDB"
Uid = 'SA'
SA_Password = 'password123!'

# setup parameters for mssql connection
params = urllib.parse.quote_plus(f"DRIVER={driver_name};SERVER={server_name};DATABASE={database_name};Uid={Uid};Password={SA_Password};Trusted_Certificate=yes;") # attempt to connect to Dockerized MSSQL Server
# params = urllib.parse.quote_plus(f"DRIVER={driver_name};SERVER={server_name};DATABASE={database_name};Trusted_Certificate=yes;") # Use for local MSSQL Server Database (Windows Authentication)

app.config['SQLALCHEMY_DATABASE_URI'] = f'mssql+pyodbc:///?odbc_connect={params}' # config to connect to mssql server
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///database.db' # config to create local sqlite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Table for Recipe
class RecipeModel(db.Model):
    __tablename__ = 'recipe_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.String(500), nullable=False)
    steps = db.Column(db.String(500), nullable=False)
    prep_time_in_minutes = db.Column(db.Integer, nullable=False)
    comments = db.relationship('CommentModel', backref='recipe_table')
    ratings = db.relationship('RatingModel', backref='recipe_table')

    def __repr__(self):
        return f"Recipe(name={self.name},ingredients={self.ingredients},steps={self.steps},prep_time_in_minutes={self.prep_time_in_minutes})"

# Table model for Comments
class CommentModel(db.Model):
    __tablename__ = 'comment_table'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(200))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe_table.id'))
    
    def __repr__(self):
        return f"Comment(id={self.id},comment={self.comment},recipe_id={self.recipe_id})"

# Table model for Ratings
class RatingModel(db.Model):
    __tablename__ = 'rating_table'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe_table.id'))
    
    def __repr__(self):
        return f"Rating(id={self.id},rating={self.rating},recipe_id={self.recipe_id})"

# register the database
# with app.app_context():
db.create_all() # this works only on local mssql server set up and other sql platforms (sqlite.db, mysql, etc.)
                # cannot figure out how to setup in dockerized mssql server

# For parsing recipe post requests
recipe_post_args = reqparse.RequestParser()
recipe_post_args.add_argument("name", type=str, required=True)
recipe_post_args.add_argument("ingredients", type=str, required=True)
recipe_post_args.add_argument("steps", type=str, required=True)
recipe_post_args.add_argument("prep_time_in_minutes", type=int, required=True)

# For parsing comment post requests
comment_post_args = reqparse.RequestParser()
comment_post_args.add_argument("comment", type=str, required=True)

# For parsing rating post requests
rating_post_args = reqparse.RequestParser()
rating_post_args.add_argument("rating", type=int, required=True)

# For proper recipe post formatting
recipe_resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'ingredients': fields.String,
    'steps': fields.String,
    'prep_time_in_minutes': fields.Integer,
}

# For proper comment post formatting
comment_resource_fields = {
    'id': fields.Integer,
    'comment': fields.String,
    'recipe_id': fields.Integer
}

# For proper comment post formatting
rating_resource_fields = {
    'id': fields.Integer,
    'rating': fields.Integer,
    'recipe_id': fields.Integer
}


# Outputs from endpoints will be in JSON formatting
# API Endpoints handling
# Resource for Recipe list
class RecipeList(Resource):
    # GET /recipe/ endpoint
    def get(self):
        recipes = RecipeModel.query.order_by(RecipeModel.id.desc()).all() # get all recipes, sorted by most recent (highest recipe_id)
        result = {}     # output initialization
        for recipe in recipes:
            result[recipe.id] = {
                                 'name': recipe.name, 
                                 'ingredients': recipe.ingredients,
                                 'steps': recipe.steps, 
                                 'prep_time_in_minutes': recipe.prep_time_in_minutes
                                }
        return result
    # POST /recipe endpoint
    @marshal_with(recipe_resource_fields)
    def post(self):
        args = recipe_post_args.parse_args()
        recipe = RecipeModel(name=args['name'],
                             ingredients=args['ingredients'], 
                             steps=args['steps'], 
                             prep_time_in_minutes=args['prep_time_in_minutes']
                             )
        db.session.add(recipe)
        db.session.commit()
        return recipe, 201
        
# Resource for Recipe
class Recipe(Resource):
    # GET /recipe/<id> endpoint
    @marshal_with(recipe_resource_fields)
    def get(self, recipe_id):
        result = RecipeModel.query.filter_by(id=recipe_id).one_or_none()
        if result is None:
            abort(404, message= f"Could not find recipe with id:{recipe_id}")
        return result
    
    # PUT /recipe/<id> endpoint
    @marshal_with(recipe_resource_fields) 
    def put(self,recipe_id):
        args = recipe_post_args.parse_args()
        recipe = RecipeModel.query.filter_by(id=recipe_id).one_or_none()
        if recipe is None:
            abort(404, message= f"Could not find recipe with id:{recipe_id}")
        if args['name']:
            recipe.name = args['name']
        if args['ingredients']:
            recipe.ingredients = args['ingredients']
        if args['steps']:
            recipe.steps = args['steps']
        if args['prep_time_in_minutes']:
            recipe.prep_time_in_minutes = args['prep_time_in_minutes']
        db.session.commit()
        return recipe

    # DELETE /recipe/<id> endpoint
    def delete(self,recipe_id):
        result = RecipeModel.query.filter_by(id=recipe_id).first()
        db.session.delete(result)
        db.session.commit()
        return 'Recipe Deleted', 204

# Resource for Comment list
class Comment(Resource):
    # POST /recipe/<id>/comments/ endpoint
    @marshal_with(comment_resource_fields)
    def post(self, recipe_id):
        recipe = RecipeModel.query.filter_by(recipe_id=recipe_id).one_or_none()
        if recipe is None:
            abort(404, message= "No such recipe from recipe_id.")
        args = comment_post_args.parse_args()
        comment = CommentModel(comment = args["comment"],
                               recipe_id = recipe_id)
        db.session.add(comment)
        db.session.commit()
        return comment, 201
    
    # GET /recipe/<id>/comments/ endpoint
    def get(self,recipe_id):
        # check if recipe from recipe_id exists
        recipe = RecipeModel.query.filter_by(id=recipe_id).one_or_none()
        if recipe is None:
            abort(404, message= "No such recipe from recipe_id.")
        comments = CommentModel.query.filter_by(recipe_id=recipe_id)
        if comments is None:
            abort(404, message= "No comments found for this recipe.")
        result = {}
        for comment in comments:
            result[comment.id] = {'comment': comment.comment,'id': comment.id}
        return result

# Resource for Rating
class Rating(Resource):
    # POST /recipe/<id>/ratings/ endpoint
    @marshal_with(rating_resource_fields)
    def post(self, recipe_id):
        # check if recipe from recipe_id exists
        recipe = RecipeModel.query.filter_by(recipe_id=recipe_id).one_or_none()
        if recipe is None:
            abort(404, message= "No such recipe from recipe_id.")
        # create rating entry for recipe
        args = rating_post_args.parse_args()
        # check if rating is within 1-5
        if args['rating'] > 5 or args['rating'] < 1:
            abort(404, message= "Use integers valued from 1 to 5 only.")
        rating = RatingModel(rating = args["rating"],
                               recipe_id = recipe_id)
        db.session.add(rating)
        db.session.commit()
        return rating, 201

# Resources initialization    
api.add_resource(RecipeList, "/recipes/")
api.add_resource(Recipe, "/recipes/<int:recipe_id>/")
api.add_resource(Comment, "/recipes/<int:recipe_id>/comments/")
api.add_resource(Rating, "/recipes/<int:recipe_id>/ratings/")

#bonus attempt for ui
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True) # run in debug mode
    # app.run(host='0.0.0.0', port=5000) # run in docker container
