import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'pedido', pathMatch: 'full' },
  {
    path: 'pedido',
    loadComponent: () => import('./pedido/pedido').then((c) => c.Pedido),
  },
  {
    path: 'pedidos',
    loadComponent: () => import('./pedidos-realizados/pedidos-realizados').then((c) => c.PedidosRealizados),
  },
  {
    path: 'detalles/:id',
    loadComponent: () => import('./detalles-pedido/detalles-pedido').then((c) => c.DetallesPedido),
  },
  { path: '**', redirectTo: 'pedido' },
];
