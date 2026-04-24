function carregarDetalhes(element) {
    // Impede propagação para não abrir o modal duas vezes
    event.stopPropagation();
    
    // Pega os dados do card
    const card = element.closest('.card');
    const dadosStr = card.querySelector('[data-viagem]').getAttribute('data-viagem');
    const dados = JSON.parse(dadosStr);
    
    // Preenche o modal com os detalhes
    const modalBody = document.getElementById('detalhesModalBody');
    
    modalBody.innerHTML = `
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-6">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-person-badge"></i> Motorista
                        </div>
                        <div class="detalhe-valor">
                            <strong>${dados.motorista}</strong>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-hash"></i> ID da Viagem
                        </div>
                        <div class="detalhe-valor">
                            <span class="badge bg-secondary">#${dados.id}</span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-12">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-truck"></i> Veículo
                        </div>
                        <div class="detalhe-valor">
                            <strong>${dados.veiculo}</strong> - Placa: <span class="text-uppercase">${dados.placa}</span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-geo-alt"></i> Destino
                        </div>
                        <div class="detalhe-valor">
                            <i class="bi bi-pin-map-fill text-danger"></i> ${dados.destino}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-people"></i> Passageiros
                        </div>
                        <div class="detalhe-valor">
                            ${dados.passageiros || 'Não informado'}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-calendar-check"></i> Data/Hora Partida
                        </div>
                        <div class="detalhe-valor">
                            <i class="bi bi-clock-fill text-success"></i> ${dados.dataPartida}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-calendar-x"></i> Data/Hora Chegada
                        </div>
                        <div class="detalhe-valor">
                            <i class="bi bi-clock-fill text-warning"></i> ${dados.dataChegada}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-12">
                    <div class="detalhe-item">
                        <div class="detalhe-label">
                            <i class="bi bi-person-circle"></i> Solicitado por
                        </div>
                        <div class="detalhe-valor">
                            ${dados.usuario}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-3 p-3 bg-light rounded">
                <div class="d-flex align-items-center justify-content-between">
                    <div>
                        <i class="bi bi-info-circle-fill text-primary"></i>
                        <small class="text-muted">Duração da viagem</small>
                        <h6 class="mb-0">Em trânsito</h6>
                    </div>
                    <div class="progress w-50">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" 
                             style="width: 100%"></div>
                    </div>
                    <i class="bi bi-check-circle-fill text-success fs-4"></i>
                </div>
            </div>
        </div>
    `;
}

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