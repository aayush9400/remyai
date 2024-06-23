const { google } = require('googleapis');
const config = require('../config/config');
const ScheduleUtils = require('../utils/scheduleUtils');
const GoogleUtils = require('../utils/googleUtils');
const fs = require('fs');
const path = require('path');
const { DateTime } = require('luxon');

const credentials = JSON.parse(fs.readFileSync(config.clientSecretsFile));

const oauth2Client = new google.auth.OAuth2(
    credentials.web.client_id,
    credentials.web.client_secret,
    config.redirectUri
);

exports.index = async (req, res) => {
    if (!req.session.user) {
        return res.redirect('/user/login');
    }

    oauth2Client.setCredentials(req.session.tokens);

    try {
        const calendar = google.calendar({ version: 'v3', auth: oauth2Client });
        const googleUtils = new GoogleUtils(calendar);
        const userTimezone = await googleUtils.getUserTimezone();
        const events = await googleUtils.getAllEvents(userTimezone);
        const userInfo = req.session.user || {};
        res.render('homepage', { layout: 'layout', events, userInfo });
    } catch (err) {
        console.error('Error fetching events:', err);
        res.status(500).send('Error fetching events');
    }
};

exports.schedule = async (req, res) => {
    if (!req.session || !req.session.tokens) {
        return res.redirect('/user/login');
    }

    oauth2Client.setCredentials(req.session.tokens);
    const service = google.calendar({ version: 'v3', auth: oauth2Client });
    const googleUtils = new GoogleUtils(service);

    try {
        const userTimezone = await googleUtils.getUserTimezone();
        const mealPlanPath = path.resolve(__dirname, '../config/meal_plan.json');
        const mealPlan = JSON.parse(fs.readFileSync(mealPlanPath, 'utf8'));

        const events = await googleUtils.getAllEvents(userTimezone);
        const scheduleUtils = new ScheduleUtils();
        const freeSlots = scheduleUtils.getFreeSlots(events, userTimezone);

        const schedule = freeSlots.length === 0 ?
            scheduleUtils.createScheduleWithDefaultTimes(mealPlan, userTimezone) :
            scheduleUtils.createSchedule(freeSlots, mealPlan, userTimezone);

        const mealCalendarId = await googleUtils.getOrCreateMealCalendar();
        await googleUtils.addMealTimesToCalendar(schedule, mealCalendarId, userTimezone);

        const startOfWeek = DateTime.local().setZone(userTimezone).startOf('week').toISO();
        const endOfWeek = DateTime.local().setZone(userTimezone).endOf('week').toISO();

        const mealEvents = await service.events.list({
            calendarId: mealCalendarId,
            timeMin: startOfWeek,
            timeMax: endOfWeek,
            singleEvents: true,
            orderBy: 'startTime'
        }).then(response => response.data.items);

        const userInfo = req.session.user || {};
        res.render('homepage', { layout: 'layout', events: mealEvents, userInfo });
    } catch (err) {
        console.error('Error fetching events:', err);
        res.status(500).send('Error fetching events');
    }
};

