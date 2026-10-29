-- S7: OC con lineas + proveedor, y categoria (familia) por producto.
-- Aditiva: se puede aplicar antes de desplegar el backend nuevo sin romper el actual.

ALTER TABLE products ADD COLUMN IF NOT EXISTS category varchar(50);
ALTER TABLE products ADD COLUMN IF NOT EXISTS supplier varchar(100);
-- Los productos existentes fueron cargados a nivel familia (BEBIDAS, LACTEOS...): su categoria es ellos mismos.
UPDATE products SET category = family WHERE category IS NULL;

ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS supplier varchar(100);
-- family/quantity/trigger_stock/reorder_point_s/order_up_to_s pasan a las lineas; quedan nullable
-- en la cabecera hasta borrarlas en una migracion posterior (cuando el backend nuevo este desplegado).
ALTER TABLE purchase_orders ALTER COLUMN family DROP NOT NULL;
ALTER TABLE purchase_orders ALTER COLUMN quantity DROP NOT NULL;

CREATE TABLE IF NOT EXISTS purchase_order_lines (
    id serial PRIMARY KEY,
    order_id integer NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    family varchar(50) NOT NULL,
    quantity numeric(12, 2) NOT NULL,
    unit_cost numeric(12, 2),
    trigger_stock numeric(12, 2),
    reorder_point_s numeric(12, 2),
    order_up_to_s numeric(12, 2)
);
CREATE INDEX IF NOT EXISTS ix_purchase_order_lines_order_id ON purchase_order_lines(order_id);
CREATE INDEX IF NOT EXISTS ix_purchase_order_lines_family ON purchase_order_lines(family);
-- Igual que el resto de tablas: sin politicas, el anon key no puede leerla (el backend usa postgres/bypassrls).
ALTER TABLE purchase_order_lines ENABLE ROW LEVEL SECURITY;

-- Cada orden vieja (una fila por familia) pasa a ser una OC de una linea.
INSERT INTO purchase_order_lines (order_id, family, quantity, unit_cost, trigger_stock, reorder_point_s, order_up_to_s)
SELECT po.id, po.family, po.quantity,
       (SELECT p.unit_cost FROM products p
        WHERE p.business_id = po.business_id AND p.store_nbr = po.store_nbr AND p.family = po.family LIMIT 1),
       po.trigger_stock, po.reorder_point_s, po.order_up_to_s
FROM purchase_orders po
WHERE po.family IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM purchase_order_lines l WHERE l.order_id = po.id);
