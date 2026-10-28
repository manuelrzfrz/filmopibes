import { createContext, useState, useEffect } from 'react';
import { getUsers } from '../api/filmsApi';

//eslint-disable-next-line react-refresh/only-export-components
export const UserContext = createContext();

export function UserProvider({ children }) {
  const [users, setUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [loadingUsers, setLoadingUsers] = useState(true);

  useEffect(() => {
    getUsers()
      .then((data) => {
        setUsers(data);
        if (data.length > 0) {
          const defaultUser = data.find((u) => u.nombre.toLowerCase().includes('manolo')) || data[0];
          setCurrentUser(defaultUser);
        }
      })
      .catch((err) => console.error('Error cargando usuarios:', err))
      .finally(() => setLoadingUsers(false));
  }, []);

  return (
    <UserContext.Provider value={{ users, currentUser, setCurrentUser, loadingUsers }}>
      {children}
    </UserContext.Provider>
  );
}