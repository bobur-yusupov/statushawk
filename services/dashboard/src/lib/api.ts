import axios from "axios";

export const api = axios.create({
    // baseURL: 'http://localhost:8000/api/v1',
    baseURL: 'http://api.statushawk.local/api/v1',
    headers: {
        'Content-Type': 'application/json',
    }
});

api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn("Session expired or invalid token. Logging out...");

            localStorage.removeItem("token");
            window.dispatchEvent(new Event("storage"));

            if (window.location.pathname !== "/login") {
                window.location.href = "/login";
            }
        }
        return Promise.reject(error);
    }
)