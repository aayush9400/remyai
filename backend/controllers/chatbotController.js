const axios = require('axios');

exports.startChat = (req, res) => {
    req.session.chatHistory = [];
    req.session.questionIndex = 0;  // Track the question index
    req.session.userResponses = []; // Track user responses

    // Bot introduction
    const botIntroduction = "Hi, I'm Remy, your personal kitchen assistant. Let's get started with a few questions to know you better.";
    
    req.session.chatHistory.push({ user: false, text: botIntroduction });
    res.render('chat', { chatHistory: req.session.chatHistory });
};

exports.chat = async (req, res) => {
    const userMessage = req.body.message;
    const chatHistory = req.session.chatHistory || [];
    const userEmail = req.session.user.email;  // Get user email from session
    const questionIndex = req.session.questionIndex || 0;

    // Add the user's message to the chat history
    chatHistory.push({ user: true, text: userMessage });

    try {
        // Send the user's message and user email to the Python service
        const response = await axios.post('http://0.0.0.0:5000/chat', { 
            message: userMessage,
            user_email: userEmail,
            question_index: questionIndex,  // Send the current question index
            user_responses: req.session.userResponses  // Send the user responses
        });

        const botReply = response.data.reply;

        // Add the bot's reply to the chat history
        chatHistory.push({ user: false, text: botReply });

        // Update the question index and user responses
        req.session.questionIndex = response.data.next_question_index;
        if (response.data.current_question) {
            req.session.userResponses.push({
                question: response.data.current_question,
                answer: userMessage
            });
        }

        // Update the session chat history
        req.session.chatHistory = chatHistory;

        // Render the chat view with the updated chat history
        res.render('chat', { chatHistory });
    } catch (error) {
        console.error('Error communicating with Python service:', error);
        res.status(500).send('Error communicating with Python service');
    }
};
