-- ============================================================
-- InsightSQL - PostgreSQL Schema
-- Base de datos para el agente SQL conversacional
-- ============================================================

-- ============================================================
-- SECCIÓN 1: TABLAS DEL DATASET OLIST
-- ============================================================

-- ----------------------------------------------------------
-- customers
-- Clientes del marketplace. Cada fila es un customer único por pedido.
-- ----------------------------------------------------------
CREATE TABLE customers (
    customer_id               VARCHAR(50)  NOT NULL,
    customer_unique_id        VARCHAR(50)  NOT NULL,
    customer_zip_code_prefix  VARCHAR(8)   NOT NULL,
    customer_city             VARCHAR(100) NOT NULL,
    customer_state            CHAR(2)      NOT NULL,

    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

CREATE INDEX idx_customers_unique_id ON customers (customer_unique_id);

COMMENT ON TABLE  customers IS 'Clientes registrados. customer_id es único por pedido; customer_unique_id identifica al comprador real.';
COMMENT ON COLUMN customers.customer_unique_id IS 'ID persistente del comprador real entre múltiples pedidos.';


-- ----------------------------------------------------------
-- sellers
-- Vendedores registrados en la plataforma.
-- ----------------------------------------------------------
CREATE TABLE sellers (
    seller_id               VARCHAR(50)  NOT NULL,
    seller_zip_code_prefix  VARCHAR(8)   NOT NULL,
    seller_city             VARCHAR(100) NOT NULL,
    seller_state            CHAR(2)      NOT NULL,

    CONSTRAINT pk_sellers PRIMARY KEY (seller_id)
);

COMMENT ON TABLE sellers IS 'Vendedores que operan dentro del marketplace.';


-- ----------------------------------------------------------
-- products
-- Catálogo de productos publicados en la plataforma.
-- ----------------------------------------------------------
CREATE TABLE products (
    product_id                  VARCHAR(50)   NOT NULL,
    product_category_name       VARCHAR(100),
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            NUMERIC(10, 2),
    product_length_cm           NUMERIC(8, 2),
    product_height_cm           NUMERIC(8, 2),
    product_width_cm            NUMERIC(8, 2),

    CONSTRAINT pk_products PRIMARY KEY (product_id)
);

CREATE INDEX idx_products_category ON products (product_category_name);

COMMENT ON TABLE products IS 'Catálogo de productos disponibles en el marketplace.';


-- ----------------------------------------------------------
-- orders
-- Pedidos realizados por los clientes. Tabla central del schema.
-- ----------------------------------------------------------
CREATE TABLE orders (
    order_id                       VARCHAR(50)  NOT NULL,
    customer_id                    VARCHAR(50)  NOT NULL,
    order_status                   VARCHAR(20)  NOT NULL,
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP,

    CONSTRAINT pk_orders        PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX idx_orders_customer_id    ON orders (customer_id);
CREATE INDEX idx_orders_purchase_date  ON orders (order_purchase_timestamp);
CREATE INDEX idx_orders_status         ON orders (order_status);

COMMENT ON TABLE  orders IS 'Pedidos del marketplace. Tabla central que conecta clientes, pagos, reviews e ítems.';
COMMENT ON COLUMN orders.order_status IS 'Estado: created, invoiced, approved, processing, shipped, delivered, unavailable, canceled.';
COMMENT ON COLUMN orders.order_purchase_timestamp IS 'Fecha y hora en que el cliente realizó la compra.';
COMMENT ON COLUMN orders.order_estimated_delivery_date IS 'Fecha de entrega estimada informada al cliente.';


-- ----------------------------------------------------------
-- order_items
-- Líneas de ítem dentro de cada pedido.
-- ----------------------------------------------------------
CREATE TABLE order_items (
    order_id            VARCHAR(50)    NOT NULL,
    order_item_id       INTEGER        NOT NULL,
    product_id          VARCHAR(50)    NOT NULL,
    seller_id           VARCHAR(50)    NOT NULL,
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2) NOT NULL,
    freight_value       NUMERIC(10, 2) NOT NULL,

    CONSTRAINT pk_order_items      PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_items_order      FOREIGN KEY (order_id)
        REFERENCES orders (order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_items_product    FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_items_seller     FOREIGN KEY (seller_id)
        REFERENCES sellers (seller_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX idx_items_order_id    ON order_items (order_id);
CREATE INDEX idx_items_product_id  ON order_items (product_id);
CREATE INDEX idx_items_seller_id   ON order_items (seller_id);

COMMENT ON TABLE  order_items IS 'Ítems individuales de cada pedido. Un order puede contener productos de distintos sellers.';
COMMENT ON COLUMN order_items.price IS 'Precio del producto en el momento de la compra (en BRL).';
COMMENT ON COLUMN order_items.freight_value IS 'Valor del flete para ese ítem específico (en BRL).';


-- ----------------------------------------------------------
-- order_payments
-- Pagos asociados a cada pedido.
-- ----------------------------------------------------------
CREATE TABLE order_payments (
    order_id              VARCHAR(50)    NOT NULL,
    payment_sequential    INTEGER        NOT NULL,
    payment_type          VARCHAR(30)    NOT NULL,
    payment_installments  INTEGER        NOT NULL DEFAULT 1,
    payment_value         NUMERIC(10, 2) NOT NULL,

    CONSTRAINT pk_order_payments PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

COMMENT ON TABLE  order_payments IS 'Información de pago por pedido. Un pedido puede tener múltiples secuencias de pago.';
COMMENT ON COLUMN order_payments.payment_type IS 'Método: credit_card, boleto, voucher, debit_card, not_defined.';
COMMENT ON COLUMN order_payments.payment_installments IS 'Número de cuotas elegidas por el cliente.';


-- ----------------------------------------------------------
-- order_reviews
-- Reseñas de clientes sobre sus pedidos.
-- ----------------------------------------------------------
CREATE TABLE order_reviews (
    review_id                VARCHAR(50)  NOT NULL,
    order_id                 VARCHAR(50)  NOT NULL,
    review_score             SMALLINT     NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title     VARCHAR(255),
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP,
    review_answer_timestamp  TIMESTAMP,

    CONSTRAINT pk_order_reviews PRIMARY KEY (review_id),
    CONSTRAINT fk_reviews_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_reviews_order_id  ON order_reviews (order_id);
CREATE INDEX idx_reviews_score     ON order_reviews (review_score);

COMMENT ON TABLE  order_reviews IS 'Reseñas y calificaciones dejadas por los compradores.';
COMMENT ON COLUMN order_reviews.review_score IS 'Calificación del 1 al 5.';


-- ============================================================
-- SECCIÓN 2: TABLAS DEL SISTEMA (memoria del chat)
-- ============================================================

-- ----------------------------------------------------------
-- conversations
-- Sesiones de conversación del chat.
-- ----------------------------------------------------------
CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations (user_id);

COMMENT ON TABLE conversations IS 'Sesiones de chat. Cada usuario puede tener múltiples conversaciones.';
COMMENT ON COLUMN conversations.user_id IS 'Identificador del usuario (viene del JWT).';


-- ----------------------------------------------------------
-- messages
-- Mensajes individuales dentro de una conversación.
-- Incluye metadata del agente para auditoría y transparencia.
-- ----------------------------------------------------------
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    sql_generated   TEXT,
    intencion_json  JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages (conversation_id);
CREATE INDEX idx_messages_created_at      ON messages (created_at);

COMMENT ON TABLE messages IS 'Mensajes de la conversación. Los campos sql_generated e intencion_json solo se llenan en mensajes del agente.';
COMMENT ON COLUMN messages.role IS 'Rol: user (pregunta) o assistant (respuesta del agente).';
COMMENT ON COLUMN messages.sql_generated IS 'SQL que generó el agente para responder. NULL en mensajes del usuario.';
COMMENT ON COLUMN messages.intencion_json IS 'JSON con la intención descompuesta: {metrica, dimension, filtro, granularidad}. NULL en mensajes del usuario.';
