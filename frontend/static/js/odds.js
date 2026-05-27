const WS_HOST = window.location.hostname;
const WS_PORT = 8001;
const WS_URL  = `ws://${WS_HOST}:${WS_PORT}/ws/events/${EVENT_ID}/odds/`;

let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;

function connectWebSocket() {
    socket = new WebSocket(WS_URL);

    socket.onopen = function () {
        console.log(`[WS] Conectado al evento ${EVENT_ID}`);
        reconnectAttempts = 0;
    };

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data.type === "odds_snapshot") {
            data.selections.forEach(sel => updateOdds(sel));
        }
        if (data.type === "odds_update") {
            updateOdds(data);
        }
    };

    socket.onclose = function () {
        if (reconnectAttempts < MAX_RECONNECT) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        }
    };

    socket.onerror = function () { socket.close(); };
}

function updateOdds(sel) {
    const els = document.querySelectorAll(
        `[data-outcome="${sel.outcome}"][data-market="${sel.market_id}"]`
    );
    els.forEach(el => {
        const nuevo = parseFloat(sel.odds).toFixed(2);
        if (el.textContent !== nuevo) {
            el.textContent = nuevo;
            el.classList.add("odds-changed");
            setTimeout(() => el.classList.remove("odds-changed"), 1500);
        }
    });
}

// Keepalive ping cada 30s
setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ping" }));
    }
}, 30000);

connectWebSocket();