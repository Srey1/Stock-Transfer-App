import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    x = 1
    first_savings = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
    first_symbol = db.execute("SELECT symbol FROM stock_data WHERE id = :user_id", user_id = session["user_id"])
    first_shares = db.execute("SELECT shares FROM stock_data WHERE id = :user_id", user_id = session["user_id"])




    savings = first_savings[0]["cash"]
    final_symbols = []
    final_shares = []
    final_prices = []
    final_values = []
    final_names = []

    true_value = float(savings)



    x = 0

    if len(first_symbol) == 0:
        amt_stocks = 0
    else:
        amt_stocks = len(first_symbol)

        while x < amt_stocks:
            final_symbols.append(first_symbol[x]["symbol"])
            final_shares.append(first_shares[x]["shares"])
            price_dict = lookup(first_symbol[x]["symbol"])
            price = price_dict["price"]
            name = price_dict["name"]
            final_prices.append(price)
            final_names.append(name)
            value = price * (first_shares[x]["shares"])
            final_values.append(value)
            x += 1

    #print(final_symbols)
    #print(final_shares)
    #print(final_prices)
    #print(final_values)
    #print(final_names)

    for items in final_values:
        true_value += items



    return render_template("index.html", savings = savings, final_symbols = final_symbols, final_shares = final_shares, final_prices = final_prices, final_values = final_values, final_names = final_names, amt_stocks = amt_stocks, true_value = true_value)




@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        amt_shares = request.form.get("shares")
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)
        # Ensure the shares were submitted
        elif not request.form.get("shares"):
            return apology("must provide the amount of shares", 403)

        savings = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
        stock = lookup(symbol)
        stock_price = stock["price"]
        #print(stock_price)
        final_savings = savings[0]["cash"]
        total_price = float(stock_price) * float(amt_shares)
        if total_price > final_savings:
            return apology("NO")

        new_savings = final_savings - total_price

        string_savings = str(new_savings)

        # Getting the time
        current = datetime.now()

        time = current.strftime("%d/%m/%Y %H:%M:%S")

        intamount = int(amt_shares)

        #db.execute("UPDATE users (cash) VALUES (:cash) WHERE id = :user_id", cash = new_savings, user_id = session["user_id"])
        db.execute("UPDATE users SET cash = :price WHERE id = :user_id", price=new_savings, user_id=session["user_id"])

        db.execute("INSERT INTO stock_data (id, symbol, shares, price) VALUES (:id, :symbol, :shares, :price)", id = session["user_id"], symbol = symbol, shares = amt_shares, price = string_savings)

        db.execute("INSERT INTO final_historyy (id, symbol, shares, price, time) VALUES (:id, :symbol, :shares, :price, :time)", id = session["user_id"], symbol = symbol, shares = intamount, price = total_price, time = time)


        flash("Bought!")
        return redirect("/")

    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    first_symbol = db.execute("SELECT symbol FROM final_historyy WHERE id = :user_id", user_id = session["user_id"])
    first_shares = db.execute("SELECT shares FROM final_historyy WHERE id = :user_id", user_id = session["user_id"])
    first_price = db.execute("SELECT price FROM final_historyy WHERE id = :user_id", user_id = session["user_id"])
    first_time = db.execute("SELECT time FROM final_historyy WHERE id = :user_id", user_id = session["user_id"])

    final_symbols = []
    final_shares = []
    final_price = []
    final_time = []



    x = 0

    if len(first_symbol) == 0:
        amt_stocks = 0
    else:
        amt_stocks = len(first_symbol)

    while x < amt_stocks:
        final_symbols.append(first_symbol[x]["symbol"])
        final_shares.append(first_shares[x]["shares"])
        final_price.append(first_price[x]["price"])
        final_time.append(first_time[x]["time"])
        x += 1

    print(final_symbols)
    print(final_shares)
    print(final_price)
    print(final_time)

    return render_template("history.html", final_symbols = final_symbols, final_shares = final_shares, final_price = final_price, final_time = final_time, amt_stocks = amt_stocks )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        given_stock = request.form.get("stock")
        if not given_stock:
            return apology("Please enter a stock symbol!")
        stock_info = lookup(given_stock)
        #key_list = list(my_dict.keys())
        #key_list[position]
        price = stock_info["price"]
        print(stock_info)
        return render_template("quoted.html", stock_info=stock_info, price = price)

    else:
        return render_template("quote.html")
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirm password was submitted
        elif not request.form.get("confirm"):
            return apology("must confirm password", 403)

        if request.form.get("password") != request.form.get("confirm"):
            return apology("Your password does not match your confirmed password")

        if request.form.get("username") == request.form.get("password"):
            return apology("Username and password need to be different")

        # Password Check
        if len(request.form.get("password")) < 5:
            return apology("You password length has to be greater than 5 charectors")

        numbers = ["1","2","3","4","5","6","7","8","9"]
        counter = False
        for charectors in request.form.get("password"):
            for nums in numbers:
                if charectors == nums:
                    counter = True
                else:
                    pass
        if counter == False:
            return apology("Your password must contain one or more numbers")

        upper_case = False

        for charector in request.form.get("password"):
            if charector.isupper() == True:
                upper_case = True

        if upper_case == False:
            return apology("Your password must contain some upper case letters")

        lower_case = False

        for charector in request.form.get("password"):
            if charector.islower() == True:
                lower_case = True

        if lower_case == False:
            return apology("Your password must contain some lower case letters")

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if rows:
            return apology("username and/or password already taken", 403)

        # Query database for username
        inserted = db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username = request.form.get("username"), password = generate_password_hash(request.form.get("password")))



        session["user_id"] = inserted
        flash("Registered!")
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # Making the variables
        symbol = request.form.get("symbol")

        amt_shares = request.form.get("shares")

        if symbol == None:
            return apology("Invalid Symbol")

        stock = lookup(symbol)

        print(stock)

        stock_price = stock["price"]

        total_price = float(stock_price) * float(amt_shares)

        savings = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])

        final_savings = savings[0]["cash"]

        new_savings = final_savings + total_price

        current_shares = db.execute("SELECT shares FROM stock_data WHERE id = :user_id AND symbol = :symbol", user_id = session["user_id"], symbol = symbol)

        #print(current_shares)

        shares = int(current_shares[0]["shares"])

        shares_left = int(shares) - int(amt_shares)

        current = datetime.now()

        time = current.strftime("%d/%m/%Y %H:%M:%S")

        # Error Handling

        if int(amt_shares) <= 0:
            return apology("Please give a number of shares greater than 1")

        if int(amt_shares) > shares:
            return apology("You do not own enough shares to sell this many")

        negative_shares = int(amt_shares) * -1

        # Updating database

        db.execute("UPDATE users SET cash = :price WHERE id = :user_id", price=new_savings, user_id=session["user_id"])
        db.execute("UPDATE stock_data SET shares = :amt_shares WHERE id = :user_id AND symbol = :symbol", amt_shares = shares_left, user_id=session["user_id"], symbol = symbol)
        db.execute("INSERT INTO final_historyy (id, symbol, shares, price, time) VALUES (:id, :symbol, :shares, :price, :time)", id = session["user_id"], symbol = symbol, shares = negative_shares, price = total_price, time = time)


        return redirect("/")
    else:
        current_symbols = db.execute("SELECT symbol FROM stock_data WHERE id = :user_id", user_id = session["user_id"])
        x = 0
        amt_symbols = len(current_symbols)

        final_symbols = []

        while x < amt_symbols:
            final_symbols.append(current_symbols[x]["symbol"])
            x += 1

        return render_template("sell.html", final_symbols = final_symbols, amt_symbols = amt_symbols)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
