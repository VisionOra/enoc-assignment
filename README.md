# Voice Restaurant Ordering System

A voice-powered restaurant ordering system similar to [Vuen AI](https://restaurant.vuen.ai/). This system allows customers to order food using voice commands with instant visual feedback showing menu items as they're mentioned.

## Features

- **Voice Ordering**: Press and hold to speak your order
- **Instant Visual Feedback**: Menu items appear instantly (<200ms) when mentioned
- **Real-time Cart Updates**: Cart updates automatically as items are added/removed
- **AI-Powered Understanding**: Uses OpenAI for speech-to-text and order interpretation
- **WebSocket Communication**: Real-time bidirectional communication
- **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (add your API key here)
│   ├── create_placeholders.py  # Generate placeholder images
│   └── static/
│       └── Menu/               # Menu item images
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.js
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

5. (Optional) Replace placeholder images in `static/Menu/` with actual food images

6. Start the backend server:
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. (Optional) Configure API URL in `.env`:
   ```
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_WS_URL=ws://localhost:8000
   ```

4. Start the development server:
   ```bash
   npm start
   ```

   The app will open at `http://localhost:3000`

## Usage

1. **Voice Ordering**:
   - Click and hold the microphone button
   - Speak your order (e.g., "I'd like a Big Burger Combo and some fries")
   - Release the button
   - Watch as items appear instantly and get added to your cart

2. **Manual Ordering**:
   - Click on any menu item to add it to your cart
   - Use +/- buttons to adjust quantities

3. **Checkout**:
   - Click "Proceed to Checkout"
   - Fill in your delivery details
   - Confirm your order

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/menu` | Get all menu items |
| GET | `/api/cart` | Get current cart |
| POST | `/api/cart/add` | Add item to cart |
| POST | `/api/cart/remove` | Remove item from cart |
| POST | `/api/cart/clear` | Clear the cart |
| POST | `/api/order/checkout` | Process checkout |
| POST | `/api/transcribe` | Transcribe audio (REST) |
| WS | `/ws/voice` | WebSocket for voice ordering |

## WebSocket Events

### Client to Server
```json
{
  "type": "audio",
  "audio": "<base64-encoded-audio>"
}
```

### Server to Client
```json
{
  "type": "items_detected",
  "items": [...],
  "transcript": "user's speech"
}
```

```json
{
  "type": "response",
  "transcript": "user's speech",
  "message": "AI response",
  "cart": {...},
  "action": "add|remove|clear|checkout"
}
```

## Menu Items

| Item | Price |
|------|-------|
| Big Burger Combo | $14.89 |
| Double Cheeseburger | $5.79 |
| Cheeseburger | $3.49 |
| Hamburger | $2.99 |
| Crispy Chicken Sandwich | $4.99 |
| Chicken Nuggets (6 pc) | $4.49 |
| Crispy Fish Sandwich | $5.29 |
| Fries | $3.19 |
| Baked Apple Pie | $1.79 |
| Coca-Cola Drink | $1.49 |

## Customization

### Adding Menu Items

Edit the `MENU_DATA` dictionary in `backend/main.py`:

```python
MENU_DATA = {
    "menu_items": ["New Item", ...],
    "prices": {"New Item": 9.99, ...},
    "images": {"New Item": "/static/Menu/new_item.png", ...},
    "descriptions": {"New Item": "Description here", ...}
}
```

### Adding Item Aliases

Add aliases in the `ITEM_ALIASES` dictionary for better voice recognition:

```python
ITEM_ALIASES = {
    "new item": "New Item",
    "alias": "New Item",
    ...
}
```

## Tech Stack

- **Backend**: FastAPI, Python, OpenAI API (Whisper + GPT)
- **Frontend**: React, CSS3
- **Communication**: WebSocket, REST API

## License

MIT License
