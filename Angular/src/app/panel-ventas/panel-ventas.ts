import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DIAS_SEMANA, MESES, Venta } from '../models';
import { PizzeriaService } from '../pizzeria.service';

@Component({
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  selector: 'app-panel-ventas',
  templateUrl: './panel-ventas.html',
})
export class PanelVentas implements OnInit {
  constructor(
    private fb: FormBuilder,
    private api: PizzeriaService,
    private detector: ChangeDetectorRef,
  ) {}

  readonly dias = DIAS_SEMANA;
  readonly meses = MESES;

  formulario!: FormGroup;
  ventas: Venta[] = [];
  total = 0;
  consultado = false;
  error = '';

  ngOnInit(): void {
    this.formulario = this.fb.group({
      modo: ['dia', Validators.required],
      dia: ['lunes', Validators.required],
      mes: ['enero', Validators.required],
    });
  }

  consultar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error = 'Selecciona un día o un mes para consultar.';
      return;
    }

    const datos = this.formulario.getRawValue();
    const peticion = datos.modo === 'dia'
      ? this.api.ventasPorDia(datos.dia)
      : this.api.ventasPorMes(datos.mes);

    peticion.subscribe({
      next: (res) => {
        this.ventas = res.ventas;
        this.total = res.total;
        this.consultado = true;
        this.error = '';
        this.detector.markForCheck();
      },
      error: () => {
        this.error = 'No se pudo consultar las ventas.';
        this.detector.markForCheck();
      },
    });
  }
}
