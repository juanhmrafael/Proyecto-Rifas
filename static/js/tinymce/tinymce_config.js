// Función para inicializar TinyMCE dependiendo del modo oscuro o claro
function initTinyMCE(darkMode) {
    tinymce.init({
        height: 360,
        width: "100%",
        browser_spellcheck: true,
        cleanup_on_startup: true,
        custom_undo_redo_levels: 20,
        selector: "textarea",
        theme: "silver",
        paste_as_text: true,
        highlight_on_focus: true,
        skin: darkMode ? "oxide-dark" : "oxide",  // Usa el tema claro u oscuro
        content_css: darkMode ? "dark" : "default",  // Cambia el CSS según el modo
        plugins: `
            link lists code help wordcount insertdatetime searchreplace emoticons preview
        `,
        toolbar1: `
            undo redo | formatselect | bold italic forecolor backcolor |
            alignleft aligncenter alignright alignjustify lineheight | bullist numlist outdent indent | emoticons insertdatetime preview |
            removeformat
        `,
        menubar: "edit insert format tools",
        statusbar: false,
        remove_script_host: true,
        convert_urls: false,
        branding: false,
        promotion: false,
        language: "es",
        images_upload_url: null,  // Deshabilita la subida de imágenes
        content_style: darkMode
            ? "body { background-color: rgb(55 65 81); }"  // Fondo y texto personalizados en oscuro
            : "body {  }",  // Fondo y texto en modo claro
    });
}

// Detectar el esquema de color del sistema operativo
const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

// Inicializar TinyMCE con el tema adecuado
initTinyMCE(darkModeMediaQuery.matches);

// Escuchar cambios en el esquema de color
darkModeMediaQuery.addEventListener('change', (e) => {
    const darkModeOn = e.matches;
    tinymce.remove();  // Elimina la instancia actual de TinyMCE
    initTinyMCE(darkModeOn);  // Reinicia TinyMCE con el tema actualizado
});