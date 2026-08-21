import { create } from 'zustand';

// 1. LEER ALMACENAMIENTO DIRECTAMENTE
const storedToken = localStorage.getItem('token');
const storedUser = localStorage.getItem('user');

// 2. PARSEAR USUARIO DE FORMA SEGURA
let parsedUser = null;
try {
  if (storedUser) {
    parsedUser = JSON.parse(storedUser);
  }
} catch (error) {
  console.error("Error al leer el usuario del localStorage", error);
}

// 3. CREAR EL STORE
export const useAuthStore = create((set, get) => ({
  // Guardamos los datos directamente si existen en el navegador
  token: storedToken || null,
  user: parsedUser || null,

  // ACCIÓN PARA INICIAR SESIÓN
  login: (token, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    set({ token, user });
  },

  // ACCIÓN PARA CERRAR SESIÓN
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ token: null, user: null });
  },

  // ACCIÓN PARA ACTUALIZAR DATOS DEL USUARIO EN SESIÓN
  updateUser: (updatedUserData) => {
    const currentUser = get().user;
    const newUser = { ...currentUser, ...updatedUserData };
    localStorage.setItem('user', JSON.stringify(newUser));
    set({ user: newUser });
  },
}));