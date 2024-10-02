/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
    darkMode: 'media',
    content: [
        // Plantillas HTML en la carpeta de la app Tailwind
        '../templates/**/*.html',

        // Plantillas HTML en el directorio de templates global
        '../../templates/**/*.html',

        // Otras plantillas de Django
        '../../**/templates/**/*.html',

        // Excluir node_modules y buscar solo en tus archivos JS
        // '../../**/*.js',
        // '!../../**/node_modules/**/*',

        // Incluir Flowbite y Simple Datatables desde node_modules
        './node_modules/flowbite/**/*.js',
        './node_modules/simple-datatables/**/*.js',
        './js/main.js',
    ],
    theme: {
        screens: {
            'xs': '330px',
            ...defaultTheme.screens,
        },
        extend: {},
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
        require('flowbite/plugin')({
            datatables: true,
        }),
    ],
}

