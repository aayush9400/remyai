const { google } = require('googleapis');
const { DateTime } = require('luxon'); // Add this line

class GoogleUtils {
    constructor(service) {
        this.service = service;
    }

    async getUserTimezone() {
        const settings = await this.service.settings.get({ setting: 'timezone' }).then(response => response.data);
        return settings.value;
    }

    async getOrCreateMealCalendar() {
        const calendarList = await this.service.calendarList.list().then(response => response.data.items);
        let mealCalendar = calendarList.find(calendar => calendar.summary === 'Meal Plan');

        if (!mealCalendar) {
            const newCalendar = await this.service.calendars.insert({ resource: { summary: 'Meal Plan', timeZone: 'UTC' } });
            return newCalendar.data.id;
        }

        return mealCalendar.id;
    }

    async getAllEvents(userTimezone) {
        const events = [];
        const [startOfWeek, endOfWeek] = this.getCurrentWeekRange(userTimezone);
        const calendarList = await this.service.calendarList.list().then(response => response.data.items);

        for (const calendar of calendarList) {
            const eventsResult = await this.service.events.list({
                calendarId: calendar.id,
                timeMin: startOfWeek.toISO(),
                timeMax: endOfWeek.toISO(),
                singleEvents: true,
                orderBy: 'startTime',
                timeZone: userTimezone
            });

            events.push(...eventsResult.data.items);
        }

        events.sort((a, b) => DateTime.fromISO(a.start.dateTime).toMillis() - DateTime.fromISO(b.start.dateTime).toMillis());
        return events;
    }

    async addMealTimesToCalendar(schedule, calendarId, userTimezone) {
        for (const item of schedule) {
            const event = {
                summary: `Cook ${item.dish} for ${item.meal}`,
                start: { dateTime: item.start.toISO(), timeZone: userTimezone },
                end: { dateTime: item.end.toISO(), timeZone: userTimezone }
            };

            await this.service.events.insert({ calendarId, resource: event });
        }
    }

    getCurrentWeekRange(userTimezone) {
        const tz = userTimezone; // Assuming userTimezone is a string like 'America/Indiana/Indianapolis'
        const today = DateTime.local().setZone(tz);
        const startOfWeek = today.startOf('week');
        const endOfWeek = startOfWeek.plus({ days: 7 });
        return [startOfWeek, endOfWeek];
    }
}

module.exports = GoogleUtils;
