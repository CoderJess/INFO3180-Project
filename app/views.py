"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file creates your application.
"""

from app import app, db
from flask import render_template, request, jsonify, send_file
from app.models import User, Profile, Favourite
from sqlalchemy import func
import os
from app import app, db, csrf
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
    send_from_directory,
    jsonify,
)
from werkzeug.utils import secure_filename
from app.models import User, Profile, Favourite
from app.forms import LoginForm, ProfileForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash

from flask_wtf.csrf import generate_csrf

from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
from sqlalchemy.exc import SQLAlchemyError

##Helper Function

blacklisted_tokens = set()


def create_token(user_id):  # jwt token
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=6),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):  # jwt token
    return jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])


def jwt_required(f):  ##jwt required decorator to attach to the relevant routes
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"message": "Missing token"}), 401

        try:
            token = auth_header.split(" ")[1]  # "Bearer <token>"

            # Check if the token is blacklisted
            if token in blacklisted_tokens:
                return (
                    jsonify(
                        {"message": "Token has been blacklisted. Please log in again."}
                    ),
                    401,
                )

            data = decode_token(token)
            user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except Exception as e:
            return jsonify({"message": "Invalid token"}), 401

        return f(user_id, *args, **kwargs)

    return wrapper


####
####
####

# this is the route for the index page
# and the static files (assets) folder
# this is where the vue app will be served from
# the vue app will be served from the index.html file in the static folder


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/assets/<path:filename>")
def send_assets(filename):
    """Serve static files from the assets directory."""
    return app.send_static_file(os.path.join("assets", filename))


@app.route("/<path:filename>")
def send_favicon(filename):
    """Serve static file icon from the static directory."""
    return app.send_static_file(filename)


####
####
####


###
# Routing for application.
###


@app.route("/api/register", methods=["POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():

        try:
            username = form.username.data
            password = form.password.data
            name = form.name.data
            email = form.email.data

            photo = form.photo.data
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            user = User(username, password, name, email, filename)

            db.session.add(user)
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "User registered successfully",
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "name": user.name,
                            "email": user.email,
                            "photo": filename,
                        },
                    }
                ),
                201,
            )

        except SQLAlchemyError as e:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "message": "Something went wrong while saving to the database.",
                        "error": str(e.__dict__.get("orig")),
                    }
                ),
                500,
            )
    return (
        jsonify(
            {
                "errors": form.errors,
                "message": "User registration failed due to validation errors.",
            }
        ),
        400,
    )


@app.route(
    "/api/csrf-token", methods=["GET"]
)
def get_csrf():
    return jsonify({"csrf_token": generate_csrf()})


@app.route("/uploads/<filename>", methods=["GET"])
def get_image(filename):
    upload_folder = os.path.join(os.getcwd(), app.config["UPLOAD_FOLDER"])

    return send_from_directory(upload_folder, filename)


@app.route("/api/auth/login", methods=["POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user is not None and check_password_hash(user.password, password):

            token = create_token(user.id)

            return (
                jsonify(
                    {
                        "message": "Login successful",
                        "user": {
                            "id": user.id,
                            "username": user.username,                       
                        },
                        "token": token,
                    }
                ),
                200,
            )
        else:
            return jsonify({"message": "Invalid username or password"}), 401
    return (
        jsonify(
            {
                "errors": form.errors,
                "message": "User login failed due to validation errors.",
            }
        ),
        400,
    )


@csrf.exempt
@app.route("/api/auth/logout", methods=["POST"])
@jwt_required
def logout(user_id):
    # Get the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"message": "Missing token"}), 401

    token = auth_header.split(" ")[1]  # "Bearer <token>"

    # Add the token to the blacklist
    blacklisted_tokens.add(token)

    return jsonify({"message": f"Logout successful for User {user_id}"}), 200


@app.route("/api/profiles", methods=["GET"])
@csrf.exempt
@jwt_required
def get_all_profiles(user_id):

    results = (
        db.session.query(Profile, User)
        .join(User, Profile.user_id_fk == User.id)
        .filter(User.id != user_id)
        .order_by(Profile.created_at.desc())
        .all()
    )

    profiles_with_user_info = []
    for profile, user in results:
        profiles_with_user_info.append(
            {
                "id": profile.id,
                "user_id": user.id,
                "description": profile.description,
                "parish": profile.parish,
                "biography": profile.biography,
                "sex": profile.sex,
                "race": profile.race,
                "birth_year": profile.birth_year,
                "height": profile.height,
                "fav_cuisine": profile.fav_cuisine,
                "fav_colour": profile.fav_colour,
                "fav_school_sibject": profile.fav_school_subject,
                "political": profile.political,
                "religious": profile.religious,
                "family_oriented": profile.family_oriented,
                "username": user.username,
                "photo": user.photo,
                "date_joined": user.date_joined.isoformat(),
                "profile_created": profile.created_at.isoformat(),
            }
        )

    return jsonify(profiles_with_user_info), 200


@app.route("/api/profiles", methods=["POST"])
def create_profile():

    form = ProfileForm()

    if form.validate_on_submit:

        user_id = form.user_id.data

        # Check if user already has 3 profiles
        profile_count = Profile.query.filter_by(user_id_fk=user_id).count()
        if profile_count >= 3:
            return jsonify({"message": "You can only create up to 3 profiles."}), 400

        description = form.description.data
        parish = form.parish.data
        biography = form.biography.data
        sex = form.sex.data
        race = form.race.data
        birth_year = form.birth_year.data
        height = form.height.data
        fav_cuisine = form.fav_cuisine.data
        fav_colour = form.fav_colour.data
        fav_school_subject = form.fav_school_subject.data
        political = form.political.data
        religious = form.religious.data
        family_oriented = form.family_oriented.data

        profile = Profile(
            user_id,
            description,
            parish,
            biography,
            sex,
            race,
            birth_year,
            height,
            fav_cuisine,
            fav_colour,
            fav_school_subject,
            political,
            religious,
            family_oriented,
        )

        db.session.add(profile)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Profile created successfully",
                    "profile": profile.to_dict(),
                }
            ),
            201,
        )

    return (
        jsonify(
            {
                "errors": form.errors,
                "message": "User login failed due to validation errors.",
            }
        ),
        400,
    )

# Get details of a specific profile
@app.route("/api/profiles/<int:profile_id>", methods=["GET"])
@csrf.exempt
@jwt_required
def get_profile(user_id, profile_id):
    print("get_profile route was reached")
    result = (
        db.session.query(Profile, User)
        .join(User, Profile.user_id_fk == User.id)
        .filter(Profile.id == profile_id)
        .first()
    )

    if not result:
        return jsonify({"message": "Profile not found."}), 404

    profile, user = result

    profile_data = {
        "id": profile.id,
        "user_id": user.id,
        "description": profile.description,
        "parish": profile.parish,
        "biography": profile.biography,
        "sex": profile.sex,
        "race": profile.race,
        "birth_year": profile.birth_year,
        "height": profile.height,
        "fav_cuisine": profile.fav_cuisine,
        "fav_colour": profile.fav_colour,
        "fav_school_sibject": profile.fav_school_subject,
        "political": profile.political,
        "religious": profile.religious,
        "family_oriented": profile.family_oriented,
        "username": user.username,
        "photo": user.photo,
        "date_joined": user.date_joined.isoformat(),
        "profile_created": profile.created_at.isoformat(),
    }

    return jsonify(profile_data), 200


# Add user to favourites
@app.route("/api/profiles/<int:user_id2>/favourite", methods=["POST"])
@csrf.exempt
@jwt_required
def favourite_user(user_id, user_id2):
    current_user_id = user_id
    if current_user_id == user_id2:
        return jsonify({"error": "You can't favourite yourself."}), 400

    already_fav = Favourite.query.filter_by(
        user_id_fk=current_user_id, fav_user_id_fk=user_id2
    ).first()
    if already_fav:
        return jsonify({"message": "User is already in favourites."}), 200

    fav = Favourite(user_id_fk=current_user_id, fav_user_id_fk=user_id2)
    db.session.add(fav)
    db.session.commit()
    return jsonify({"message": "User added to favourites"}), 201


# UPDATE PROFILE
@app.route("/api/profiles/<int:profile_id>", methods=["PUT"])
@csrf.exempt
@jwt_required
def update_profile(user_id, profile_id):
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    data = request.get_json()

    for field in [
        "description",
        "parish",
        "biography",
        "sex",
        "race",
        "birth_year",
        "height",
        "fav_cuisine",
        "fav_colour",
        "fav_school_subject",
        "political",
        "religious",
        "family_oriented",
    ]:
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()
    return jsonify({"message": "Profile updated", "profile": profile.to_dict()}), 200


@app.route("/api/profiles/matches/<int:profile_id>", methods=["GET"])
@csrf.exempt
@jwt_required
def match_profiles(user_id, profile_id):

    current = Profile.query.filter_by(id=profile_id, user_id_fk=user_id).first()
    if not current:
        return jsonify({"error": "Profile not found"}), 404

    matches = []
    all_profiles = Profile.query.filter(
        Profile.id != profile_id, Profile.user_id_fk != user_id
    ).all()

    match_fields = [
        "fav_cuisine",
        "fav_colour",
        "fav_school_subject",
        "political",
        "religious",
        "family_oriented",
    ]

    for profile in all_profiles:
        if not profile.birth_year or not current.birth_year:
            continue
        if abs(profile.birth_year - current.birth_year) > 5:
            continue

        if not profile.height or not current.height:
            continue
        height_diff_inches = abs(profile.height - current.height) * 39.37
        if not (3 <= int(height_diff_inches) <= 10):
            continue

        matched_fields = [
            field
            for field in match_fields
            if getattr(profile, field) == getattr(current, field)
        ]
        if len(matched_fields) < 3:
            continue

        profile_dict = profile.to_dict()

        owner = User.query.get(profile.user_id_fk)
        profile_dict["name"] = owner.name if owner else None

        profile_dict["matched_fields"] = matched_fields
        matches.append(profile_dict)

    return jsonify(matches), 200

@app.route("/api/search", methods=["GET"])
@csrf.exempt
@jwt_required
def search_profiles(user_id):
    name = request.args.get("name")
    birth_year = request.args.get("birth_year")
    sex = request.args.get("sex")
    race = request.args.get("race")

    query = (
        db.session.query(Profile, User)
        .join(User, Profile.user_id_fk == User.id)
        .filter(User.id != user_id)
    )

    if name:
        query = query.filter(func.lower(User.username).like(f"%{name.lower()}%"))
    if birth_year:
        query = query.filter(Profile.birth_year == int(birth_year))
    if sex:
        query = query.filter(func.lower(Profile.sex) == sex.lower())
    if race:
        query = query.filter(func.lower(Profile.race) == race.lower())

    results = query.order_by(Profile.created_at.desc()).all()

    profiles_with_user_info = []
    for profile, user in results:
        profiles_with_user_info.append(
            {
                "id": profile.id,
                "user_id": user.id,
                "description": profile.description,
                "parish": profile.parish,
                "biography": profile.biography,
                "sex": profile.sex,
                "race": profile.race,
                "birth_year": profile.birth_year,
                "height": profile.height,
                "fav_cuisine": profile.fav_cuisine,
                "fav_colour": profile.fav_colour,
                "fav_school_sibject": profile.fav_school_subject,
                "political": profile.political,
                "religious": profile.religious,
                "family_oriented": profile.family_oriented,
                "username": user.username,
                "photo": user.photo,
                "date_joined": user.date_joined.isoformat(),
                "profile_created": profile.created_at.isoformat(),
            }
        )

    return jsonify(profiles_with_user_info), 200

@app.route("/api/users/<int:user_id2>", methods=["GET"])
@csrf.exempt
@jwt_required
def get_user(user_id, user_id2):
    user = db.session.get(User, user_id2)
    if user:
        return jsonify(user.to_dict()), 200
    return jsonify({"error": "User not found"}), 404

@app.route("/api/users/<int:user_id2>/favourites", methods=["GET"])
@csrf.exempt
@jwt_required
def user_favourites(user_id, user_id2):
    favs = Favourite.query.filter_by(user_id_fk=user_id2).all()
    data = []
    for fav in favs:
        user = db.session.get(User, fav.fav_user_id_fk)
        if user:
            data.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "photo": user.photo,
                }
            )
    return jsonify(data), 200


@app.route("/api/users/favourites/<int:N>", methods=["GET"])
@csrf.exempt
@jwt_required
def top_favourited_users(user_id, N):
    counts = (
        db.session.query(
            Favourite.fav_user_id_fk,
            func.count(Favourite.fav_user_id_fk).label("count"),
        )
        .group_by(Favourite.fav_user_id_fk)
        .order_by(func.count(Favourite.fav_user_id_fk).desc())
        .limit(N)
        .all()
    )

    result = []
    for user_id, count in counts:
        user = db.session.get(User, user_id)
        if user:
            udata = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "photo": user.photo,
                "favourite_count": count,
            }
            result.append(udata)

    return jsonify(result), 200


@app.route("/api/users/<int:user_id>/profiles", methods=["GET"])
@csrf.exempt
@jwt_required
def get_user_profiles(current_user_id, user_id):
    profiles = Profile.query.filter_by(user_id_fk=user_id).all()

    if not profiles:
        return jsonify({"message": "No profiles found for this user."}), 404

    profiles_data = [profile.to_dict() for profile in profiles]
    return jsonify(profiles_data), 200

# The functions below should be applicable to all Flask apps.

# Function to collect form errors from Flask-WTF
def form_errors(form):
    error_messages = []
    """Collects form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            message = "Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error,
            )
            error_messages.append(message)

    return error_messages


@app.route("/<file_name>.txt")
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + ".txt"
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers["X-UA-Compatible"] = "IE=Edge,chrome=1"
    response.headers["Cache-Control"] = "public, max-age=0"
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template("404.html"), 404
