import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PizzaItem } from '../models';

@Component({
  imports: [CommonModule],
  selector: 'app-resumen-pedido',
  templateUrl: './resumen-pedido.html',
})
export class ResumenPedido {
  @Input() pizzas: PizzaItem[] = [];
  @Input() total = 0;
  @Input() guardando = false;
  @Output() quitarPizza = new EventEmitter<number>();
  @Output() terminarPedido = new EventEmitter<void>();
}
