const express = require('express');
const router = express.Router();
const calendarController = require('../controllers/calendarController');

router.get('/', calendarController.index);
router.post('/schedule', calendarController.schedule);

module.exports = router;
