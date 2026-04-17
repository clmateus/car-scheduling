let veiculoAtivoId = null;
let abaAtiva = 'identificacao';

function abrirModalCarro(veiculoId) {
    veiculoAtivoId = veiculoId;
    abaAtiva = 'identificacao';

    // Marca aba Identificação como ativa
    document.querySelectorAll('#abas-veiculo .nav-link')
        .forEach(btn => btn.classList.remove('active'));

    const btnIdentificacao = document.querySelector('#abas-veiculo [data-aba="identificacao"]');
    if (btnIdentificacao) btnIdentificacao.classList.add('active');

    carregarAba('identificacao', veiculoId);
}

function trocarAba(btn) {
    if (!veiculoAtivoId) return;

    document.querySelectorAll('#abas-veiculo .nav-link')
        .forEach(b => b.classList.remove('active'));

    btn.classList.add('active');

    abaAtiva = btn.dataset.aba;
    carregarAba(abaAtiva, veiculoAtivoId);
}

function carregarAba(aba, veiculoId) {
    htmx.ajax('GET', `/veiculos/tab/${aba}/${veiculoId}/`, {
        target: '#tab-body',
        swap: 'innerHTML'
    });
}

// Ao salvar a documentação com sucesso, recarrega a aba Identificação automaticamente
document.body.addEventListener('refreshIdentificacao', function () {
    if (!veiculoAtivoId) return;

    document.querySelectorAll('#abas-veiculo .nav-link')
        .forEach(b => b.classList.remove('active'));

    const btnIdentificacao = document.querySelector('#abas-veiculo [data-aba="identificacao"]');
    if (btnIdentificacao) btnIdentificacao.classList.add('active');

    carregarAba('identificacao', veiculoAtivoId);
});

document.body.addEventListener('atualizarComentarios', function () {
    // força clicar na aba comentários
});