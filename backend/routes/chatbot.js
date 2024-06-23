const express = require('express');
const router = express.Router();
const chatbotController = require('../controllers/chatbotController');

router.get('/', chatbotController.startChat);
router.post('/ask', chatbotController.ask);

module.exports = router;
