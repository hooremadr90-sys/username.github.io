from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Working!'

if __name__ == '__main__':
    print("Starting server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
    