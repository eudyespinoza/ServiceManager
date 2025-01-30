// ------------------------
// FUNCIONES GENERALES
// ------------------------

// Mostrar notificación con Toast
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0 show`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    toastContainer.appendChild(toast);

    setTimeout(() => toast.remove(), 3000); // Elimina el toast tras 3 segundos
}

// Abrir modal de confirmación (reutilizado)
function openModal(title, body, confirmCallback) {
    const modalElement = document.getElementById('confirmationModal');
    const modal = new bootstrap.Modal(modalElement);
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    const confirmButton = document.getElementById('modalConfirmBtn');

    // Configurar el modal
    modalTitle.textContent = title;
    modalBody.innerHTML = body;
    confirmButton.style.display = ''; // Mostrar el botón de confirmación
    confirmButton.onclick = () => {
        confirmCallback();
        modal.hide();
    };

    modal.show();
}

// Función para inicializar los tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Inicializar Tooltips de Bootstrap
document.addEventListener('DOMContentLoaded', initializeTooltips);

// ------------------------
// FUNCIONES DE TABLAS
// ------------------------

// Búsqueda dinámica en tablas
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const trs = table.getElementsByTagName('tr');

    for (let i = 1; i < trs.length; i++) { // Ignora el encabezado (i=1)
        let visible = false;
        const tds = trs[i].getElementsByTagName('td');
        for (let j = 0; j < tds.length; j++) {
            if (tds[j] && tds[j].innerText.toLowerCase().indexOf(filter) > -1) {
                visible = true;
            }
        }
        trs[i].style.display = visible ? '' : 'none'; // Oculta o muestra la fila
    }
}

// ------------------------
// FUNCIONES DE FORMULARIOS
// ------------------------

// Borrar cliente
function borrarCliente(clienteId) {
    openModal(
        'Confirmar eliminación',
        '¿Está seguro de que desea eliminar este cliente?',
        () => {
            fetch(`/clientes/borrar/${clienteId}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast('Cliente eliminado exitosamente', 'success');
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        showToast(`Error: ${data.message}`, 'danger');
                    }
                })
                .catch(error => showToast(`Hubo un problema: ${error.message}`, 'danger'));
        }
    );
}

// Manejo general de formularios con fetch
function submitForm(event, form, onSuccessMessage = 'Acción completada con éxito') {
    event.preventDefault();

    const formData = new FormData(form);
    const action = form.action;

    fetch(action, {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              showToast(onSuccessMessage, 'success');
              setTimeout(() => location.reload(), 2000); // Recarga tras 2 segundos
          } else {
              showToast(`Error: ${data.message}`, 'danger');
          }
      }).catch(error => {
          showToast(`Hubo un problema con la solicitud: ${error.message}`, 'danger');
      });
}

// ------------------------
// INICIALIZACIÓN DE FUNCIONALIDADES
// ------------------------

// Flatpickr para campos de fecha y hora
function initFlatpickr(selector, config = {}) {
    flatpickr(selector, {
        enableTime: true,
        dateFormat: "d-m-Y H:i",
        time_24hr: true,
        locale: "es", // Configuración en español
        ...config // Permite pasar configuraciones adicionales
    });
}

// Inicializar búsqueda en tablas
function initSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.addEventListener('keyup', () => searchTable(inputId, tableId));
    }
}

// ------------------------
// EJEMPLOS DE INICIALIZACIÓN
// ------------------------

// Ejemplo de inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar búsqueda en tabla de clientes
    initSearch('searchInput', 'clientesTable');

    // Inicializar Flatpickr en el campo de fecha y hora
    initFlatpickr('#fecha_hora');
});

// Cargar detalle del cliente
function loadClienteDetalle(clienteId) {
    const modalElement = document.getElementById('confirmationModal');
    const modal = new bootstrap.Modal(modalElement);
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    const confirmButton = document.getElementById('modalConfirmBtn');

    // Mostrar el overlay de carga
    showLoadingOverlay();

    // Configuración inicial del modal
    modalTitle.textContent = 'Detalle del Cliente';
    modalBody.innerHTML = '<p class="text-center">Consultando detalles...</p>';
    confirmButton.style.display = 'none';

    // Realizar solicitud AJAX
    fetch(`/clientes/detalle/${clienteId}`)
        .then(response => response.text())
        .then(data => {
            modalBody.innerHTML = data;
            modal.show();
            initializeTooltips();
        })
        .catch(error => {
            modalBody.innerHTML = `<p class="text-center text-danger">Error al cargar detalles: ${error.message}</p>`;
            modal.show();
        })
        .finally(() => {
            // Ocultar el overlay de carga
            hideLoadingOverlay();
        });
}

// Llama a initializeTooltips al cargar dinámicamente otros detalles
function loadDireccionDetalle(direccionId) {
    const modalElement = document.getElementById('confirmationModal');
    const modal = new bootstrap.Modal(modalElement);
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.textContent = 'Detalle de la Dirección';
    modalBody.innerHTML = '<p class="text-center">Consultando detalles...</p>';

    fetch(`/direcciones/detalle/${direccionId}`)
        .then(response => response.text())
        .then(data => {
            modalBody.innerHTML = data;
            modal.show();

            // Reinicializar tooltips
            initializeTooltips();
        })
        .catch(error => {
            modalBody.innerHTML = `<p class="text-center text-danger">Error al cargar detalles: ${error.message}</p>`;
            modal.show();
        });
}

function loadServicioDetalle(servicioId) {
    const modalElement = document.getElementById('confirmationModal');
    const modal = new bootstrap.Modal(modalElement);
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.textContent = 'Detalle del Servicio';
    modalBody.innerHTML = '<p class="text-center">Consultando detalles...</p>';

    fetch(`/servicios/detalle/${servicioId}`)
        .then(response => response.text())
        .then(data => {
            modalBody.innerHTML = data;
            modal.show();

            // Reinicializar tooltips
            initializeTooltips();
        })
        .catch(error => {
            modalBody.innerHTML = `<p class="text-center text-danger">Error al cargar detalles: ${error.message}</p>`;
            modal.show();
        });
}

// Mostrar overlay de carga
function showLoadingOverlay(message = "Cargando...") {
    const overlay = document.getElementById('loadingOverlay');
    const overlayMessage = overlay.querySelector('.loading-content p');
    overlayMessage.textContent = message;
    overlay.classList.remove('d-none');
}

// Ocultar overlay de carga
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('d-none');
}

// Abrir modal dinámico
function openDynamicModal(url, title, isDetail = false) {
    // Determinar el modal a usar
    const modalId = isDetail ? 'dynamicModalDetail' : 'dynamicModal';
    const modalElement = document.getElementById(modalId);
    const modalTitle = modalElement.querySelector('.modal-title');
    const modalContent = modalElement.querySelector('.modal-body');

    // Ajustar z-index del backdrop
    const modalBackdrop = document.querySelector('.modal-backdrop');
    if (modalBackdrop) {
        modalBackdrop.style.zIndex = '1050'; // Fondo detrás de los modales
    }

    // Configurar contenido inicial
    modalTitle.textContent = title;
    modalContent.innerHTML = '<p class="text-center">Cargando contenido...</p>';

    // Mostrar el overlay de carga
    showLoadingOverlay();

    // Mostrar el modal
    const modal = new bootstrap.Modal(modalElement);

    // Cargar contenido dinámico
    fetch(url)
        .then(response => response.text())
        .then(data => {
            modalContent.innerHTML = data;
            initializeTooltips(); // Reinicializar tooltips
        })
        .catch(error => {
            modalContent.innerHTML = `<p class="text-danger text-center">Error al cargar contenido: ${error.message}</p>`;
        })
        .finally(() => {
            // Ocultar el overlay de carga
            hideLoadingOverlay();
            modal.show();
        });
}

function loadDynamicModal(url, title) {
    const modalElement = document.getElementById('dynamicModal');
    const modalTitle = document.getElementById('dynamicModalTitle');
    const modalContent = document.getElementById('dynamicModalContent');

    modalTitle.textContent = title;
    modalContent.innerHTML = '<p class="text-center">Cargando contenido...</p>';

    // Mostrar el modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // Cargar contenido dinámico
    fetch(url)
        .then(response => response.text())
        .then(data => {
            modalContent.innerHTML = data;
            initializeTooltips();  // Reiniciar tooltips si hay elementos con ellos
        })
        .catch(error => {
            modalContent.innerHTML = `<p class="text-danger text-center">Error al cargar contenido: ${error.message}</p>`;
        });
}


// Enviar formularios dinámicos
function submitDynamicForm(event, form) {
    event.preventDefault();

    const formData = new FormData(form);
    const action = form.action;

    fetch(action, {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const modalElement = document.getElementById('dynamicModal');
                bootstrap.Modal.getInstance(modalElement).hide();  // Cerrar modal
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 1000);  // Recargar página principal
            } else {
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            showToast(`Error al procesar el formulario: ${error.message}`, 'danger');
        });
}