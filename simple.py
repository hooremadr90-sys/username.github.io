print("Starting test...")
from flask import Flask
print("Flask imported")
app = Flask(__name__)
print("App created")

@app.route('/')
def home():
    return "Hello"

print("Route defined")

if __name__ == '__main__':
    print("About to run...")
    app.run(debug=True, host='127.0.0.1', port=5000)
