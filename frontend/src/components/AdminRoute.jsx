import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/auth_store'; 

export default function AdminRoute() 
{
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);

  //SI NO HAY TOKEN LO REDIRECCIONAMOS AL LOGIN
  if (!token) 
  {
    return <Navigate to="/login" replace />;
  }

  //SI SU ROL NO ES 1 (ADMINISTRADOR) LO REDIRECCIONAMOS A INICIO
  if (user?.id_rol !== 1) 
  {
    return <Navigate to="/home" replace />;
  }

  return <Outlet />;
}