import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr 
import base64
from io import BytesIO
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime

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


booking_function ={
    "name": "get_booking",
    "description": "Create the booking for the customer when they confirm that they want to book the flight, for example when a customer says 'I want to book the flight'",
    "parameters": {
        "type":"object",
        "properties": {
            "destination_city":{
                "type": "string",
                "description": " the city that the customer wants to fly to",
            },
            "departure_date": {
                "type": "string",
                "description": "date of departure(YYYY-MM-DD)",
                },
            "return_date":{
                "type": "string",
                "description": "Date of return(YYYY-MM-DD)",
            },
            "passanger_name":{
                "type": "string",
                "description": " Full name of the passanger",
            }
        },
        "reqyured": ["destination_city","departure_date", "return_date", "passanger_name"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function":booking_function}
    ]


# def artist(city):
#     try:
#         image_response = openai.images.generate(
#             model="dall-e-3",
#             prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city} in the syle of Monet ",
#             size="1024x1024", # smallest size for dall-e
#             n=1,
#             response_format="b64_json",
#         )
#         image_base64 = image_response.data[0].b64_json
#         image_data = base64.b64decode(image_base64)
#         return Image.open(BytesIO(image_data))
#     except Exception as e:
#         print("Image generation failed:", e)
#         return None

def talker(message):
    response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx", # or alloy
        input=message
        
    )
    
    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play(audio)
  

def chat(history):
    
    # If it first message from chat bot
    if not history:
        greeting = "Hello! Welcome to FlightAI. How can I help you today?"
        history = [{"role": "assistant", "content": greeting}]
        talker(greeting)
        return history, None
    
    messages = [{"role":"system", "content": system_message}] + history 
    response = openai.chat.completions.create(model=gpt_model, messages=messages, tools=tools)
    image = None
    
    # This is what comes back from the LLM
    # user , ass, user, asss
    if response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message # collects the message from gpt
        response, city = handle_tool_call(message) # unpack the messsage from gpt
        messages.append(message) # must add 2 new roles. the message that we got back from gtp
        messages.append(response)
        # image = artist(city)
        response = openai.chat.completions.create(model=gpt_model, messages=messages)
        
    reply = response.choices[0].message.content 
    history += [{"role": "assistant", "content":reply}]
    
    # audio
    talker(reply)
    
    return history, image
        
    # return response.choices[0].message.content

def get_ticket_price(destination_city):
    print(f"Too get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

def get_booking_details(destination_city,departure_date, return_date, passanger_name):
     print(f"Too get_booking_details called for {destination_city},{departure_date}, {return_date}, {passanger_name}")
     return f"Flight booked for {passanger_name} to {destination_city} from {departure_date} to {return_date}."
    

def handle_tool_call(message):
    
    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
   
    if tool_name == "get_ticket_price":
        city = arguments.get("destination_city")
        price = get_ticket_price(city)
        response = {
            "role": "tool",
            "content": json.dumps({"destination_city": city, "price": price}),
            "tool_call_id": tool_call.id
            }
        return response, city

    elif tool_name == "get_booking":
        city = arguments.get("destination_city")
        departure = arguments.get("departure_date")
        return_date = arguments.get("return_date")
        name = arguments.get("passenger_name")
        confirmation = get_booking_details(city, departure, return_date, name)
        response = {
            "role": "tool",
            "content": json.dumps({"confirmation": confirmation}),
            "tool_call_id": tool_call.id
        }
        return response, city

    else:
        raise ValueError(f"Unknown tool: {tool_name}")
        

# gr.ChatInterface(fn=chat, type="messages").launch()

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr. Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clear = gr.Button("Clear")

    def do_entry(message, history):
        history += [{"role": "user", "content": message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=[chatbot], outputs=[chatbot, image_output]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)
ui.launch(inbrowser=True)

# translate to another language
# add agent that can listen to auto and conver to text
 