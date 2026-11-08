import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PedidoResumen } from '../models';
import { PizzeriaService } from '../pizzeria.service';

@Component({
  imports: [CommonModule, RouterLink],
  selector: 'app-pedidos-realizados',
  templateUrl: './pedidos-realizados.html',
})
export class PedidosRealizados implements OnInit {
  constructor(
    private api: PizzeriaService,
    private detector: ChangeDetectorRef,
  ) {}

  pedidos: PedidoResumen[] = [];
  cargando = true;
  error = '';

  ngOnInit(): void {
    this.api.pedidosRealizados().subscribe({
      next: (res) => {
        this.pedidos = Array.isArray(res) ? res : [];
        this.cargando = false;
        this.detector.markForCheck();
      },
      error: () => {
        this.error = 'No se pudieron cargar los pedidos realizados.';
        this.cargando = false;
        this.detector.markForCheck();
      },
    });
  }
}
