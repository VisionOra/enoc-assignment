import os
import json
import base64
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Voice Restaurant Ordering System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def log(message: str, level: str = "INFO"):
    """Print detailed log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}")

# Menu data
MENU_DATA = {
    "menu_items": [
        "Big Burger Combo",
        "Double Cheeseburger",
        "Cheeseburger",
        "Hamburger",
        "Crispy Chicken Sandwich",
        "Chicken Nuggets (6 pc)",
        "Crispy Fish Sandwich",
        "Fries",
        "Baked Apple Pie",
        "Coca-Cola Drink"
    ],
    "prices": {
        "Big Burger Combo": 14.89,
        "Double Cheeseburger": 5.79,
        "Cheeseburger": 3.49,
        "Hamburger": 2.99,
        "Crispy Chicken Sandwich": 4.99,
        "Chicken Nuggets (6 pc)": 4.49,
        "Crispy Fish Sandwich": 5.29,
        "Fries": 3.19,
        "Baked Apple Pie": 1.79,
        "Coca-Cola Drink": 1.49
    },
    "images": {
        "Big Burger Combo": "/static/Menu/Big_Burger_Combo.png",
        "Double Cheeseburger": "/static/Menu/Double_Cheeseburger.png",
        "Cheeseburger": "/static/Menu/Cheeseburger.png",
        "Hamburger": "/static/Menu/Hamburger.png",
        "Crispy Chicken Sandwich": "/static/Menu/Crispy_Chicken_Sandwich.png",
        "Chicken Nuggets (6 pc)": "/static/Menu/Chicken_Nuggets__6_pc.png",
        "Crispy Fish Sandwich": "/static/Menu/Filet_Fish_Sandwich.png",
        "Fries": "/static/Menu/Fries.png",
        "Baked Apple Pie": "/static/Menu/Apple_Pie.png",
        "Coca-Cola Drink": "/static/Menu/coca_cola.png"
    },
    "descriptions": {
        "Big Burger Combo": "a classic beef burger with pickles, onions, ketchup & mustard, plus golden crispy fries and a refreshing medium Coca-Cola.",
        "Double Cheeseburger": "two juicy beef patties with melted American cheese, crisp pickles, onions, ketchup & mustard on a toasted bun.",
        "Cheeseburger": "a single beef patty with melted American cheese, crisp pickles, onions, ketchup & mustard on a soft bun.",
        "Hamburger": "a simple and timeless beef patty with pickles, onions, ketchup & mustard on a classic bun.",
        "Crispy Chicken Sandwich": "a golden-brown crispy chicken fillet with fresh shredded lettuce and creamy mayonnaise on a toasted bun.",
        "Chicken Nuggets (6 pc)": "six bite-size, all-white-meat chicken nuggets with choice of sauces: BBQ, Honey Mustard, Ranch, or Spicy.",
        "Crispy Fish Sandwich": "a golden fried fish fillet with tartar sauce and shredded lettuce on a soft steamed bun.",
        "Fries": "crispy outside, fluffy inside fries cut from premium potatoes and cooked to order.",
        "Baked Apple Pie": "a warm handheld pie with spiced apples in a flaky lattice crust.",
        "Coca-Cola Drink": "ice-cold, refreshing Coca-Cola perfect with any item or combo."
    }
}

SYSTEM_PROMPT = f"""You are a friendly voice assistant receptionist at Burger Spot restaurant. You help customers place their orders through natural voice conversation.

Available menu items and prices:
{json.dumps(MENU_DATA['prices'], indent=2)}

Menu descriptions:
{json.dumps(MENU_DATA['descriptions'], indent=2)}

MENU ITEM NAME MAPPING (use exact names from this list):
- "Big Burger Combo" - for combo, burger combo, big burger
- "Double Cheeseburger" - for double cheese, double cheeseburger  
- "Cheeseburger" - for cheeseburger, cheese burger
- "Hamburger" - for hamburger, regular burger, plain burger
- "Crispy Chicken Sandwich" - for chicken sandwich, crispy chicken
- "Chicken Nuggets (6 pc)" - for nuggets, chicken nuggets
- "Crispy Fish Sandwich" - for fish sandwich, fish fillet, filet fish
- "Fries" - for fries, french fries
- "Baked Apple Pie" - for apple pie, pie, dessert
- "Coca-Cola Drink" - for coke, cola, coca cola, soda, drink

MULTI-LANGUAGE SUPPORT:
- You can speak in: English, Spanish, French, Arabic, German, Italian, Portuguese, Chinese, Japanese, Hindi
- If customer asks to speak in another language (e.g., "speak in Spanish", "habla español", "parle français", "تكلم عربي"), switch to that language
- When switching languages, respond in the NEW language confirming the switch
- Keep speaking in the chosen language until customer asks to switch again
- Menu item names should stay in English (for system compatibility) but descriptions can be in the chosen language
- Default language is English

Your behavior:
1. Be warm, friendly, and conversational - like a real restaurant employee
2. When customer mentions ANY menu item (asking about it OR ordering), ALWAYS include it in "detected_items" so we can show them the picture
3. When customer says they want to order something (e.g., "I'll have...", "give me...", "order...", "I want..."), add it to their order and ask "Would you like anything else with that?"
4. When customer says "that's all", "no thanks", "nothing else", "I'm done", "checkout", "finalize", etc., set is_final to true
5. Keep responses SHORT - 1-2 sentences max. This is voice, not text.
6. If customer requests a language change, acknowledge it in the NEW language and continue in that language

ORDER FLOW:
- Customer mentions item → Show picture (detected_items), if ordering add to cart, ask "Would you like anything else?"
- Customer says yes/wants more → Continue taking order
- Customer says no/that's all → Finalize with "Great! Your order is ready. Your total is $X.XX. Thank you!"

Return a JSON object with:
- "items": array of {{"item_name": "exact menu item name", "quantity": number}} for items to ADD (only when customer is actually ordering)
- "remove_items": array of {{"item_name": "exact menu item name", "quantity": number}} for items to REMOVE
- "action": "add" | "remove" | "clear" | "finalize" | "greeting" | "menu_inquiry" | "question" | "language_change"
- "response": your spoken response to the customer (SHORT and conversational, IN THE CURRENT LANGUAGE)
- "detected_items": array of EXACT menu item names from the list above that were mentioned or discussed (ALWAYS include when any item is talked about)
- "is_final": true ONLY if customer confirms they want to checkout/finalize, false otherwise
- "language": the language code for the response ("en", "es", "fr", "ar", "de", "it", "pt", "zh", "ja", "hi") - include this when language changes or periodically

CRITICAL RULES:
1. ALWAYS populate "detected_items" when ANY menu item is mentioned, asked about, or ordered - use the EXACT names from the menu
2. Only add to "items" array when customer explicitly wants to ORDER (not just asking about it)
3. When adding items, ALWAYS ask "Would you like anything else with that?" or similar
4. Match item names flexibly but output EXACT menu names in detected_items and items
5. Respond in the language the customer requested - be fluent and natural in that language"""

# In-memory storage
orders = []

# Item name aliases for flexible matching
ITEM_ALIASES = {
    "big burger combo": "Big Burger Combo",
    "combo": "Big Burger Combo",
    "burger combo": "Big Burger Combo",
    "big burger": "Big Burger Combo",
    "double cheeseburger": "Double Cheeseburger",
    "double cheese": "Double Cheeseburger",
    "cheeseburger": "Cheeseburger",
    "cheese burger": "Cheeseburger",
    "hamburger": "Hamburger",
    "regular burger": "Hamburger",
    "plain burger": "Hamburger",
    "crispy chicken sandwich": "Crispy Chicken Sandwich",
    "chicken sandwich": "Crispy Chicken Sandwich",
    "crispy chicken": "Crispy Chicken Sandwich",
    "chicken nuggets (6 pc)": "Chicken Nuggets (6 pc)",
    "chicken nuggets": "Chicken Nuggets (6 pc)",
    "nuggets": "Chicken Nuggets (6 pc)",
    "6 piece nuggets": "Chicken Nuggets (6 pc)",
    "crispy fish sandwich": "Crispy Fish Sandwich",
    "fish sandwich": "Crispy Fish Sandwich",
    "fish fillet": "Crispy Fish Sandwich",
    "filet fish": "Crispy Fish Sandwich",
    "fries": "Fries",
    "french fries": "Fries",
    "baked apple pie": "Baked Apple Pie",
    "apple pie": "Baked Apple Pie",
    "pie": "Baked Apple Pie",
    "coca-cola drink": "Coca-Cola Drink",
    "coca cola": "Coca-Cola Drink",
    "coke": "Coca-Cola Drink",
    "cola": "Coca-Cola Drink",
    "soda": "Coca-Cola Drink",
    "drink": "Coca-Cola Drink",
}

def normalize_item_name(name: str) -> str:
    """Normalize an item name to the exact menu name."""
    if not name:
        return None
    name_lower = name.lower().strip()
    # Direct match in menu
    for menu_item in MENU_DATA["prices"].keys():
        if menu_item.lower() == name_lower:
            return menu_item
    # Check aliases
    if name_lower in ITEM_ALIASES:
        return ITEM_ALIASES[name_lower]
    # Partial match
    for alias, menu_name in ITEM_ALIASES.items():
        if alias in name_lower or name_lower in alias:
            return menu_name
    return None


def generate_speech(text: str) -> bytes:
    """Generate speech audio from text using OpenAI TTS."""
    log(f"Generating speech for: '{text[:50]}...' " if len(text) > 50 else f"Generating speech for: '{text}'")
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="mp3"
        )
        audio_data = response.content
        log(f"Speech generated successfully, size: {len(audio_data)} bytes")
        return audio_data
    except Exception as e:
        log(f"TTS Error: {e}", "ERROR")
        return None


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio using OpenAI Whisper."""
    log(f"Transcribing audio, size: {len(audio_bytes)} bytes")
    try:
        # Save temporarily
        temp_file = f"temp_audio_{id(audio_bytes)}.webm"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        with open(temp_file, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        os.remove(temp_file)
        log(f"Transcription result: '{transcript.text}'")
        return transcript.text
    except Exception as e:
        log(f"Transcription error: {e}", "ERROR")
        return ""


def process_with_ai(text: str, conversation_history: list) -> dict:
    """Process user input with GPT to extract order info."""
    log(f"Processing with AI: '{text}'")
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        for msg in conversation_history[-10:]:
            messages.append(msg)

        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        log(f"AI Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        log(f"AI processing error: {e}", "ERROR")
        return {
            "items": [],
            "action": "question",
            "response": "I'm sorry, could you please repeat that?",
            "detected_items": [],
            "is_final": False
        }


@app.get("/")
async def root():
    return {"message": "Voice Restaurant Ordering System API"}


@app.get("/api/menu")
async def get_menu():
    """Get full menu."""
    return {"menu": [
        {"name": item, "price": MENU_DATA["prices"][item],
         "image": MENU_DATA["images"][item], "description": MENU_DATA["descriptions"][item]}
        for item in MENU_DATA["menu_items"]
    ]}


@app.get("/api/orders")
async def get_orders():
    """Get all orders."""
    return {"orders": orders}


@app.websocket("/ws/voice")
async def websocket_voice(websocket: WebSocket):
    """WebSocket endpoint for voice ordering."""
    await websocket.accept()
    log("=" * 50)
    log("New WebSocket connection established")

    # Session state
    cart = {"items": [], "total": 0.0}
    conversation_history = []

    try:
        # Wait for start signal
        log("Waiting for start signal from client...")

        while True:
            data = await websocket.receive_json()
            log(f"Received message type: {data.get('type')}")

            if data["type"] == "start_session":
                log("Start session requested, generating welcome message...")

                welcome_text = "Welcome to Burger Spot! I'm here to take your order. What can I get for you today?"
                log(f"AGENT SAYS: {welcome_text}")

                # Generate welcome audio
                audio = generate_speech(welcome_text)

                if audio:
                    audio_b64 = base64.b64encode(audio).decode()
                    log(f"Sending welcome audio to client, base64 length: {len(audio_b64)}")

                    await websocket.send_json({
                        "type": "audio",
                        "audio": audio_b64
                    })
                    log("Welcome audio sent successfully")
                else:
                    log("Failed to generate welcome audio!", "ERROR")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to generate audio"
                    })

            elif data["type"] == "audio":
                log("Received audio from user")

                # Decode audio
                audio_bytes = base64.b64decode(data["audio"])
                log(f"Decoded audio size: {len(audio_bytes)} bytes")

                # Validate audio size (minimum 10KB for meaningful audio)
                MIN_AUDIO_SIZE = 10000
                if len(audio_bytes) < MIN_AUDIO_SIZE:
                    log(f"Audio too small ({len(audio_bytes)} bytes < {MIN_AUDIO_SIZE}), ignoring", "WARN")
                    # Don't respond, just ignore - let frontend handle the feedback
                    continue

                # Transcribe
                user_text = transcribe_audio(audio_bytes)

                if not user_text or len(user_text.strip()) < 2:
                    log("Empty or too short transcription, ignoring", "WARN")
                    # Only respond if audio was substantial but couldn't be understood
                    if len(audio_bytes) > 30000:
                        error_audio = generate_speech("I didn't catch that. Could you please repeat?")
                        if error_audio:
                            await websocket.send_json({
                                "type": "audio",
                                "audio": base64.b64encode(error_audio).decode()
                            })
                    continue

                log(f"USER SAID: {user_text}")

                # Add to conversation history
                conversation_history.append({"role": "user", "content": user_text})

                # Process with AI
                ai_result = process_with_ai(user_text, conversation_history)

                # Add AI response to history
                conversation_history.append({"role": "assistant", "content": ai_result["response"]})

                log(f"AGENT SAYS: {ai_result['response']}")
                log(f"Action: {ai_result.get('action')}, Items: {ai_result.get('items')}, Detected: {ai_result.get('detected_items')}")

                # Process cart updates
                if ai_result.get("action") == "add" and ai_result.get("items"):
                    for item in ai_result["items"]:
                        raw_item_name = item.get("item_name")
                        quantity = item.get("quantity", 1)
                        
                        # Normalize the item name
                        item_name = normalize_item_name(raw_item_name)
                        if not item_name:
                            log(f"Could not normalize item name: {raw_item_name}", "WARN")
                            continue

                        if item_name in MENU_DATA["prices"]:
                            # Check if already in cart
                            found = False
                            for cart_item in cart["items"]:
                                if cart_item["name"] == item_name:
                                    cart_item["quantity"] += quantity
                                    found = True
                                    log(f"Updated cart: {item_name} x{cart_item['quantity']}")
                                    break

                            if not found:
                                cart["items"].append({
                                    "name": item_name,
                                    "quantity": quantity,
                                    "price": MENU_DATA["prices"][item_name],
                                    "image": MENU_DATA["images"][item_name]
                                })
                                log(f"Added to cart: {item_name} x{quantity}")

                    cart["total"] = sum(i["price"] * i["quantity"] for i in cart["items"])
                    log(f"Cart total: ${cart['total']:.2f}")

                elif ai_result.get("action") == "remove" and ai_result.get("remove_items"):
                    for item in ai_result["remove_items"]:
                        raw_item_name = item.get("item_name")
                        quantity = item.get("quantity", 1)
                        
                        # Normalize the item name
                        item_name = normalize_item_name(raw_item_name)
                        if not item_name:
                            continue

                        for i, cart_item in enumerate(cart["items"]):
                            if cart_item["name"] == item_name:
                                cart_item["quantity"] -= quantity
                                if cart_item["quantity"] <= 0:
                                    cart["items"].pop(i)
                                    log(f"Removed from cart: {item_name}")
                                else:
                                    log(f"Updated cart: {item_name} x{cart_item['quantity']}")
                                break

                    cart["total"] = sum(i["price"] * i["quantity"] for i in cart["items"])

                elif ai_result.get("action") == "clear":
                    cart = {"items": [], "total": 0.0}
                    log("Cart cleared")

                # Check for order finalization
                if ai_result.get("action") == "finalize" or ai_result.get("is_final"):
                    if cart["items"]:
                        order_data = {
                            "id": len(orders) + 1,
                            "items": cart["items"].copy(),
                            "total": cart["total"],
                            "status": "confirmed"
                        }
                        orders.append(order_data)
                        log(f"ORDER CONFIRMED: #{order_data['id']}, Total: ${order_data['total']:.2f}")

                        # Send order confirmation
                        await websocket.send_json({
                            "type": "order_confirmed",
                            "order": order_data
                        })

                        # Clear cart
                        cart = {"items": [], "total": 0.0}

                # Send items to display (if any mentioned)
                display_items = []
                for item_name in ai_result.get("detected_items", []):
                    # Normalize the item name to handle variations
                    normalized_name = normalize_item_name(item_name)
                    if normalized_name and normalized_name in MENU_DATA["prices"]:
                        # Avoid duplicates
                        if not any(d["name"] == normalized_name for d in display_items):
                            display_items.append({
                                "name": normalized_name,
                                "price": MENU_DATA["prices"][normalized_name],
                                "image": MENU_DATA["images"][normalized_name],
                                "description": MENU_DATA["descriptions"][normalized_name]
                            })
                            log(f"Detected item for display: {normalized_name}")

                if display_items:
                    log(f"Sending display items: {[i['name'] for i in display_items]}")
                    await websocket.send_json({
                        "type": "show_items",
                        "items": display_items
                    })

                # Send cart update
                await websocket.send_json({
                    "type": "cart_update",
                    "cart": cart
                })

                # Generate and send audio response
                audio = generate_speech(ai_result["response"])

                if audio:
                    audio_b64 = base64.b64encode(audio).decode()
                    log(f"Sending response audio, base64 length: {len(audio_b64)}")

                    await websocket.send_json({
                        "type": "audio",
                        "audio": audio_b64
                    })
                    log("Response audio sent")
                else:
                    log("Failed to generate response audio!", "ERROR")

                log("-" * 30)

    except WebSocketDisconnect:
        log("Client disconnected")
    except Exception as e:
        log(f"WebSocket error: {e}", "ERROR")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    log("Starting Voice Restaurant Ordering System...")
    log(f"OpenAI API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
