# Remy.ai

Remy.ai is a smart kitchen assistant that helps users plan their meals, manage their pantry, and maintain a healthy diet. The app integrates with Google Calendar to schedule meals and provides a chatbot interface powered by OpenAI for personalized assistance.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Google Calendar Integration**: Plan and schedule meals directly into your Google Calendar.
- **Chatbot Assistant**: Interactive chatbot that learns user preferences and provides personalized meal suggestions.
- **Meal Planning**: Generate meal plans based on user preferences and dietary restrictions.
- **Dark Mode**: Toggle between light and dark modes for better user experience.

## Tech Stack

- **Frontend**: HTML, CSS, EJS, JavaScript, Bootstrap
- **Backend**: Node.js, Express.js, FastAPI (Python)
- **Database**: (Optional) MongoDB or MySQL for user data storage
- **APIs**: Google Calendar API, OpenAI GPT-3

## Project Structure

remy.ai/ \
│\
├── backend/\
│ ├── controllers/\
│ │ ├── calendarController.js\
│ │ ├── chatbotController.js\
│ │ ├── homeController.js\
│ │ └── userController.js\
│ ├── public/\
│ │ ├── css/\
│ │ │ └── styles.css\
│ │ └── js/\
│ │ └── theme.js\
│ ├── routes/\
│ │ ├── calendar.js\
│ │ ├── chatbot.js\
│ │ ├── home.js\
│ │ └── user.js\
│ ├── utils/\
│ │ ├── apiUtils.js\
│ │ ├── googleUtils.js\
│ │ └── scheduleUtils.js\
│ ├── views/\
│ │ ├── calendar.ejs\
│ │ ├── chat.ejs\
│ │ ├── home.ejs\
│ │ ├── layout.ejs\
│ │ ├── login.ejs\
│ │ └── partials/\
│ │ ├── header.ejs\
│ │ └── footer.ejs\
│ ├── config/\
│ │ ├── config.js\
│ │ └── meal_plan.json\
│ ├── app.js\
│ ├── package.json\
│ └── package-lock.json\
│\
├── python/\
│ ├── services/\
│ │ └── api.py\
│ ├── main.py\
│ ├── requirements.txt\
│ └── .env\
│\
└── README.md\


## Setup and Installation

### Prerequisites

- Node.js
- Python 3.8+
- MongoDB or MySQL (Optional for user data storage)
- Google Cloud Project with OAuth 2.0 credentials
- OpenAI API key

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/remy.ai.git
cd remy.ai
```
2. Install Node.js dependencies:
```bash
cd backend
npm install
```
3. Set up environment variables:
Create a .env file in the backend directory and add your environment variables:
```bash
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:3000/user/callback
SESSION_SECRET=your_session_secret
```

4. Run the Node.js server:
    ```bash 
    npm start
    ```

### Python Service Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```
2. Set up environment variables:
Create a .env file in the python directory and add your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key
```
3. Run the FastAPI server:
```bash
uvicorn main:app --reload
```
## Usage
1. Open your browser and navigate to http://localhost:3000.
2. Click "Login with Google" to authenticate.
3. Interact with the chatbot and plan your meals.
4. View and manage your meal schedule on the calendar page.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License.