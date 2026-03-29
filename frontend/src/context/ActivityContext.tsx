/**
 * ActivityContext — глобальный провайдер WebSocket мониторинга активности.
 *
 * CRITICAL: useActivityMonitor ДОЛЖЕН быть подключён глобально (в Layout),
 * а не только на странице UserManagement. Иначе:
 *   - Пользователь на Dashboard = WebSocket не подключён = "офлайн"
 *   - Активных пользователей = 0 (нет данных)
 *   - heartbeat не отправляется = auto-offline через 5 минут
 *
 * Этот контекст решает проблему: WebSocket подключается ОДИН РАЗ
 * при входе в Layout и работает на ВСЕХ страницах.
 */
import React, { createContext, useContext, ReactNode } from 'react';
import { useActivityMonitor, UserStatus } from '../hooks/useActivityMonitor';

interface ActivityContextType {
  userStatuses: Map<number, UserStatus>;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
}

const ActivityContext = createContext<ActivityContextType | undefined>(undefined);

export const useActivity = (): ActivityContextType => {
  const context = useContext(ActivityContext);
  if (!context) {
    throw new Error('useActivity must be used within ActivityProvider');
  }
  return context;
};

interface ActivityProviderProps {
  children: ReactNode;
}

export const ActivityProvider: React.FC<ActivityProviderProps> = ({ children }) => {
  const { userStatuses, isConnected, connect, disconnect } = useActivityMonitor();

  return (
    <ActivityContext.Provider value={{ userStatuses, isConnected, connect, disconnect }}>
      {children}
    </ActivityContext.Provider>
  );
};
