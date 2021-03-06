"""Module contains routes, used for problem table."""
import json
import hashlib
import time
import os
import PIL


from flask import request, jsonify, Response
from flask_login import current_user
from PIL import Image

from ecomap import validator
from ecomap.app import app, logger, auto
from ecomap.db import util as db


@app.route('/api/problems')
def problems():
    """Handler for sending short data about all problem stored in db.
    Used by Google Map instance.

    :rtype: JSON
    :return:
        - If problems list not empty:
            ``[{"status": "Unsolved", "problem_type_Id": 2,
            "title": "problem 1","longitude": 25.9717, "date": 1450735578,
            "latitude": 50.2893, "problem_id": 75},
            {"status": "Unsolved", "problem_type_Id": 3,
            "title": "problem 2", "longitude": 24.7852, "date": 1450738061,
            "latitude": 49.205, "problem_id": 76}]``
        - If problem list is empty:
            ``{}``

    :statuscode 200: no errors

    """
    problem_tuple = db.get_all_problems()
    parsed_json = []
    if problem_tuple:
        for problem in problem_tuple:
            parsed_json.append({
                'problem_id': problem[0], 'title': problem[1],
                'latitude': problem[2], 'longitude': problem[3],
                'problem_type_Id': problem[4], 'status': problem[5],
                'date': problem[6]})
    return Response(json.dumps(parsed_json), mimetype='application/json')


@app.route('/api/problem_detailed_info/<int:problem_id>', methods=['GET'])
def detailed_problem(problem_id):
    """This method returns object with detailed problem data.
    
    :rtype: JSON
    :param problem_id: `{problem_id: 82}`
    :return:
            - If problem exists:
                ``[[{"content": "Text with situation", "status": "Unsolved",
                "date": 1450954447, "severity": "1", "title": "problem",
                "latitude": 52.7762, "proposal": "proposal how to solve",
                "problem_type_id": 3, "problem_id": 82, "longitude": 34.2114}],
                [{"activity_type": "Added", "user_id": 5,
                "problem_id": 82, "created_date": 1450954447}], 
                [{"url": "/uploads/problems/82/0d0d3ef56a16bd069e.png",
                "user_id": 5, "description": "description to photo"}], 
                [{"user_id": 5, "name": "User", "problem_id": 82,
                "content": "Comment", "created_date": 1450954929000,
                "id": 5}]]``
            - If problem not exists:
                ``{"message": " resource not exists"}``

    :statuscode 404: problem not exists
    :statuscode 200: problem displayed

    """
    problem_data = db.get_problem_by_id(problem_id)
    activities_data = db.get_activity_by_problem_id(problem_id)
    photos_data = db.get_problem_photos(problem_id)
    comments_data = db.get_comments_by_problem_id(problem_id)
    photos = []
    activities = {}
    comments = []

    if problem_data:
        problems = {
            'problem_id': problem_data[0], 'title': problem_data[1],
            'content': problem_data[2], 'proposal': problem_data[3],
            'severity': problem_data[4], 'status': problem_data[5],
            'latitude': problem_data[6], 'longitude': problem_data[7],
            'problem_type_id': problem_data[8], 'date': problem_data[9]}
    else:
        return jsonify({'message': ' resource not exists'}), 404

    if activities_data:
        activities = {
            'created_date': activities_data[0],
            'problem_id': activities_data[1],
            'user_id': activities_data[2],
            'activity_type': activities_data[3]}
    if photos_data:
        for photo_data in photos_data:
            photos.append({'url': photo_data[0],
                           'description': photo_data[1],
                           'user_id': photo_data[2]})
    if comments_data:
        for comment in comments_data:
            comments.append({'id': comment[0],
                             'content': comment[1],
                             'problem_id': comment[2],
                             'created_date': comment[3] * 1000,
                             'user_id': comment[4],
                             'name': '%s %s' % (comment[5], comment[6])})

    response = Response(json.dumps([[problems], [activities],
                                    photos, comments]),
                        mimetype='application/json')
    return response


@app.route('/api/problem_post', methods=['POST'])
def post_problem():
    """Function which adds data about created problem into DB.

    :content-type: multipart/form-data

    :fparam title: Title of problem ('problem with rivers')
    :fparam type: id of problem type (2)
    :fparam lat: lat coordinates (49.8256101)
    :fparam longitude: lon coordinates (24.0600542)
    :fparam content: description of problem ('some text')
    :fparam proposal: proposition for solving problem ('text')

    :rtype: JSON
    :return:
            - If request data is invalid:
                    ``{'status': False, 'error': [list of errors]}``
            - If all ok:
                    ``{"added_problem": "problem title", "problem_id": 83}``
    
    :statuscode 400: request is invalid
    :statuscode 200: problem was successfully posted

    """
    if request.method == 'POST' and request.form:
        data = request.form
        logger.warning(json.dumps(request.form))
        logger.info(data)
        valid = validator.problem_post(data)
        if valid['status']:
            logger.debug('Checks problem post validation. %s', valid)
            user_id = current_user.uid
            posted_date = int(time.time())
            last_id = db.problem_post(data['title'],
                                      data['content'],
                                      data['proposal'],
                                      data['latitude'],
                                      data['longitude'],
                                      data['type'],
                                      posted_date,
                                      user_id)
            if last_id:
                db.problem_activity_post(last_id, posted_date,
                                         user_id, 'Added')
            logger.debug('New problem post was created with id %s', last_id)
            response = jsonify(added_problem=data['title'],
                               problem_id=last_id)
        else:
            response = Response(json.dumps(valid),
                                mimetype='application/json'), 400
        return response


@app.route('/api/usersProblem/<int:user_id>', methods=['GET'])
def get_user_problems(user_id):
    """This method retrieves all user's problem from db and shows it in user
    profile page on `my problems` tab.

        :rtype: JSON
        :param  user_id: id of user (int)
        :return:
            - If user has problems:
                ``[{"id": 190,"title": "name",
                "latitude": 51.419765,
                "longitude": 29.520264,
                "problem_type_id": 1,
                "status": 0,
                "date": "2015-02-24T14:27:22.000Z",
                "severity": '3',
                "is_enabled": 1
                },{...}]``
            - If user haven't:
                ``{}``

        :statuscode 200: no errors
        
    """
    problems_list = []
    problem_tuple = db.get_user_problems(user_id)
    logger.info(problem_tuple)
    for problem in problem_tuple:
        problems_list.append({'id': problem[0],
                              'title': problem[1],
                              'latitude': problem[2],
                              'logitude': problem[3],
                              'problem_type_id': problem[4],
                              'status': problem[5],
                              'date': problem[6] * 1000,
                              'severity': problem[8],
                              'is_enabled': problem[7]})
    return Response(json.dumps(problems_list), mimetype='application/json')


@app.route('/api/all_usersProblem', methods=['GET'])
def get_all_users_problems():
    """This method retrieves all user's problem from db.

        :query limit: limit number. default is 5
        :query offset: offset number. default is 0
        :rtype: JSON
        :return: list of user's problem represented with next objects:

            ``[{"id": 190,
            "title": "name",
            "latitude": 51.419765,
            "longitude": 29.520264,
            "problem_type_id": 1,
            "status": 0,
            "date": "2015-02-24T14:27:22.000Z",
            "severity": '3',
            "is_enabled": 1},...]``

    """
    offset = request.args.get('offset') or 0
    per_page = request.args.get('per_page') or 5

    count = db.count_problems()
    total_count = {}
    problems_list = []
    problem_tuple = db.get_all_users_problems(offset, per_page)

    if problem_tuple:
        for problem in problem_tuple:
            problems_list.append({'id': problem[0],
                                  'title': problem[1],
                                  'latitude': problem[2],
                                  'longitude': problem[3],
                                  'problem_type_id': problem[4],
                                  'status': problem[5],
                                  'date': problem[6] * 1000,
                                  'severity': problem[8],
                                  'is_enabled': problem[7]})
    if count:
        total_count = {'total_problem_count': count[0]}

    return Response(json.dumps([problems_list, [total_count]]),
                    mimetype='application/json')


@app.route('/api/photo/<int:problem_id>', methods=['POST'])
def problem_photo(problem_id):
    """Controller for handling adding problem photos.

    **param** problem_id - id of problem instance for uploading new photos.

    :content-type: multipart/form-data

    :fparam file: image file in base64. Content-Type: image/png
    :fparam name: image name (`'image.jpg'`)
    :fparam description: description of image (`'some text'`)

    :return: json object with success message or message with error status.

        - if success:
            ``{"added_file": "/uploads/problems/77/df4c22114eb24442e8b6.png"}``

    :statuscode 400: error with attaching image or request is invalid
    :statuscode 200: successfully added

    """
    response = jsonify(), 400
    extension = '.png'
    static_url = '/uploads/problems/%s/' % problem_id
    f_path = os.environ['STATICROOT'] + static_url
    user_id = current_user.uid
    now = time.time()*100000
    unique_key = (int(now)+user_id)
    hashed_name = hashlib.md5(str(unique_key))
    f_name = '%s%s' % (hashed_name.hexdigest(), extension)

    if request.method == 'POST':
        problem_img = request.files['file']
        photo_descr = request.form['description']

        if problem_img and validator.validate_image_file(problem_img):
            if not os.path.exists(f_path):
                os.makedirs(os.path.dirname('%s%s' % (f_path, f_name)))
            problem_img.save(os.path.join(f_path, f_name))
            img_path = '%s%s' % (static_url, f_name)

            basewidth = 100
            img = Image.open(os.path.join(f_path, f_name))
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
            f_name = '%s%s%s' % (hashed_name.hexdigest(), '.min', extension)
            img.save(os.path.join(f_path, f_name))

            db.add_problem_photo(problem_id, img_path, photo_descr, user_id)
            response = json.dumps({'added_file': img_path})
        else:
            response = jsonify(error='error with import file'), 400
    return response


@app.route('/api/problem/add_comment', methods=['POST'])
def post_comment():
    """Adds new comment to problem.

    :rtype: JSON
    :request args: `{content: "comment", problem_id: "77"}`
    :return:
        - if success:
            ``{"message": "Comment successfully added."}``
        - if some error:
            ``{error: "type of validation error"}``

    :statuscode 400: error with adding comment or request is invalid
    :statuscode 200: successfully added

    """
    data = request.get_json()
    valid = validator.check_post_comment(data)

    if valid['status']:
        created_date = int(time.time())
        db.add_comment(current_user.uid,
                       data['problem_id'],
                       data['content'],
                       created_date)
        db.problem_activity_post(data['problem_id'],
                                 created_date,
                                 current_user.uid,
                                 'Updated')
        response = jsonify(message='Comment successfully added.'), 200
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400

    return response


@app.route('/api/problem_comments/<int:problem_id>', methods=['GET'])
def get_comments(problem_id):
    """Return all problem comments

        :rtype: JSON
        :param problem_id: id of problem (int)
        :return:
            - If problem has comments:
                ``[{content: "some comment",
                created_date: 1451001050000,
                id: 29,
                name: "user name",
                problem_id: 77,
                user_id: 6,
                },{...}]``
            - If user hasn't:
                ``{}``

        :statuscode 200: no errors

    """

    comments_data = db.get_comments_by_problem_id(problem_id)
    comments = []

    if comments_data:
        for comment in comments_data:
            comments.append({'id': comment[0],
                             'content': comment[1],
                             'problem_id': comment[2],
                             'created_date': comment[3] * 1000,
                             'user_id': comment[4],
                             'name': '%s %s' % (comment[5], comment[6])})
    response = Response(json.dumps(comments),
                        mimetype='application/json')
    return response
