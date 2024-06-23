const { google } = require('googleapis');
const config = require('../config/config');
const fs = require('fs');

const credentials = JSON.parse(fs.readFileSync(config.clientSecretsFile));

const oauth2Client = new google.auth.OAuth2(
    credentials.web.client_id,
    credentials.web.client_secret,
    config.redirectUri
);

exports.login = (req, res) => {
    const authorizationUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: config.scopes
    });
    res.redirect(authorizationUrl);
};

exports.callback = async (req, res) => {
    const { code } = req.query;
    try {
        const { tokens } = await oauth2Client.getToken(code);
        req.session.tokens = tokens;
        oauth2Client.setCredentials(tokens);

        const userInfoService = google.oauth2('v2').userinfo;
        const userInfo = await userInfoService.get({ auth: oauth2Client }).then(response => response.data);
        req.session.user = userInfo;

        console.log('User Info:', userInfo);

        res.redirect('/chatbot'); // Redirect to chatbot after login
    } catch (err) {
        console.error('Error getting token:', err);
        res.status(500).send('Error getting token');
    }
};

exports.logout = (req, res) => {
    req.session.destroy(err => {
        if (err) {
            console.error('Error logging out:', err);
            return res.status(500).send('Error logging out');
        }
        res.redirect('/');
    });
};
