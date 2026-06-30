# User Stories — Proyecto Final Móvil Banco Andino

## Módulo: Fuerza de Ventas (App Flutter)

### US-FV-01: Gestión de Cartera
**Como** oficial de crédito,
**quiero** ver mi cartera diaria con filtros y ordenamiento,
**para** priorizar mis visitas a clientes.

**RF**: La cartera debe mostrar cliente, tipo de gestión, prioridad, score, monto y estado de visita. Debe permitir filtrar y ordenar. Debe registrar visita con GPS.

### US-FV-02: Ficha del Cliente
**Como** oficial de crédito,
**quiero** consultar la ficha completa de un cliente (posición, historial, oferta, semáforo de riesgo),
**para** evaluar su situación financiera antes de ofrecer un crédito.

**RF**: La ficha debe incluir datos personales, deuda total, cuentas vigentes/en mora, días de mora, historial de créditos, oferta pre-aprobada e indicadores de comportamiento (puntualidad, días promedio de mora).

### US-FV-03: Pre-evaluación de Crédito
**Como** oficial de crédito,
**quiero** pre-evaluar a un cliente (elegibilidad, si es sujeto de crédito),
**para** determinar si califica para un crédito antes de formalizar la solicitud.

**RF**: El sistema debe evaluar ingresos, deuda actual, score crediticio y generar una recomendación.

### US-FV-04: Consulta de Buró
**Como** oficial de crédito,
**quiero** consultar el buró del cliente (SBS + lista negra) con su consentimiento firmado,
**para** verificar su historial crediticio y cumplir la normativa.

**RF**: La consulta debe mostrar calificación SBS, deuda total en el sistema financiero, y verificar si está en lista negra. Debe registrar el consentimiento.

### US-FV-05: Solicitud de Crédito
**Como** oficial de crédito,
**quiero** registrar una solicitud de crédito mediante un stepper con simulador de cronograma,
**para** que el cliente conozca sus cuotas y pueda firmar digitalmente.

**RF**: El stepper debe incluir: datos del cliente, monto/plazo, simulación de cuotas (RF 47), garantía, firma digital y confirmación.

### US-FV-06: Sincronización Offline
**Como** oficial de crédito,
**quiero** que las solicitudes se encolen en sync_outbox cuando no haya conexión,
**para** seguir trabajando en campo sin internet.

**RF**: Al recuperar conexión, el backend debe procesar la cola y promover al núcleo financiero.

---

## Módulo: App Clientes (Homebanking Flutter)

### US-CL-01: Login con DNI
**Como** cliente del banco,
**quiero** iniciar sesión con mi número de DNI,
**para** acceder a mis productos bancarios.

### US-CL-02: Consulta de Saldos
**Como** cliente,
**quiero** ver el saldo de mis cuentas de ahorro,
**para** conocer mi disponibilidad financiera.

### US-CL-03: Consulta de Créditos
**Como** cliente,
**quiero** ver mis créditos activos con su cronograma de pagos,
**para** planificar mis finanzas.

**RF**: El cronograma debe mostrar número de cuota, fecha de vencimiento, monto, capital, interés y saldo.

### US-CL-04: Movimientos
**Como** cliente,
**quiero** ver los movimientos recientes de mis cuentas,
**para** llevar un control de mis gastos e ingresos.

### US-CL-05: Tarjetas
**Como** cliente,
**quiero** consultar la información de mis tarjetas (línea, saldo utilizado, fecha de corte),
**para** gestionar mis consumos.

### US-CL-06: Notificaciones
**Como** cliente,
**quiero** recibir notificaciones de recordatorio de pago y novedades,
**para** estar al tanto de mis obligaciones.

### US-CL-07: Operaciones
**Como** cliente,
**quiero** realizar transferencias y pagos desde mi app,
**para** operar mis productos sin ir al banco.

**RF**: Las operaciones deben persistir en la BD y reflejarse en los saldos.

---

## Módulo: Portal React (Back Office)

### US-PO-01: Login de Asesor
**Como** asesor/supervisor/admin,
**quiero** iniciar sesión con mi email y contraseña,
**para** acceder al panel de administración.

### US-PO-02: Gestión de Solicitudes
**Como** administrador,
**quiero** ver las solicitudes pendientes y aprobarlas o rechazarlas,
**para** procesar los créditos solicitados por los clientes.

### US-PO-03: Reportes y Estadísticas
**Como** supervisor/admin,
**quiero** ver reportes y estadísticas de créditos,
**para** monitorear el desempeño del negocio.

---

## Requisitos Transversales

### RF-SEC-01: Autenticación JWT
Todas las piezas deben usar JWT para autenticación, con token almacenado en flutter_secure_storage.

### RF-SEC-02: Control de Acceso por Roles
Matriz de permisos: asesor / supervisor / administrador / cliente.
- Cliente: solo sus propios datos.
- Asesor: cartera, solicitudes propias, consultas.
- Supervisor: reportes, solicitudes del equipo.
- Administrador: todo.

### RF-SEC-03: Bloqueo por Intentos
5 intentos fallidos de login bloquean la cuenta por 30 minutos.

### RF-SYNC-01: Arquitectura Offline-First
Las apps Flutter deben priorizar la BD local (SQLite) y sincronizar con el backend mediante sync_outbox.

### RF-SYNC-02: Puente al Núcleo Financiero
El backend debe promover solicitudes aprobadas a las tablas dcliente/dsolicitud (simulando bd_core_financiero).
