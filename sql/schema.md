# Schema PostgreSQL — InsightSQL

## Requisitos previos

- PostgreSQL 16+ instalado
- Acceso a PostgreSQL local (usuario con permisos para crear tablas)

## Crear la base de datos

```bash
# Crear la base de datos (solo si no existe)
createdb insightsql

# O desde psql
psql -c "CREATE DATABASE insightsql;"
```

## Ejecutar el schema

```bash
# Desde la raíz del proyecto
psql -d insightsql -f schema.sql
```
## Verificar que las tablas se crearon

```bash
psql -d insightsql -c "\dt"
```


**Resultado esperado:**

```
                List of relations
 Schema |         Name          | Type  | Owner
--------+-----------------------+-------+-------
 public | customers             | table | user
 public | conversations         | table | user
 public | messages              | table | user
 public | order_items           | table | user
 public | order_payments        | table | user
 public | order_reviews         | table | user
 public | orders                | table | user
 public | products              | table | user
 public | sellers               | table | user
(9 rows)
```

## Eliminar y recrear (si necesitas empezar desde cero)

```bash
psql -d insightsql -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -d insightsql -f db/schema.sql
```