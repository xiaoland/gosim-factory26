import React from 'react';
import ReactDOM from 'react-dom/client';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Toaster } from '@/components/ui/sonner';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { pageRoutes } from './navigation';
import './theme.css';
import './style.css';

const client = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
});

const router = createBrowserRouter([{ path: '/', element: <App />, children: pageRoutes }]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <TooltipProvider><RouterProvider router={router} /><Toaster position="top-right" richColors closeButton /></TooltipProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
