 // Configuração do Canvas de Assinatura
    const canvas = document.getElementById('signature-canvas');
    const ctx = canvas.getContext('2d');
    let desenhando = false;
    
    // Ajusta o tamanho real do canvas
    function setupCanvas() {
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        
        // Configurações iniciais do contexto
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = '#1f2937';
        ctx.fillStyle = '#f9fafb';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    
    // Função para desenhar
    function desenhar(e) {
        if (!desenhando) return;
        
        e.preventDefault();
        
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        let clientX, clientY;
        
        if (e.touches) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        const x = (clientX - rect.left) * scaleX;
        const y = (clientY - rect.top) * scaleY;
        
        ctx.lineTo(x, y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x, y);
    }
    
    function iniciarDesenho(e) {
        desenhando = true;
        desenhar(e);
        ctx.beginPath();
    }
    
    function pararDesenho() {
        desenhando = false;
        ctx.beginPath();
    }
    
    // Eventos do mouse
    canvas.addEventListener('mousedown', iniciarDesenho);
    canvas.addEventListener('mouseup', pararDesenho);
    canvas.addEventListener('mousemove', desenhar);
    
    // Eventos touch para mobile
    canvas.addEventListener('touchstart', iniciarDesenho);
    canvas.addEventListener('touchend', pararDesenho);
    canvas.addEventListener('touchmove', desenhar);
    
    // Limpar assinatura
    document.getElementById('btnResetarCanvas').addEventListener('click', function() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#f9fafb';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        document.getElementById('assinatura-input').value = '';
    });
    
    // Salvar assinatura em Base64
    function salvarAssinatura(event) {
        const input = document.getElementById('assinatura-input');
        
        // Verifica se o canvas está vazio
        const canvasData = canvas.toDataURL('image/png');
        const blankCanvas = document.createElement('canvas');
        blankCanvas.width = canvas.width;
        blankCanvas.height = canvas.height;
        const blankCtx = blankCanvas.getContext('2d');
        blankCtx.fillStyle = '#f9fafb';
        blankCtx.fillRect(0, 0, blankCanvas.width, blankCanvas.height);
        
        if(canvasData === blankCanvas.toDataURL('image/png')) {
            event.preventDefault();
            alert('Por favor, assine no campo acima antes de finalizar.');
            input.value = "";
            return false;
        } else {
            input.value = canvasData;
        }
    }
    
    // Converter foto para Base64
    document.getElementById('foto-input').addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                alert('A imagem não pode ter mais que 5MB.');
                this.value = '';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('foto_base64_input').value = e.target.result;
            };
            reader.onerror = function() {
                alert('Erro ao ler o arquivo. Tente novamente.');
            };
            reader.readAsDataURL(file);
        } else {
            document.getElementById('foto_base64_input').value = '';
        }
    });
    
    // Inicializar canvas quando a página carregar
    window.addEventListener('load', function() {
        setupCanvas();
        // Reajustar quando a janela for redimensionada
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                const oldData = canvas.toDataURL();
                setupCanvas();
                // Restaurar assinatura se existir
                if (oldData && oldData !== canvas.toDataURL()) {
                    const img = new Image();
                    img.onload = function() {
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    };
                    img.src = oldData;
                }
            }, 250);
        });
    });