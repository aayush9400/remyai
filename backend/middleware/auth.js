function ensureAuthenticated(req, res, next) {
    if (req.session.user) {
        return next();
    }
    res.redirect('/user/login');
}

module.exports = ensureAuthenticated;
