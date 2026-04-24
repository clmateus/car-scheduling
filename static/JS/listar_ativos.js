document.addEventListener("DOMContentLoaded", function() {
        const searchInput = document.getElementById("searchInput");
        const columns = document.querySelectorAll(".ativo-col");
        const filterBtns = document.querySelectorAll(".filter-btn");
        let activeCategory = "";

        function applyFilters() {
            const searchValue = searchInput.value.toLowerCase();
            
            columns.forEach(col => {
                const textContent = col.innerText.toLowerCase();
                const matchesSearch = textContent.includes(searchValue);
                const matchesCategory = activeCategory === "" || textContent.includes(activeCategory);
                
                col.style.display = (matchesSearch && matchesCategory) ? "" : "none";
            });
        }

        searchInput.addEventListener("keyup", applyFilters);

        filterBtns.forEach(btn => {
            btn.addEventListener("click", function() {
                filterBtns.forEach(b => b.classList.remove("active"));
                this.classList.add("active");
                
                activeCategory = this.getAttribute("data-filter");
                applyFilters();
            });
        });
    });