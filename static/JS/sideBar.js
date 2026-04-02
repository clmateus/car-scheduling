document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');

    menuBtn.addEventListener('click', () => {
        // Toggle: Se a classe existe, remove. Se não existe, adiciona.
        sidebar.classList.toggle('closed');
    });
});