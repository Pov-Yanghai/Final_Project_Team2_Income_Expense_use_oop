import re 
import csv
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
## library for graph visualization
import seaborn as sns 
import matplotlib.pyplot as plt
plt.style.use('seaborn-v0_8-darkgrid')
## ----------------------
## FIle store users infromation for admin 
USER_FILE = "users.csv"
### clear system easy for testing 
def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

# Transaction classes
class Transaction(ABC):
    def __init__(self, amount, date, description, currency):
        self.amount = abs(amount) ## amount is absolute value ensure amount is not negative 
        self.date = date
        self.description = description
        self.currency = currency

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def __str__(self):
        pass
# Income class child class 
class Income(Transaction):
    def __init__(self, amount, date, source, description=None, currency="INR"):
        super().__init__(amount, date, description, currency)
        self.source = source
## Type income 
    def get_type(self):
        return "Income"
## format 
    def __str__(self):
        return (f"{self.date.strftime('%d/%m/%Y')} | INCOME  | "
                f"Source: {self.source} | "
                f"{self.amount:.2f}{self.currency} | {self.description}")
### Exspense class  child class 
class Expense(Transaction):
    def __init__(self, amount, date, category, subcategory,mode, description=None, currency="INR"):
        super().__init__(amount, date, description, currency)  ## super function 
        self.category = category  
        self.subcategory = subcategory
        self.mode = mode
## Type Expese 
    def get_type(self):
        return "Expense"

    def __str__(self):
        return (f"{self.date.strftime('%d/%m/%Y')} | EXPENSE | "
                f"{self.mode} | {self.category}/{self.subcategory} | "
                f"{self.amount:.2f}{self.currency} | {self.description}")
## Report To user if user expsense more than income 
class Report_To_User:
    def __init__(self, transactions):
        self.transactions = transactions

    def generate(self):
        report = {
            'total_income': 0,
            'total_expense': 0,
            'income_sources': {},
            'expense_categories': {},
            'payment_modes': {}
        }

        for transaction in self.transactions:
            if isinstance(transaction, Income):
                report['total_income'] += transaction.amount
                report['income_sources'][transaction.source] = report['income_sources'].get(transaction.source, 0) + transaction.amount
            elif isinstance(transaction, Expense):
                report['total_expense'] += transaction.amount
                key = f"{transaction.category}/{transaction.subcategory}"
                report['expense_categories'][key] = report['expense_categories'].get(key, 0) + transaction.amount
                report['payment_modes'][transaction.mode] = report['payment_modes'].get(transaction.mode, 0) + transaction.amount

        report['net_savings'] = report['total_income'] - report['total_expense']
        return report

# User Management
class User:
    def __init__(self, user_id, fullname, username, password, role="User"):
        self._user_id = user_id
        self.fullname = fullname
        self._username = username
        self._password = password
        self.role = role
        self._transactions = []
        self._filename = "house.csv"
        self._load_transactions()
    ### Graph for user bar chart( compare their expense and income monthly and pie chart show what they get income and expsense monthly)
    def generate_user_graphs(self):
        """Generate financial graphs for regular users with enhanced visuals"""
        month_input = input("Enter month (MM/YYYY): ")
        if not check_input_month_and_year(month_input):
            print("Invalid month format! Use MM/YYYY")
            return

        target_month = datetime.strptime(month_input, "%m/%Y")
        filtered = [
            t for t in self._transactions
            if t.date.month == target_month.month
            and t.date.year == target_month.year
        ]
        
        if not filtered:
            print("No transactions found for this month")
            return

        # Income vs Expense Comparison
        income = sum(t.amount for t in filtered if isinstance(t, Income))
        expense = sum(t.amount for t in filtered if isinstance(t, Expense))
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(['Income', 'Expense'], [income, expense], color=['green', 'red'])
        ax.set_title(f"Income vs Expense - {month_input}", fontsize=14)
        ax.set_ylabel("Amount", fontsize=12)
        
        # Display value above each bar
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 50, f"{yval:.2f}", ha='center', fontsize=12)
        
        plt.show()

        # Expense Breakdown (Pie Chart)
        expenses = [t for t in filtered if isinstance(t, Expense)]
        if expenses:
            categories = {}
            for t in expenses:
                key = f"{t.category}/{t.subcategory}"
                categories[key] = categories.get(key, 0) + t.amount
            
            fig, ax = plt.subplots(figsize=(8, 8))
            colors = sns.color_palette("coolwarm", len(categories))
            wedges, texts, autotexts = ax.pie(categories.values(), labels=None, autopct='%1.1f%%',
                                            startangle=140, colors=colors,
                                            wedgeprops={'edgecolor': 'black'})
            ax.set_title(f"Expense Categories - {month_input}", fontsize=14)
            plt.setp(autotexts, size=10, weight='bold')
            
            # Add legend with percentage values
            legend_labels = [f"{cat}: {amt:.2f}" for cat, amt in categories.items()]
            plt.legend(legend_labels, loc="best", bbox_to_anchor=(1, 0.5))
            plt.show()
        if income > 0:
            income_sources = [t for t in filtered if isinstance(t, Income)]
            if income_sources:
                income_categories = {}
                for t in income_sources:
                    # Use 'source' as the key for income breakdown
                    key = t.source if t.source else 'Unknown'
                    income_categories[key] = income_categories.get(key, 0) + t.amount

                fig, ax = plt.subplots(figsize=(8, 8))
                colors = sns.color_palette("viridis", len(income_categories))  # Using a vibrant palette for better contrast
                wedges, texts, autotexts = ax.pie(income_categories.values(), labels=None, autopct='%1.1f%%',
                                                startangle=140, colors=colors,
                                                wedgeprops={'edgecolor': 'black'})
                ax.set_title(f"Income Sources - {month_input}", fontsize=14)
                plt.setp(autotexts, size=10, weight='bold')
                
                # Add legend with percentage values
                legend_labels = [f"{cat}: {amt:.2f}" for cat, amt in income_categories.items()]
                plt.legend(legend_labels, loc="best", bbox_to_anchor=(1, 0.5))
                plt.show()


## load transaction from file that detail user input  for user management  and store in house.csv file 
    def _load_transactions(self):
        if os.path.exists(self._filename):
            try:
                df = pd.read_csv(
                    self._filename,
                    parse_dates=['Date'],
                    dayfirst=False,
                    dtype={'UserID': str, 'Currency': 'category'},
                    on_bad_lines='skip'
                )
  ## Ensure require columns exist, filling missing with empty  string ''
                for col in ['Subcategory', 'Mode', 'Note', 'Currency']:
                    if col not in df.columns:
                        df[col] = ''

   # Filter and clean data
                df['UserID'] = df['UserID'].astype(str)
                df = df[df['UserID'] == self._user_id]
                df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
                df = df.dropna(subset=['Date'])

                self._transactions = []
                for _, row in df.iterrows():
                    try:
                        if row['Income/Expense'] == 'Income': ## check if column of row is Income and then load  each row 
                            self._transactions.append(Income(
                                amount=row['Amount'],
                                date=row['Date'],
                                source=row['Category'],
                                description=row['Note'],
                                currency=row['Currency']
                            ))
                        else:
                            self._transactions.append(Expense(
                                amount=row['Amount'],
                                date=row['Date'],
                                category=row['Category'],
                                subcategory=row['Subcategory'],
                                mode=row['Mode'],
                                description=row['Note'],
                                currency=row['Currency']
                            ))
                    except Exception as error_message:
                        print(f"Error loading transaction: {error_message}")
            except Exception as error_message:
                print(f"Error loading transactions: {error_message}")
## save transaction for each user to house transaction 
    def save_transactions(self):
        if not self._transactions:
            return ## nothing to save
        try:
             ## Column for the CSV that will save to 
            columns = ['UserID', 'Date', 'Mode', 'Category', 'Subcategory', 'Note', 'Amount', 'Income/Expense', 'Currency']
            new_data = []
            for transaction in self._transactions:
                entry = {
                    'UserID': self._user_id,
                    'Date': transaction.date.strftime('%d/%m/%Y'),
                    'Mode': transaction.mode if isinstance(transaction, Expense) else '',
                    'Category': transaction.source if isinstance(transaction, Income) else transaction.category,
                    'Subcategory': transaction.subcategory if isinstance(transaction, Expense) else '',
                    'Note': transaction.description or '',
                    'Amount': transaction.amount,
                    'Income/Expense': transaction.get_type(),
                    'Currency': transaction.currency
                }
                new_data.append(entry)## Add Transaction to list new_data

            if os.path.exists(self._filename): ## Check if file already exists
                existing_df = pd.read_csv(self._filename, dtype={'UserID': str}) ## Read existing file ensure no duplicate
                new_df = pd.DataFrame(new_data, columns=columns)## Create Data Frame for new trasaction
                combined_df = pd.concat([existing_df, new_df])  ## merge new and existing transaction 
                combined_df = combined_df.drop_duplicates( ## Drop dupplicate transaction 
                    subset=['UserID', 'Date', 'Amount', 'Income/Expense'],
                    keep='last'
                )
            else:
                ## if the file not exist, create new data frame for example new new correctt to column in csv file 
                combined_df = pd.DataFrame(new_data, columns=columns)
            ## after add save to file 
            combined_df.to_csv(self._filename, index=False)
        except Exception as e:
            print(f"Error saving transactions: {e}")## if error occurs in file  print this 
## add transaction to house.csv file details user information 
    def add_transaction(self, transaction):   ## add transaction to user table 
        self._transactions.append(transaction)
        self.save_transactions()

    def get_transactions(self):
        return self._transactions.copy()
# user id is private 
    @property
    def user_id(self):
        return self._user_id
## username is private 
    @property
    def username(self):
        return self._username
## password verification for password ensure password is correct
    def verify_password(self, password):
        return self._password == password

class Admin(User):
    def __init__(self, user_id, fullname, username, password):
        super().__init__(user_id, fullname, username, password, role="Admin")
    ## show admin activity each user 
    def generate_admin_graphs(self):
        """Generate admin analytics dashboard with enhanced visuals"""
        if not os.path.exists("house.csv"):
            print("No transactions found!")
            return
        
        try:
            # Load and process the data
            df = pd.read_csv("house.csv", parse_dates=['Date'], dayfirst=True, infer_datetime_format=True)
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df.dropna(subset=['Date'])
            df['Month'] = df['Date'].dt.to_period('M')
            
            # Aggregate data by month and income/expense
            monthly = df.groupby('Month').agg(
                Income=('Amount', lambda x: x[df['Income/Expense'] == 'Income'].sum()),
                Expense=('Amount', lambda x: x[df['Income/Expense'] == 'Expense'].sum())
            ).reset_index()

            # Monthly Trends Chart
            fig, ax1 = plt.subplots(figsize=(12, 6))
            ax1.plot(monthly['Month'].astype(str), monthly['Income'], marker='o', linestyle='-', color='green', label='Income')
            ax1.plot(monthly['Month'].astype(str), monthly['Expense'], marker='o', linestyle='-', color='red', label='Expense')
            ax1.set_title("System-wide Monthly Trends", fontsize=16, weight='bold')
            ax1.set_xlabel("Month", fontsize=12)
            ax1.set_ylabel("Amount (Currency)", fontsize=12)
            ax1.legend(loc='upper left')
            plt.xticks(rotation=45)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.show()

            # User Activity Heatmap
            activity = df.groupby(['UserID', 'Month']).size().unstack(fill_value=0)
            
            plt.figure(figsize=(12, 6))
            sns.heatmap(activity, cmap="Blues", annot=True, fmt="d", linewidths=0.5, cbar_kws={'label': 'Number of Transactions'})
            plt.title("User Transaction Activity (Monthly)", fontsize=16, weight='bold')
            plt.xlabel("Month", fontsize=12)
            plt.ylabel("User ID", fontsize=12)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        

        except Exception as e:
            print(f"Error generating admin graphs: {e}")
def load_users():   ## ## load users  completely function to load users from user.csv file
    users = []
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        user_id = row['UserID']
                        fullname = row['Full Name']
                        username = row['Username']
                        password = row['Password']
                        role = row.get('Role', 'User').strip() # Ensure clean role value 
                        if role == 'Admin':
                            user = Admin(user_id, fullname, username, password)
                        else:
                            user = User(user_id, fullname, username, password, role)
                        users.append(user)
                    except KeyError as e:
                        print(f"Error loading user: {e}")
        except Exception as e:
            print(f"Error loading users: {e}")

    admin_exists = any(user.role == "Admin" for user in users)
    if not admin_exists:
        existing_ids = [user.user_id for user in users]
        if "1" not in existing_ids:
            admin = Admin("1", "Admin", "admin", "admin123")
            users.append(admin)
            save_users(users)
        else:
            print("Error: User ID '1' is already taken by a regular user")
    
    return users
## Save user name to user.csv file    file store only information users.csv 
def save_users(users):
    try:
        with open(USER_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["UserID", "Full Name", "Username", "Password", "Role"])
            for user in users:
                writer.writerow([
                    user.user_id,
                    user.fullname,
                    user.username,
                    user._password,
                    user.role
                ])
    except Exception as e:
        print(f"Error saving users: {e}")
## function add transaction from user input their monthly transaction 
def add_transaction(user):  ## ## completed function add transaction to user
    try:
        print("\nAdd New Transaction:")
        date = input("Date (DD/MM/YYYY): ")
        mode = input("Mode (Cash/Bank/etc): ").strip()
        category = input("Category: ").strip()
        subcategory = input("Subcategory: ").strip() or "Miscellaneous"
        note = input("Note: ").strip()
        amount = float(input("Amount: "))
        trans_type = input("Type (Income/Expense): ").capitalize()
        currency = input("Currency (INR): ") or "INR"

        parsed_date = datetime.strptime(date, "%d/%m/%Y")

        if trans_type == "Income":
            transaction = Income(
                amount=amount,
                date=parsed_date,
                source=category,
                description=note,
                currency=currency
            )
        else:
            transaction = Expense(
                amount=amount,
                date=parsed_date,
                category=category,
                subcategory=subcategory,
                mode=mode,
                description=note,
                currency=currency
            )

        user.add_transaction(transaction)
        print("Transaction added successfully!")

    except ValueError as error_message:
        print(f"\nInvalid input: {error_message}")
    except Exception as error_message:
        print(f"\nError: {error_message}")
## check input correct for mat 
def check_input_month_and_year(input_string):
    try:
        ## using the `strptime` method of `datetime` to convert the string into a datetime object.
        datetime.strptime(input_string, "%m/%Y")## format to input months and year
        return True
    except ValueError:
        return False
    
#   update the transaction
def update_transaction(user=None):
    while True:
        try:
            date_inputed = input("Enter date (DD/MM/YYYY): ").strip()
            category_inputed = input("Enter category: ").strip()
            amount_inputed = float(input("Enter amount: "))

            file_read = []
            matched_row = None
            match_index = -1

            #Read all rows from file
            with open('house.csv', 'r', newline='') as f_read:
                reader = csv.reader(f_read)
                file_read = list(reader)

            #Search for matching row
            for index, row in enumerate(file_read):
                if len(row) < 8:
                    continue  # skip incomplete rows

                row_date = row[1].strip()
                row_category = row[3].strip()
                try:
                    row_amount = float(row[6])
                except:
                    continue  # skip rows where amount is not a number

                if row_date == date_inputed and row_category.lower() == category_inputed.lower() and row_amount == amount_inputed:
                    matched_row = row
                    match_index = index
                    break

            if matched_row:
                print("\n===Transaction Found===")
                print("---------------------------------------------------------------------------------")
                print(" | ".join(matched_row))
                print("---------------------------------------------------------------------------------")
                # Take new input to update fields
                print("->Leave blank will keep current value<-")

                new_date = input(f"Update '{matched_row[1]}' to ?: ").strip()
                new_category = input(f"Update '${matched_row[3]}' to ?: ").strip()
                new_note = input(f"Update note '{matched_row[5]}' to ?: ")
                new_amount = input(f"Update '{matched_row[6]}' to ?: ").strip()
                new_inr = input(f"Update '{matched_row[8]}' to ?: ").strip()

                if new_date:
                    matched_row[1] = new_date
                if new_category:
                    matched_row[3] = new_category
                if new_note:
                    matched_row[5] = new_note
                if new_amount:
                    matched_row[6] = new_amount
                if new_inr:
                    matched_row[8] = new_inr
                

                #Replace the old row in file_read with updated row
                file_read[match_index] = matched_row

                #Write the updated data back to the file
                with open('house.csv', 'w', newline='') as f_write:
                    writer = csv.writer(f_write)
                    writer.writerows(file_read)

                print("\nTransaction have update.")
                break
            else:
                print("\nMissing (Date,or  Category, orAmount). Please try again.\n")

        except ValueError as ve:
            print(f"Invalid input: {ve}. Try again.")
        except Exception as e:
            print(f"Unexpected error: {e}")

def generate_report_ui(user):
    month_input = input("Enter month (MM/YYYY): ")
    if not check_input_month_and_year(month_input):
        print("Invalid month format! Use MM/YYYY (format:  03/2023)")   ## check by month and report to user by month 
        return
 # if it true format  Parsing the string into a datetime object  like input 03/2025 => %m/%Y 
    target_month = datetime.strptime(month_input, "%m/%Y")
    filtered = [
        transaction for transaction in user.get_transactions()## user loop to find transaction in transactions check user by month and year 
        if transaction.date.month == target_month.month
        and transaction.date.year == target_month.year
    ]

    if not filtered:
        print("\nNo transactions found for this month")
        return

    report = Report_To_User(filtered).generate()

    print(f"\n{' Monthly Financial Report ':=^50}")
    print(f"Period: {month_input}")
    print(f"\nIncome: {report['total_income']:.2f}")
    print(f"Expenses: {report['total_expense']:.2f}")
    print(f"Net Savings: {report['net_savings']:.2f}")


    print("\nIncome Sources:")
    for source, amount in report['income_sources'].items():
        print(f"- {source}: {amount:.2f}")

    print("\nExpense Categories:")
    for category, amount in report['expense_categories'].items():
        print(f"- {category}: {amount:.2f}")

    print("\nPayment Methods:")
    for mode, amount in report['payment_modes'].items():
        print(f"- {mode}: {amount:.2f}")

    if report['total_income'] < report['total_expense']:
        print("\nWarning: You are overspending ⚠️")
        print("- You should consider cutting back on unnecessary expenses!")
        print("- Track your daily expenses and prioritize essential spending only.")
    
    elif report['total_expense'] >= 0.8* report['total_income']:
        print("\nWarning: You are spending too much on expenses ⚠️")
        print("- You have spent more than 80% of your income")
        print("- Track your daily expenses and prioritize essential spending only.")


    
##Transactio for admin 
def report_transaction(user):
    month_input = input("Enter month (MM/YYYY) or leave blank to See all transaction: ")
    transactions = user.get_transactions()
    
    if month_input:
        if not check_input_month_and_year(month_input):
            print("Invalid month format. Please try again.")
            return
        target_month = datetime.strptime(month_input, "%m/%Y")
        transactions = [
            transaction for transaction in transactions
            if transaction.date.month == target_month.month
            and transaction.date.year == target_month.year
        ]

    print(f"\n{' Transaction History ':=^50}")
    if transactions:
        print(f"{'Date':<10} | {'Type':<7} | {'Category':<20} | {'Amount':<10} | {'Description'}")
        print("-" * 70) ## format interface to user 
        for transaction in transactions:
                 ## format date 
            date_str = transaction.date.strftime('%d/%m/%Y')
            t_type = transaction.get_type()
               ## Type of transaction type (Expensse and Income )
            category = (transaction.source if isinstance(transaction, Income)
                        else f"{transaction.category}/{transaction.subcategory}")
            amount = f"{transaction.amount:.2f}{transaction.currency}"
             # Get description 
            description = transaction.description or ""
            
            print(f"{date_str} | {t_type:<7} | {category:<20} | {amount:>10} | {description}")
        print("-" * 70)
        print(f"Total transactions: {len(transactions)}")
        ## Toatal of transaction 
    else:
        print("No transactions found")

# delete transaction by date 
def delete_transaction_by_date(date):
    house_file = 'house.csv'
    users_file = 'users.csv'
    
    def filter_transactions(file_path, date):
        updated_rows = []
        deleted = False 
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file)
            header = next(reader)
            updated_rows.append(header)
            for row in reader:
                # date is in the second column (DD/MM/YY)
                if date in row[1]: 
                    deleted = True 
                else:
                    updated_rows.append(row)
        if deleted:
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(updated_rows)
            # Successfully deleted
            return True 
        else:
            return False 
        
    house_deleted = filter_transactions(house_file,date)
    users_deleted = filter_transactions(users_file,date)
    
    if house_deleted or users_deleted:
        print(f"Transactions from {date} have been deleted successfully.")
    else:
        print(f"No transactions found for {date}.")


# delete user from transaction by id
def delete_transaction_by_id(transaction_id):
    house_deleted = False
    users_deleted = False
    # Read house.csv and filter out the transaction
    with open('house.csv', mode='r', newline='') as file:
        reader = csv.reader(file)
        house_transactions = [row for row in reader]
    updated_house_transactions = [row for row in house_transactions if row and row[0] != transaction_id]
    if len(updated_house_transactions) < len(house_transactions):
        house_deleted = True
    # Update house.csv
    with open('house.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(updated_house_transactions)
    # Read users.csv and filter out the transaction
    with open('users.csv', mode='r', newline='') as file:
        reader = csv.reader(file)
        users_transactions = [row for row in reader]
    updated_users_transactions = [row for row in users_transactions if row and row[0] != transaction_id]

    if len(updated_users_transactions) < len(users_transactions):
        users_deleted = True
    # Update users.csv
    with open('users.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(updated_users_transactions)
    # Print appropriate message
    if house_deleted or users_deleted:
        print(f"Transaction ID {transaction_id} deleted successfully.")
    else:
        print(f"Transaction ID {transaction_id} not found.")

## login () function 
def login():
    clear_screen()
    print("\n" + "="*39) 
    print("\n=============== Log In ================\n")
    print("="*39) 
  
    username = input("Enter your Username: ").strip()
    password = input("Enter your Password: ").strip()
    users = load_users()
    
    if not users:
        print("No users found. Please sign up first.")
        input()
        return None

    for user in users:
        if user.username == username and user.verify_password(password):
            print(f"\nLogin successful! Welcome {username} ({user.role})")
            return user
    print("\nInvalid username or password")
    input()
    return None
## user menu for user interface that user can choose option  
def user_menu(user):
    while True:
        clear_screen()
        print("\n"+"="*38)
        print(f"\n========== Welcome {user.username} ==========\n")
        print("="*38)
        if isinstance(user, Admin):   ## if they admin admin's interface 
            print("1. View All Transactions")
            print("2. View User Transactions")
            print("3. System Statistics")
            print("4. Delete User From System")
            print("5. Analyse System Statistics")
            print("6. Logout")
            choice = input("Choose option: ").strip()
            if choice == '1':
                view_all_transactions()
            elif choice == '2':
                user_id = input("Enter user ID: ")
                users = load_users()
                target = next((user for user in users if user.user_id == user_id), None)
                if target:
                    report_transaction(target)
                else:
                    print("User not found!")
            elif choice == '3':
                print("\nSystem Statistics:")
                users = load_users()
                print(f"Total Users: {len(users)}")
                print(f"Admins: {sum(1 for user in users if isinstance(user, Admin))}")
                print(f"Regular Users: {sum(1 for user in users if not isinstance(user, Admin))}")
            elif choice == "4":
                transaction_id = input("Enter Transaction ID to delete: ")
                delete_transaction_by_id(transaction_id)
            elif choice == '5':
                user.generate_admin_graphs()
            elif choice == '6':
                break
            else:
                print("Invalid choice!")
        else:   ### if they are user not admin 
            print("1. Add Transaction")
            print("2. Update Transaction")
            print("3. View Monthly Report")
            print("4. View Transaction History")
            print("5. Delete Transaction")
            print("6. View Your activities monthly report by Graph")
            print("7. Logout")
            choice = input("Choose option: ").strip()
            if choice == '1':
                add_transaction(user)
            elif choice == '2':
                update_transaction(user)
            elif choice == '3':
                generate_report_ui(user)
            elif choice == '4':
                report_transaction(user)
            elif choice == "5":
                date_to_delete = input("Enter the date (MM/YYYY) to delete transactions: ")
                delete_transaction_by_date(date_to_delete)
            elif choice == '6':
                user.generate_user_graphs()
            elif choice == '7':
                break 
            else:
                print("Invalid choice!")
        input("\nPress Enter to continue...")
## view all transaction for admin 
def view_all_transactions():
    if os.path.exists("house.csv"):
        try:
            df = pd.read_csv("house.csv", dtype={'UserID': str})
            print("\nAll Transactions:")
            print(df.to_string(index=False))
        except Exception as e:
            print(f"Error reading transactions: {e}")
    else:
        print("No transactions found!")

## check password 
def is_valid_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not any(char.isupper() for char  in password):
        return "Password must contain at least one uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None 
# Signup for new user
def signup():
    clear_screen()
    print("\n" + "="*39) 
    print("\n=============== Sign Up ===============")
    print("\n" + "="*39) 
    while True:
        fullname = input("Enter your full name: ").strip() # Using strip() to remove unwant space
        if not re.match("^[A-Za-z ]+$", fullname):
            print("Do not put any digit or special characters.")
        elif len(fullname) > 30:
            print("Your full name is too long! Please enter a name with 30 characters or fewer.")
        elif len(fullname) == 0:
            print("Full name cannot be empty. Please enter your name.")
        else:
            break
    username = input("Enter your username: ").strip()
    while True:
        password = input("Enter your password: ").strip()
        error = is_valid_password(password)
        if error:
            print(f"Invalid password: {error}")
        else:
            while True:
                confirm_password = input("Confirm password: ")
                if confirm_password == password:
                    break
                else:
                    print("Password do not match! Please try again.")
            break
    users = load_users()
    if any(u.username == username for u in users):
        print("Username already exists!")
        input("Press any key to continue...")
        return None
## increase id for each user after they input 
    existing_ids = [int(u.user_id) for u in users if u.user_id.isdigit()]
    new_id = str(max(existing_ids) + 1) if existing_ids else '1'

    new_user = User(new_id, fullname, username, password)
    users.append(new_user)
    save_users(users)
    print("\nRegistration successful!")
    return new_user

def main():
    while True:
        clear_screen()
        print("\n" + "="*50)
        print("\n====== User's Monthly Income/Expense Tracker =====\n")
        print("="*50)
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit")
        choice = input("Choose option: ").strip()

        if choice == '1':
            user = login()
            if user:
                user_menu(user)
        elif choice == '2':
            user = signup()
            if user:
                input("Press Enter to continue...")
        elif choice == '3':
            print("Goodbye! Thanks for Come to Test our project!")
            break
        else:
            print("Invalid choice!")
            input("Press Enter to continue...")

if __name__ == '__main__':
    main()  
    ### Sina


