#!/bin/sh
source .venv/bin/activate 
pip install -r requirements.txt

#python -u -m flask --app main run --debug

#export FLASK_APP=app.py
#flask run --host=0.0.0.0 --port=8080

#source .venv/bin/activate
python -u -m flask --app app run --debug