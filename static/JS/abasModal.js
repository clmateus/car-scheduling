// Script para abas
let veiculoAtivoId = null;

function abrirModalCarro(veiculoId) {
    veiculoAtivoId = veiculoId;
    carregarAba('identificacao', veiculoId);
}

function trocarAba(elemento) {
    const aba = elemento.dataset.aba;
    if (aba && veiculoAtivoId) {
        // Atualiza visual
        document.querySelectorAll('#abas-veiculo .tab').forEach(tab => {
            tab.classList.remove('tab-active');
        });
        elemento.classList.add('tab-active');
        
        // Carrega conteúdo
        carregarAba(aba, veiculoAtivoId);
    }
}

function carregarAba(aba, veiculoId) {
    const target = document.getElementById('tab-body');
    if (!target) return;
    
    target.innerHTML = '<div class="flex justify-center p-12"><div class="loading loading-spinner loading-lg"></div></div>';
    
    fetch(`/transporte/veiculos/tab/${aba}/${veiculoId}/`)
        .then(response => response.text())
        .then(html => { target.innerHTML = html; })
        .catch(error => {
            target.innerHTML = `<div class="alert alert-error m-4">Erro: ${error}</div>`;
        });
}