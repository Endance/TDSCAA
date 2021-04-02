import time
import random
import numpy as np
import pandas as pd
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from gensim.models import Word2Vec, FastText
from nltk.tokenize import sent_tokenize, TweetTokenizer
from flask import Flask, render_template, url_for, request, redirect

def update_sentence(sentence):
  with open('Q&A/SentencesWithWords.txt', 'a') as f:
    f.writelines([sentence])


def train_model():
  with open('Q&A/SentencesWithWords.txt') as f:
    sentences = [line.strip().lower() for line in f.readlines()]

  #split words for training
  tknzr = TweetTokenizer()
  sentences = tuple((tknzr.tokenize(s) for s in sentences))

  w2v_model = Word2Vec(sentences=sentences, window=10, min_count=0, workers=4, sg = 0, cbow_mean = 1, sample = 0 )
  return w2v_model


def predict_stuff(model, sentence_with_blank):
  # This is _____ sentence.
  tknzr = TweetTokenizer()
  words = [word.lower() for word in tknzr.tokenize(sentence_with_blank) if not word.startswith('__')]
  return model.predict_output_word(words, topn=10)

# Open the Cards Against txt file
file1 = open('Q&A/funny_sentences.txt')

# Open the Words txt file
file2 = open('Q&A/69_Words.txt', encoding="utf8")
 
# Read the both files and store each line in a a seperate list
cardText = file1.readlines()
options = file2.readlines()

# Choose a random question card
def get_random():
    card = random.choice(cardText)

# Train model and get bot answers
    model = train_model()
    sentence_with_blank = card.replace('blank', '_____')

    possible_answers = predict_stuff(model, sentence_with_blank)

# Generate and pick your random answer cards
    bot_answers = random.choices(possible_answers, k=15)
    bot_ans = []

    for i in bot_answers:
        bot_ans.append(i[0])

    bot_set = set(bot_ans)
    bot_answers = list(bot_set)

    return  card, bot_answers

card, bot_answers = get_random()


#Initiate server and SQLAlchemy database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

#Creating model for database bound to session
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(40), nullable=False)
    answers = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return '<Player %r>' % self.id

shots_amount = random.randint(3,7)
questions_id = ["A", "B", "C", "D", "E", "F", "G", "H"]
answers = []
votes = []

# Game page
@app.route('/game/', methods=['POST', 'GET'])
def game():
    players = Todo.query.order_by(Todo.id).all()

    if len(votes) == len(answers):
            if len(votes) > 1:
                global card, bot_answers
                card, bot_answers = get_random()
                return redirect('/game/reset/')

    if request.method == 'POST':
        answer = request.form['answer']
        if answer not in answers:
            answers.append(answer)
    
        return redirect('/game/')
    else:
        return render_template('index.html', card=card, qid=questions_id, players=players, ans=answers, bot_answers=bot_answers)

@app.route('/game/reset/')
def reset_game():
    answers.clear()
    votes.clear()
    return redirect('/game/')

@app.route('/game/vote_reset/')
def reset_votes():
    votes.clear()
    return redirect('/game/voting/')

@app.route("/game/new_card")
def get_new_card():
    answers.clear()
    votes.clear()
    answers.extend(['dummy1', 'dummy2'])
    votes.extend(['dummy1', 'dummy2'])
    return redirect('/game/')
    
@app.route('/game/voting/', methods=['POST', 'GET'])
def voting():
    players = Todo.query.order_by(Todo.id).all()

    if request.method == 'POST':
        vote = request.form['vote']
        votes.append(vote)
        return redirect('/game/voting/')
    else:
        return render_template('voting.html', card=card, qid=questions_id, players=players, ans=answers, votes=votes)

@app.route('/game/winner/')
def winning():
    players = Todo.query.order_by(Todo.id).all()
    winner = max(set(votes), key = votes.count)
    windex = questions_id.index(winner)

    win_answer = answers[windex]
    card_win = card.replace("blank", win_answer)

    update_sentence(card_win)

    player_win = players[windex]

    return render_template('win.html', player_win=player_win,card_win=card_win, players=players, shots_amount=shots_amount)

# Route for chosing names and intiating names
@app.route('/', methods=['POST', 'GET'])
def start():
        if request.method == 'POST':
            new_player = request.form['player_name']
            player = Todo(content=new_player)

            try:
                db.session.add(player)
                db.session.commit()
                return redirect('/')
            except:
                return 'There was an issue submitting the player'

        else:
            players = Todo.query.order_by(Todo.id).all()
            return render_template('start.html', players=players)

@app.route('/delete/<int:id>')
def delete(id):
    player_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(player_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'The task has failed'

@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    player = Todo.query.get_or_404(id)

    if request.method == 'POST':
        player.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'The task has failed'
    else:
        return render_template('update.html', player=player)

if __name__ == '__main__':
    app.run(debug=True)




