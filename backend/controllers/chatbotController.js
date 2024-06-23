const questions = [
    "What is your favorite cuisine?",
    "Do you have any food allergies?",
    "What are your dietary preferences/restrictions?",
    "What is your daily calorie intake goal?",
    "Can you tell me what you currently have in your pantry?"
];

exports.startChat = (req, res) => {
    if (!req.session.chatHistory) {
        req.session.chatHistory = [];
    }
    req.session.chatHistory.push({ user: false, text: questions[0] });
    res.render('chat', { layout: 'layout', chatHistory: req.session.chatHistory });
};

exports.ask = (req, res) => {
    const userInput = req.body.userInput;
    req.session.chatHistory.push({ user: true, text: userInput });
    
    const nextQuestionIndex = req.session.chatHistory.filter(entry => !entry.user).length;
    if (nextQuestionIndex < questions.length) {
        req.session.chatHistory.push({ user: false, text: questions[nextQuestionIndex] });
        res.render('chat', { layout: 'layout', chatHistory: req.session.chatHistory });
    } else {
        res.redirect('/calendar');
    }
};
