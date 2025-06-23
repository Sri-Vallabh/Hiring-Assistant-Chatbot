import sqlite3
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import re
import html
import json
from tools import (
    init_db,
    insert_candidate,
    insert_question_rating,
    validate_and_extract_stacks,
    generate_tech_questions,
    evaluate_answers
)

from dotenv import load_dotenv
import os

# --- Setup ---
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')


# --- Streamlit UI ---
st.title("TalentScout - AI Hiring Assistant")
# WhatsApp-like chat styles
st.markdown("""
    <style>
    .chat-container {
        display: flex;
        margin: 10px 0;
        max-width: 80%;
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 20px;
        max-width: 80%;
        font-size: 15px;
        line-height: 1.4;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .chat-left {
        justify-content: flex-start;
    }
    .chat-right {
        justify-content: flex-end;
        margin-left: auto;
    }
    .assistant-bubble {
        background-color: #e2f0ff;
        color: #000;
    }
    .user-bubble {
        background-color: #dcf8c6;
        color: #000;
    }
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        margin: 0 8px;
    }
    </style>
""", unsafe_allow_html=True)


INFO_FIELDS = [
    ("full_name", "Full Name"),
    ("email", "Email Address"),
    ("phone", "Phone Number"),
    ("experience", "Years of Experience"),
    ("position", "Desired Position"),
    ("location", "Current Location"),
]

# --- Session State Init ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.info_collected = False
    st.session_state.candidate_data = {}
    st.session_state.tech_stack_phase = False
    st.session_state.tech_stacks = []
    st.session_state.current_stack_idx = 0
    st.session_state.questions = []
    st.session_state.answers = {}
    st.session_state.evaluations = []
    st.session_state.candidate_id = None
    st.session_state.show_final_message = False
    st.session_state.step = 0
    st.session_state.messages.append({"role": "assistant", "content": "👋 Hi! I'm your AI hiring assistant. Let's get started. What's your full name?"})
st.session_state.feedback_phase = False



# --- Chat Display (Only for info collection phase) ---
# --- Chat Display (WhatsApp-like bubbles) ---
if not st.session_state.tech_stacks:
    for msg in st.session_state.messages:
        role = msg["role"]
        content = html.escape(msg["content"])  # Escapes special HTML characters to prevent rendering issues
        is_user = role == "user"
        align_class = "chat-right" if is_user else "chat-left"
        bubble_class = "user-bubble" if is_user else "assistant-bubble"
        avatar_url = (
            "https://cdn-icons-png.flaticon.com/512/456/456212.png"  # User icon
            if is_user 
            else "https://cdn-icons-png.flaticon.com/512/4712/4712109.png"  # Assistant icon
        )

        with st.container():
            if is_user:
                st.markdown(f"""
                    <div class="chat-container {align_class}">
                        <div class="chat-bubble {bubble_class}">{content}</div>
                        <img class="avatar" src="{avatar_url}">
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-container {align_class}">
                        <img class="avatar" src="{avatar_url}">
                        <div class="chat-bubble {bubble_class}">{content}</div>
                    </div>
                """, unsafe_allow_html=True)


# --- Chat Input (Info Gathering Phase) ---
if not st.session_state.info_collected:
    prompt = st.chat_input("Type your response...")
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Show user bubble
       

        with st.container():
            escaped_prompt = html.escape(prompt)
            st.markdown(f"""
                <div class="chat-container chat-right">
                    <div class="chat-bubble user-bubble">{escaped_prompt}</div>
                    <img class="avatar" src="https://cdn-icons-png.flaticon.com/512/456/456212.png">
                </div>
            """, unsafe_allow_html=True)

        # Create chat instance
        chat = ChatOpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model="llama3-8b-8192",
            temperature=0.2
        )

        # History including system prompt
        chat_history = [
            {"role": "system", "content":
             "You are a friendly AI hiring assistant. Conversationally collect the following information from the candidate, one at a time: full name, email address, phone number, years of experience, desired position, current location. Validate that full_name, phone should be 10 digits, and location are non-empty strings, email format is valid, and experience is a number >= 0. Once all information is collected and valid, reply ONLY with the JSON object containing all fields (keys: full_name, email, phone, experience, position, location) and the message"}
        ] + st.session_state.messages

        # Get LLM response
        with st.spinner("Storing..."):
            response = chat.invoke(chat_history)

        assistant_msg = response.content
        # Extract JSON info
        try:
            json_match = re.search(r'(\{.*?\})', assistant_msg, re.DOTALL)
            if json_match:
                candidate_data = json.loads(json_match.group(1))
                valid = all(
                    candidate_data.get(field) not in [None, ""]
                    for field, _ in INFO_FIELDS
                ) and re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", candidate_data['email'])

                if valid:
                    # Save valid candidate data
                    st.session_state.candidate_data = candidate_data
                    st.session_state.info_collected = True
                    st.session_state.tech_stack_phase = True

                    # Friendly user summary message
                    summary_msg = (
                        f"✅ Thanks, {candidate_data['full_name']}!\n\n"
                        f"📧 **Email**: {candidate_data['email']}\n\n"
                        f"📱 **Phone**: {candidate_data['phone']}\n\n"
                        f"💼 **Experience**: {candidate_data['experience']} years\n\n"
                        f"🎯 **Position**: {candidate_data['position']}\n\n"
                        f"📍 **Location**: {candidate_data['location']}\n\n"
                        f"All information collected. Please enter your tech stacks (comma-separated):"
                    )

                    st.session_state.messages.append({"role": "assistant", "content": summary_msg})
                    st.rerun()
            else:
                st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

                # Show assistant bubble
                with st.container():
                    st.markdown(f"""
                        <div class="chat-container chat-left">
                            <img class="avatar" src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png">
                            <div class="chat-bubble assistant-bubble">{assistant_msg}</div>
                        </div>
                    """, unsafe_allow_html=True)
        except Exception:
            pass

# If JSON parsing succeeds and it's time to ask for tech stacks
if st.session_state.tech_stack_phase and not st.session_state.show_final_message:
    tech_stack_input = st.chat_input("Enter your tech stacks (comma-separated)...")
    
    if tech_stack_input:
        # Escape HTML to avoid injection issues
        escaped_prompt = html.escape(tech_stack_input)

        # Display user's message with WhatsApp-like style
        with st.container():
            st.markdown(f"""
                <div class="chat-container chat-right">
                    <div class="chat-bubble user-bubble">{escaped_prompt}</div>
                    <img class="avatar" src="https://cdn-icons-png.flaticon.com/512/456/456212.png">
                </div>
            """, unsafe_allow_html=True)

        # Append message to session history
        st.session_state.messages.append({"role": "user", "content": tech_stack_input})


        stacks, validation_msg = validate_and_extract_stacks(
            st.session_state.candidate_data.get("position", ""),
            tech_stack_input,groq_api_key
        )
        print(f"Extracted Stacks: {stacks}")
        if stacks:
            st.session_state.tech_stacks = stacks
            st.session_state.tech_stack_phase = False
            st.session_state.current_stack_idx = 0
            st.session_state.evaluations = []
            st.session_state.messages.append({"role": "assistant", "content": validation_msg})
            st.rerun()
        else:
            st.session_state.messages.append({"role": "assistant", "content": validation_msg})
            st.rerun()


# --- Tech Stack Q&A Flow (as before) ---
if st.session_state.tech_stacks and not st.session_state.tech_stack_phase and not st.session_state.show_final_message:
    current_stack = st.session_state.tech_stacks[st.session_state.current_stack_idx]
    st.subheader(f"Technical Screening for: {current_stack}")

    # Generate questions if not already done
    if not st.session_state.questions and not st.session_state.feedback_phase and st.session_state.step != 10:
        with st.spinner(f"Generating questions for {current_stack}..."):
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    questions = generate_tech_questions(current_stack, groq_api_key)
                    if questions:
                        st.session_state.questions = questions
                        st.session_state.answers = {i: "" for i in range(len(questions))}
                        break  # Success, exit the retry loop
                except Exception as e:
                    if attempt == max_attempts - 1:
                        st.error(f"❌ Failed after {max_attempts} attempts. Please refresh or try later.")
            else:
                st.error(f"❌ Could not generate questions for '{current_stack}' after multiple attempts.")


    # Display questions and collect answers
    if st.session_state.questions and not st.session_state.feedback_phase and st.session_state.step != 10:
        with st.form(f"answers_form_{current_stack}"):
            for i, qa in enumerate(st.session_state.questions):
                st.markdown(f"**Question {i+1}:** {qa['question']}")
                st.markdown(f"*Hint:* {qa['hint']}")
                st.session_state.answers[i] = st.text_area(
                    f"Your answer for question {i+1}",
                    value=st.session_state.answers[i],
                    key=f"answer_{i}_{current_stack}"
                )
            submitted = st.form_submit_button("Submit Answers")
            if submitted:
                if all(st.session_state.answers[i].strip() for i in range(len(st.session_state.questions))):
                    st.session_state.step = 10
                    st.session_state.feedback_phase = True
                    st.rerun()
                else:
                    st.warning("Please answer all questions before submitting.")

    # Evaluate answers for this stack
    if st.session_state.step == 10:
        st.session_state.feedback_phase = True
        st.subheader(f"Evaluation for: {current_stack}")
        try:
            with st.spinner("Evaluating answers..."):
                evaluations = evaluate_answers(
                    current_stack,
                    st.session_state.questions,
                    st.session_state.answers,groq_api_key
                )
            if evaluations:
                if len(st.session_state.evaluations) <= st.session_state.current_stack_idx:
                    st.session_state.evaluations.append(evaluations)
                else:
                    st.session_state.evaluations[st.session_state.current_stack_idx] = evaluations
            else:
                st.error("Evaluation failed or returned empty.")
        except Exception as e:
            st.error(f"Error evaluating answers: {e}")
            st.session_state.evaluations.append([])

        

        # --- Feedback Phase (Clean Screen) ---
        if st.session_state.feedback_phase:
            current_stack = st.session_state.tech_stacks[st.session_state.current_stack_idx]
            evaluations = st.session_state.evaluations[st.session_state.current_stack_idx]

            st.markdown(f"<h2 style='text-align:center;'>⭐ Feedback for <code>{current_stack}</code></h2>", unsafe_allow_html=True)

            total_stars = sum(int(item.get('stars', 0)) for item in evaluations if isinstance(item, dict))
            st.markdown(f"<div style='text-align:center; font-size:1.5em;'>Total Stars: <span style='color:gold'>{'⭐' * total_stars}</span> ({total_stars}/9)</div>", unsafe_allow_html=True)
            st.divider()

            for idx, item in enumerate(evaluations):
                if not isinstance(item, dict):
                    continue
                stars = int(item.get('stars', 0))
                feedback = item.get('feedback', '')
                st.markdown(f"**Question {idx+1}:**")
                st.markdown(f"<span style='color:gold; font-size:1.2em'>{'⭐' * stars}{'☆' * (3 - stars)}</span> ({stars}/3)", unsafe_allow_html=True)
                st.markdown(f"**Feedback:** {feedback}")
                st.divider()

            next_stack_idx = st.session_state.current_stack_idx + 1

            # Show "Next Stack" only if more stacks are left
            if next_stack_idx < len(st.session_state.tech_stacks):
                if st.button("➡️ Next Stack"):
                    st.session_state.current_stack_idx = next_stack_idx
                    st.session_state.questions = []
                    st.session_state.answers = {}
                    st.session_state.step = 8
                    st.session_state.feedback_phase = True
                    st.rerun()

            # Only show "Add Another Stack" and "Finish All Stacks" if this is the final stack
            else:
                with st.container():
                    st.markdown("### ➕ Add Another Tech Stack")
                    st.markdown("You can evaluate yourself in more tech stacks before finishing.")
                    new_stack_input = st.text_input("Enter another stack (e.g., FastAPI, AWS)", placeholder="e.g. FastAPI, AWS")

                    if st.button("✅ Add This Stack"):
                        if new_stack_input.strip():
                            new_stacks, msg = validate_and_extract_stacks(
                                st.session_state.candidate_data.get("position", ""),
                                new_stack_input,groq_api_key
                            )
                            if not new_stacks:
                                st.warning("⚠️ No valid new tech stacks found. Please try again.")
                            else:
                                # Filter out already listed stacks (case-insensitive match)
                                existing = [s.lower() for s in st.session_state.tech_stacks]
                                duplicates = [s for s in new_stacks if s.lower() in existing]
                                fresh_stacks = [s for s in new_stacks if s.lower() not in existing]

                                if duplicates:
                                    st.info(f"ℹ️ Stack(s) already listed: {', '.join(duplicates)}")

                                if fresh_stacks:
                                    st.session_state.tech_stacks.extend(fresh_stacks)
                                    st.session_state.current_stack_idx = len(st.session_state.tech_stacks) - len(fresh_stacks)
                                    st.session_state.questions = []
                                    st.session_state.answers = {}
                                    st.session_state.step = 0
                                    st.session_state.feedback_phase = False
                                    st.session_state.show_final_message = False
                                    st.rerun()

                    st.markdown("---")
                    if st.button("🏁 Finish All Stacks"):
                        st.session_state.show_final_message = True
                        st.rerun()
# --- Final Thank You Message ---
# Insert candidate if not already done
                if st.session_state.candidate_id is None:
                    st.session_state.candidate_id = insert_candidate({
                        'full_name': st.session_state.candidate_data['full_name'],
                        'email': st.session_state.candidate_data['email'],
                        'phone': st.session_state.candidate_data['phone'],
                        'experience': st.session_state.candidate_data['experience'],
                        'position': st.session_state.candidate_data['position'],
                        'location': st.session_state.candidate_data['location'],
                        'tech_stacks': st.session_state.tech_stacks
                    })

                # Insert question ratings for this stack
                for eval_item in evaluations:
                    if isinstance(eval_item, dict):
                        question = eval_item.get('question', '')
                        stars = int(eval_item.get('stars', 0))
                        feedback = eval_item.get('feedback', '')
                        insert_question_rating(
                            st.session_state.candidate_id,
                            current_stack,
                            question,
                            stars,
                            feedback
                        )
if st.session_state.get("show_final_message", False):
    st.markdown(
        "<h2 style='text-align:center; color:green;'>🙏 Thank you for participating!</h2>"
        "<p style='text-align:center;'>Your responses are under review.<br>Our HR team may contact you for further steps.</p>",
        unsafe_allow_html=True
    )
    st.stop()
