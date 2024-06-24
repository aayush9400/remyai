const express = require('express');
const session = require('express-session');
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const homeRoutes = require('./routes/home');
const userRoutes = require('./routes/user');
const chatbotRoutes = require('./routes/chatbot');
const calendarRoutes = require('./routes/calendar');

const app = express();
const PORT = 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(expressLayouts);
app.set('layout', 'layout'); // Set the default layout

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

app.use(session({
    secret: 'YOUR_SECRET_KEY',
    resave: false,
    saveUninitialized: true
}));

app.use((req, res, next) => {
    res.locals.user = req.session.user;
    next();
});

app.use('/', homeRoutes);
app.use('/user', userRoutes);
app.use('/chatbot', chatbotRoutes);
app.use('/calendar', calendarRoutes);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
