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

    var modalEvento = new bootstrap.Modal(document.getElementById('modal_evento'));
    var modalInsercao = new bootstrap.Modal(document.getElementById('modal_insercao'));
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
      themeSystem: 'bootstrap5',
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
        let dataFormatada = info.dateStr;

        if (dataFormatada.length === 10) {
          dataFormatada += 'T08:00';
        } else {
          dataFormatada = dataFormatada.substring(0, 16);
        }
        document.getElementById('dataHoraPartida').value = dataFormatada;
        document.getElementById('dataHoraChegada').value = '';
        modalInsercao.show()
      },
      eventClick: function(info){
        window.location.href = '/transporte/viagens/?q=' + info.event.id;
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
          document.getElementById('tituloPrincipal').innerHTML = 'Mobile'
        } else {
          calendar.changeView('dayGridMonth');
          calendar.setOption('titleFormat', { month: 'long' });
          document.getElementById('tituloPrincipal').innerHTML = 'Desktop'
        }
      }
    });
    calendar.render();

    document.body.addEventListener('atualizarCalendario', function() {
      calendar.refetchEvents();
      
      ['modal_insercao', 'modal_edicao', 'modal_evento'].forEach(function(modalId) {
        var modalEl = document.getElementById(modalId);
        if (modalEl) {
          var modalInstance = bootstrap.Modal.getInstance(modalEl);
          if (modalInstance) {
            modalInstance.hide();
          }
        }
      });
    })

    setInterval(function() {
      calendar.refetchEvents();
    }, 15000);

  document.body.addEventListener('htmx:afterSwap', function(event) {
      if (event.detail.target.id === 'resultadoModal') {
          const conteudo = event.detail.target.innerHTML.toLowerCase();
          if (conteudo.includes('sucesso') || conteudo.includes('agendado')) {
              const toastEl = document.getElementById('liveToast');
              const toast = bootstrap.Toast.getOrCreateInstance(toastEl);
              toast.show();
          }
      }
  });

  document.body.addEventListener('htmx:afterRequest', function(event) {
    const form = event.detail.elt;
    if (form.getAttribute('hx-post') && form.getAttribute('hx-post').includes('remover')) {
      if (event.detail.successful) {
        const toastEl = document.getElementById('liveToastCancelado');
        const toast = bootstrap.Toast.getOrCreateInstance(toastEl);
        toast.show();
      }
    }
  });
})
  
function trocarAba(botao) {
    const aba = botao.getAttribute("data-aba");

    htmx.ajax('GET', `/transporte//veiculos/tab/${aba}/${veiculoAtual}/`, '#tab-body');
}
htmx.ajax('GET', `/transporte//veiculos/tab/identificacao/${id}/`, '#tab-body');