class Utils {
    static renderHomepage(events, userInfo) {
        const userEmail = userInfo.given_name || 'Unknown';
        let html = `<h1>Welcome, ${userEmail}!</h1>`;
        html += '<a href="/logout">Logout</a><br><br>';
        html += '<h2>Your Current Calendar</h2>';
        events.forEach(event => {
            const start = event.start.dateTime || event.start.date;
            const end = event.end.dateTime || event.end.date;
            html += `<p>${start} - ${end}: ${event.summary}</p>`;
        });
        html += `
            <form action="/calendar/schedule" method="post">
                <button type="submit">Plan Meals</button>
            </form>
        `;
        return html;
    }

    static renderCalendar(events, userInfo) {
        const userEmail = userInfo.given_name || 'Unknown';
        let html = `<h1>Meal Plan Calendar</h1>`;
        html += `<p>Logged in as: ${userEmail}</p>`;
        html += '<a href="/logout">Logout</a>';
        events.forEach(event => {
            const start = event.start.dateTime || event.start.date;
            const end = event.end.dateTime || event.end.date;
            html += `<p>${start} - ${end}: ${event.summary}</p>`;
        });
        return html;
    }

    static credentialsToDict(credentials) {
        return {
            token: credentials.token,
            refresh_token: credentials.refresh_token,
            token_uri: credentials.token_uri,
            client_id: credentials.client_id,
            client_secret: credentials.client_secret,
            scopes: credentials.scopes
        };
    }

    static credentialsFromDict(credentialsDict) {
        return new google.auth.OAuth2(
            credentialsDict.client_id,
            credentialsDict.client_secret,
            credentialsDict.token_uri
        ).setCredentials({
            access_token: credentialsDict.token,
            refresh_token: credentialsDict.refresh_token
        });
    }
}

module.exports = Utils;
