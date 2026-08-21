//const API_URL = import.meta.env.VITE_API_URL;

export const despertarBackend = async () => {
    try {
        await fetch('https://inf412-agro-enlace.onrender.com/');
        console.log("Ping enviado: Backend preparado.");
    } catch (error) {
        console.log("Esperando conexión con el servidor...");
    }
};