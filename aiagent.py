import mysql.connector
import spacy
import re
# Add this at the top of your code
import os
import openai

openai.api_key = "<<KEY_FROM_OPEN_AI>>"
# os.getenv("OPENAI_API_KEY")  # Set this in your environment
# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# MySQL Database Configuration
DB_CONFIG = {
    "host": "mysql-redis-rahul-f27b.k.aivencloud.com",
    "port": 15161,
    "user": "avnadmin",
    "password": "<<PASSWORD>>",
    "database": "defaultdb",
    "ssl_ca": "<<PATH_TO_ROOT.CA>>",
    "ssl_verify_identity": True
}

def extract_entities(text):
    doc = nlp(text)
    entities = {"empfirname": None, "year": None}

    # Extract employee name
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["empfirname"] = ent.text
            break

    # Year extraction
    year_pattern = r'\b(20\d{2}|19\d{2})\b'
    matches = re.findall(year_pattern, text)
    entities["year"] = matches[0] if matches else None
    return entities

def get_leave_balance(emp_name, year):
    try:
        if not re.match(r'^\d{4}$', str(year)):
            return None

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT leaves_left FROM EMP_LEAVES WHERE empfirname = %s AND year = %s", 
                      (emp_name, year))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result[0] if result else None

    except mysql.connector.Error as e:
        print(f"Database error: {str(e)}")
        return None

def get_travel_preferences():
    """Collect user's travel preferences through Y/N questions"""
    def get_yn(prompt):
        while True:
            response = input(prompt).strip().lower()
            if response in ('y', 'n'):
                return response
            print("Please enter Y or N only.")

    preferences = {}
    
    # Initial suggestion question
    if get_yn("\nWould you like travel suggestions for your leave? (Y/N): ") == 'n':
        return None

    # Category selection
    print("\nSelect preferred travel categories (Y/N):")
    preferences['beaches'] = get_yn("  - Beach destinations? (Y/N): ") == 'y'
    preferences['national_parks'] = get_yn("  - National Parks? (Y/N): ") == 'y'
    preferences['cities'] = get_yn("  - Major cities? (Y/N): ") == 'y'
    preferences['road_trips'] = get_yn("  - Road trip routes? (Y/N): ") == 'y'
    preferences['historical'] = get_yn("  - Historical sites? (Y/N): ") == 'y'

    return {k:v for k,v in preferences.items() if v}

import openai  # Add this import at the top

def generate_response(leave_info, travel_prefs):
    """Generate final response with leave balance and OpenAI travel suggestions"""
    response = []
    
    # Leave balance information
    if leave_info['balance'] is None:
        response.append(f"No leave record found for {leave_info['name']} in {leave_info['year']}.")
    else:
        response.append(f"{leave_info['name']}, you have {leave_info['balance']} leaves left for {leave_info['year']}.")
    
    # Add travel suggestions if requested and balance exists
    if travel_prefs and leave_info['balance']:
        try:
            # Construct destinations from preferences
            destinations = ", ".join([k.replace('_', ' ').title() for k,v in travel_prefs.items() if v])
            print(f"\n[DEBUG] Destinations: {destinations}")  # Debug 1
            print(f"[DEBUG] Vacation Days: {leave_info['balance']}")  # Debug 2
            
            # Create system prompt
            system_prompt = """Suggest tourist locations based on below destinations types in United states only and 
                            number of days available for vacation. Please provide day by day iteranary. Provide a concise 
                            list with brief descriptions."""
            print(f"\n[DEBUG] System Prompt:\n{system_prompt}")  # Debug 3
            
            # Create user prompt
            user_prompt = f"""
            Destinations: {destinations}
            Number of vacation days: {leave_info['balance']}
            """
            print(f"\n[DEBUG] User Prompt:\n{user_prompt}")  # Debug 4
            
            # Call OpenAI API
            print("\n[DEBUG] Attempting OpenAI API call...")  # Debug 5
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            print(f"[DEBUG] API Response Received")  # Debug 6
            
            response.append("\nTravel suggestions:")
            response.append(completion.choices[0].message.content)
            
        except Exception as e:
            print(f"\n[ERROR] OpenAI API Failure Details: {str(e)}")  # Debug 7
            response.append("\nCould not generate travel suggestions due to technical error.")
    
    return '\n'.join(response)
def process():
    # Collection user query
    text = input("Enter your leave query: ").strip()
    
    
    # Collect user preferences
    travel_prefs = get_travel_preferences()
    
    # Extract Entities. Empfistname
    entities = extract_entities(text)

    # Error handling
    errors = []
    if not entities["empfirname"]: errors.append("employee name")
    if not entities["year"]: errors.append("valid year")
    if errors:
        print(f"Missing: {', '.join(errors)}. Try: 'How many leaves does John have in 2023?'")
        return

    # Get data from Persistence storage - leave balance
    leave_balance = get_leave_balance(entities["empfirname"], entities["year"])
    
    # Explicitly print retrieved balance
    print(f"\n[DEBUG] Retrieved leave balance: {leave_balance}")

    
    # Generate final output
    leave_info = {
        'name': entities["empfirname"],
        'year': entities["year"],
        'balance': leave_balance
    }
    
    print("\n" + "="*50)
    # Feed Data retrieved from persistent storage and feed to LLM along with Approriate System and user prompts
    print(generate_response(leave_info, travel_prefs))
    print("="*50)

if __name__ == "__main__":
    process()