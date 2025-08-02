import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr 

load_dotenv(override=True)

gpt_model ="gpt-4o-mini"
openai = OpenAI()

system_message =" You are a helpful assistant for an Airline called FlightAI."
system_message += "Give a short, courteos answers, no more than 1 sentence."
system_message += "Always be accurate. If you do not know the anwers, say so"

# when you create this tool, this is how it needs to look 
price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499"}
tools = [{"type": "function", "function": price_function}]

def chat(message, history):
    messages = [{"role":"system", "content": message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=gpt_model, messages=messages, tools=tools)
    
    # This is what comes back from the LLM
    # user , ass, user, asss
    if response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message # collects the message from gpt
        response, city = handle_tool_call(message) # unpack the messsage from gpt
        messages.append(message) # must add 2 new roles. the message that we got back from gtp
        messages.append(response)
        response = openai.chat.completions.create(model=gpt_model, messages=messages)
        
    return response.choices[0].message.content

def get_ticket_price(destination_city):
    print(f"Too get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get('destination_city')
    price = get_ticket_price(city)
    response = {
        "role": "tool",
        "content": json.dumps({"destination_city": city, "price": price}),
        "tool_call_id": tool_call.id
        }
    return response, city

gr.ChatInterface(fn=chat, type="messages").launch()
# def chat(message, history):
#     messages =[{"role": "system", "content": system_message}] + history +[{"role":"user", "content": message}]
#     response = openai.chat.completions.create(model=gpt_model, messages=messages)
    
# gr.ChatInterface(fn=chat, type="messages").launch()

# ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499"}







# # And this is included in a list of tools:

# tools = [{"type": "function", "function": price_function}]

 