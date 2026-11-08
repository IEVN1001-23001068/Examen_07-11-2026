import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';
import { INGREDIENTES_PIZZA, PRECIOS, Tamano } from '../models';

@Component({
  imports: [CommonModule, ReactiveFormsModule],
  selector: 'app-formulario-pedido',
  templateUrl: './formulario-pedido.html',
})
export class FormularioPedido {
  @Input() formularioCliente!: FormGroup;
  @Input() formularioPizza!: FormGroup;
  @Input() tamanos: Tamano[] = ['chica', 'mediana', 'grande'];
  @Input() precios: Record<Tamano, number> = PRECIOS;
  @Input() ingredientesDisponibles = INGREDIENTES_PIZZA;
  @Output() agregarPizza = new EventEmitter<void>();
}
