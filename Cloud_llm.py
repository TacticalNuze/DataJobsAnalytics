import os
import re
import csv
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

def initialize():
    """Load the environment variables"""
    load_dotenv()
    return os.environ.get("GROQ_API_KEY")
class Recommandation(BaseModel):
    ID: int
    Q2_BESOIN_INTERNE:str
    Q2_BESOIN_INTERNE_CLASSIFICATION:list[str]
    Q3_BESOIN_CLIENT:str
    Q3_BESOIN_CLIENT_CLASSIFICATION:list[str]
    Q5_TECHNOLOGIE:str
    Q5_TECHNOLOGIE_CLASSIFICATION:list[str]

client = Groq(api_key=initialize())
file_name="Besoins_Data_IA.csv"
# Read input data

try:
    with open("Besoins_Data_IA.csv", "rt", encoding="utf-8") as file:
        query = file.read()
except FileNotFoundError:
    print("Error: Besoins_Data_IA.csv file not found")
    exit(1)

# Generate AI response
chat_content = f"Classify each problem by AI tool category and return JSON matching the predefined pattern, {query}"

try:
    chat_completion = client.chat.completions.create(
        messages=[
            {   "role": "user",
                "content": chat_content},
            {
                "role": "system",
                "content": "You are a LLM that outputs responses in JSON.\n"
                # Pass the json schema to the model. Pretty printing improves results.
                f" The JSON object must use the schema: {json.dumps(Recommandation.model_json_schema())},  do not replace any of the fields except classification fields",
            },
            ],
        model="llama3-70b-8192",
        
    )
except Exception as e:
    print(f"API Error: {str(e)}")
    exit(1)
print("The LLM response is:" ,chat_completion.choices[0].message.content)
# Process response safely
response_text = ""
try:
    if chat_completion.choices and len(chat_completion.choices) > 0:
        response_text = chat_completion.choices[0].message.content or ""
except AttributeError:
    print("Error: Unexpected API response structure")
    exit(1)

# Clean markdown only if response exists
if response_text:
    text_file=open("response.txt","a")
    text_file.write(response_text)
    text_file.close()

    response_text = response_text.replace('```json', '').replace('```', '')
else:
    print("Error: Empty response from API")
    exit(1)

# Parse JSON data
"""parsed_data = []
if response_text:
    for match in re.findall(pattern, response_text, re.DOTALL):
        try:
            parsed_data.append(json.loads(match))
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}\nProblematic entry: {match}")"""

# Save to CSV
"""if parsed_data:
    try:
        with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["ID", "problem", "solution", "category"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(parsed_data)
        print("Successfully saved to output.csv")
    except Exception as e:
        print(f"File Save Error: {str(e)}")
else:
    print("No valid data to save")"""