module.exports = {
    clientSecretsFile: 'config/client_secret.json',
    port: process.env.PORT || 3000,
    pythonServiceUrl: process.env.PYTHON_SERVICE_URL || 'http://localhost:5001',
    scopes: [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ],
    redirectUri: "http://localhost:3000/user/callback",
    sessionSecret: process.env.SESSION_SECRET || 'YOUR_SECRET_KEY'
};
