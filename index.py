from flask import Flask  #importing Flask to make everything work

app = Flask(__name__)

@app.route('/')
def root():  # function
  return 'Hello World!'

if __name__ == '__main__':
  app.run(debug=True)