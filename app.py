from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'health-plus-secret-key-2024'  # Change this in production

# Health assessment calculations
def calculate_bmi(weight_kg, height_m):
    """Calculate BMI"""
    if height_m <= 0:
        return None
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return {"value": round(bmi, 1), "category": category}

def assess_cardiovascular(bp_systolic, bp_diastolic):
    """Assess cardiovascular health based on blood pressure"""
    if bp_systolic < 120 and bp_diastolic < 80:
        status = "Normal"
        risk = "Low"
    elif bp_systolic < 130 and bp_diastolic < 80:
        status = "Elevated"
        risk = "Medium"
    elif bp_systolic < 140 or bp_diastolic < 90:
        status = "Stage 1 Hypertension"
        risk = "Medium-High"
    else:
        status = "Stage 2 Hypertension"
        risk = "High"
    
    return {"status": status, "risk": risk}

def assess_stroke_risk(age, bp_systolic, smoking, diabetes, heart_disease):
    """Non-laboratory stroke risk assessment"""
    score = 0
    
    # Age factor
    if age >= 75:
        score += 4
    elif age >= 65:
        score += 2
    
    # Blood pressure
    if bp_systolic >= 140:
        score += 2
    elif bp_systolic >= 130:
        score += 1
    
    # Risk factors
    if smoking:
        score += 2
    if diabetes:
        score += 2
    if heart_disease:
        score += 3
    
    if score >= 7:
        risk = "High"
    elif score >= 4:
        risk = "Medium"
    else:
        risk = "Low"
    
    return {"score": score, "risk": risk}

def assess_metabolic(waist_circumference, gender, bp_systolic):
    """Non-invasive metabolic health assessment"""
    factors = 0
    
    # Waist circumference
    if gender.lower() == 'male':
        if waist_circumference >= 102:
            factors += 1
    else:
        if waist_circumference >= 88:
            factors += 1
    
    # Blood pressure
    if bp_systolic >= 130:
        factors += 1
    
    if factors == 0:
        status = "Healthy"
    elif factors == 1:
        status = "At Risk"
    else:
        status = "Metabolic Syndrome Risk"
    
    return {"factors": factors, "status": status}

def assess_respiratory(spo2):
    """Assess respiratory health based on SpO2"""
    if spo2 >= 95:
        status = "Normal"
    elif spo2 >= 90:
        status = "Mild Hypoxemia"
    else:
        status = "Severe Hypoxemia - Seek Medical Attention"
    
    return {"status": status, "spo2": spo2}

def assess_fitness(resting_hr, age):
    """Assess physical fitness based on resting heart rate"""
    max_hr = 220 - age
    
    if resting_hr < 60:
        status = "Athlete Level"
    elif resting_hr < 70:
        status = "Excellent"
    elif resting_hr < 80:
        status = "Good"
    elif resting_hr < 90:
        status = "Average"
    else:
        status = "Below Average"
    
    return {"status": status, "hr_zone": f"{round((resting_hr/max_hr)*100)}% of max"}

def assess_body_composition(bf_percentage, gender, age):
    """Assess body composition based on BIA body fat percentage"""
    if gender.lower() == 'male':
        if age < 30:
            if bf_percentage < 8:
                status = "Essential Fat"
            elif bf_percentage < 14:
                status = "Athletes"
            elif bf_percentage < 18:
                status = "Fitness"
            elif bf_percentage < 25:
                status = "Average"
            else:
                status = "Obese"
        else:
            if bf_percentage < 11:
                status = "Essential Fat"
            elif bf_percentage < 17:
                status = "Athletes"
            elif bf_percentage < 22:
                status = "Fitness"
            elif bf_percentage < 28:
                status = "Average"
            else:
                status = "Obese"
    else:
        if age < 30:
            if bf_percentage < 16:
                status = "Essential Fat"
            elif bf_percentage < 20:
                status = "Athletes"
            elif bf_percentage < 24:
                status = "Fitness"
            elif bf_percentage < 31:
                status = "Average"
            else:
                status = "Obese"
        else:
            if bf_percentage < 20:
                status = "Essential Fat"
            elif bf_percentage < 25:
                status = "Athletes"
            elif bf_percentage < 29:
                status = "Fitness"
            elif bf_percentage < 36:
                status = "Average"
            else:
                status = "Obese"
    
    return {"status": status, "percentage": bf_percentage}

def assess_posture(alignment_score, balance_score):
    """Assess posture and musculoskeletal health"""
    total_score = alignment_score + balance_score
    
    if total_score >= 8:
        status = "Excellent Posture"
    elif total_score >= 6:
        status = "Good Posture"
    elif total_score >= 4:
        status = "Fair - Needs Improvement"
    else:
        status = "Poor - Consult Professional"
    
    return {"status": status, "score": total_score}

def assess_mental_health(phq9_score):
    """Assess mental health using PHQ-9 depression screening"""
    if phq9_score <= 4:
        severity = "Minimal or None"
        recommendation = "Continue monitoring"
    elif phq9_score <= 9:
        severity = "Mild"
        recommendation = "Consider self-care strategies"
    elif phq9_score <= 14:
        severity = "Moderate"
        recommendation = "Consider professional consultation"
    elif phq9_score <= 19:
        severity = "Moderately Severe"
        recommendation = "Seek professional help"
    else:
        severity = "Severe"
        recommendation = "Immediate professional consultation recommended"
    
    return {"severity": severity, "score": phq9_score, "recommendation": recommendation}

def assess_temperature(temp_celsius):
    """Assess general wellness based on body temperature"""
    if 36.1 <= temp_celsius <= 37.2:
        status = "Normal"
    elif temp_celsius < 36.1:
        status = "Hypothermia Risk"
    elif temp_celsius <= 38.0:
        status = "Low-Grade Fever"
    else:
        status = "Fever - Seek Medical Attention"
    
    return {"status": status, "temperature": temp_celsius}

def assess_grip_strength(grip_kg, gender, age):
    """Assess functional health based on grip strength"""
    if gender.lower() == 'male':
        if age < 30:
            if grip_kg >= 50:
                status = "Excellent"
            elif grip_kg >= 40:
                status = "Good"
            elif grip_kg >= 30:
                status = "Average"
            else:
                status = "Below Average"
        else:
            if grip_kg >= 45:
                status = "Excellent"
            elif grip_kg >= 35:
                status = "Good"
            elif grip_kg >= 25:
                status = "Average"
            else:
                status = "Below Average"
    else:
        if age < 30:
            if grip_kg >= 30:
                status = "Excellent"
            elif grip_kg >= 25:
                status = "Good"
            elif grip_kg >= 20:
                status = "Average"
            else:
                status = "Below Average"
        else:
            if grip_kg >= 28:
                status = "Excellent"
            elif grip_kg >= 22:
                status = "Good"
            elif grip_kg >= 18:
                status = "Average"
            else:
                status = "Below Average"
    
    return {"status": status, "strength": grip_kg}

def assess_lifestyle(smoking_status, physical_activity_minutes):
    """Assess lifestyle and risk factors"""
    risk_score = 0
    
    if smoking_status.lower() == 'current':
        risk_score += 3
    elif smoking_status.lower() == 'former':
        risk_score += 1
    
    if physical_activity_minutes < 150:
        risk_score += 2
    elif physical_activity_minutes < 300:
        risk_score += 1
    
    if risk_score == 0:
        status = "Low Risk Lifestyle"
    elif risk_score <= 2:
        status = "Moderate Risk Lifestyle"
    else:
        status = "High Risk Lifestyle"
    
    return {"status": status, "risk_score": risk_score}

def assess_vision(acuity_denominator):
    """Assess vision based on Snellen chart"""
    # acuity_denominator is the bottom number (e.g., 20 for 20/20, 30 for 20/30)
    # Smaller denominator = better vision (up to 20)
    if acuity_denominator <= 20:
        status = "Normal Vision (20/20)"
    elif acuity_denominator <= 30:
        status = "Mild Vision Impairment"
    elif acuity_denominator <= 60:
        status = "Moderate Vision Impairment"
    else:
        status = "Severe Vision Impairment - Consult Eye Care Professional"
    
    return {"status": status, "acuity": f"20/{int(acuity_denominator)}"}

def assess_hearing(frequency_results):
    """Assess hearing based on pure-tone screening"""
    normal_count = sum(1 for result in frequency_results.values() if result <= 25)
    
    if normal_count == len(frequency_results):
        status = "Normal Hearing"
    elif normal_count >= len(frequency_results) * 0.7:
        status = "Mild Hearing Loss"
    elif normal_count >= len(frequency_results) * 0.5:
        status = "Moderate Hearing Loss"
    else:
        status = "Significant Hearing Loss - Consult Audiologist"
    
    return {"status": status, "normal_frequencies": normal_count}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/assessments')
def assessments():
    return render_template('assessments.html')

@app.route('/assessment/<assessment_type>')
def assessment_form(assessment_type):
    return render_template(f'assessments/{assessment_type}.html', assessment_type=assessment_type)

@app.route('/submit/<assessment_type>', methods=['POST'])
def submit_assessment(assessment_type):
    if 'results' not in session:
        session['results'] = {}
    
    # Clear sample flag when user submits real assessment
    session['is_sample'] = False
    
    result = None
    
    if assessment_type == 'bmi':
        weight = float(request.form.get('weight'))
        height = float(request.form.get('height')) / 100  # Convert cm to m
        result = calculate_bmi(weight, height)
    
    elif assessment_type == 'cardiovascular':
        systolic = int(request.form.get('systolic'))
        diastolic = int(request.form.get('diastolic'))
        result = assess_cardiovascular(systolic, diastolic)
    
    elif assessment_type == 'stroke-risk':
        age = int(request.form.get('age'))
        systolic = int(request.form.get('systolic'))
        smoking = request.form.get('smoking') == 'yes'
        diabetes = request.form.get('diabetes') == 'yes'
        heart_disease = request.form.get('heart_disease') == 'yes'
        result = assess_stroke_risk(age, systolic, smoking, diabetes, heart_disease)
    
    elif assessment_type == 'metabolic':
        waist = float(request.form.get('waist'))
        gender = request.form.get('gender')
        systolic = int(request.form.get('systolic'))
        result = assess_metabolic(waist, gender, systolic)
    
    elif assessment_type == 'respiratory':
        spo2 = int(request.form.get('spo2'))
        result = assess_respiratory(spo2)
    
    elif assessment_type == 'fitness':
        resting_hr = int(request.form.get('resting_hr'))
        age = int(request.form.get('age'))
        result = assess_fitness(resting_hr, age)
    
    elif assessment_type == 'body-composition':
        bf_percentage = float(request.form.get('bf_percentage'))
        gender = request.form.get('gender')
        age = int(request.form.get('age'))
        result = assess_body_composition(bf_percentage, gender, age)
    
    elif assessment_type == 'posture':
        alignment = int(request.form.get('alignment'))
        balance = int(request.form.get('balance'))
        result = assess_posture(alignment, balance)
    
    elif assessment_type == 'mental-health':
        phq9_score = sum(int(request.form.get(f'q{i}')) for i in range(1, 10))
        result = assess_mental_health(phq9_score)
    
    elif assessment_type == 'temperature':
        temp = float(request.form.get('temperature'))
        result = assess_temperature(temp)
    
    elif assessment_type == 'grip-strength':
        grip = float(request.form.get('grip_strength'))
        gender = request.form.get('gender')
        age = int(request.form.get('age'))
        result = assess_grip_strength(grip, gender, age)
    
    elif assessment_type == 'lifestyle':
        smoking = request.form.get('smoking_status')
        activity = int(request.form.get('physical_activity', 0))
        result = assess_lifestyle(smoking, activity)
    
    elif assessment_type == 'vision':
        # Simplified - in real app would use actual Snellen chart results
        acuity = float(request.form.get('acuity'))
        result = assess_vision(acuity)
    
    elif assessment_type == 'hearing':
        frequencies = {
            '250': int(request.form.get('freq_250', 0)),
            '500': int(request.form.get('freq_500', 0)),
            '1000': int(request.form.get('freq_1000', 0)),
            '2000': int(request.form.get('freq_2000', 0)),
            '4000': int(request.form.get('freq_4000', 0)),
        }
        result = assess_hearing(frequencies)
    
    session['results'][assessment_type] = {
        'result': result,
        'timestamp': datetime.now().isoformat()
    }
    session.modified = True
    
    flash(f'{assessment_type.replace("-", " ").title()} assessment completed!', 'success')
    return redirect(url_for('results'))

@app.route('/results')
def results():
    results_data = session.get('results', {})
    is_sample = session.get('is_sample', False)
    
    # Define all assessment types in order
    all_assessments = [
        'bmi', 'cardiovascular', 'stroke-risk', 'metabolic', 'respiratory',
        'fitness', 'body-composition', 'posture', 'mental-health', 'temperature',
        'grip-strength', 'lifestyle', 'vision', 'hearing'
    ]
    
    # Create a dictionary with all assessments, marking unassessed ones
    complete_results = {}
    for assessment_type in all_assessments:
        if assessment_type in results_data:
            complete_results[assessment_type] = results_data[assessment_type]
        else:
            complete_results[assessment_type] = None  # Mark as not assessed
    
    return render_template('results.html', results=complete_results, is_sample=is_sample)

@app.route('/sample-results')
def sample_results():
    """Display sample results for demonstration purposes"""
    from datetime import datetime, timedelta
    
    # Create comprehensive sample results
    sample_data = {
        'bmi': {
            'result': calculate_bmi(75, 1.75),  # 75kg, 175cm
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        'cardiovascular': {
            'result': assess_cardiovascular(125, 82),
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        'stroke-risk': {
            'result': assess_stroke_risk(45, 125, False, False, False),
            'timestamp': (datetime.now() - timedelta(days=2)).isoformat()
        },
        'metabolic': {
            'result': assess_metabolic(88, 'male', 125),
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        'respiratory': {
            'result': assess_respiratory(98),
            'timestamp': datetime.now().isoformat()
        },
        'fitness': {
            'result': assess_fitness(68, 35),
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        'body-composition': {
            'result': assess_body_composition(18, 'male', 35),
            'timestamp': (datetime.now() - timedelta(days=2)).isoformat()
        },
        'posture': {
            'result': assess_posture(4, 4),
            'timestamp': (datetime.now() - timedelta(days=3)).isoformat()
        },
        'mental-health': {
            'result': assess_mental_health(6),
            'timestamp': datetime.now().isoformat()
        },
        'temperature': {
            'result': assess_temperature(36.8),
            'timestamp': datetime.now().isoformat()
        },
        'grip-strength': {
            'result': assess_grip_strength(42, 'male', 35),
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        'lifestyle': {
            'result': assess_lifestyle('never', 180),
            'timestamp': (datetime.now() - timedelta(days=2)).isoformat()
        },
        'vision': {
            'result': assess_vision(20),
            'timestamp': (datetime.now() - timedelta(days=6)).isoformat()
        },
        'hearing': {
            'result': assess_hearing({
                '250': 15,
                '500': 18,
                '1000': 20,
                '2000': 22,
                '4000': 25
            }),
            'timestamp': (datetime.now() - timedelta(days=6)).isoformat()
        }
    }
    
    session['results'] = sample_data
    session['is_sample'] = True
    session.modified = True
    return redirect(url_for('results'))

@app.route('/clear')
def clear_session():
    session.clear()
    flash('All assessment results cleared.', 'info')
    return redirect(url_for('results'))

if __name__ == '__main__':
    app.run(debug=True)

