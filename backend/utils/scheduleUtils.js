const { DateTime, Duration } = require('luxon');

class ScheduleUtils {
    constructor(mealTimes = null) {
        this.mealTimes = mealTimes || {
            'breakfast': { 'start': '06:00', 'end': '10:00' },
            'lunch': { 'start': '11:00', 'end': '14:00' },
            'dinner': { 'start': '18:00', 'end': '21:00' }
        };

        for (const meal in this.mealTimes) {
            this.mealTimes[meal].start = DateTime.fromFormat(this.mealTimes[meal].start, 'HH:mm');
            this.mealTimes[meal].end = DateTime.fromFormat(this.mealTimes[meal].end, 'HH:mm');
        }
    }

    filterSlotsByMealTime(freeSlots, mealTimeRange, cookTimeMinutes) {
        const filteredSlots = [];
        for (const slot of freeSlots) {
            const [start, end] = slot;
            const mealStart = start.set({ hour: mealTimeRange.start.hour, minute: mealTimeRange.start.minute });
            const mealEnd = start.set({ hour: mealTimeRange.end.hour, minute: mealTimeRange.end.minute });

            if (start < mealEnd && end > mealStart) {
                const latestStartTime = Math.min(end.toMillis(), mealEnd.toMillis()) - Duration.fromObject({ minutes: cookTimeMinutes }).toMillis();
                if (latestStartTime >= Math.max(start.toMillis(), mealStart.toMillis())) {
                    filteredSlots.push([DateTime.fromMillis(Math.max(start.toMillis(), mealStart.toMillis())), DateTime.fromMillis(latestStartTime)]);
                }
            }
        }
        return filteredSlots;
    }

    createSchedule(freeSlots, mealPlan, userTimezone) {
        const schedule = [];
        const tz = userTimezone;
        const today = DateTime.local().setZone(tz);
        const startOfWeek = today.startOf('week');
        const usedSlots = [];

        for (const [day, meals] of Object.entries(mealPlan.week)) {
            const dayStart = startOfWeek.plus({ days: Object.keys(mealPlan.week).indexOf(day) }).startOf('day').setZone(tz);
            const dayEnd = startOfWeek.plus({ days: Object.keys(mealPlan.week).indexOf(day) }).endOf('day').setZone(tz);

            const dayFreeSlots = freeSlots.filter(slot => dayStart <= slot[0] && slot[0] < dayEnd);

            for (const [meal, details] of Object.entries(meals)) {
                const mealTimeRange = this.mealTimes[meal];
                const cookTimeMinutes = Duration.fromISOTime(details.time).as('minutes');
                const mealSlots = this.filterSlotsByMealTime(dayFreeSlots, mealTimeRange, cookTimeMinutes);

                // console.log(`Day: ${day}, Meal: ${meal}, MealSlots:`, mealSlots); // Log the meal slots

                for (const slot of mealSlots) {
                    const [start, end] = slot;
                    const duration = (end.toMillis() - start.toMillis()) / 60000; // Convert to minutes

                    if (cookTimeMinutes <= duration) {
                        schedule.push({
                            day,
                            meal,
                            dish: details.dish,
                            start,
                            end: start.plus({ minutes: cookTimeMinutes })
                        });
                        usedSlots.push(slot);
                        break;
                    }
                }

                // Remove used slots to prevent overlap
                usedSlots.forEach(slot => {
                    const index = freeSlots.indexOf(slot);
                    if (index > -1) {
                        freeSlots.splice(index, 1);
                    }
                });
            }
        }

        return schedule;
    }

    createScheduleWithDefaultTimes(mealPlan, userTimezone) {
        const schedule = [];
        const tz = userTimezone;
        const today = DateTime.local().setZone(tz);
        const startOfWeek = today.startOf('week');

        for (const [day, meals] of Object.entries(mealPlan.week)) {
            const dayOffset = Object.keys(mealPlan.week).indexOf(day);
            for (const [meal, details] of Object.entries(meals)) {
                const startTime = this.mealTimes[meal].start;
                const cookTime = Duration.fromISOTime(details.time).as('minutes');
                const start = startOfWeek.plus({ days: dayOffset }).set({ hour: startTime.hour, minute: startTime.minute }).setZone(tz);
                const end = start.plus({ minutes: cookTime });
                schedule.push({
                    day,
                    meal,
                    dish: details.dish,
                    start,
                    end
                });
            }
        }

        return schedule;
    }

    getFreeSlots(events, userTimezone, dayStart = '06:00', dayEnd = '21:00', minDuration = 30) {
        const freeSlots = [];
        const tz = userTimezone;
        const dayStartTime = DateTime.fromFormat(dayStart, 'HH:mm').setZone(tz);
        const dayEndTime = DateTime.fromFormat(dayEnd, 'HH:mm').setZone(tz);

        const eventsByDay = {};

        for (const event of events) {
            const eventDate = DateTime.fromISO(event.start.dateTime).setZone(tz).toISODate();
            if (!eventsByDay[eventDate]) {
                eventsByDay[eventDate] = [];
            }
            eventsByDay[eventDate].push(event);
        }

        for (const day in eventsByDay) {
            eventsByDay[day].sort((a, b) => DateTime.fromISO(a.start.dateTime).toMillis() - DateTime.fromISO(b.start.dateTime).toMillis());
        }

        const today = DateTime.local().setZone(tz).toISODate();
        const startOfWeek = DateTime.fromISO(today).startOf('week');

        for (let i = 0; i < 7; i++) {
            const currentDay = startOfWeek.plus({ days: i }).toISODate();
            const dayStartDt = DateTime.fromISO(currentDay).set({ hour: dayStartTime.hour, minute: dayStartTime.minute }).setZone(tz);
            const dayEndDt = DateTime.fromISO(currentDay).set({ hour: dayEndTime.hour, minute: dayEndTime.minute }).setZone(tz);

            if (!eventsByDay[currentDay]) {
                if (dayEndDt.diff(dayStartDt, 'minutes').minutes >= minDuration) {
                    freeSlots.push([dayStartDt, dayEndDt]);
                }
            } else {
                const dailyEvents = eventsByDay[currentDay];

                if (DateTime.fromISO(dailyEvents[0].start.dateTime).diff(dayStartDt, 'minutes').minutes >= minDuration) {
                    freeSlots.push([dayStartDt, DateTime.fromISO(dailyEvents[0].start.dateTime)]);
                }

                for (let j = 0; j < dailyEvents.length - 1; j++) {
                    const endCurrent = DateTime.fromISO(dailyEvents[j].end.dateTime);
                    const startNext = DateTime.fromISO(dailyEvents[j + 1].start.dateTime);
                    if (startNext.diff(endCurrent, 'minutes').minutes >= minDuration) {
                        freeSlots.push([endCurrent, startNext]);
                    }
                }

                if (dayEndDt.diff(DateTime.fromISO(dailyEvents[dailyEvents.length - 1].end.dateTime), 'minutes').minutes >= minDuration) {
                    freeSlots.push([DateTime.fromISO(dailyEvents[dailyEvents.length - 1].end.dateTime), dayEndDt]);
                }
            }
        }

        // console.log('Free Slots:', freeSlots); // Log the free slots
        return freeSlots;
    }

    getCurrentWeekRange(userTimezone) {
        const tz = userTimezone;
        const today = DateTime.local().setZone(tz);
        const startOfWeek = today.startOf('week');
        const endOfWeek = startOfWeek.plus({ days: 7 });
        return [startOfWeek, endOfWeek];
    }
}

module.exports = ScheduleUtils;
