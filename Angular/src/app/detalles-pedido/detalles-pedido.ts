import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DetallePedido } from '../models';
import { PizzeriaService } from '../pizzeria.service';

@Component({
  imports: [CommonModule, RouterLink],
  selector: 'app-detalles-pedido',
  templateUrl: './detalles-pedido.html',
})



export class DetallesPedido implements OnInit {
  constructor(
    private api: PizzeriaService,
    private route: ActivatedRoute,
    private detector: ChangeDetectorRef,
  ) {}

  idPedido = 0;
  detalles: DetallePedido[] = [];
  confirmacion = '';
  cargando = true;
  error = '';

  ngOnInit(): void {
    this.confirmacion = window.history.state?.confirmacion ?? '';
    const id = this.route.snapshot.paramMap.get('id');
    this.idPedido = Number(id);

    if (!id || isNaN(this.idPedido) || this.idPedido < 1) {
      this.error = 'El número de pedido no es válido.';
      this.cargando = false;
      return;
    }

    this.api.detallePedido(this.idPedido).subscribe({
      next: (res) => {
        this.detalles = Array.isArray(res) ? res : [];
        this.cargando = false;
        this.detector.markForCheck();
      },
      error: () => {
        this.error = 'No se pudo cargar el detalle del pedido.';
        this.cargando = false;
        this.detector.markForCheck();
      },
    });
  }
}
