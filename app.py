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

def assess_prostate(age, family_history, psa_level, symptoms):
    """Assess prostate cancer risk based on risk factors"""
    risk_score = 0
    
    # Age factor
    if age >= 70:
        risk_score += 3
    elif age >= 60:
        risk_score += 2
    elif age >= 50:
        risk_score += 1
    
    # Family history
    if family_history:
        risk_score += 2
    
    # PSA level (if provided, in ng/mL)
    if psa_level:
        if psa_level >= 10:
            risk_score += 3
        elif psa_level >= 4:
            risk_score += 2
        elif psa_level >= 2.5:
            risk_score += 1
    
    # Symptoms
    if symptoms:
        risk_score += 1
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Immediate consultation with urologist recommended"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "Regular screening and consultation with healthcare provider recommended"
    else:
        risk = "Low Risk"
        recommendation = "Continue regular health check-ups and screening as per guidelines"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_hiv(age, risk_behaviors, symptoms, recent_exposure):
    """Assess HIV risk based on behavioral and clinical factors"""
    risk_score = 0
    
    # Age factor (younger adults may have higher risk behaviors)
    if 18 <= age <= 35:
        risk_score += 1
    
    # Risk behaviors
    if risk_behaviors:
        risk_score += 3
    
    # Recent exposure
    if recent_exposure:
        risk_score += 4
    
    # Symptoms (if present, may indicate need for testing)
    if symptoms:
        risk_score += 2
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Immediate HIV testing recommended. Consider PEP if exposure within 72 hours"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "HIV testing recommended. Practice safe behaviors and consider PrEP"
    else:
        risk = "Low Risk"
        recommendation = "Regular HIV testing as per guidelines. Continue safe practices"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_pregnancy(weeks_pregnant, blood_pressure, symptoms, previous_complications):
    """Assess pregnancy health and risk factors"""
    risk_factors = 0
    status = "Normal Pregnancy"
    
    # Gestational age considerations
    if weeks_pregnant < 12:
        trimester = "First Trimester"
    elif weeks_pregnant < 28:
        trimester = "Second Trimester"
    else:
        trimester = "Third Trimester"
    
    # Blood pressure (pregnancy hypertension)
    if blood_pressure:
        systolic, diastolic = blood_pressure
        if systolic >= 140 or diastolic >= 90:
            risk_factors += 2
            status = "Monitor Blood Pressure"
        elif systolic >= 130 or diastolic >= 85:
            risk_factors += 1
    
    # Symptoms (concerning symptoms)
    if symptoms:
        risk_factors += 1
    
    # Previous complications
    if previous_complications:
        risk_factors += 2
    
    if risk_factors >= 3:
        risk = "High Risk Pregnancy"
        recommendation = "Close monitoring by obstetrician required. Follow-up appointments essential"
    elif risk_factors >= 1:
        risk = "Moderate Risk"
        recommendation = "Regular prenatal care and monitoring recommended"
    else:
        risk = "Low Risk"
        recommendation = "Continue routine prenatal care and healthy pregnancy practices"
    
    return {
        "trimester": trimester,
        "weeks": weeks_pregnant,
        "status": status,
        "risk": risk,
        "risk_factors": risk_factors,
        "recommendation": recommendation
    }

def assess_breast_cancer(age, family_history, genetic_factors, previous_biopsy, breast_density, hormonal_factors):
    """Assess breast cancer risk based on multiple factors"""
    risk_score = 0
    
    # Age factor
    if age >= 60:
        risk_score += 2
    elif age >= 40:
        risk_score += 1
    
    # Family history
    if family_history == 'first_degree':
        risk_score += 3
    elif family_history == 'second_degree':
        risk_score += 1
    
    # Genetic factors (BRCA mutations, etc.)
    if genetic_factors:
        risk_score += 4
    
    # Previous biopsy (atypical hyperplasia, etc.)
    if previous_biopsy:
        risk_score += 2
    
    # Breast density
    if breast_density == 'high':
        risk_score += 1
    
    # Hormonal factors (early menarche, late menopause, etc.)
    if hormonal_factors:
        risk_score += 1
    
    if risk_score >= 7:
        risk = "High Risk"
        recommendation = "Consultation with breast specialist and genetic counseling recommended. Enhanced screening may be indicated"
    elif risk_score >= 4:
        risk = "Moderate Risk"
        recommendation = "Regular mammography and clinical breast exams. Discuss screening schedule with healthcare provider"
    else:
        risk = "Low Risk"
        recommendation = "Continue routine breast cancer screening as per age-appropriate guidelines"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_tuberculosis(age, symptoms, exposure, immunocompromised, previous_tb):
    """Assess tuberculosis risk based on symptoms and risk factors"""
    risk_score = 0
    
    # Age factor (very young and elderly at higher risk)
    if age < 5 or age >= 65:
        risk_score += 1
    
    # Symptoms
    if symptoms:
        risk_score += 3
    
    # Exposure to TB
    if exposure:
        risk_score += 3
    
    # Immunocompromised status
    if immunocompromised:
        risk_score += 2
    
    # Previous TB infection
    if previous_tb:
        risk_score += 2
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Immediate medical evaluation recommended. TB testing (skin test or blood test) and chest X-ray may be indicated"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "Consult with healthcare provider for TB screening. Monitor symptoms closely"
    else:
        risk = "Low Risk"
        recommendation = "Continue routine health monitoring. Be aware of TB symptoms and risk factors"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_covid19(symptoms, exposure, vaccination_status, underlying_conditions, age_group):
    """Assess COVID-19 risk based on symptoms and risk factors"""
    risk_score = 0
    
    # Symptoms
    if symptoms:
        risk_score += 3
    
    # Recent exposure
    if exposure:
        risk_score += 2
    
    # Vaccination status
    if vaccination_status == 'not_vaccinated':
        risk_score += 2
    elif vaccination_status == 'partially_vaccinated':
        risk_score += 1
    
    # Underlying conditions
    if underlying_conditions:
        risk_score += 2
    
    # Age group (older adults at higher risk)
    if age_group == 'elderly':
        risk_score += 2
    elif age_group == 'adult':
        risk_score += 1
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Consider COVID-19 testing. Isolate and monitor symptoms. Seek medical attention if symptoms worsen or if you have difficulty breathing"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "Monitor symptoms closely. Consider COVID-19 testing. Practice isolation if symptomatic"
    else:
        risk = "Low Risk"
        recommendation = "Continue preventive measures (hand hygiene, mask-wearing in crowded places). Stay up to date with vaccinations"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_malaria(symptoms, travel_history, area_residence, previous_malaria, prevention_measures):
    """Assess malaria risk based on symptoms and exposure factors"""
    risk_score = 0
    
    # Symptoms
    if symptoms:
        risk_score += 3
    
    # Travel to endemic areas
    if travel_history:
        risk_score += 3
    
    # Residence in endemic area
    if area_residence:
        risk_score += 2
    
    # Previous malaria infection
    if previous_malaria:
        risk_score += 1
    
    # Prevention measures (if not using, increases risk)
    if not prevention_measures:
        risk_score += 1
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Immediate medical evaluation and malaria testing (blood smear or rapid diagnostic test) recommended. Early treatment is crucial"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "Consult with healthcare provider for malaria testing if symptomatic. Use preventive measures if in endemic areas"
    else:
        risk = "Low Risk"
        recommendation = "Continue preventive measures if in or traveling to endemic areas. Be aware of symptoms"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_liver_problem(symptoms, alcohol_use, medications, family_history, previous_liver_issues):
    """Assess liver problem risk based on symptoms and risk factors"""
    risk_score = 0
    
    # Symptoms
    if symptoms:
        risk_score += 3
    
    # Alcohol use
    if alcohol_use == 'heavy':
        risk_score += 3
    elif alcohol_use == 'moderate':
        risk_score += 1
    
    # Medications (some can affect liver)
    if medications:
        risk_score += 1
    
    # Family history
    if family_history:
        risk_score += 1
    
    # Previous liver issues
    if previous_liver_issues:
        risk_score += 2
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Immediate medical evaluation recommended. Liver function tests and imaging may be indicated"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "Consult with healthcare provider. Liver function tests may be recommended"
    else:
        risk = "Low Risk"
        recommendation = "Maintain healthy lifestyle. Limit alcohol consumption. Regular health check-ups recommended"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_hepatitis_b(age, vaccination_status, exposure, symptoms, risk_behaviors):
    """Assess Hepatitis B risk based on vaccination status and risk factors"""
    risk_score = 0
    
    # Age factor (higher risk in certain age groups)
    if 20 <= age <= 49:
        risk_score += 1
    
    # Vaccination status
    if vaccination_status == 'not_vaccinated':
        risk_score += 3
    elif vaccination_status == 'unknown':
        risk_score += 2
    
    # Exposure
    if exposure:
        risk_score += 3
    
    # Symptoms
    if symptoms:
        risk_score += 2
    
    # Risk behaviors
    if risk_behaviors:
        risk_score += 2
    
    if risk_score >= 6:
        risk = "High Risk"
        recommendation = "Hepatitis B testing recommended. If not vaccinated, consider vaccination. Post-exposure prophylaxis may be needed if recent exposure"
    elif risk_score >= 3:
        risk = "Moderate Risk"
        recommendation = "Hepatitis B testing and vaccination recommended. Practice safe behaviors"
    else:
        risk = "Low Risk"
        recommendation = "Continue preventive measures. Ensure vaccination is up to date. Regular screening as per guidelines"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_diabetes(age, family_history, symptoms, bmi_category, physical_activity, blood_pressure):
    """Assess diabetes risk based on risk factors"""
    risk_score = 0
    
    # Age factor
    if age >= 45:
        risk_score += 2
    elif age >= 35:
        risk_score += 1
    
    # Family history
    if family_history:
        risk_score += 2
    
    # Symptoms
    if symptoms:
        risk_score += 3
    
    # BMI category
    if bmi_category in ['Overweight', 'Obese']:
        risk_score += 2
    elif bmi_category == 'Normal weight':
        risk_score += 0
    
    # Physical activity
    if physical_activity == 'low':
        risk_score += 1
    
    # Blood pressure (high BP increases risk)
    if blood_pressure:
        risk_score += 1
    
    if risk_score >= 7:
        risk = "High Risk"
        recommendation = "Diabetes screening (fasting blood glucose, HbA1c) strongly recommended. Consult with healthcare provider for comprehensive evaluation"
    elif risk_score >= 4:
        risk = "Moderate Risk"
        recommendation = "Diabetes screening recommended. Lifestyle modifications including diet and exercise may help reduce risk"
    else:
        risk = "Low Risk"
        recommendation = "Continue healthy lifestyle. Regular screening as per age-appropriate guidelines (typically every 3 years after age 45)"
    
    return {"risk_score": risk_score, "risk": risk, "recommendation": recommendation}

def assess_hydration(urine_color, thirst_level, activity_level, fluid_intake, symptoms):
    """Assess hydration status based on multiple indicators"""
    hydration_score = 0
    status = "Well Hydrated"
    
    # Urine color (pale = well hydrated, dark = dehydrated)
    if urine_color == 'pale':
        hydration_score += 2
    elif urine_color == 'light_yellow':
        hydration_score += 1
    elif urine_color == 'dark':
        hydration_score -= 2
        status = "Dehydrated"
    
    # Thirst level
    if thirst_level == 'not_thirsty':
        hydration_score += 1
    elif thirst_level == 'very_thirsty':
        hydration_score -= 2
        if status == "Well Hydrated":
            status = "Mildly Dehydrated"
    
    # Activity level (affects fluid needs)
    if activity_level == 'high':
        hydration_score -= 1
    
    # Fluid intake
    if fluid_intake == 'adequate':
        hydration_score += 2
    elif fluid_intake == 'low':
        hydration_score -= 2
        if status == "Well Hydrated":
            status = "Mildly Dehydrated"
    
    # Symptoms
    if symptoms:
        hydration_score -= 2
        if status == "Well Hydrated":
            status = "Mildly Dehydrated"
        elif status == "Mildly Dehydrated":
            status = "Dehydrated"
    
    # Determine final status
    if hydration_score >= 3:
        status = "Well Hydrated"
        recommendation = "Continue maintaining adequate fluid intake. Aim for 8-10 glasses of water daily, more if active"
    elif hydration_score >= 0:
        status = "Mildly Dehydrated"
        recommendation = "Increase fluid intake. Drink water regularly throughout the day. Monitor urine color and thirst"
    else:
        status = "Dehydrated"
        recommendation = "Increase fluid intake immediately. Drink water, electrolyte solutions if needed. Seek medical attention if symptoms are severe"
    
    return {"status": status, "hydration_score": hydration_score, "recommendation": recommendation}

def generate_medical_report(assessment_type, result):
    """Generate a professional medical report for each assessment result"""
    reports = {
        'bmi': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500">
            <h4 class="font-semibold text-blue-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Your Body Mass Index (BMI) of <strong>{r['value']}</strong> indicates a <strong>{r['category']}</strong> classification.
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> BMI is a screening tool that estimates body fat based on height and weight. 
                {'Maintaining a healthy weight through balanced nutrition and regular physical activity is recommended.' if r['category'] in ['Normal weight', 'Underweight'] else 'Consider consulting with a healthcare provider or registered dietitian to develop a personalized weight management plan. Regular monitoring and lifestyle modifications may be beneficial.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Note:</strong> BMI does not account for muscle mass, bone density, or body composition. For a comprehensive assessment, consult with a healthcare professional.
            </p>
        </div>
        """,
        'cardiovascular': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-red-50 rounded-lg border-l-4 border-red-500">
            <h4 class="font-semibold text-red-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Your blood pressure reading indicates <strong>{r['status']}</strong> with a <strong>{r['risk']}</strong> risk level.
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Blood pressure is within normal ranges. Continue maintaining a healthy lifestyle with regular exercise, a balanced diet, and stress management.' if r['risk'] == 'Low' else 'Elevated blood pressure may increase cardiovascular risk. Lifestyle modifications including reduced sodium intake, regular exercise, weight management, and stress reduction are recommended. Regular monitoring and consultation with a healthcare provider is advised.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Maintain current lifestyle habits and annual blood pressure checks.' if r['risk'] == 'Low' else 'Schedule a consultation with your healthcare provider for comprehensive cardiovascular assessment and potential treatment options.'}
            </p>
        </div>
        """,
        'stroke-risk': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-orange-50 rounded-lg border-l-4 border-orange-500">
            <h4 class="font-semibold text-orange-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Your stroke risk assessment score is <strong>{r['score']}</strong>, indicating a <strong>{r['risk']}</strong> risk level.
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Your risk factors for stroke appear to be well-managed. Continue maintaining healthy lifestyle habits including regular exercise, a balanced diet, and regular medical check-ups.' if r['risk'] == 'Low' else 'Multiple risk factors have been identified. Comprehensive risk factor modification is recommended, including blood pressure management, smoking cessation if applicable, diabetes control, and regular cardiovascular monitoring.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Annual cardiovascular risk assessment is recommended.' if r['risk'] == 'Low' else 'Consult with a healthcare provider or cardiologist for personalized stroke prevention strategies and potential medical interventions.'}
            </p>
        </div>
        """,
        'metabolic': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-green-50 rounded-lg border-l-4 border-green-500">
            <h4 class="font-semibold text-green-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Metabolic health assessment indicates: <strong>{r['status']}</strong> with <strong>{r['factors']}</strong> risk factor(s) identified.
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Metabolic parameters appear to be within healthy ranges. Continue maintaining a balanced diet, regular physical activity, and healthy lifestyle habits.' if r['status'] == 'Healthy' else 'Metabolic risk factors have been identified. Focus on lifestyle modifications including weight management, increased physical activity, dietary improvements, and blood pressure control. Regular monitoring of metabolic parameters is recommended.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Continue current healthy lifestyle practices.' if r['status'] == 'Healthy' else 'Consider consultation with a healthcare provider or endocrinologist for comprehensive metabolic assessment and personalized intervention strategies.'}
            </p>
        </div>
        """,
        'respiratory': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-teal-50 rounded-lg border-l-4 border-teal-500">
            <h4 class="font-semibold text-teal-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Oxygen saturation (SpO₂) reading: <strong>{r['spo2']}%</strong> - Status: <strong>{r['status']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Oxygen saturation is within normal range, indicating adequate oxygen delivery to tissues. Continue maintaining good respiratory health through regular exercise and avoiding respiratory irritants.' if r['status'] == 'Normal' else 'Reduced oxygen saturation may indicate respiratory compromise. This requires immediate medical evaluation, especially if accompanied by shortness of breath, chest pain, or other symptoms.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'No immediate action required. Maintain healthy respiratory habits.' if r['status'] == 'Normal' else 'Seek immediate medical attention. Contact your healthcare provider or emergency services if experiencing respiratory distress.'}
            </p>
        </div>
        """,
        'fitness': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-purple-50 rounded-lg border-l-4 border-purple-500">
            <h4 class="font-semibold text-purple-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Physical fitness assessment: <strong>{r['status']}</strong> (Heart rate zone: {r['hr_zone']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Excellent cardiovascular fitness level. Your resting heart rate indicates strong cardiovascular conditioning. Continue your current exercise regimen.' if 'Athlete' in r['status'] or 'Excellent' in r['status'] else 'Cardiovascular fitness assessment suggests room for improvement. Regular aerobic exercise, gradually increasing intensity and duration, can improve cardiovascular health and reduce resting heart rate over time.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Maintain current exercise routine. Consider periodic fitness assessments to track progress.' if 'Athlete' in r['status'] or 'Excellent' in r['status'] else 'Aim for at least 150 minutes of moderate-intensity aerobic exercise per week. Consult with a fitness professional or healthcare provider before starting a new exercise program.'}
            </p>
        </div>
        """,
        'body-composition': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-pink-50 rounded-lg border-l-4 border-pink-500">
            <h4 class="font-semibold text-pink-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Body composition analysis: <strong>{r['status']}</strong> (Body fat: {r['percentage']}%)
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Body composition is within optimal ranges for your demographic. Continue maintaining a balanced diet and regular strength training to preserve muscle mass.' if 'Athletes' in r['status'] or 'Fitness' in r['status'] else 'Body composition analysis suggests areas for improvement. Focus on a combination of resistance training to build muscle mass and cardiovascular exercise to reduce body fat. Nutritional guidance from a registered dietitian may be beneficial.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Maintain current training and nutrition practices.' if 'Athletes' in r['status'] or 'Fitness' in r['status'] else 'Consider consultation with a fitness professional and registered dietitian for a personalized body composition improvement plan.'}
            </p>
        </div>
        """,
        'posture': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-indigo-50 rounded-lg border-l-4 border-indigo-500">
            <h4 class="font-semibold text-indigo-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Postural assessment score: <strong>{r['score']}/10</strong> - Status: <strong>{r['status']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Postural alignment and balance are excellent. Continue maintaining good posture habits and regular physical activity to preserve musculoskeletal health.' if 'Excellent' in r['status'] or 'Good' in r['status'] else 'Postural assessment indicates areas requiring attention. Poor posture can contribute to musculoskeletal pain, reduced mobility, and increased injury risk. Targeted exercises and ergonomic modifications may be beneficial.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Continue current practices. Regular posture checks are recommended.' if 'Excellent' in r['status'] or 'Good' in r['status'] else 'Consider consultation with a physical therapist or chiropractor for a comprehensive postural assessment and personalized corrective exercise program.'}
            </p>
        </div>
        """,
        'mental-health': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-500">
            <h4 class="font-semibold text-yellow-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                PHQ-9 Depression Screening Score: <strong>{r['score']}</strong> - Severity: <strong>{r['severity']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Minimal depressive symptoms detected. Continue monitoring mental health and maintaining healthy coping strategies.' if 'Minimal' in r['severity'] else 'Depressive symptoms have been identified. Mental health is an important component of overall wellness. Professional support can be highly effective in managing symptoms and improving quality of life.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. {'This screening tool is not a diagnostic instrument. For comprehensive mental health evaluation, consult with a licensed mental health professional.' if 'Minimal' not in r['severity'] else ''}
            </p>
        </div>
        """,
        'temperature': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-cyan-50 rounded-lg border-l-4 border-cyan-500">
            <h4 class="font-semibold text-cyan-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Body temperature: <strong>{r['temperature']}°C</strong> - Status: <strong>{r['status']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Body temperature is within normal physiological range, indicating no signs of fever or hypothermia.' if r['status'] == 'Normal' else 'Abnormal body temperature may indicate underlying health conditions, infection, or environmental factors. Monitor for additional symptoms and consider medical evaluation.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'No immediate action required. Continue monitoring if symptoms develop.' if r['status'] == 'Normal' else 'If temperature persists outside normal range or is accompanied by other symptoms, consult with a healthcare provider for evaluation.'}
            </p>
        </div>
        """,
        'grip-strength': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-lime-50 rounded-lg border-l-4 border-lime-500">
            <h4 class="font-semibold text-lime-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Grip strength: <strong>{r['strength']} kg</strong> - Status: <strong>{r['status']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Grip strength is within excellent range, indicating good functional capacity and muscle strength.' if 'Excellent' in r['status'] else 'Grip strength is a marker of overall muscle function and functional capacity. Lower grip strength may indicate reduced muscle mass or strength, which can impact daily activities and overall health.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Maintain current strength training routine.' if 'Excellent' in r['status'] else 'Consider incorporating resistance training, particularly hand and forearm strengthening exercises. Consult with a physical therapist or fitness professional for a personalized strength training program.'}
            </p>
        </div>
        """,
        'lifestyle': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-amber-50 rounded-lg border-l-4 border-amber-500">
            <h4 class="font-semibold text-amber-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Lifestyle risk assessment: <strong>{r['status']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Lifestyle factors are well-managed with low health risk. Continue maintaining healthy habits including regular physical activity and avoiding tobacco use.' if r['status'] == 'Low Risk Lifestyle' else 'Lifestyle risk factors have been identified that may impact long-term health. Modifications in smoking habits, physical activity levels, and other lifestyle factors can significantly reduce health risks.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Continue current healthy lifestyle practices.' if r['status'] == 'Low Risk Lifestyle' else 'Consider lifestyle modification programs, smoking cessation support if applicable, and consultation with healthcare providers for personalized risk reduction strategies.'}
            </p>
        </div>
        """,
        'vision': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-violet-50 rounded-lg border-l-4 border-violet-500">
            <h4 class="font-semibold text-violet-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Visual acuity: <strong>{r['acuity']}</strong> - Status: <strong>{r['status']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Visual acuity is within normal range. Continue regular eye care and protect eyes from UV exposure.' if 'Normal' in r['status'] else 'Visual impairment has been detected. Regular comprehensive eye examinations are important for monitoring vision health and detecting treatable conditions early.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Annual comprehensive eye examination is recommended for all adults.' if 'Normal' in r['status'] else 'Schedule a comprehensive eye examination with an optometrist or ophthalmologist for detailed evaluation and appropriate management.'}
            </p>
        </div>
        """,
        'hearing': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-rose-50 rounded-lg border-l-4 border-rose-500">
            <h4 class="font-semibold text-rose-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Hearing assessment: <strong>{r['status']}</strong> (Normal frequencies: {r['normal_frequencies']}/5)
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Hearing function appears to be within normal ranges across tested frequencies. Continue protecting hearing from excessive noise exposure.' if 'Normal' in r['status'] else 'Hearing loss has been detected across one or more frequencies. Early detection and management can help preserve remaining hearing function and improve communication.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {'Annual hearing screening is recommended. Protect ears from loud noises.' if 'Normal' in r['status'] else 'Schedule a comprehensive audiological evaluation with a licensed audiologist for detailed assessment, diagnosis, and appropriate intervention options including hearing aids if indicated.'}
            </p>
        </div>
        """,
        'prostate': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-slate-50 rounded-lg border-l-4 border-slate-500">
            <h4 class="font-semibold text-slate-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Prostate cancer risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Prostate cancer risk appears to be low based on current assessment. Continue regular health check-ups and discuss screening options with your healthcare provider based on age and guidelines.' if r['risk'] == 'Low Risk' else 'Multiple risk factors for prostate cancer have been identified. Early detection through appropriate screening is important for optimal outcomes.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Prostate-specific antigen (PSA) testing and digital rectal examination should be discussed with a urologist based on individual risk factors and current screening guidelines.
            </p>
        </div>
        """,
        'hiv': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-emerald-50 rounded-lg border-l-4 border-emerald-500">
            <h4 class="font-semibold text-emerald-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                HIV risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'HIV risk appears to be low based on current assessment. Continue practicing safe behaviors and regular testing as recommended.' if r['risk'] == 'Low Risk' else 'Risk factors for HIV transmission have been identified. Early testing, prevention strategies, and appropriate medical care are essential for optimal health outcomes.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. HIV testing is confidential and available through healthcare providers, community health centers, and testing sites. Pre-exposure prophylaxis (PrEP) may be considered for ongoing risk reduction.
            </p>
        </div>
        """,
        'pregnancy': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-fuchsia-50 rounded-lg border-l-4 border-fuchsia-500">
            <h4 class="font-semibold text-fuchsia-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Pregnancy assessment: <strong>{r['trimester']}</strong> ({r['weeks']} weeks) - Risk Level: <strong>{r['risk']}</strong>
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Pregnancy appears to be progressing normally. Continue routine prenatal care, maintain a healthy diet, take prenatal vitamins, and follow your healthcare provider\'s recommendations.' if r['risk'] == 'Low Risk' else 'Pregnancy risk factors have been identified that require monitoring. Close follow-up with your obstetrician and adherence to medical recommendations are essential for maternal and fetal health.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Regular prenatal visits, appropriate nutrition, adequate rest, and avoiding harmful substances are important throughout pregnancy.
            </p>
        </div>
        """,
        'breast-cancer': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-pink-50 rounded-lg border-l-4 border-pink-500">
            <h4 class="font-semibold text-pink-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Breast cancer risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Breast cancer risk appears to be low based on current assessment. Continue routine breast cancer screening as per age-appropriate guidelines, including regular mammography and clinical breast exams.' if r['risk'] == 'Low Risk' else 'Multiple risk factors for breast cancer have been identified. Early detection through appropriate screening and risk reduction strategies are important for optimal outcomes.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Breast self-awareness, clinical breast examinations, and mammography are important components of breast health. Discuss personalized screening recommendations with your healthcare provider.
            </p>
        </div>
        """,
        'tuberculosis': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-amber-50 rounded-lg border-l-4 border-amber-500">
            <h4 class="font-semibold text-amber-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Tuberculosis risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Tuberculosis risk appears to be low based on current assessment. Continue routine health monitoring and be aware of TB symptoms.' if r['risk'] == 'Low Risk' else 'Risk factors for tuberculosis have been identified. TB is a serious but treatable disease. Early detection and treatment are essential to prevent transmission and complications.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. TB testing (tuberculin skin test or interferon-gamma release assay) and chest imaging may be recommended based on risk factors and symptoms.
            </p>
        </div>
        """,
        'covid19': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-red-50 rounded-lg border-l-4 border-red-500">
            <h4 class="font-semibold text-red-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                COVID-19 risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'COVID-19 risk appears to be low. Continue preventive measures including hand hygiene, mask-wearing in crowded places, and staying up to date with vaccinations.' if r['risk'] == 'Low Risk' else 'Risk factors for COVID-19 have been identified. COVID-19 can range from mild to severe. Early testing and appropriate management are important.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. If symptomatic, isolate and consider COVID-19 testing. Seek immediate medical attention for severe symptoms like difficulty breathing.
            </p>
        </div>
        """,
        'malaria': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-green-50 rounded-lg border-l-4 border-green-500">
            <h4 class="font-semibold text-green-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Malaria risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Malaria risk appears to be low. Continue preventive measures if in or traveling to endemic areas.' if r['risk'] == 'Low Risk' else 'Risk factors for malaria have been identified. Malaria is a serious but treatable disease. Early diagnosis and treatment are crucial to prevent complications.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Use insect repellent, bed nets, and antimalarial prophylaxis if in endemic areas. Seek immediate medical attention if symptoms develop.
            </p>
        </div>
        """,
        'liver-problem': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-500">
            <h4 class="font-semibold text-yellow-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Liver health risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Liver health risk appears to be low. Maintain healthy lifestyle, limit alcohol consumption, and continue regular health check-ups.' if r['risk'] == 'Low Risk' else 'Risk factors for liver problems have been identified. The liver is vital for many body functions. Early detection and management of liver conditions are important.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Liver function tests (ALT, AST, bilirubin) and imaging may be recommended. Avoid alcohol if liver problems are suspected.
            </p>
        </div>
        """,
        'hepatitis-b': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-orange-50 rounded-lg border-l-4 border-orange-500">
            <h4 class="font-semibold text-orange-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Hepatitis B risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Hepatitis B risk appears to be low. Ensure vaccination is up to date and continue preventive measures.' if r['risk'] == 'Low Risk' else 'Risk factors for Hepatitis B have been identified. Hepatitis B is a vaccine-preventable viral infection that can cause liver disease. Early detection and vaccination are important.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Hepatitis B testing (HBsAg, anti-HBc) and vaccination are important preventive measures. Post-exposure prophylaxis may be needed if recent exposure.
            </p>
        </div>
        """,
        'diabetes': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-indigo-50 rounded-lg border-l-4 border-indigo-500">
            <h4 class="font-semibold text-indigo-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Diabetes risk assessment: <strong>{r['risk']}</strong> (Risk Score: {r['risk_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Diabetes risk appears to be low. Continue maintaining a healthy lifestyle with balanced diet and regular physical activity.' if r['risk'] == 'Low Risk' else 'Risk factors for diabetes have been identified. Diabetes is a chronic condition that affects how your body processes blood sugar. Early detection and management are important to prevent complications.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. Lifestyle modifications including healthy diet, regular exercise, and weight management can help reduce diabetes risk.
            </p>
        </div>
        """,
        'hydration': lambda r: f"""
        <div class="medical-report mt-4 p-4 bg-cyan-50 rounded-lg border-l-4 border-cyan-500">
            <h4 class="font-semibold text-cyan-900 mb-2"><i class="fas fa-stethoscope mr-2"></i>Medical Interpretation</h4>
            <p class="text-sm text-gray-700 mb-2">
                Hydration status: <strong>{r['status']}</strong> (Hydration Score: {r['hydration_score']})
            </p>
            <p class="text-sm text-gray-700 mb-2">
                <strong>Clinical Assessment:</strong> {'Hydration status appears to be adequate. Continue maintaining good fluid intake throughout the day.' if r['status'] == 'Well Hydrated' else 'Hydration status indicates room for improvement. Adequate hydration is essential for optimal body function, including temperature regulation, nutrient transport, and waste removal.'}
            </p>
            <p class="text-sm text-gray-600 italic">
                <strong>Recommendation:</strong> {r['recommendation']}. General guideline: aim for 8-10 glasses (2-2.5 liters) of water daily, more if you're active, in hot weather, or ill.
            </p>
        </div>
        """
    }
    
    if assessment_type in reports and result:
        return reports[assessment_type](result)
    return ""

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
    
    elif assessment_type == 'prostate':
        age = int(request.form.get('age'))
        family_history = request.form.get('family_history') == 'yes'
        psa_level = float(request.form.get('psa_level', 0)) if request.form.get('psa_level') else None
        symptoms = request.form.get('symptoms') == 'yes'
        result = assess_prostate(age, family_history, psa_level, symptoms)
    
    elif assessment_type == 'hiv':
        age = int(request.form.get('age'))
        risk_behaviors = request.form.get('risk_behaviors') == 'yes'
        symptoms = request.form.get('symptoms') == 'yes'
        recent_exposure = request.form.get('recent_exposure') == 'yes'
        result = assess_hiv(age, risk_behaviors, symptoms, recent_exposure)
    
    elif assessment_type == 'pregnancy':
        weeks_pregnant = int(request.form.get('weeks_pregnant'))
        systolic = int(request.form.get('systolic')) if request.form.get('systolic') else None
        diastolic = int(request.form.get('diastolic')) if request.form.get('diastolic') else None
        blood_pressure = (systolic, diastolic) if systolic and diastolic else None
        symptoms = request.form.get('symptoms') == 'yes'
        previous_complications = request.form.get('previous_complications') == 'yes'
        result = assess_pregnancy(weeks_pregnant, blood_pressure, symptoms, previous_complications)
    
    elif assessment_type == 'breast-cancer':
        age = int(request.form.get('age'))
        family_history = request.form.get('family_history', 'none')
        genetic_factors = request.form.get('genetic_factors') == 'yes'
        previous_biopsy = request.form.get('previous_biopsy') == 'yes'
        breast_density = request.form.get('breast_density', 'normal')
        hormonal_factors = request.form.get('hormonal_factors') == 'yes'
        result = assess_breast_cancer(age, family_history, genetic_factors, previous_biopsy, breast_density, hormonal_factors)
    
    elif assessment_type == 'tuberculosis':
        age = int(request.form.get('age'))
        symptoms = request.form.get('symptoms') == 'yes'
        exposure = request.form.get('exposure') == 'yes'
        immunocompromised = request.form.get('immunocompromised') == 'yes'
        previous_tb = request.form.get('previous_tb') == 'yes'
        result = assess_tuberculosis(age, symptoms, exposure, immunocompromised, previous_tb)
    
    elif assessment_type == 'covid19':
        symptoms = request.form.get('symptoms') == 'yes'
        exposure = request.form.get('exposure') == 'yes'
        vaccination_status = request.form.get('vaccination_status', 'unknown')
        underlying_conditions = request.form.get('underlying_conditions') == 'yes'
        age_group = request.form.get('age_group', 'adult')
        result = assess_covid19(symptoms, exposure, vaccination_status, underlying_conditions, age_group)
    
    elif assessment_type == 'malaria':
        symptoms = request.form.get('symptoms') == 'yes'
        travel_history = request.form.get('travel_history') == 'yes'
        area_residence = request.form.get('area_residence') == 'yes'
        previous_malaria = request.form.get('previous_malaria') == 'yes'
        prevention_measures = request.form.get('prevention_measures') == 'yes'
        result = assess_malaria(symptoms, travel_history, area_residence, previous_malaria, prevention_measures)
    
    elif assessment_type == 'liver-problem':
        symptoms = request.form.get('symptoms') == 'yes'
        alcohol_use = request.form.get('alcohol_use', 'none')
        medications = request.form.get('medications') == 'yes'
        family_history = request.form.get('family_history') == 'yes'
        previous_liver_issues = request.form.get('previous_liver_issues') == 'yes'
        result = assess_liver_problem(symptoms, alcohol_use, medications, family_history, previous_liver_issues)
    
    elif assessment_type == 'hepatitis-b':
        age = int(request.form.get('age'))
        vaccination_status = request.form.get('vaccination_status', 'unknown')
        exposure = request.form.get('exposure') == 'yes'
        symptoms = request.form.get('symptoms') == 'yes'
        risk_behaviors = request.form.get('risk_behaviors') == 'yes'
        result = assess_hepatitis_b(age, vaccination_status, exposure, symptoms, risk_behaviors)
    
    elif assessment_type == 'diabetes':
        age = int(request.form.get('age'))
        family_history = request.form.get('family_history') == 'yes'
        symptoms = request.form.get('symptoms') == 'yes'
        bmi_category = request.form.get('bmi_category', 'Normal weight')
        physical_activity = request.form.get('physical_activity', 'moderate')
        blood_pressure = request.form.get('blood_pressure') == 'yes'
        result = assess_diabetes(age, family_history, symptoms, bmi_category, physical_activity, blood_pressure)
    
    elif assessment_type == 'hydration':
        urine_color = request.form.get('urine_color', 'light_yellow')
        thirst_level = request.form.get('thirst_level', 'normal')
        activity_level = request.form.get('activity_level', 'moderate')
        fluid_intake = request.form.get('fluid_intake', 'moderate')
        symptoms = request.form.get('symptoms') == 'yes'
        result = assess_hydration(urine_color, thirst_level, activity_level, fluid_intake, symptoms)
    
    # Generate medical report for the result
    medical_report = generate_medical_report(assessment_type, result) if result else ""
    
    session['results'][assessment_type] = {
        'result': result,
        'timestamp': datetime.now().isoformat(),
        'medical_report': medical_report
    }
    session.modified = True

    # Debug logging to help diagnose issues when results don't appear
    app.logger.info(f"Stored result for {assessment_type}: {session['results'][assessment_type]}")

    # Provide a clearer flash message if the assessment returned no result
    if result is None:
        flash(f'{assessment_type.replace("-", " ").title()} assessment returned no result — please check your inputs.', 'error')
        return redirect(url_for('assessment_form', assessment_type=assessment_type))
    else:
        flash(f'{assessment_type.replace("-", " ").title()} assessment completed!', 'success')

    return redirect(url_for('results'))

@app.route('/results')
def results():
    results_data = session.get('results', {})
    is_sample = session.get('is_sample', False)
    
    # Only include assessments that were actually taken (have results)
    # Filter out None results and ensure result is not None
    filtered_results = {}
    for assessment_type, data in results_data.items():
        if data and data.get('result') is not None:
            # Generate medical report if not already present
            if 'medical_report' not in data or not data.get('medical_report'):
                data['medical_report'] = generate_medical_report(assessment_type, data['result'])
            filtered_results[assessment_type] = data
    
    return render_template('results.html', results=filtered_results, is_sample=is_sample)

@app.route('/sample-results')
def sample_results():
    """Display sample results for demonstration purposes"""
    from datetime import datetime, timedelta
    
    # Create comprehensive sample results
    sample_data = {}
    sample_results_data = {
        'bmi': calculate_bmi(75, 1.75),  # 75kg, 175cm
        'cardiovascular': assess_cardiovascular(125, 82),
        'stroke-risk': assess_stroke_risk(45, 125, False, False, False),
        'metabolic': assess_metabolic(88, 'male', 125),
        'respiratory': assess_respiratory(98),
        'fitness': assess_fitness(68, 35),
        'body-composition': assess_body_composition(18, 'male', 35),
        'posture': assess_posture(4, 4),
        'mental-health': assess_mental_health(6),
        'temperature': assess_temperature(36.8),
        'grip-strength': assess_grip_strength(42, 'male', 35),
        'lifestyle': assess_lifestyle('never', 180),
        'vision': assess_vision(20),
        'hearing': assess_hearing({
            '250': 15,
            '500': 18,
            '1000': 20,
            '2000': 22,
            '4000': 25
        })
    }
    
    timestamps = {
        'bmi': (datetime.now() - timedelta(days=1)).isoformat(),
        'cardiovascular': (datetime.now() - timedelta(days=1)).isoformat(),
        'stroke-risk': (datetime.now() - timedelta(days=2)).isoformat(),
        'metabolic': (datetime.now() - timedelta(days=1)).isoformat(),
        'respiratory': datetime.now().isoformat(),
        'fitness': (datetime.now() - timedelta(days=1)).isoformat(),
        'body-composition': (datetime.now() - timedelta(days=2)).isoformat(),
        'posture': (datetime.now() - timedelta(days=3)).isoformat(),
        'mental-health': datetime.now().isoformat(),
        'temperature': datetime.now().isoformat(),
        'grip-strength': (datetime.now() - timedelta(days=1)).isoformat(),
        'lifestyle': (datetime.now() - timedelta(days=2)).isoformat(),
        'vision': (datetime.now() - timedelta(days=6)).isoformat(),
        'hearing': (datetime.now() - timedelta(days=6)).isoformat()
    }
    
    # Build sample data with medical reports
    for assessment_type, result in sample_results_data.items():
        sample_data[assessment_type] = {
            'result': result,
            'timestamp': timestamps[assessment_type],
            'medical_report': generate_medical_report(assessment_type, result)
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

# Debug endpoint to inspect session results during local development
@app.route('/_debug/session')
def debug_session():
    # Return a JSON representation of session['results'] for quick inspection
    return json.dumps(session.get('results', {}), default=str), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    app.run(debug=True)

