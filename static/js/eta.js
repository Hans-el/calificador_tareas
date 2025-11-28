function iniciarProgreso() {
    const barra = document.getElementById("barra_progreso");
    const eta = document.getElementById("eta");

    const evento = new EventSource("/progreso");

    evento.onmessage = function(e) {
        const data = JSON.parse(e.data);

        barra.style.width = data.progreso + "%";
        barra.innerText = data.progreso + "%";

        eta.innerText = data.eta;

        if (data.progreso >= 100) {
            evento.close();
        }
    }
}
