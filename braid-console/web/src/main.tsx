import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import 'antd/dist/reset.css';
import './style.css';

const client = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <ConfigProvider locale={zhCN} theme={{ token: {
        colorPrimary: '#2563eb', colorText: '#182230', colorTextSecondary: '#667085',
        colorBorder: '#dce2e9', borderRadius: 7, fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      } }}>
        <AntApp><App /></AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
