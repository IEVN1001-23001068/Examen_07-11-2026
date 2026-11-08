import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidationErrors, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { INGREDIENTES_PIZZA, PizzaItem, PRECIOS, Tamano } from '../models';
import { PizzeriaService } from '../pizzeria.service';
import { FormularioPedido } from '../formulario-pedido/formulario-pedido';
import { PanelVentas } from '../panel-ventas/panel-ventas';
import { ResumenPedido } from '../resumen-pedido/resumen-pedido';

function requiereIngrediente(control: AbstractControl): ValidationErrors | null {
  const haySeleccionado = Object.values(control.value ?? {}).some((valor) => valor === true);
  return haySeleccionado ? null : { required: true };
}

@Component({
  imports: [CommonModule, FormularioPedido, ResumenPedido, PanelVentas],
  selector: 'app-pedido',
  templateUrl: './pedido.html',
})
export class Pedido implements OnInit {
  constructor(
    private fb: FormBuilder,
    private api: PizzeriaService,
    private router: Router,
    private detector: ChangeDetectorRef,
  ) {}

  readonly precios = PRECIOS;
  readonly tamanos: Tamano[] = ['chica', 'mediana', 'grande'];
  readonly ingredientesDisponibles = INGREDIENTES_PIZZA;

  formularioCliente!: FormGroup;
  formularioPizza!: FormGroup;
  pizzas: PizzaItem[] = [];
  total = 0;
  error = '';
  guardando = false;

  ngOnInit(): void {
    this.formularioCliente = this.fb.group({
      nombre: ['', [Validators.required, Validators.maxLength(50)]],
      direccion: ['', [Validators.required, Validators.maxLength(60)]],
      telefono: ['', [Validators.required, Validators.maxLength(15)]],
      fecha: ['', Validators.required],
    });

    this.formularioPizza = this.fb.group({
      tamano: ['chica', Validators.required],
      ingredientes: this.fb.group({
        jamon: [false],
        pina: [false],
        champinones: [false],
      }, { validators: requiereIngrediente }),
      noPizzas: [1, [Validators.required, Validators.min(1)]],
    });
  }

  agregar(): void {
    if (this.formularioPizza.invalid) {
      this.formularioPizza.markAllAsTouched();
      this.error = this.formularioPizza.get('ingredientes')?.invalid
        ? 'Selecciona al menos un ingrediente.'
        : 'Elige un tamaño y un número de pizzas válido.';
      return;
    }

    const datosPizza = this.formularioPizza.getRawValue();
    const ingredientesSeleccionados = INGREDIENTES_PIZZA.filter(
      (ingrediente) => datosPizza.ingredientes[ingrediente.id],
    );
    const ingredientes = ingredientesSeleccionados.map((ingrediente) => ingrediente.nombre).join(', ');
    const precioIngredientes = ingredientesSeleccionados.reduce(
      (totalIngredientes, ingrediente) => totalIngredientes + ingrediente.precio,
      0,
    );
    const cantidad = Number(datosPizza.noPizzas);

    this.error = '';
    this.pizzas.push({
      tamano: datosPizza.tamano as Tamano,
      ingredientes,
      no_pizzas: cantidad,
      subtotal: (PRECIOS[datosPizza.tamano as Tamano] + precioIngredientes) * cantidad,
    });
    this.calcularTotal();
    this.formularioPizza.reset({
      tamano: datosPizza.tamano,
      ingredientes: { jamon: false, pina: false, champinones: false },
      noPizzas: 1,
    });
  }

  quitar(index: number): void {
    this.pizzas.splice(index, 1);
    this.calcularTotal();
  }

  calcularTotal(): void {
    this.total = 0;
    for (let i = 0; i < this.pizzas.length; i++) {
      this.total += this.pizzas[i].subtotal;
    }
  }

  terminar(): void {
    if (this.guardando) {
      return;
    }

    if (this.formularioCliente.invalid) {
      this.formularioCliente.markAllAsTouched();
      this.error = 'Completa los datos del cliente.';
      return;
    }

    if (!this.pizzas.length) {
      this.error = 'Agrega al menos una pizza al pedido.';
      return;
    }

    const datosCliente = this.formularioCliente.getRawValue();
    const [anio, mes, dia] = datosCliente.fecha.split('-').map(Number);
    this.error = '';
    this.guardando = true;

    this.api.crearPedido({
      nombre: datosCliente.nombre.trim(),
      direccion: datosCliente.direccion.trim(),
      telefono: datosCliente.telefono.trim(),
      dia,
      mes,
      anio,
      totalCosto: this.total,
      pizzas: this.pizzas,
    }).subscribe({
      next: (res) => {
        this.router.navigate(['/detalles', res.idPedido], {
          state: { confirmacion: res.mensaje },
        });
      },
      error: () => {
        this.guardando = false;
        this.error = 'No se pudo guardar el pedido. Revisa la conexión con Flask.';
        this.detector.markForCheck();
      },
    });
  }
}
