# Diagrama de Casos de Uso - CINE-UNAB

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA CINE-UNAB                        │
└─────────────────────────────────────────────────────────────┘

                        ┌─────────────┐
                        │   Cliente   │
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
         ┌────▼────┐      ┌────▼────┐    ┌────▼────┐
         │Registr. │      │ Iniciar  │    │  Ver    │
         │  Cuenta │      │ Sesión   │    │Películas│
         └─────────┘      └─────────┘    └────┬────┘
                                              │
                                    ┌─────────┴────────┐
                                    │                  │
                           ┌────────▼────────┐  ┌──────▼──────┐
                           │ Ver Película    │  │  Seleccionar│
                           │   Detalle       │  │  Función    │
                           └────────────────┘  └──────┬───────┘
                                                      │
                                    ┌─────────────────┴────────┐
                                    │                          │
                           ┌────────▼────┐          ┌──────────▼───┐
                           │ Elegir       │          │ Seleccionar  │
                           │ Asientos     │          │ Método Pago  │
                           └────────┬─────┘          └──────────────┘
                                    │
                           ┌────────▼────┐
                           │ Confirmar    │
                           │ Compra       │
                           └──────────────┘


                        ┌──────────────┐
                        │Administrador │
                        └──────┬───────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼────┐         ┌─────▼──────┐      ┌─────▼────┐
    │Gestionar│         │  Modificar │      │ Destacar │
    │ Películas        │  Precios    │      │ Película │
    └────────┘         └──────┬──────┘      └─────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              ┌─────▼─────┐       ┌──────▼──────┐
              │Gestionar  │       │ Gestionar   │
              │  Salas    │       │ Horarios    │
              └───────────┘       └─────────────┘
```

## Descripción de Actores

### 👤 **Cliente**
- Registrarse y crear cuenta
- Iniciar sesión con email y contraseña
- Ver catálogo de películas
- Seleccionar funciones disponibles
- Elegir asientos en la sala
- Realizar compra con diferentes métodos de pago
- Ver detalles de películas

### 🔧 **Administrador**
- Gestionar películas (añadir, editar, eliminar)
- Modificar precios de entradas
- Destacar películas en cartelera
- Administrar salas
- Gestionar horarios de funciones
- Todas las acciones del cliente
