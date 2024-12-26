import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import openai
import os
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
openai.api_key = os.getenv("OPENAI_API_KEY")
PDF_PATH = os.getenv("PDF_PATH")
WEBSITE_URL = os.getenv("WEBSITE_URL")

# Functions (unchanged)

# ----------------------
# Streamlit UI and App Logic
# ----------------------
st.set_page_config(page_title="AIBYTEC Chatbot", layout="centered", page_icon=":robot:")

# Session State Initialization
if "page" not in st.session_state:
    st.session_state['page'] = 'form'
if "chat_history" not in st.session_state:
    st.session_state['chat_history'] = []

# ----------------------
# PAGE 1: User Info Form
# ----------------------
if st.session_state['page'] == 'form':

    st.markdown("<h2 style='text-align: center;'>Please Provide Your Details</h2>", unsafe_allow_html=True)
    with st.form(key="user_form"):
        # Simplified and compact input fields
        col1, col2 = st.columns([3, 1])  # More space for the name, less for the button
        with col1:
            name = st.text_input("Name")
            email = st.text_input("Email")
            contact_no = st.text_input("Contact No.")
            specific_needs_and_challenges = st.text_input("Task to be Performed")
            training = st.text_input("Preferred Course")
            mode_of_training = st.selectbox("Mode of Training", ["Online", "Onsite"])
            
            # Preferred Time/Contact Mode with options for Email and WhatsApp
            contact_mode = st.radio("Preferred Contact Mode", ["Email", "WhatsApp"])

            if contact_mode == "Email":
                preferred_time_contact_mode = st.time_input("Preferred Time (Email)", key="email_time")
            elif contact_mode == "WhatsApp":
                preferred_time_contact_mode = st.time_input("Preferred Time (WhatsApp)", key="whatsapp_time")

        with col2:
            submitted = st.form_submit_button("Proceed to Chat")
            continue_chat = st.form_submit_button("Skip and Join Chat")

        # Submit button handling
        if submitted:
            if name and email and contact_no:
                send_email(name, email, contact_no, specific_needs_and_challenges, training, mode_of_training, preferred_time_contact_mode)
                st.session_state['page'] = 'chat'
                st.rerun()
            else:
                st.warning("Please fill out all required fields.")
        
        # Skip to Chatbot
        if continue_chat:
            st.session_state['page'] = 'chat'
            st.rerun()

# ----------------------
# PAGE 2: Chatbot Interface
# ----------------------
elif st.session_state['page'] == 'chat':
    if not st.session_state['chat_history']:
        st.session_state['chat_history'].append({
            "user": "", 
            "bot": "Hello! I'm your AI chatbot. How can I assist you today?"
        })
    
    # Streamlined chat history display
    for entry in st.session_state['chat_history']:
        if entry['user']:  # Show user messages
            st.markdown(
                f"""
                <div style="
                    background-color: #2C6D9D; 
                    padding: 8px;
                    color: #fff;
                    border-radius: 12px; 
                    margin-bottom: 8px;
                    width: fit-content;
                    max-width: 75%;
                    overflow: hidden;
                    font-family: Arial, sans-serif;
                ">
                    {entry['user']}
                </div>
                """, 
                unsafe_allow_html=True
            )
        if entry['bot']:  # Show bot messages
            st.markdown(
                f"""
                <div style="
                    background-color: #4A4A4A; 
                    padding: 8px; 
                    color: #fff; 
                    border-radius: 12px; 
                    margin-bottom: 8px;
                    margin-left: auto;
                    width: fit-content;
                    max-width: 75%;
                    overflow: hidden;
                    font-family: Arial, sans-serif;
                ">
                    {entry['bot']}
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Load PDF and Website content once
    pdf_text = extract_pdf_text(PDF_PATH) if os.path.exists(PDF_PATH) else "PDF file not found."
    website_text = scrape_website(WEBSITE_URL)

    # Fixed input bar at bottom
    user_input = st.chat_input("Ask me anything...")
    if user_input:
        # Display bot's response
        with st.spinner("Generating response..."):
            bot_response = chat_with_ai(user_input, website_text, pdf_text, st.session_state['chat_history'])
        # Append user query and bot response to chat history
        st.session_state['chat_history'].append({"user": user_input, "bot": bot_response})
        # Re-run to display updated chat history
        st.rerun()
