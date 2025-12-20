const colors = require('tailwindcss/colors');

/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                slate: colors.slate,
                indigo: colors.indigo,
                purple: colors.purple,
                pink: colors.pink,
                primary: {
                    DEFAULT: '#e94560',
                    50: '#fef2f4',
                    100: '#fee2e6',
                    200: '#fdcad3',
                    300: '#fba4b4',
                    400: '#f7708b',
                    500: '#e94560',
                    600: '#d62f51',
                    700: '#b42244',
                    800: '#961f40',
                    900: '#801f3c',
                },
                dark: {
                    DEFAULT: '#1a1a2e',
                    50: '#16213e',
                    100: '#0f3460',
                    200: '#0f0f1a',
                },
                accent: {
                    green: '#4ecca3',
                    red: '#ff6b6b',
                    yellow: '#ffd369',
                },
            },
            fontFamily: {
                sans: ['Inter', 'Segoe UI', 'sans-serif'],
            },
        },
    },
    plugins: [],
};
