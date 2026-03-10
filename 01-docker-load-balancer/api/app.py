import os
import psycopg2
from flask import Flask

app = Flask(__name__)


INSTANCE_NAME = os.environ.get("INSTANCE_NAME","api")

@app.route("/")
def home():
	return {"message": "Hello", "instance" :INSTANCE_NAME}


@app.route("/db")
def check_db():
	try:
		conn = psycopg2.connect(
 		   host=os.environ.get("DB_HOST", "db"),
   		   dbname=os.environ.get("DB_NAME", "mydb"),
   	           user=os.environ.get("DB_USER", "user"),
   		   password=os.environ.get("DB_PASSWORD", "password")
		)
		conn.close()
		return {"instance": INSTANCE_NAME, "Database": "conect"}
	
	except Exception as e:
		return {"intance": INSTANCE_NAME, "Database": "error"}, 500
 
if __name__ =="__main__":
	app.run(host="0.0.0.0", port=5000)

