# Taller Moto

Aplicacion de escritorio multiplataforma para registrar clientes, motocicletas y el historial de ordenes de trabajo de un taller.

## Requisitos

- Python 3.10 o posterior
- Windows o Linux

## Instalacion y ejecucion

Desde la carpeta del proyecto, crea y activa un entorno virtual:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Luego, en ambos sistemas:

```bash
python -m pip install -e .
taller-moto
```

## Primera version

- Registra clientes y varias motocicletas por cliente.
- Exige matricula/placa y una foto para cada motocicleta.
- Guarda ordenes transcritas desde el registro fisico, con kilometraje, motivo, diagnostico, trabajo realizado y estado.
- Permite cambiar el estado de una orden y consultar el historial en la lista de ordenes.

Por ahora, los datos se guardan localmente en SQLite y las fotos se copian al directorio de datos de la aplicacion. La interfaz depende de un contrato de servicio y no de SQLite directamente; la implementacion local adapta la base de datos a ese contrato. Esto prepara el punto de extension para conectar un cliente de API al futuro servidor LAN. El servidor, la API, las cuentas de usuario y los permisos aun no estan implementados, por lo que esta version sigue siendo de un solo equipo y no debe usarse con datos sensibles en un entorno compartido. No se guardan fotos de las reparaciones. La facturacion no esta habilitada en esta version.

La base de datos no debe compartirse como archivo entre varias computadoras. Para el futuro acceso por LAN, los equipos deberan conectarse a un servicio central; la aplicacion mantiene la persistencia separada de la interfaz para facilitar esa evolucion.

## Pruebas

```bash
python -m unittest discover -s tests -v
```
