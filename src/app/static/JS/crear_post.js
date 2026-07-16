document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form[enctype="multipart/form-data"]');
    const inputArchivo = document.getElementById('adjuntos');
    const listaArchivos = document.getElementById('lista-adjuntos');
    const estadoVacio = document.getElementById('preview-empty');

    if (!form || !inputArchivo || !listaArchivos || !estadoVacio) {
        return;
    }

    const archivosSeleccionados = [];

    const obtenerClave = (archivo) => `${archivo.name}-${archivo.size}-${archivo.lastModified}`;

    const formatearTamano = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const renderizarVistaPrevia = () => {
        listaArchivos.innerHTML = '';

        if (archivosSeleccionados.length === 0) {
            estadoVacio.classList.remove('hidden');
            return;
        }

        estadoVacio.classList.add('hidden');

        archivosSeleccionados.forEach((archivo, index) => {
            const item = document.createElement('li');
            item.className = 'flex items-center justify-between gap-3 rounded-xl border border-slate-300 bg-white px-4 py-3';

            const extension = archivo.name.split('.').pop()?.toUpperCase() || 'FILE';
            const tipo = archivo.type || `${extension} file`;

            item.innerHTML = `
                <div class="min-w-0">
                    <p class="truncate font-semibold text-azul-marino">${archivo.name}</p>
                    <p class="text-xs text-gris-oscuro">${formatearTamano(archivo.size)} · ${tipo}</p>
                </div>
                <button type="button" class="eliminar-adjunto rounded-lg bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700" data-index="${index}">
                    Eliminar
                </button>
            `;

            listaArchivos.appendChild(item);
        });
    };

    const sincronizarInput = () => {
        const dataTransfer = new DataTransfer();
        archivosSeleccionados.forEach((archivo) => dataTransfer.items.add(archivo));
        inputArchivo.files = dataTransfer.files;
    };

    const agregarArchivos = (nuevosArchivos) => {
        Array.from(nuevosArchivos || []).forEach((archivo) => {
            const yaExiste = archivosSeleccionados.some((actual) => obtenerClave(actual) === obtenerClave(archivo));
            if (!yaExiste) {
                archivosSeleccionados.push(archivo);
            }
        });

        sincronizarInput();
        renderizarVistaPrevia();
    };

    inputArchivo.addEventListener('change', (event) => {
        agregarArchivos(event.target.files);
        event.target.value = '';
    });

    listaArchivos.addEventListener('click', (event) => {
        const boton = event.target.closest('.eliminar-adjunto');
        if (!boton) return;

        const index = Number(boton.dataset.index);
        if (Number.isNaN(index)) return;

        archivosSeleccionados.splice(index, 1);
        sincronizarInput();
        renderizarVistaPrevia();
    });

    form.addEventListener('submit', () => {
        sincronizarInput();
    });

    renderizarVistaPrevia();
});
