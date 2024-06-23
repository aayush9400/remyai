document.addEventListener("DOMContentLoaded", function () {
    const toggleDarkModeButton = document.getElementById('toggle-dark-mode');
    const body = document.body;

    toggleDarkModeButton.addEventListener('click', function () {
        body.classList.toggle('dark-mode');
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });

    // Load the saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
    }
});
