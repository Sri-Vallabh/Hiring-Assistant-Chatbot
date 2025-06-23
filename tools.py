import sqlite3
import re
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chains import LLMChain
from langchain.schema import HumanMessage

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect('talentscout_candidates.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email_address TEXT NOT NULL UNIQUE,
            phone_number TEXT NOT NULL,
            years_of_experience INTEGER NOT NULL,
            desired_position TEXT NOT NULL,
            current_location TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            tech_stack TEXT NOT NULL,
            question TEXT NOT NULL,
            stars INTEGER NOT NULL,
            feedback TEXT,
            FOREIGN KEY(candidate_id) REFERENCES candidates(id)
        )
    ''')
    conn.commit()
    conn.close()

def insert_candidate(data):
    conn = sqlite3.connect('talentscout_candidates.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO candidates (full_name, email_address, phone_number, years_of_experience, desired_position, current_location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['full_name'], data['email'], data['phone'],
            data['experience'], data['position'], data['location']
        ))
        candidate_id = cursor.lastrowid
        conn.commit()
        return candidate_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def insert_question_rating(candidate_id, tech_stack, question, stars, feedback):
    conn = sqlite3.connect('talentscout_candidates.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO question_ratings (candidate_id, tech_stack, question, stars, feedback)
            VALUES (?, ?, ?, ?, ?)
        ''', (candidate_id, tech_stack, question, stars, feedback))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting rating: {e}")
        return False
    finally:
        conn.close()

# --- LLM Functions ---
def validate_and_extract_stacks(position, input_text, groq_api_key):
    chat = ChatOpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        model="llama3-8b-8192",
        temperature=0.1
    )

    response_schemas = [
        ResponseSchema(name="stacks", description="List of valid, corrected tech stack names from the input"),
        ResponseSchema(name="message", description="Brief message validating and explaining extracted stacks")
    ]
    parser = StructuredOutputParser.from_response_schemas(response_schemas)

    prompt = PromptTemplate(
    template=(
        "You are a skilled AI assistant helping screen candidates for a tech job.\n"
        "The candidate is applying for the role: '{position}'.\n"
        "They entered the following tech stack input: '{input_text}'.\n\n"

        "Your tasks:\n"
        "1. From the input, extract only the valid **technical stack names** (e.g., programming languages, frameworks, tools).\n"
        "2. Ignore any non-technical terms (e.g., 'swimming', 'singing', etc.).\n"
        "3. Validate whether each extracted stack is relevant to the job role. If it is not relevant, remove it.\n"
        "4. Correct any spelling or formatting errors (e.g., 'pythn' → 'Python').\n"
        "5. Return an empty list if no valid stacks are found.\n\n"
        "{format_instructions}"
    ),
    input_variables=["position", "input_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)


    chain = LLMChain(llm=chat, prompt=prompt)

    try:
        raw_output = chain.run(position=position, input_text=input_text)
        parsed = parser.parse(raw_output)
        stacks = parsed.get("stacks", [])
        message = parsed.get("message", "")
        return stacks, message
    except Exception as e:
        print(f"[ERROR] Stack validation failed: {e}")
        return [], "⚠️ Couldn't parse LLM output properly. Please try entering your tech stacks again."

def generate_tech_questions(stack_name, groq_api_key):
    chat = ChatOpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        model="llama3-8b-8192",
        temperature=0.3
    )

    response_schemas = [
        ResponseSchema(name="question", description="The interview question"),
        ResponseSchema(name="hint", description="A helpful hint without revealing the answer"),
    ]
    parser = StructuredOutputParser.from_response_schemas(response_schemas)

    prompt = PromptTemplate(
        input_variables=["stack_name"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
        template=(
            "Generate 3 technical interview questions related to '{stack_name}'.\n"
            "Each must have a 'question' and a 'hint'.\n"
            "{format_instructions}"
        )
    )

    try:
        raw_output = chat.invoke([HumanMessage(content=prompt.format(stack_name=stack_name))]).content
        match = re.search(r'(\[.*\])', raw_output, re.DOTALL)
        questions_json = json.loads(match.group(1)) if match else []
        return questions_json[:3]
    except Exception as e:
        print(f"[ERROR generating questions]: {e}")
        return []

def evaluate_answers(stack_name, questions, answers, groq_api_key):
    chat = ChatOpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        model="llama3-8b-8192",
        temperature=0.0
    )

    response_schemas = [
        ResponseSchema(name="question", description="The original interview question"),
        ResponseSchema(name="stars", description="Rating from 0 to 3 stars"),
        ResponseSchema(name="feedback", description="Brief explanation or feedback")
    ]
    parser = StructuredOutputParser.from_response_schemas(response_schemas)

    qa_text = ""
    for idx, q in enumerate(questions):
        qa_text += f"\nQuestion {idx + 1}: {q['question']}\nAnswer: {answers.get(idx, '')}\n"

    prompt_template = PromptTemplate(
        input_variables=["qa_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
        template=(
            "You are a technical interviewer for the stack '{stack_name}'. Evaluate each answer.\n"
            "If you find any answer to be not satisfactory or gibberish, give it 0 stars. "
            "For each question below, evaluate the answer and assign a star rating (0 to 3 stars). "
            "Give a brief feedback for each. Return your evaluation as a JSON array with: "
            "'question', 'stars' (0-3), and 'feedback'.\n\n"
            "Here are the Q&A pairs:\n"
            "{qa_text}\n"
            "{format_instructions}"
        )
    )

    try:
        full_prompt = prompt_template.format(qa_text=qa_text, stack_name=stack_name)
        response = chat.invoke([HumanMessage(content=full_prompt)]).content
        match = re.search(r'(\[.*\])', response, re.DOTALL)
        parsed = json.loads(match.group(1)) if match else []
        return parsed
    except Exception as e:
        print(f"[ERROR evaluating answers]: {e}")
        return []
