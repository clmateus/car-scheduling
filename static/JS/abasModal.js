let veiculoAtivoId = null;
let abaAtiva = 'identificacao';

function abrirModalCarro(veiculoId) {
    veiculoAtivoId = veiculoId;
    abaAtiva = 'identificacao';

    document.querySelectorAll('#abas-veiculo .nav-link')
        .forEach(btn => btn.classList.remove('active'));

    document.querySelector('[data-aba="identificacao"]')
        .classList.add('active');

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

// Adicionar feedback visual ao salvar
function salvarAbaAtual() {
    const form = document.querySelector('#tab-body form');
    
    if (form) {
        const saveBtn = document.querySelector('.modal-footer .btn-success');
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Salvando...';
        
        // Reabilitar após o envio
        form.addEventListener('htmx:afterRequest', function() {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
            
        htmx.trigger(form, 'submit');
    })
}
    document.querySelector('form')?.addEventListener('htmx:xhr:progress', function(evt) {
        const progressBar = document.getElementById('upload-progress');
        if (progressBar && evt.detail.lengthComputable) {
            progressBar.style.display = 'block';
            const percent = (evt.detail.loaded / evt.detail.total) * 100;
            progressBar.value = percent;
            
            if (percent >= 100) {
                setTimeout(() => {
                    progressBar.style.display = 'none';
                }, 1000);
            }
        }
    })
}

    document.querySelector('form')?.addEventListener('htmx:xhr:progress', function(evt) {
        const progressBar = document.getElementById('upload-progress');
        if (progressBar && evt.detail.lengthComputable) {
            progressBar.style.display = 'block';
            const percent = (evt.detail.loaded / evt.detail.total) * 100;
            progressBar.value = percent;
            
            if (percent >= 100) {
                setTimeout(() => {
                    progressBar.style.display = 'none';
                }, 1000);
            }
        }
    });