import os
import re
import csv
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
import pandas as pd



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
def clean_response(chat_completion):
    # Process response safely
    response_text = ""
    try:
        if chat_completion.choices and len(chat_completion.choices) > 0:
            response_text = chat_completion.choices[0].message.content or ""
    except AttributeError:
        print("Error: Unexpected API response structure")
        exit(1)
    print("The returned text from the LLM",chat_completion.choices[0].message.content)
    # Clean markdown only if response exists
    if response_text:
        text_file=open("response.txt","a")
        text_file.write(response_text)
        text_file.close()

        response_text = response_text.replace('```json', '').replace('```', '')
        return response_text
    else:
        print("Error: Empty response from API")
        exit(1)
def matchJson(json_response):
    pattern = re.compile(r'''
    \{
        \s*"ID"\s*:\s*(\d+),                             # ID: number
        \s*"Q2_BESOIN_INTERNE"\s*:\s*"([^"]*)",         # Q2_BESOIN_INTERNE: text
        \s*"Q2_BESOIN_INTERNE_CLASSIFICATION"\s*:\s*(\[[^\]]*\]),  # Q2_BESOIN_INTERNE_CLASSIFICATION: list
        \s*"Q3_BESOIN_CLIENT"\s*:\s*"([^"]*)",         # Q3_BESOIN_CLIENT: text
        \s*"Q3_BESOIN_CLIENT_CLASSIFICATION"\s*:\s*(\[[^\]]*\]),  # Q3_BESOIN_CLIENT_CLASSIFICATION: list
        \s*"Q5_TECHNOLOGIE"\s*:\s*"([^"]*)",           # Q5_TECHNOLOGIE: text
        \s*"Q5_TECHNOLOGIE_CLASSIFICATION"\s*:\s*(\[[^\]]*\])  # Q5_TECHNOLOGIE_CLASSIFICATION: list
    \}
''', re.VERBOSE)
    matches = pattern.findall(json_response)
    return matches

def create_final_Json(response_text):
    matches=matchJson(response_text)
    print("The final JSON: ",matches)

    data_list = []
    for match in matches:
        data_list.append({
            "ID": int(match[0]),
            "Q2_BESOIN_INTERNE": match[1],
            "Q2_BESOIN_INTERNE_CLASSIFICATION": json.loads(match[2]),  # Convert list string to actual list
            "Q3_BESOIN_CLIENT": match[3],
            "Q3_BESOIN_CLIENT_CLASSIFICATION": json.loads(match[4]),  # Convert list string to actual list
            "Q5_TECHNOLOGIE": match[5],
            "Q5_TECHNOLOGIE_CLASSIFICATION": json.loads(match[6])  # Convert list string to actual list
        })
    return data_list
def save_to_xlsx(df:pd.DataFrame):
    for col in df.select_dtypes(include=[list]).columns:
        df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    # Save to Excel
    df.to_excel("output.xlsx", index=False)

    print("Excel file saved successfully.")

# Read input data
client = Groq(api_key=initialize())
file_name="Besoins_Data_IA.xlsx"
sheet_name="Data"
def read_xlsx(file_name,sheet_name):
    try:
        # Read thefile
        df = pd.read_excel(file_name, engine="openpyxl",index_col=0,sheet_name=sheet_name)
        query=df.to_csv(sep=',')
        # Check if the file is empty
        if df.empty:
            print(f"Warning: {file_name} is empty!")
    except FileNotFoundError:
        print(f"Error: {file_name} file not found")
        exit(1)
    return query

def generate_LLM_request():
    # Generate AI response
    chat_content = f"Classify each problem by AI tool category and return JSON matching the predefined pattern, {read_xlsx(file_name,sheet_name)}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {   "role": "user",
                    "content": chat_content},
                {
                    "role": "system",
                    "content": "You are a LLM that outputs responses in JSON.\n"
                    # Pass the json schema to the model. Pretty printing improves results.
                    f" The JSON object must use the schema: {json.dumps(Recommandation.model_json_schema())},do not add any text except for the json, do not replace any of the fields in the input except classification fields, if one the fields is empty or you cannot answer the classification shoud be NEED MORE DETAILS",
                }
                ],
            model="llama3-70b-8192",
            
        )
    except Exception as e:
        print(f"API Error: {str(e)}")
        exit(1)
    return chat_completion

data_to_write=[]
count=1
while data_to_write==[]:
    try:
        response_text=clean_response(generate_LLM_request())
        data_to_write=create_final_Json(response_text)
        df=pd.DataFrame(data_to_write)
        try:
            save_to_xlsx(df)
        except Exception as e:
            print(f"Couldnt save file {str(e)}")
    except:
        print("Error parsing data")


