// tailwind.config.js
module.exports = {
  content: [
    "./views/**/*.ejs",
    "./public/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FF5733', // Orange
        secondary: '#2c3e50', // Dark Gray for light mode
        light: '#ffffff', // Light background
        dark: '#121212', // Dark background
        accent: '#FF5733' // Orange for buttons and highlights
      },
    },
  },
  plugins: [],
}
