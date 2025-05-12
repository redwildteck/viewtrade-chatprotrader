import os, re, json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
client = OpenAI()


# Page configuration
current_page = os.path.splitext(os.path.basename(__file__))[0].replace(' ','_')
st.set_page_config(page_title="ViewTrade ChatbotTrader", layout="wide")


# Initialize chat history
if current_page not in st.session_state:
    st.session_state[current_page] = {"messages":
        [{"role": "system", "content": (
            "I am a knowledgeable stock sentiment analyst, "
            "and analyze a stock under current market and news."
        )}]}


# Sidebar settings
st.sidebar.header("Settings")
model = st.sidebar.selectbox(
    "Model", ["gpt-3.5-turbo", "gpt-4o-mini"]
)

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)
max_tokens = st.sidebar.number_input("Max Tokens (60-240)", 60, 240, 120)


def interpret_trade_command(model, temperature, max_tokens, instruction):
    user_prompt = f"""Convert the following stock trading command into JSON format. 
    Only support `market` and `limit` order types. Output must be valid JSON.
    
    Examples:
    Buy 100 shares of AAPL at market price
    Sell 50 shares of TSLA at limit price $700
    
    Output format:
    {{
      "action": "buy" | "sell",
      "symbol": "AAPL",
      "quantity": 100,
      "order_type": "market" | "limit",
      "limit_price": 700  // Optional, only for limit orders
    }}
    
    Now please convert: {instruction}
    """
    
    response = client.chat.completions.create(
        model = model,
        temperature = temperature,
        max_tokens = max_tokens,
        messages=[st.session_state[current_page]["messages"][0],
                  {"role": "user", "content": user_prompt}],
    )

    raw_json = response.choices[0].message.content

    return raw_json


# Main UI
st.title("ViewTrade ChatProTrader Sentiment Analysis")
st.markdown(
    "Please enter a trade execution instruction (market/limit) below, "
    "for example: 'Buy 10 shares of AAPL if it drops below $180'."
)


# Chat input
input_msg = "Enter your trade execution (market/limit order only) request here"
input_msg += " (e.g., ‘Buy 10 shares of AAPL if it drops below $180’) ..."

if instruction := st.chat_input(placeholder=input_msg):
    with st.spinner("Generating execution command ..."):
        try:
            raw_json = interpret_trade_command(model, temperature, max_tokens, instruction)
            cleaned = re.sub(r"```(?:json)?\n?", "", raw_json, flags=re.IGNORECASE).strip()
            # reply = "```json\n" + json.dumps(json.loads(cleaned), indent=2) + "\n```"
            reply = json.loads(cleaned)
            
        except Exception as e:
            reply = "⚠️ Sorry, it can't be parsed as a valid trade order, please retry!"
            
        st.session_state[current_page]["messages"].append({"role": "user", "content": instruction})
        st.session_state[current_page]["messages"].append({"role": "assistant", "content": reply})
        # st.chat_message("assistant").write(reply)


# Display chat history
if "messages" in st.session_state[current_page]:
    for msg in st.session_state[current_page]["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])
