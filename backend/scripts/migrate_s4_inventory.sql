-- Sprint 4: Tablas de inventario
-- Aplicar en Supabase proyecto xqiehkshtedrodhtdkzv

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    store_nbr INTEGER NOT NULL,
    family VARCHAR(50) NOT NULL,
    unit_cost NUMERIC(12,2),
    order_cost NUMERIC(12,2) DEFAULT 5000,
    holding_rate NUMERIC(5,4) DEFAULT 0.25,
    lead_time_days INTEGER DEFAULT 7,
    moq NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_id, store_nbr, family)
);

CREATE TABLE IF NOT EXISTS stock_levels (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    store_nbr INTEGER NOT NULL,
    family VARCHAR(50) NOT NULL,
    quantity NUMERIC(12,2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_id, store_nbr, family)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    store_nbr INTEGER NOT NULL,
    family VARCHAR(50) NOT NULL,
    quantity NUMERIC(12,2) NOT NULL,
    trigger_stock NUMERIC(12,2),
    reorder_point_s NUMERIC(12,2),
    order_up_to_S NUMERIC(12,2),
    policy_used VARCHAR(10) DEFAULT 's_s',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','confirmed','in_transit','received','cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expected_delivery DATE,
    received_at TIMESTAMPTZ
);
