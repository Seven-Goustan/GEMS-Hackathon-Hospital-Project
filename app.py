from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs

PLACEHOLDER = '<!-- RESULTS_PLACEHOLDER -->'

# Must match the option/checkbox values in index.html. Anything else that comes in
# the POST body is dropped (or falls back to the default) rather than echoed back.
AGE_GROUPS = ('youth', 'adult', 'senior')
ACTIVITY_LEVELS = ('sedentary', 'moderate', 'active')
CONDITION_NAMES = {
    'hypertension': 'High blood pressure',
    'diabetes': 'Type 2 diabetes',
    'joint_pain': 'Joint pain',
    'acid_reflux': 'Acid reflux',
}
CONCERN_NAMES = {
    'fatigue': 'Fatigue',
    'anxiety': 'Anxiety or stress',
    'insomnia': 'Sleep concerns',
    'brain_fog': 'Focus concerns',
    'burnout': 'Burnout',
}


def as_list_items(lines):
    return "".join("<li>" + line + "</li>" for line in lines)


def diet_advice(conditions, concerns):
    tips = ["Choose regular meals with vegetables, a protein source, and high-fibre carbohydrates."]

    if "diabetes" in conditions:
        tips.append("For diabetes: favour high-fibre foods and steady meal patterns; follow your care team's food and medication advice.")
    if "hypertension" in conditions:
        tips.append("For blood pressure: choose less processed food where practical and follow your clinician's sodium guidance.")
    if "joint_pain" in conditions:
        tips.append("For joint comfort: include a variety of whole foods, such as leafy vegetables, nuts, and oily fish if suitable.")
    if "acid_reflux" in conditions:
        tips.append("For reflux: notice personal food triggers and consider smaller meals; avoid lying down soon after eating.")

    # brain fog and burnout have no food-specific advice, only the wellbeing card covers them
    if "fatigue" in concerns:
        tips.append("For fatigue: plan regular meals and water breaks; seek medical advice if fatigue is new, severe, or persistent.")
    if "anxiety" in concerns: 
        tips.append("For stress or anxiety: notice whether caffeine affects you and consider reducing it if it worsens symptoms.")


    if "insomnia" in concerns:
        tips.append("For sleep: keep a consistent bedtime routine and limit stimulating drinks or activities near bedtime.")

    return as_list_items(tips)


def activity_advice(activity, conditions, concerns):
    if activity == "sedentary":
        tips = ["Start with a comfortable 10–20 minute walk or gentle movement on most days."]
    elif activity == "moderate":
        tips = ["Keep a steady routine of moderate activity, such as a brisk walk, at a pace that feels manageable."]
    else:
        tips = ["Balance your regular activity with recovery days and strength or flexibility work as appropriate."]

    if "joint_pain" in conditions:
        tips.append("For joint pain: choose low-impact movement, such as swimming or cycling, and stop if pain increases.")
    if "hypertension" in conditions:
        tips.append("For high blood pressure: build activity gradually, avoid breath-holding during effort, and follow medical advice.")
    if "diabetes" in conditions:
        tips.append("For diabetes: follow your clinician's guidance about activity, medications, and checking blood glucose.")

    if "fatigue" in concerns or "burnout" in concerns:
        tips.append("For low energy: try shorter, gentle sessions and rest when needed instead of pushing through exhaustion.")

    return as_list_items(tips)


def wellbeing_advice(concerns):
    # if no onnw ticked anything still 8t gives sugesstions
    if not concerns:
        return as_list_items([
            "Try a brief daily pause such as slow breathing, a short walk, or a quiet screen-free break.",
            "Keep a regular sleep and wake schedule when possible, and reach out for support if concerns persist .",
        ])

    tips = []
    if "fatigue" in concerns:
        tips.append("For fatigue: schedule manageable rest breaks and discuss ongoing or worsening tiredness with a clinician.")
    
    
    
    if "anxiety" in concerns:
        tips.append("For anxiety or stress: try slow breathing or grounding; contact a trusted person or qualified professional for support.")
    if "insomnia" in concerns:
        tips.append("For sleep concerns: use a consistent wind-down routine and discuss persistent sleep problems with a clinician.")
    if "brain_fog" in concerns:
        tips.append("For focus: break tasks into smaller steps, take short breaks, and seek advice if symptoms persist or worsen.")
    
    if "burnout" in concerns:
        tips.append("For burnout: set realistic priorities, take regular breaks, and ask for support with ongoing demands.")
    return as_list_items(tips)


def profile_summary(age, activity, conditions, concerns):
    if age == "youth":
        age_label = "Youth (under 18)"
        age_note = "A trusted adult and qualified healthcare professional should help guide health changes."
    elif age == "senior":
        age_label = "Senior (65+)"
        age_note = "Choose changes that fit your abilities and discuss new activity or health concerns with a clinician."
    else:
        age_label = "Adult (18–64)"
        age_note = "Adjust these general suggestions to your needs and any guidance from your care team."

    activity_label = {"moderate": "Moderate", "active": "Active"}.get(activity, "Sedentary")

    # keep the order the boxes were ticked in (and repeats, if a client sends an6)
    picked_conditions = ", ".join(CONDITION_NAMES[c] for c in conditions) or None
    picked_concerns = ", ".join(CONCERN_NAMES[c] for c in concerns) or None

    return (
        "<p><strong>Age group:</strong> " + age_label + "</p>"
        + "<p><strong>Activity level:</strong> " + activity_label + "</p>"
        + "<p><strong>Selected physical health factors:</strong> " + (picked_conditions or "None") + "</p>"
        + "<p><strong>Selected wellbeing factors:</strong> " + (picked_concerns or "None") + "</p>"
        + "<p>" + age_note + "</p>"
    )


def load_page():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


class HospitalHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        form = parse_qs(self.rfile.read(length).decode('utf-8'))

        age = form.get('age', ['adult'])[0]
        if age not in AGE_GROUPS:
            age = 'adult'
        activity = form.get('activity', ['sedentary'])[0]
        if activity not in ACTIVITY_LEVELS:
            activity = 'sedentary'
        conditions = [c for c in form.get('physical', []) if c in CONDITION_NAMES]
        concerns = [c for c in form.get('mental', []) if c in CONCERN_NAMES]
        page = load_page()
        if page is None:
            page = "<h1>Error: index.html not found!</h1>"

        # the indentation inside this string ends up in the page source, so it is
        # written to line up with the <div class="container"> it lands in
        plan = f"""
        <div class="result-box">
            <h2>Your Personalized Wellness Plan</h2>
            <p>This general plan is based on the choices you selected. It is not a diagnosis or a substitute for professional medical advice.</p>
            <div class="card">
                <h3>Profile Summary</h3>
                {profile_summary(age, activity, conditions, concerns)}
            </div>
            <div class="card">
                <h3>1. Food and Nutrition</h3>
                <ul>{diet_advice(conditions, concerns)}</ul>
            </div>
            <div class="card">
                <h3>2. Movement and Activity</h3>
                <ul>{activity_advice(activity, conditions, concerns)}</ul>
            </div>
            <div class="card">
                <h3>3. Wellbeing and Recovery</h3>
                <ul>{wellbeing_advice(concerns)}</ul>
            </div>
            <div class="card">
                <h3>Simple Next Steps</h3>
                <ol>
                    <li>Choose one small suggestion that feels realistic for this week.</li>
                    <li>Notice how you feel and adjust gently; stop if an activity causes pain or makes you feel unwell.</li>
                    <li>Check with a qualified healthcare professional before making changes related to a health condition.</li>
                </ol>
            </div>
        </div>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.replace(PLACEHOLDER, plan).encode('utf-8'))
    def do_GET(self):
        # anything other than the form page (css, favicon...) goes to the normal static handler
        if self.path not in ('/', '/index.html'):
            return super().do_GET()
        # headers go out before we know whether the file exists, so a missing
        # index.html is still a 200 with an error message in the body
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        page = load_page()
        if page is None:
            self.wfile.write(b"<h1>Error: index.html not found!</h1>")
        else:
            self.wfile.write(page.replace(PLACEHOLDER, '').encode('utf-8'))
if __name__ == '__main__':
    httpd = HTTPServer(('', 8000), HospitalHandler)
    print("=" * 50)
    print("Hospital Patient Care Server Running!")
    print("Open your browser and navigate to: http://localhost:8000")
    print("=" * 50)
    httpd.serve_forever()