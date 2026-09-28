from flask import Flask, render_template, request
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)


# ==========================================
# FILES
# ==========================================

CSV_FILE = "atm_transactions.csv"
ACCOUNT_FILE = "accounts.csv"
PAYMENT_FILE = "payments.csv"


# ==========================================
# LOAD ATM DATA
# ==========================================

def load_data():

    file_path = os.path.join(
        os.path.dirname(__file__),
        CSV_FILE
    )

    df = pd.read_csv(file_path)

    df = df.dropna(how="all")

    df["TransactionAmount"] = pd.to_numeric(
        df["TransactionAmount"],
        errors="coerce"
    ).fillna(0)

    df["AccountBalance"] = pd.to_numeric(
        df["AccountBalance"],
        errors="coerce"
    ).fillna(0)

    df["LoginAttempts"] = pd.to_numeric(
        df["LoginAttempts"],
        errors="coerce"
    ).fillna(0)

    df["CustomerAge"] = pd.to_numeric(
        df["CustomerAge"],
        errors="coerce"
    ).fillna(0)

    return df


# ==========================================
# CREATE / UPDATE ACCOUNT FILE
# ==========================================

def create_account_file():

    if not os.path.exists(ACCOUNT_FILE):

        df = pd.DataFrame(
            columns=[
                "Name",
                "Mobile",
                "Email",
                "UPI_ID",
                "PIN",
                "Account_Type"
            ]
        )

        df.to_csv(
            ACCOUNT_FILE,
            index=False
        )

    else:

        accounts = pd.read_csv(ACCOUNT_FILE)

        if "Account_Type" not in accounts.columns:

            accounts["Account_Type"] = "Savings Account"

            accounts.to_csv(
                ACCOUNT_FILE,
                index=False
            )


# ==========================================
# CREATE PAYMENT FILE
# ==========================================

def create_payment_file():

    if not os.path.exists(PAYMENT_FILE):

        df = pd.DataFrame(
            columns=[
                "Account_Type",
                "Receiver_UPI",
                "Amount",
                "Description",
                "Payment_Method",
                "Date"
            ]
        )

        df.to_csv(
            PAYMENT_FILE,
            index=False
        )


create_account_file()
create_payment_file()


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
def index():

    df = load_data()

    total_transactions = len(df)

    total_amount = df["TransactionAmount"].sum()

    average_amount = df["TransactionAmount"].mean()

    debit_count = (
        df["TransactionType"]
        .astype(str)
        .str.lower()
        .eq("debit")
        .sum()
    )

    credit_count = (
        df["TransactionType"]
        .astype(str)
        .str.lower()
        .eq("credit")
        .sum()
    )

    channel_data = (
        df["Channel"]
        .value_counts()
        .to_dict()
    )

    transaction_type_data = (
        df["TransactionType"]
        .value_counts()
        .to_dict()
    )

    location_data = (
        df["Location"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    occupation_data = (
        df["CustomerOccupation"]
        .value_counts()
        .to_dict()
    )

    suspicious_login = df[
        df["LoginAttempts"] >= 3
    ]

    suspicious_count = len(suspicious_login)

    return render_template(
        "index.html",
        total_transactions=total_transactions,
        total_amount=total_amount,
        average_amount=average_amount,
        debit_count=debit_count,
        credit_count=credit_count,
        suspicious_count=suspicious_count,
        channel_data=channel_data,
        transaction_type_data=transaction_type_data,
        location_data=location_data,
        occupation_data=occupation_data
    )


# =====================================================
# CREATE ACCOUNT
# =====================================================

@app.route("/create-account", methods=["GET", "POST"])
def create_account():

    if request.method == "POST":

        name = request.form["name"]

        mobile = request.form["mobile"]

        email = request.form["email"]

        upi_id = request.form["upi_id"]

        pin = request.form["pin"]

        confirm_pin = request.form["confirm_pin"]

        account_type = request.form["account_type"]


        # Check PIN

        if pin != confirm_pin:

            return "PINs do not match."


        # Check PIN length

        if len(pin) != 4 or not pin.isdigit():

            return "PIN must contain exactly 4 digits."


        # Read accounts

        accounts = pd.read_csv(
            ACCOUNT_FILE
        )


        # Check duplicate UPI

        if not accounts.empty:

            if upi_id in accounts["UPI_ID"].astype(str).values:

                return "This UPI ID already exists."


        # Create new account

        new_account = pd.DataFrame([{

            "Name": name,

            "Mobile": mobile,

            "Email": email,

            "UPI_ID": upi_id,

            "PIN": pin,

            "Account_Type": account_type

        }])


        # Save account

        new_account.to_csv(
            ACCOUNT_FILE,
            mode="a",
            header=False,
            index=False
        )


        return render_template(
            "account_created.html",
            name=name,
            mobile=mobile,
            email=email,
            upi_id=upi_id,
            account_type=account_type
        )


    return render_template(
        "create_account.html"
    )


# =====================================================
# SEND MONEY
# =====================================================

@app.route("/send-money", methods=["GET", "POST"])
def send_money():

    if request.method == "POST":

        # Get account type
        account_type = request.form["account_type"]

        # Get receiver UPI
        receiver_upi = request.form["receiver_upi"]

        # Get amount
        amount = request.form["amount"]

        # Get description
        description = request.form["description"]

        # Get payment method
        payment_method = request.form["payment_method"]


        # ------------------------------------------
        # Convert amount
        # ------------------------------------------

        try:

            amount = float(amount)

        except ValueError:

            return "Please enter a valid amount."


        # Check amount

        if amount <= 0:

            return "Amount must be greater than 0."


        # ------------------------------------------
        # Read accounts
        # ------------------------------------------

        accounts = pd.read_csv(
            ACCOUNT_FILE
        )


        # ------------------------------------------
        # Check receiver UPI
        # ------------------------------------------

        if receiver_upi not in accounts["UPI_ID"].astype(str).values:

            return "Receiver UPI ID not found."


        # ------------------------------------------
        # Current date and time
        # ------------------------------------------

        date = datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )


        # ------------------------------------------
        # Create payment
        # ------------------------------------------

        new_payment = pd.DataFrame([{

            "Account_Type": account_type,

            "Receiver_UPI": receiver_upi,

            "Amount": amount,

            "Description": description,

            "Payment_Method": payment_method,

            "Date": date

        }])


        # ------------------------------------------
        # Save payment
        # ------------------------------------------

        new_payment.to_csv(
            PAYMENT_FILE,
            mode="a",
            header=False,
            index=False
        )


        # ------------------------------------------
        # Payment success
        # ------------------------------------------

        return render_template(
            "payment_success.html",

            receiver=receiver_upi,

            amount=amount,

            date=date
        )


    # ------------------------------------------
    # Open Send Money page
    # ------------------------------------------

    return render_template(
        "send_money.html"
    )


# =====================================================
# PAYMENT HISTORY
# =====================================================

@app.route("/payment-history")
def payment_history():

    payments = pd.read_csv(
        PAYMENT_FILE
    )

    records = payments.to_dict(
        orient="records"
    )

    return render_template(
        "payment_history.html",
        records=records
    )


# =====================================================
# ATM TRANSACTIONS
# =====================================================

@app.route("/transactions")
def transactions():

    df = load_data()

    search = request.args.get(
        "search",
        ""
    ).strip()


    if search:

        mask = df.astype(str).apply(

            lambda row:

            row.str.contains(
                search,
                case=False,
                na=False
            ).any(),

            axis=1
        )

        df = df[mask]


    records = df.to_dict(
        orient="records"
    )

    columns = df.columns.tolist()


    return render_template(
        "transactions.html",
        records=records,
        columns=columns,
        search=search
    )


# =====================================================
# ANALYTICS
# =====================================================

@app.route("/analytics")
def analytics():

    df = load_data()

    channel_data = (
        df["Channel"]
        .value_counts()
        .to_dict()
    )

    type_data = (
        df["TransactionType"]
        .value_counts()
        .to_dict()
    )

    occupation_data = (
        df["CustomerOccupation"]
        .value_counts()
        .to_dict()
    )

    location_data = (
        df["Location"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    login_data = (
        df["LoginAttempts"]
        .value_counts()
        .sort_index()
        .to_dict()
    )


    return render_template(
        "analytics.html",
        channel_data=channel_data,
        type_data=type_data,
        occupation_data=occupation_data,
        location_data=location_data,
        login_data=login_data
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )