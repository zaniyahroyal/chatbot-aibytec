import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import openai
import os

# ----------------------
# Configuration
# ----------------------
SENDER_EMAIL =  os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL =  os.getenv("RECEIVER_EMAI")  # Target email to send data
openai.api_key =  os.getenv("OPENAI_API_KEY") # Replace with your OpenAI API key

PDF_PATH = "./Aibytec fine tuned data.pdf"  # Path to your PDF
WEBSITE_URL = "https://aibytec.com/"  # Target website URL

# ----------------------
# Functions
# ----------------------

# Function to send email
def send_email(name, email, contact_no, area_of_interest):
    subject = "New Student Profile Submission"
    body = f"""
    New Student Profile Submitted:

    Name: {name}
    Email: {email}
    Contact No.: {contact_no}
    Area of Interest: {area_of_interest}
    """
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = RECEIVER_EMAIL
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Function to extract PDF text
def extract_pdf_text(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# Function to scrape website content
def scrape_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"Error scraping website: {e}"

# Function to generate OpenAI response
def chat_with_ai(user_question, website_text, pdf_text, chat_history):
    combined_context = f"Website Content:\n{website_text}\n\nPDF Content:\n{pdf_text}"
    messages = [{"role": "system", "content": "You are a helpful assistant. Use the provided content."}]
    # Add full chat history
    for entry in chat_history:
        messages.append({"role": "user", "content": entry['user']})
        messages.append({"role": "assistant", "content": entry['bot']})
    messages.append({"role": "user", "content": f"{combined_context}\n\nQuestion: {user_question}"})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=False  # Faster response
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating response: {e}"

# ----------------------
# Streamlit UI
# ----------------------

st.set_page_config(page_title="Student Profile & AI Chatbot", layout="wide")

# Session State Initialization
if "page" not in st.session_state:
    st.session_state['page'] = 'form'
if "chat_history" not in st.session_state:
    st.session_state['chat_history'] = []

# ----------------------
# PAGE 1: User Info Form
# ----------------------
if st.session_state['page'] == 'form':
    st.title("Student Profile Submission")
    with st.form(key="user_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        contact_no = st.text_input("Contact No.")  # Replaced Field of Interest
        area_of_interest = st.text_area("Area of Interest")  # Replaced Study Preferences
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if name and email and contact_no and area_of_interest:
                send_email(name, email, contact_no, area_of_interest)
                st.session_state['page'] = 'chat'
                st.rerun()
            else:
                st.warning("Please fill out all fields.")
    
    # Add Skip Button
    if st.button("Skip and Chat"):
        st.session_state['page'] = 'chat'
        st.rerun()

# ----------------------
# PAGE 2: Chatbot Interface
# ----------------------
elif st.session_state['page'] == 'chat':
    st.title("AIBYTEC'S Chatbot")

    # Display chat history with background colors
    for entry in st.session_state['chat_history']:
        # User Message
        st.markdown(
            f"""
            <div style="
                background-color: #78bae4; 
                padding: 10px; 
                border-radius: 10px; 
                margin-bottom: 10px;
                width: fit-content;
                max-width: 80%;
            ">
                <b>User:</b> {entry['user']}
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Assistant Message
        st.markdown(
            f"""
            <div style="
                background-color: #D3D3D3; 
                padding: 10px; 
                border-radius: 10px; 
                margin-bottom: 10px;
                margin-left: auto;
                width: fit-content;
                max-width: 80%;
            ">
                <b>Assistant:</b> {entry['bot']}
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Load PDF and Website content once
    pdf_text = extract_pdf_text(PDF_PATH) if os.path.exists(PDF_PATH) else "PDF file not found."
    website_text = scrape_website(WEBSITE_URL)

    # Fixed input bar at bottom
    user_input = st.chat_input("Type your question here...", key="user_input_fixed")

    if user_input:
        # Display bot's response
        with st.spinner("Generating response..."):
            bot_response = chat_with_ai(user_input, website_text, pdf_text, st.session_state['chat_history'])
        
        # Append user query and bot response to chat history
        st.session_state['chat_history'].append({"user": user_input, "bot": bot_response})
        
        # Re-run to display updated chat history
        st.rerun()





