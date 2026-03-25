-- ============================================================
-- Church Registry System — MySQL Database Setup
-- ============================================================

CREATE DATABASE IF NOT EXISTS church_registry
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE church_registry;

-- ─── MEMBERS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_member (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    middle_name     VARCHAR(100) DEFAULT '',
    last_name       VARCHAR(100) NOT NULL,
    birthday        DATE NOT NULL,
    gender          CHAR(1) NOT NULL COMMENT 'M=Male, F=Female',
    civil_status    VARCHAR(20) NOT NULL,
    address         TEXT NOT NULL,
    contact_number  VARCHAR(20) DEFAULT '',
    email           VARCHAR(254) DEFAULT '',
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    date_registered DATE NOT NULL,
    INDEX idx_member_name (last_name, first_name),
    INDEX idx_member_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── BAPTISM ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_baptism (
    id                    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id             BIGINT UNSIGNED NOT NULL UNIQUE,
    date_baptized         DATE NOT NULL,
    priest                VARCHAR(150) NOT NULL,
    godfathers            TEXT DEFAULT '' COMMENT 'Comma-separated list of godfathers',
    godmothers            TEXT DEFAULT '' COMMENT 'Comma-separated list of godmothers',
    birth_certificate_no  VARCHAR(100) DEFAULT '',
    remarks               TEXT DEFAULT '',
    CONSTRAINT fk_baptism_member FOREIGN KEY (member_id)
        REFERENCES registry_member(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── CONFIRMATION ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_confirmation (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id           BIGINT UNSIGNED NOT NULL UNIQUE,
    date_confirmed      DATE NOT NULL,
    bishop              VARCHAR(150) NOT NULL,
    confirmation_name   VARCHAR(100) NOT NULL,
    sponsor             VARCHAR(150) DEFAULT '',
    remarks             TEXT DEFAULT '',
    CONSTRAINT fk_confirmation_member FOREIGN KEY (member_id)
        REFERENCES registry_member(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── FIRST HOLY COMMUNION ───────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_firstholycommunion (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id       BIGINT UNSIGNED NOT NULL UNIQUE,
    date_received   DATE NOT NULL,
    priest          VARCHAR(150) NOT NULL,
    remarks         TEXT DEFAULT '',
    CONSTRAINT fk_communion_member FOREIGN KEY (member_id)
        REFERENCES registry_member(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── MARRIAGE ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_marriage (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id           BIGINT UNSIGNED NOT NULL,
    spouse_name         VARCHAR(200) NOT NULL,
    date_married        DATE NOT NULL,
    priest              VARCHAR(150) NOT NULL,
    principal_sponsor   VARCHAR(150) DEFAULT '',
    secondary_sponsor   VARCHAR(150) DEFAULT '',
    remarks             TEXT DEFAULT '',
    CONSTRAINT fk_marriage_member FOREIGN KEY (member_id)
        REFERENCES registry_member(id) ON DELETE CASCADE,
    INDEX idx_marriage_member (member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── LAST RITES ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_lastrites (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id           BIGINT UNSIGNED NOT NULL UNIQUE,
    date_administered   DATE NOT NULL,
    priest              VARCHAR(150) NOT NULL,
    remarks             TEXT DEFAULT '',
    CONSTRAINT fk_lastrites_member FOREIGN KEY (member_id)
        REFERENCES registry_member(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── PLEDGES ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_pledge (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id       BIGINT UNSIGNED NOT NULL,
    description     VARCHAR(255) NOT NULL,
    amount_pledged  DECIMAL(10,2) NOT NULL,
    due_date        DATE NOT NULL,
    status          VARCHAR(10) NOT NULL DEFAULT 'unpaid' COMMENT 'unpaid|partial|paid',
    date_created    DATE NOT NULL,
    CONSTRAINT fk_pledge_member FOREIGN KEY (member_id)
        REFERENCES registry_member(id) ON DELETE CASCADE,
    INDEX idx_pledge_member (member_id),
    INDEX idx_pledge_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── PLEDGE PAYMENTS ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS registry_pledgepayment (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pledge_id   BIGINT UNSIGNED NOT NULL,
    amount      DECIMAL(10,2) NOT NULL,
    date_paid   DATE NOT NULL,
    notes       VARCHAR(255) DEFAULT '',
    CONSTRAINT fk_payment_pledge FOREIGN KEY (pledge_id)
        REFERENCES registry_pledge(id) ON DELETE CASCADE,
    INDEX idx_payment_pledge (pledge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── DJANGO AUTH TABLES (run migrations instead, but included for reference) ─
-- Django will create auth_user and session tables automatically via:
--   python manage.py migrate

-- ─── SAMPLE ADMIN USER (password: admin123) ─────────────────
-- Run this AFTER running migrations:
-- python manage.py createsuperuser
-- OR use the management command below in your shell:
-- python manage.py shell -c "
-- from django.contrib.auth.models import User;
-- User.objects.create_superuser('admin', 'admin@parish.org', 'admin123')
-- "
