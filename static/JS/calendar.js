document.addEventListener('DOMContentLoaded', function() {
    let telaMobile = window.innerWidth < 768;
    
    // Função para obter CSRF token
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }

const titulo = document.getElementById('tituloPrincipal');
if (titulo) {
    titulo.innerHTML = telaMobile ? 'Mobile' : 'Desktop';
}

    var calendarEl = document.getElementById('calendar');
    if (calendarEl) {
    var calendar = new FullCalendar.Calendar(calendarEl, {
      themeSystem: 'standard',
      locale: 'pt-br',
      initialView: telaMobile ? 'timeGridDay' : 'dayGridMonth',
      height: 'auto',
      timeZone: 'local',
      nowIndicator: true,
      selectable: true,
      navLinks: false,
      eventTextColor: '#fff',
      eventColor: '#3a86ad',
      eventDisplay: 'block',
      allDaySlot: false,
      titleFormat: telaMobile ? { month: 'short', day: '2-digit' } : { month: 'long', year:'numeric' },
      headerToolbar: {
        left: 'title',
        center: '',
        right: 'prev,next'
    },
      buttonText: {
        day: 'Hoje',
        month: 'Mês',
        today: 'Hoje',
      },
      eventTimeFormat: {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      },
      events: '/api/eventos', // URL absoluta
      dateClick: function(info){
        let dataPartida = info.dateStr;
        let dataChegada = info.dateStr;

        if (info.dateStr.length === 10) {
          dataPartida += 'T08:00';
          dataChegada += 'T18:00';
        } else {
          dataPartida = info.dateStr.substring(0, 16);
          
          let dataFim = new Date(info.date);
          dataFim.setHours(dataFim.getHours() + 2);
          
          let year = dataFim.getFullYear();
          let month = String(dataFim.getMonth() + 1).padStart(2, '0');
          let day = String(dataFim.getDate()).padStart(2, '0');
          let hours = String(dataFim.getHours()).padStart(2, '0');
          let minutes = String(dataFim.getMinutes()).padStart(2, '0');
          
          dataChegada = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
        
        document.getElementById('dataHoraPartida').value = dataPartida;
        document.getElementById('dataHoraChegada').value = dataChegada;
        document.getElementById('modal_insercao').showModal();
      },
      eventClick: function(info){
        if (info.event.extendedProps.is_manutencao) {
          let url = '/transporte/manutencoes/';
          if (info.event.extendedProps.veiculo_id) {
            url += '?veiculo_id=' + info.event.extendedProps.veiculo_id;
          }
          window.location.href = url;
        } else {
          window.location.href = '/transporte/viagens/?q=' + info.event.id;
        }
      },
      eventDrop: function(info) {
        let dados = {
          id: info.event.id,
          start: info.event.start.toISOString(),
          end: info.event.end ? info.event.end.toISOString() : null
        }

        if (!info.event.extendedProps.pode_editar) {
          alert('Você não tem permissão para alterar este agendamento.');
          info.revert();
          return;
        }

        fetch("/mudar_dia_agendamento/", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
          },
          body: JSON.stringify(dados)
        }).then(function(response) {
          if (!response.ok) {
              alert('Erro ao mudar o dia do evento!')
              info.revert()
            }
          })
          .catch(error => {
            console.error('Erro:', error)
            info.revert()
          })
      },
      windowResize: function(info) {
        let telaMobile = window.innerWidth < 768;
        if (telaMobile) {
          calendar.changeView('timeGridDay');
          calendar.setOption('titleFormat', { month: 'short', day: '2-digit' });
          const titulo = document.getElementById('tituloPrincipal');
          if (titulo) titulo.innerHTML = 'Mobile';
        } else {
          calendar.changeView('dayGridMonth');
          calendar.setOption('titleFormat', { month: 'long' });
          const titulo = document.getElementById('tituloPrincipal');
          if (titulo) titulo.innerHTML = 'Desktop';
        }
      }
    });
    calendar.render();
    }

    document.body.addEventListener('atualizarCalendario', function() {
      if (typeof calendar !== 'undefined') calendar.refetchEvents();
      
      ['modal_insercao', 'modal_edicao', 'modal_evento'].forEach(function(modalId) {
        var modalEl = document.getElementById(modalId);
        if (modalEl && modalEl.hasAttribute('open')) {
            modalEl.close();
        }
      });
    })

    setInterval(function() {
      if (typeof calendar !== 'undefined') calendar.refetchEvents();
    }, 15000);

  document.body.addEventListener('htmx:afterSwap', function(event) {
      if (event.detail.target.id === 'resultadoModal') {
          const conteudo = event.detail.target.innerHTML.toLowerCase();
          if (conteudo.includes('sucesso') || conteudo.includes('agendado')) {
              const toastEl = document.getElementById('liveToast');
              toastEl.classList.remove('hidden');
              setTimeout(() => toastEl.classList.add('hidden'), 4000);
              document.getElementById('modal_insercao').close();
          }
      }
  });

  document.body.addEventListener('htmx:afterRequest', function(event) {
    const form = event.detail.elt;
    if (form.getAttribute('hx-post') && form.getAttribute('hx-post').includes('remover')) {
      if (event.detail.successful) {
        const toastEl = document.getElementById('liveToastCancelado');
        toastEl.classList.remove('hidden');
        setTimeout(() => toastEl.classList.add('hidden'), 4000);
      }
    }
  });
})
  
let veiculoAtual = null;

function abrirModalCarro(id) {
    veiculoAtual = id;
    htmx.ajax('GET', `/transporte/veiculos/tab/identificacao/${id}/`, '#tab-body');
}

function trocarAba(botao) {
    const aba = botao.getAttribute("data-aba");

    if (veiculoAtual) {
        htmx.ajax('GET', `/transporte/veiculos/tab/${aba}/${veiculoAtual}/`, '#tab-body');
    }
}