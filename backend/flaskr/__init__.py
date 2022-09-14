import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random


from models import setup_db, Question, Category
from settings import DB_NAME, DB_USER, DB_PASSWORD

QUESTIONS_PER_PAGE = 10

db = SQLAlchemy()


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app, response="*")
    '''
  Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response
    '''
  Create an endpoint to handle GET requests
  for all available categories.
  '''
  
    @app.route('/categories')
    def access_categories():
        categories = { category.format()['id'] : category.format()['type'] for category in Category.query.all() }

        if len(categories) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "categories": categories,
            "total_categories": len(Category.query.all())
        })

    '''
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    @app.route('/questions')
    def select_all_questions():
        question_selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, question_selection)

        categories = { category.id : category.type for category in Category.query.all() }

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(question_selection),
            'categories': {category.id: category.type for category in categories},
            'current_category': None
        })

    '''
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route("/questions/<question_id>", methods=['DELETE'])
    def question_deletion(question_id):
      
        try:
            question = Question.query.get(question_id)

            if question is None:
                abort(404)

            question.delete()

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                }
            )

        except:
            abort(422)

    '''
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
    @app.route("/questions", methods=['POST'])
    def post_new_question():
        body = request.get_json()

        if not ('question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
            abort(422)

        set_question = body.get('question')
        set_answer = body.get('answer')
        set_difficulty = body.get('difficulty')
        set_category = body.get('category')

        try:
            question = Question(question=set_question, answer=set_answer, difficulty=set_difficulty, category=set_category)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id,
            })

        except:
            abort(422)

    '''
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''
    @app.route('/questions/search', methods=['POST'])
    def question_search():
        body = request.get_json()
        search_term_item = body.get('searchTerm', None)
        
        if search_term_item:
            search_results = Question.query.filter(Question.question.ilike(f'%{search_term_item}%')).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in search_results],
                'total_questions': len(search_results),
                'current_category': None
            })
        abort(404)
    '''
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):

        try:
            questions = Question.query.filter(
                Question.category == str(category_id)).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions],
                'total_questions': len(questions),
                'current_category': category_id
            })
        except:
            abort(404)

    '''
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
    @app.route('/quizzes', methods=['POST'])
    def play_quizzy():

        try:

            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            former_questions = body.get('previous_questions')

            if category['type'] == 'click':
                ready_questions = Question.query.filter(
                    Question.id.notin_((former_questions))).all()
            else:
                ready_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_((former_questions))).all()

            latest_question = ready_questions[random.randrange(
                0, len(ready_questions))].format() if len(ready_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': latest_question
            })
        except:
            abort(422)

    '''
  Create error handlers for all expected errors
  including 404 and 422.
  '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app
