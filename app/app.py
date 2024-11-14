from flask import Flask, render_template
import expense_tracker 

app = Flask(__name__)

@app.route('/')
def home():
    expenses = expense_tracker.get_expenses()
    return render_template('index.html', expenses=expenses)

if __name__ == '__main__':
    app.run(debug=True)
