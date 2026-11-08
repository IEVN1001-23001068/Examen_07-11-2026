import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { DetallePedido, PedidoNuevo, PedidoResumen, VentasResponse } from './models';

export const API_URL = 'http://127.0.0.1:5000/api';

@Injectable({ providedIn: 'root' })
export class PizzeriaService {
  constructor(private http: HttpClient) {}

  crearPedido(pedido: PedidoNuevo): Observable<{
    idPedido: number;
    totalCosto: number;
    mensaje: string;
    exito: boolean;
  }> {
    const cuerpo = {
      cliente: {
        nombres: (pedido.nombre || '').trim() || 'Cliente',
        direccion: pedido.direccion,
        telefono: pedido.telefono,
      },
      fecha: {
        dia: pedido.dia,
        mes: pedido.mes,
        anio: pedido.anio,
      },
      pizzas: pedido.pizzas.map((pizza) => ({
        tamano: pizza.tamano,
        ingredientes: pizza.ingredientes,
        cantidad: pizza.no_pizzas,
        subtotal: pizza.subtotal,
      })),
    };

    return this.http.post<any>(`${API_URL}/pedidos/`, cuerpo).pipe(
      map((res) => ({
        idPedido: res.idPedido,
        totalCosto: res.total ?? res.totalCosto ?? pedido.totalCosto,
        mensaje: res.mensaje ?? 'Pedido registrado correctamente',
        exito: res.exito ?? true,
      })),
    );
  }

  pedidosRealizados(): Observable<PedidoResumen[]> {
    return this.http.get<any>(`${API_URL}/pedidos/`).pipe(
      map((res) => {
        const lista = Array.isArray(res) ? res : res?.pedidos ?? [];
        return lista.map((p: any) => ({
          idPedido: p.idPedido,
          nombre: p.cliente?.nombres ?? p.nombre ?? 'Cliente',
          dia: p.fecha?.dia ?? p.dia,
          mes: p.fecha?.mes ?? p.mes,
          anio: p.fecha?.anio ?? p.anio,
          totalCosto: p.total ?? p.totalCosto ?? 0,
        }));
      }),
    );
  }

  ventasPorDia(dia: string): Observable<VentasResponse> {
    return this.http.get<any>(`${API_URL}/pedidos/ventas/dia/${encodeURIComponent(dia)}`).pipe(
      map((res) => ({
        ventas: (res.ventas ?? []).map((v: any) => ({
          idPedido: v.idPedido,
          nombre: v.nombreCliente ?? v.cliente ?? v.nombre ?? 'Cliente',
          totalCosto: v.total ?? v.totalCosto ?? 0,
        })),
        total: res.totalVentas ?? res.total ?? 0,
      })),
    );
  }

  ventasPorMes(mes: string): Observable<VentasResponse> {
    return this.http.get<any>(`${API_URL}/pedidos/ventas/mes/${encodeURIComponent(mes)}`).pipe(
      map((res) => ({
        ventas: (res.ventas ?? []).map((v: any) => ({
          idPedido: v.idPedido,
          nombre: v.nombreCliente ?? v.cliente ?? v.nombre ?? 'Cliente',
          totalCosto: v.total ?? v.totalCosto ?? 0,
        })),
        total: res.totalVentas ?? res.total ?? 0,
      })),
    );
  }

  detallePedido(idPedido: number): Observable<DetallePedido[]> {
    return this.http.get<any>(`${API_URL}/pedidos/${idPedido}`).pipe(
      map((res) => {
        const pedido = res?.pedido ?? res ?? {};
        const fecha = pedido.fecha ?? {};
        const pizzas = pedido.pizzas ?? [];
        return pizzas.map((p: any) => ({
          tamano: p.tamano ?? p.tamaño,
          ingredientes: p.ingredientes ?? p.ingrediente,
          no_pizzas: p.cantidad ?? p.no_pizzas ?? 0,
          subtotal: p.subtotal ?? 0,
          idPedido: pedido.idPedido ?? idPedido,
          dia: fecha.dia ?? pedido.dia,
          mes: fecha.mes ?? pedido.mes,
          anio: fecha.anio ?? pedido.anio,
          totalCosto: pedido.total ?? pedido.totalCosto ?? 0,
        }));
      }),
    );
  }
}
