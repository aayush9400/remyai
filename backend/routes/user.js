const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');

router.get('/login', userController.login);
router.get('/callback', userController.callback);
router.get('/logout', userController.logout);

module.exports = router;
