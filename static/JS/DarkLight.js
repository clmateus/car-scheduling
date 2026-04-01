function toggleTheme() {
    const html = document.documentElement;
    const btn = document.getElementById('theme-toggle');

    if (html.getAttribute('data-theme') === 'dark') {
        // --- SAINDO DO DARK / ENTRANDO NO LIGHT ---
        html.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        
        if (btn) {
            btn.textContent = '🌑 Dark Mode';
            // No site LIGHT, o botão deve ser DARK (contraste)
            btn.classList.remove('btn-light');
            btn.classList.add('btn-secondary');
        }
    } else {
        // --- SAINDO DO LIGHT / ENTRANDO NO DARK ---
        html.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        
        if (btn) {
            btn.textContent = '☀️ Light Mode';
            // No site DARK, o botão deve ser LIGHT (contraste)
            btn.classList.remove('btn-dark');
            btn.classList.add('btn-light');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const btn = document.getElementById('theme-toggle');

    if (saved === 'dark' || (!saved && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (btn) {
            btn.textContent = '☀️ Light Mode';
            // Estado Dark: Botão Light
            btn.classList.remove('btn-dark');
            btn.classList.add('btn-light');
        }
    } else {
        if (btn) {
            btn.textContent = '🌑 Dark Mode';
            // Estado Light: Botão Dark
            btn.classList.remove('btn-light');
            btn.classList.add('btn-dark');
        }
    }
});