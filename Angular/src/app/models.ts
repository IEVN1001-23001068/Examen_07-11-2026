export type Tamano = 'chica' | 'mediana' | 'grande';

export const PRECIOS: Record<Tamano, number> = {
  chica: 40,
  mediana: 80,
  grande: 120,
};

export const INGREDIENTES_PIZZA = [
  { id: 'jamon', nombre: 'Jamón', precio: 10 },
  { id: 'pina', nombre: 'Piña', precio: 10 },
  { id: 'champinones', nombre: 'Champiñones', precio: 10 },
] as const;

export const DIAS_SEMANA = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];

export const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

export interface Cliente {
  idCliente?: number;
  nombre: string;
  direccion: string;
  telefono: string;
  dia: number;
  mes: number;
  anio: number;
}

export interface Pedido {
  idPedido?: number;
  idCliente: number;
  dia: number;
  mes: number;
  anio: number;
  totalCosto: number;
}

export interface PizzaItem {
  tamano: Tamano;
  ingredientes: string;
  no_pizzas: number;
  subtotal: number;
}

export interface PedidoNuevo {
  nombre: string;
  direccion: string;
  telefono: string;
  dia: number;
  mes: number;
  anio: number;
  totalCosto: number;
  pizzas: PizzaItem[];
}

export interface Venta {
  idPedido: number;
  nombre: string;
  totalCosto: number;
}

export interface PedidoResumen {
  idPedido: number;
  nombre: string;
  dia: number;
  mes: number;
  anio: number;
  totalCosto: number;
}

export interface VentasResponse {
  ventas: Venta[];
  total: number;
}

export interface DetallePedido extends PizzaItem {
  idPedido: number;
  dia: number;
  mes: number;
  anio: number;
  totalCosto: number;
}
