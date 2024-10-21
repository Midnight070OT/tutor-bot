from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

def load_tutor_data():
    """Load the tutor data from the CSV."""
    file_path = r"C:\Users\danuf_0rg2aqw\ngrok\Schedule By Class(MATH).csv"
    data = pd.read_csv(file_path)

    courses = data.iloc[0, 1:].dropna().tolist()
    tutors = {}
    for _, row in data.iloc[1:].iterrows():
        tutor_name = row["Tutor/Specialist"]
        if pd.notna(tutor_name):
            tutor_courses = [
                course for course, available in zip(courses, row[1:]) if available == 'x'
            ]
            tutors[tutor_name] = tutor_courses

    return tutors, courses

tutors, courses = load_tutor_data()

@app.route("/availability", methods=["GET", "POST"])
def availability():
    if "availability" not in session:
        session["availability"] = {tutor: False for tutor in tutors.keys()}
    if "accepted_students" not in session:
        session["accepted_students"] = {tutor: 0 for tutor in tutors.keys()}
    if "declined_sessions" not in session:
        session["declined_sessions"] = {tutor: 0 for tutor in tutors.keys()}

    if request.method == "POST":
        session["availability"] = {
            tutor: (tutor in request.form) for tutor in tutors.keys()
        }
        session.modified = True
        return redirect(url_for("availability"))

    return render_template(
        "availability.html", tutors=tutors, courses=courses, availability=session["availability"]
    )

@app.route("/recommend/<course>")
def recommend(course):
    """Recommend the available tutor with the fewest accepted students."""
    declined = session.get("declined_tutors", [])

    # Filter tutors who are available, teach the requested course, and are not declined
    eligible_tutors = [
        tutor for tutor, tutor_courses in tutors.items()
        if course in tutor_courses and session["availability"].get(tutor, False) and tutor not in declined
    ]

    # If there are eligible tutors, suggest the one with the fewest accepted students
    if eligible_tutors:
        recommendation = min(
            eligible_tutors, 
            key=lambda t: session["accepted_students"].get(t, 0)  # Sort by accepted student count
        )
    else:
        session["declined_tutors"] = []  # Reset declined list if no eligible tutors
        recommendation = None

    return render_template("recommendation.html", course=course, recommendation=recommendation)


@app.route("/accept", methods=["POST"])
def accept():
    """Track accepted students per tutor."""
    tutor_name = request.form.get("tutor")
    if tutor_name:
        session["accepted_students"][tutor_name] += 1
        session.modified = True
    return redirect(url_for("availability"))

@app.route("/decline", methods=["POST"])
def decline():
    """Track declined sessions per tutor."""
    if "declined_tutors" not in session:
        session["declined_tutors"] = []

    tutor_name = request.form.get("tutor")
    if tutor_name:
        if tutor_name not in session["declined_tutors"]:
            session["declined_tutors"].append(tutor_name)

        session["declined_sessions"][tutor_name] += 1
        session.modified = True

    return redirect(request.referrer)

@app.route("/in-session", methods=["POST"])
def in_session():
    """Mark tutor as 'in a session'."""
    tutor_name = request.form.get("tutor")
    if tutor_name:
        session["availability"][tutor_name] = False  # Mark as unavailable
        session.modified = True

    return redirect(url_for("availability"))

@app.route("/stats")
def stats():
    """Display statistics for the day."""
    return render_template(
        "stats.html",
        accepted=session["accepted_students"],
        declined=session["declined_sessions"]
    )
@app.route("/reset-stats", methods=["POST"])
def reset_stats():
    """Reset all statistics and session data."""
    session["accepted_students"] = {tutor: 0 for tutor in tutors.keys()}
    session["declined_sessions"] = {tutor: 0 for tutor in tutors.keys()}
    session["declined_tutors"] = []
    session.modified = True  # Ensure session updates are saved
    return redirect(url_for("stats"))

if __name__ == "__main__":
    app.run(debug=True)
