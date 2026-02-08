from flask import Flask, render_template, session, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv('SECRET_KEY')
ADMIN_PASSWORD = os.getenv('ADMIN_TOKEN')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('Website')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db = SQLAlchemy(app)




# 1. Criteria Meta (The Categories)
class CriteriaMeta(db.Model):
    __tablename__ = 'criteria_meta'
    
    criteria_id = db.Column(db.Integer, primary_key=True)
    criteria_name = db.Column(db.Text, nullable=False)
    
    # Relationship: Allows access to studies via 'criteria.studies'
    # "secondary" tells SQLAlchemy to look through the 'all_studies' table to find the actual studies
    studies = db.relationship('StudyMeta', secondary='all_studies', backref='criterias')

# 2. Study Meta (The Projects/Candidates)
class StudyMeta(db.Model):
    __tablename__ = 'study_meta'
    
    study_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    study_name = db.Column(db.Text, nullable=False)
    
    # Relationship: Links to the votes so you can count them easily
    votes = db.relationship('PollTable', backref='study', lazy=True)

# 3. Ticket Meta (The Voters/QR Codes)
class TicketMeta(db.Model):
    __tablename__ = 'ticket_meta'
    
    # Diagram shows ticket_id is Text and is the Primary Key
    ticket_id = db.Column(db.Text, primary_key=True) 
    ticket_valid = db.Column(db.Boolean, nullable=False) #  '/'False' or 'Active'

# 4. All Studies (The "Connector" Table)
# This links Criteria to Studies (e.g., "Wind Farm" belongs to "Sustainable")
class AllStudies(db.Model):
    __tablename__ = 'all_studies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    criteria_id = db.Column(db.Integer, db.ForeignKey('criteria_meta.criteria_id'))
    study_id = db.Column(db.Integer, db.ForeignKey('study_meta.study_id'))

# 5. Poll Table (The Actual Votes)
class PollTable(db.Model):
    __tablename__ = 'poll_table'
    
    poll_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    study_id = db.Column(db.Integer, db.ForeignKey('study_meta.study_id'))
    ticket_id = db.Column(db.Text, db.ForeignKey('ticket_meta.ticket_id'))
    
    # Timestamps & Counts
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    vote_count = db.Column(db.Integer, default=1)

class AdminControls(db.Model):
    __tablename__ = 'admin'

    command_id = db.Column(db.Text, primary_key=True)
    command_state = db.Column(db.Boolean, nullable=False, default=False)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

### HOME
@app.route('/', methods=['GET', 'POST'])
def home():
    message_text = request.args.get('message', "See the Live Poll Below")
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'results':
            return redirect(url_for('results'))

    # 2. Pass it to your HTML variable {{ message }}
    return render_template('base.html', message=message_text)

def check_ticket_status(ticket_id):
    ticket_status = TicketMeta.query.filter_by(ticket_id=ticket_id).first()
    return ticket_status.ticket_valid

@app.route('/vote/<token>', methods=['GET', 'POST'])
def vote(token):
    # 1. Check if valid ticket (Ticket exists)
    ticket = TicketMeta.query.filter_by(ticket_id=token).first()
    if not ticket:
        message = "Ticket not found. Please try again."
        return redirect(url_for('home', message=message))
    
    # 2. Check if ticket is used (Status check)
    # Assuming 'check_ticket_status' returns False if used/invalid
    ticket_status = check_ticket_status(token)
    if ticket_status == False:
        message = "Ticket is invalid.\nYou may have already voted. If you believe this is wrong, please contact the admin."
        return redirect(url_for('home', message=message))
    
    # 3. Check if Poll is Open
    # Note: Using your variable 'command_state' from your snippet
    if get_poll_status().command_state == False:
        message = "Voting is not yet open. Please try again later."
        return redirect(url_for('home', message=message))

    # --- POST REQUEST: PROCESS THE VOTES ---
    if request.method == 'POST':
        try:
            # Step A: Loop through the dropdown data
            for key, value in request.form.items():
                # We are looking for keys like 'cat_1', 'cat_2', etc.
                if key.startswith('cat_'):
                    study_id_selected = int(value)
                    
                    # Create the Vote Entry
                    new_vote = PollTable(
                        ticket_id=token, 
                        study_id=study_id_selected
                    )
                    db.session.add(new_vote)
    
            # Step B: Burn the Ticket (Mark as invalid)
            # We already fetched the 'ticket' object at the top of the function
            ticket.ticket_valid = False  # Or whatever value you use for "Used"

            # Step C: Save everything
            db.session.commit()
            
            # Step D: Show Success Message
            success_message = "Your vote has been submitted successfully! Thank you."
            return redirect(url_for('home', message=success_message))

        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}"

    # --- GET REQUEST: RENDER THE FORM ---
    # Fetch all categories.
    categories = CriteriaMeta.query.all()

    # Pass the token to the template so the form knows where to submit
    return render_template('poll.html', categories=categories, token=token)

@app.route('/results')
def results():
    categories = CriteriaMeta.query.all()
    results_data = {} # Renamed from charts_data

    for cat in categories:
        cat_name = cat.criteria_name
        results_data[cat_name] = []
        
        # 1. Get all studies and counts first
        studies_with_votes = []
        max_votes = 0
        
        for study in cat.studies:
            count = PollTable.query.filter_by(study_id=study.study_id).count()
            if count > max_votes:
                max_votes = count
            studies_with_votes.append({'name': study.study_name, 'count': count})
            
        # 2. Calculate percentage relative to the leader (or total)
        # We use relative to leader so the winner always looks like a full bar
        for item in studies_with_votes:
            if max_votes > 0:
                percent = (item['count'] / max_votes) * 100
            else:
                percent = 0
            
            results_data[cat_name].append({
                'name': item['name'],
                'count': item['count'],
                'percent': percent
            })
            
    return render_template('results.html', results_data=results_data)


### ADMIN PORTION
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        # Check if the input password matches our master password
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True  # Set the session
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid Credentials. Please try again.'
    
    # Simple HTML form rendered directly for demonstration
    return render_template('admin_login.html', error=error)

# 3. THE PROTECTED ADMIN ROUTE
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    # The Gatekeeper: Check if the key exists in the session
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get the row from your table
    poll_setting = get_poll_status()

    if request.method == 'POST':
        action = request.form.get('action')

        # --- TOGGLE SWITCH ---
        if action == 'toggle_poll':
            # Flip the boolean value in your 'command_state' column
            poll_setting.command_state = not poll_setting.command_state
            db.session.commit()
            
            state = "OPEN" if poll_setting.command_state else "CLOSED"
            flash(f"Poll is now {state}", "success")

        # --- RESET POLL ---
        elif action == 'reset_poll':
            try:
                # This wipes the votes, but keeps your categories/studies
                deleted_rows = db.session.query(PollTable).delete()
                rows = db.session.query(TicketMeta).update({TicketMeta.ticket_valid: True})
                db.session.commit()
                flash(f"Reset Complete: {deleted_rows} votes deleted.", "warning")
                flash(f"Success: {rows} tickets re-activated!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {e}", "danger")
        
        # ---- RESET DB
        elif action == 'reset_db':
            try:
                print("Resetting database...")
                # Drops all tables defined in the models
                db.session.commit()
                db.drop_all()
                print("All tables dropped.")
                
                # Recreates the tables (empty)
                db.create_all()
                flash("All tables recreated successfully. Database is now empty.")
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {e}", "danger")
        
        # --- Logout -----
        elif action == 'logout':
            session.pop('logged_in', None) # Remove the token
            return redirect(url_for('logout'))
        
        return redirect(url_for('admin_dashboard'))

    # Pass the boolean value to the template
    # poll_setting.command_state holds the True/False value
    total_votes = PollTable.query.count()
    return render_template('admin_dashboard.html', 
                           is_poll_open=poll_setting.command_state, 
                           total_votes=total_votes)

# 4. THE LOGOUT ROUTE
@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Remove the token
    return redirect(url_for('login'))

# app.py

def get_poll_status():
    """
    Retrieves the poll status from AdminControls.
    Creates the row if it doesn't exist yet.
    """
    # We use 'POLL_STATUS' as the unique ID for this setting
    status_setting = AdminControls.query.get('POLL_STATUS')
    
    if not status_setting:
        # If missing, create it! Default to False (Closed)
        status_setting = AdminControls(command_id='POLL_STATUS', command_state=False)
        db.session.add(status_setting)
        db.session.commit()
        
    return status_setting


if __name__ =="__main__":
    app.run(debug=True)