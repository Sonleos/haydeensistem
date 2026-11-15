-- ============================================================
-- HAYDEÉN SISTEMA · ESQUEMA DE BASE DE DATOS
-- Motor: MySQL 8.0+ / MariaDB 10.6+
-- Codificación: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS `haydeensistem`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `haydeensistem`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `rol_permisos`;
DROP TABLE IF EXISTS `sesiones`;
DROP TABLE IF EXISTS `movimientos_inventario`;
DROP TABLE IF EXISTS `administraciones_medicamento`;
DROP TABLE IF EXISTS `tratamiento_horarios`;
DROP TABLE IF EXISTS `tratamientos`;
DROP TABLE IF EXISTS `inventario_lotes`;
DROP TABLE IF EXISTS `medicamentos`;
DROP TABLE IF EXISTS `control_panales`;
DROP TABLE IF EXISTS `dxtx`;
DROP TABLE IF EXISTS `signos_vitales`;
DROP TABLE IF EXISTS `pacientes`;
DROP TABLE IF EXISTS `usuarios`;
DROP TABLE IF EXISTS `turnos`;
DROP TABLE IF EXISTS `personal`;
DROP TABLE IF EXISTS `roles`;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- 1. SEGURIDAD Y PERSONAL
-- ------------------------------------------------------------

CREATE TABLE `roles` (
  `id`          TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre`      VARCHAR(40)  NOT NULL,
  `descripcion` VARCHAR(160) NULL,
  `created_at`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Permisos por rol. El comodín '*' otorga acceso total (solo admin).
CREATE TABLE `rol_permisos` (
  `rol_id`     TINYINT UNSIGNED NOT NULL,
  `permiso`    VARCHAR(60)      NOT NULL,
  `created_at` TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rol_id`, `permiso`),
  CONSTRAINT `fk_rol_permisos_rol`
    FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `personal` (
  `id`               INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  `nombre`           VARCHAR(80)      NOT NULL,
  `apellidos`        VARCHAR(120)     NOT NULL,
  `documento`        VARCHAR(30)      NULL,
  `fecha_nacimiento` DATE             NULL,
  `telefono`         VARCHAR(25)      NULL,
  `email`            VARCHAR(120)     NULL,
  `rol_id`           TINYINT UNSIGNED NOT NULL,
  `estado`           ENUM('activo','libre','inactivo') NOT NULL DEFAULT 'activo',
  `fecha_ingreso`    DATE             NULL,
  `notas`            VARCHAR(255)     NULL,
  `created_at`       TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_personal_documento` (`documento`),
  KEY `idx_personal_rol` (`rol_id`),
  KEY `idx_personal_estado` (`estado`),
  KEY `idx_personal_nombre` (`apellidos`, `nombre`),
  CONSTRAINT `fk_personal_rol`
    FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `turnos` (
  `id`          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  `personal_id` INT UNSIGNED     NOT NULL,
  `fecha`       DATE             NOT NULL,
  `hora_inicio` TIME             NOT NULL,
  `hora_fin`    TIME             NOT NULL,
  `tipo`        ENUM('matutino','vespertino','nocturno','guardia') NOT NULL DEFAULT 'matutino',
  `estado`      ENUM('programado','en_curso','finalizado','ausente') NOT NULL DEFAULT 'programado',
  `notas`       VARCHAR(255)     NULL,
  `created_at`  TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_turno_personal_fecha` (`personal_id`, `fecha`, `hora_inicio`),
  KEY `idx_turnos_fecha_estado` (`fecha`, `estado`),
  CONSTRAINT `fk_turnos_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `usuarios` (
  `id`            INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  `personal_id`   INT UNSIGNED     NULL,
  `rol_id`        TINYINT UNSIGNED NOT NULL,
  `username`      VARCHAR(50)      NOT NULL,
  `password_hash` VARCHAR(255)     NOT NULL,
  `activo`        TINYINT(1)       NOT NULL DEFAULT 1,
  `ultimo_acceso` DATETIME         NULL,
  `created_at`    TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuarios_username` (`username`),
  UNIQUE KEY `uq_usuarios_personal` (`personal_id`),
  KEY `idx_usuarios_rol` (`rol_id`),
  CONSTRAINT `fk_usuarios_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_usuarios_rol`
    FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sesiones` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `usuario_id` INT UNSIGNED    NOT NULL,
  `token_hash` CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `expira_en`  DATETIME        NOT NULL,
  `ip`         VARCHAR(45)     NULL,
  `user_agent` VARCHAR(255)    NULL,
  `creada_en`  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sesiones_token` (`token_hash`),
  KEY `idx_sesiones_usuario` (`usuario_id`),
  KEY `idx_sesiones_expira` (`expira_en`),
  CONSTRAINT `fk_sesiones_usuario`
    FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 2. PACIENTES
-- ------------------------------------------------------------

CREATE TABLE `pacientes` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre`            VARCHAR(80)  NOT NULL,
  `apellidos`         VARCHAR(120) NOT NULL,
  `documento`         VARCHAR(30)  NULL,
  `fecha_nacimiento`  DATE         NULL,
  `sexo`              ENUM('masculino','femenino','otro') NOT NULL DEFAULT 'otro',
  `tipo_residencia`   ENUM('residenciado','ambulatorio') NOT NULL,
  `habitacion`        VARCHAR(20)  NULL,
  `cama`              VARCHAR(20)  NULL,
  `contacto_familiar` VARCHAR(120) NULL,
  `telefono_contacto` VARCHAR(25)  NULL,
  `alergias`          TEXT         NULL,
  `diagnostico`       TEXT         NULL,
  `peso_kg`           DECIMAL(5,2) NULL,
  `talla_m`           DECIMAL(4,2) NULL,
  `imc`               DECIMAL(5,2) GENERATED ALWAYS AS (
                        CASE
                          WHEN `peso_kg` IS NOT NULL AND `talla_m` IS NOT NULL AND `talla_m` > 0
                            THEN ROUND(`peso_kg` / (`talla_m` * `talla_m`), 2)
                          ELSE NULL
                        END
                      ) STORED,
  `estado`            ENUM('activo','hospitalizado','alta','fallecido') NOT NULL DEFAULT 'activo',
  `fecha_ingreso`     DATE         NULL,
  `created_at`        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pacientes_documento` (`documento`),
  KEY `idx_pacientes_estado` (`estado`),
  KEY `idx_pacientes_residencia` (`tipo_residencia`),
  KEY `idx_pacientes_nombre` (`apellidos`, `nombre`),
  CONSTRAINT `chk_pacientes_talla`
    CHECK (`talla_m` IS NULL OR `talla_m` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 3. INVENTARIO Y TRATAMIENTOS
-- ------------------------------------------------------------

CREATE TABLE `medicamentos` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre`                VARCHAR(120) NOT NULL,
  `principio_activo`      VARCHAR(120) NULL,
  `presentacion`          VARCHAR(80)  NULL,
  `concentracion`         VARCHAR(50)  NULL,
  `unidad`                VARCHAR(20)  NOT NULL DEFAULT 'mg',
  `stock_minimo`          INT UNSIGNED NOT NULL DEFAULT 0,
  `requiere_refrigeracion` TINYINT(1)  NOT NULL DEFAULT 0,
  `activo`                TINYINT(1)   NOT NULL DEFAULT 1,
  `created_at`            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_medicamentos_nombre` (`nombre`),
  KEY `idx_medicamentos_activo` (`activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `inventario_lotes` (
  `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `medicamento_id`      INT UNSIGNED    NOT NULL,
  `codigo_lote`         VARCHAR(60)     NOT NULL,
  `cantidad_inicial`    INT UNSIGNED    NOT NULL DEFAULT 0,
  `cantidad_disponible` INT UNSIGNED    NOT NULL DEFAULT 0,
  `fecha_caducidad`     DATE            NULL,
  `fecha_ingreso`       DATE            NOT NULL,
  `proveedor`           VARCHAR(120)    NULL,
  `costo_unitario`      DECIMAL(10,2)   NULL,
  `created_at`          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lote_medicamento` (`medicamento_id`, `codigo_lote`),
  KEY `idx_lotes_caducidad` (`fecha_caducidad`),
  KEY `idx_lotes_medicamento` (`medicamento_id`),
  CONSTRAINT `fk_lotes_medicamento`
    FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tratamientos` (
  `id`                BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  `paciente_id`       INT UNSIGNED     NOT NULL,
  `medicamento_id`    INT UNSIGNED     NOT NULL,
  `dosis`             DECIMAL(8,2)     NOT NULL,
  `unidad_dosis`      VARCHAR(20)      NOT NULL DEFAULT 'mg',
  `via_administracion` ENUM('oral','venosa','intramuscular','subcutanea','topica','rectal','inhalatoria','sublingual','otra') NOT NULL DEFAULT 'oral',
  `frecuencia_horas`  SMALLINT UNSIGNED NULL,
  `fecha_inicio`      DATETIME         NOT NULL,
  `fecha_fin`         DATETIME         NULL,
  `prescrito_por`     VARCHAR(120)     NULL,
  `indicaciones`      TEXT             NULL,
  `estado`            ENUM('activo','suspendido','finalizado') NOT NULL DEFAULT 'activo',
  `created_at`        TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tratamientos_paciente_estado` (`paciente_id`, `estado`),
  KEY `idx_tratamientos_medicamento` (`medicamento_id`),
  KEY `idx_tratamientos_fechas` (`fecha_inicio`, `fecha_fin`),
  CONSTRAINT `fk_tratamientos_paciente`
    FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_tratamientos_medicamento`
    FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `chk_tratamientos_dosis` CHECK (`dosis` > 0),
  CONSTRAINT `chk_tratamientos_frecuencia`
    CHECK (`frecuencia_horas` IS NULL OR `frecuencia_horas` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tratamiento_horarios` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tratamiento_id` BIGINT UNSIGNED NOT NULL,
  `hora`           TIME            NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_horario_tratamiento` (`tratamiento_id`, `hora`),
  CONSTRAINT `fk_horarios_tratamiento`
    FOREIGN KEY (`tratamiento_id`) REFERENCES `tratamientos` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `administraciones_medicamento` (
  `id`                BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  `tratamiento_id`    BIGINT UNSIGNED  NOT NULL,
  `horario_id`        BIGINT UNSIGNED  NULL,
  `lote_id`           BIGINT UNSIGNED  NULL,
  `personal_id`       INT UNSIGNED     NULL,
  `fecha_hora`        DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `dosis_aplicada`    DECIMAL(8,2)     NOT NULL,
  `via_administracion` ENUM('oral','venosa','intramuscular','subcutanea','topica','rectal','inhalatoria','sublingual','otra') NOT NULL,
  `estado`            ENUM('administrado','omitido','retrasado') NOT NULL DEFAULT 'administrado',
  `observaciones`     VARCHAR(255)     NULL,
  `created_at`        TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_admin_tratamiento` (`tratamiento_id`, `fecha_hora`),
  KEY `idx_admin_fecha` (`fecha_hora`),
  KEY `idx_admin_personal` (`personal_id`),
  CONSTRAINT `fk_admin_tratamiento`
    FOREIGN KEY (`tratamiento_id`) REFERENCES `tratamientos` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_admin_horario`
    FOREIGN KEY (`horario_id`) REFERENCES `tratamiento_horarios` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_admin_lote`
    FOREIGN KEY (`lote_id`) REFERENCES `inventario_lotes` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_admin_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `chk_admin_dosis` CHECK (`dosis_aplicada` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `movimientos_inventario` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `lote_id`     BIGINT UNSIGNED NOT NULL,
  `tipo`        ENUM('entrada','salida','ajuste','caducidad','devolucion') NOT NULL,
  `cantidad`    INT UNSIGNED    NOT NULL,
  `motivo`      VARCHAR(200)    NULL,
  `personal_id` INT UNSIGNED    NULL,
  `fecha_hora`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at`  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_movimientos_lote` (`lote_id`),
  KEY `idx_movimientos_fecha` (`fecha_hora`),
  KEY `idx_movimientos_tipo` (`tipo`),
  CONSTRAINT `fk_movimientos_lote`
    FOREIGN KEY (`lote_id`) REFERENCES `inventario_lotes` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_movimientos_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `chk_movimientos_cantidad` CHECK (`cantidad` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 4. CONTROL DIARIO
-- ------------------------------------------------------------

CREATE TABLE `signos_vitales` (
  `id`                     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `paciente_id`            INT UNSIGNED    NOT NULL,
  `personal_id`            INT UNSIGNED    NULL,
  `fecha_hora`             DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `presion_sistolica`      SMALLINT UNSIGNED NULL,
  `presion_diastolica`     SMALLINT UNSIGNED NULL,
  `bpm`                    SMALLINT UNSIGNED NULL,
  `saturacion_o2`          TINYINT UNSIGNED NULL,
  `frecuencia_respiratoria` TINYINT UNSIGNED NULL,
  `temperatura`            DECIMAL(4,1)    NULL,
  `observaciones`          VARCHAR(255)    NULL,
  `created_at`             TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_signos_paciente_fecha` (`paciente_id`, `fecha_hora`),
  KEY `idx_signos_fecha` (`fecha_hora`),
  KEY `idx_signos_personal` (`personal_id`),
  CONSTRAINT `fk_signos_paciente`
    FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_signos_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `chk_signos_sistolica`
    CHECK (`presion_sistolica` IS NULL OR `presion_sistolica` BETWEEN 40 AND 300),
  CONSTRAINT `chk_signos_diastolica`
    CHECK (`presion_diastolica` IS NULL OR `presion_diastolica` BETWEEN 20 AND 200),
  CONSTRAINT `chk_signos_bpm`
    CHECK (`bpm` IS NULL OR `bpm` BETWEEN 20 AND 300),
  CONSTRAINT `chk_signos_saturacion`
    CHECK (`saturacion_o2` IS NULL OR `saturacion_o2` <= 100),
  CONSTRAINT `chk_signos_respiracion`
    CHECK (`frecuencia_respiratoria` IS NULL OR `frecuencia_respiratoria` BETWEEN 4 AND 80),
  CONSTRAINT `chk_signos_temperatura`
    CHECK (`temperatura` IS NULL OR `temperatura` BETWEEN 30.0 AND 45.0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dxtx` (
  `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `paciente_id`       INT UNSIGNED    NOT NULL,
  `personal_id`       INT UNSIGNED    NULL,
  `fecha_hora`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `valor_mg_dl`       SMALLINT UNSIGNED NOT NULL,
  `tipo`              ENUM('ayunas','postprandial','aleatoria','correccion') NOT NULL DEFAULT 'aleatoria',
  `insulina_aplicada` DECIMAL(6,2)    NOT NULL DEFAULT 0.00,
  `observaciones`     VARCHAR(255)    NULL,
  `created_at`        TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_dxtx_paciente_fecha` (`paciente_id`, `fecha_hora`),
  KEY `idx_dxtx_fecha` (`fecha_hora`),
  KEY `idx_dxtx_personal` (`personal_id`),
  CONSTRAINT `fk_dxtx_paciente`
    FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_dxtx_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `control_panales` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `paciente_id`   INT UNSIGNED    NOT NULL,
  `personal_id`   INT UNSIGNED    NULL,
  `fecha_hora`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `tipo`          ENUM('orina','heces','mixto','seco') NOT NULL,
  `observaciones` VARCHAR(255)    NULL,
  `created_at`    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_panales_paciente_fecha` (`paciente_id`, `fecha_hora`),
  KEY `idx_panales_fecha` (`fecha_hora`),
  KEY `idx_panales_personal` (`personal_id`),
  CONSTRAINT `fk_panales_paciente`
    FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_panales_personal`
    FOREIGN KEY (`personal_id`) REFERENCES `personal` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 5. DATOS INICIALES
--
-- No se crean usuarios con contraseñas conocidas en el esquema.
-- Después de importar este archivo ejecuta:
--
--   python scripts/seed_system.py --apply
--
-- El seeder crea admin, medico, enfermero y administrativo con
-- contraseñas aleatorias (o las indicadas por CLI/entorno) y hashes
-- PBKDF2-SHA256.
-- ------------------------------------------------------------

INSERT IGNORE INTO `roles` (`nombre`, `descripcion`) VALUES
  ('admin',          'Administración general del sistema'),
  ('medico',         'Valoración y prescripción médica'),
  ('enfermeria',     'Cuidados y registro de signos vitales'),
  ('administrativo', 'Inventario, personal y gestión administrativa'),
  ('farmacia',       'Gestión de inventario y surtido'),
  ('recepcion',      'Atención a familiares y admisión');

-- Matriz de permisos inicial. '*' = acceso total.
INSERT IGNORE INTO `rol_permisos` (`rol_id`, `permiso`)
SELECT r.`id`, p.`permiso`
FROM `roles` r
JOIN (
            SELECT 'admin' AS rol, '*' AS permiso
  UNION ALL SELECT 'medico', 'dashboard:leer'
  UNION ALL SELECT 'medico', 'pacientes:leer'
  UNION ALL SELECT 'medico', 'personal:leer'
  UNION ALL SELECT 'medico', 'inventario:leer'
  UNION ALL SELECT 'medico', 'tratamientos:leer'
  UNION ALL SELECT 'medico', 'tratamientos:escribir'
  UNION ALL SELECT 'medico', 'control:leer'
  UNION ALL SELECT 'medico', 'administracion:escribir'

  UNION ALL SELECT 'enfermeria', 'dashboard:leer'
  UNION ALL SELECT 'enfermeria', 'pacientes:leer'
  UNION ALL SELECT 'enfermeria', 'inventario:leer'
  UNION ALL SELECT 'enfermeria', 'tratamientos:leer'
  UNION ALL SELECT 'enfermeria', 'control:leer'
  UNION ALL SELECT 'enfermeria', 'control:escribir'
  UNION ALL SELECT 'enfermeria', 'administracion:escribir'

  UNION ALL SELECT 'administrativo', 'dashboard:leer'
  UNION ALL SELECT 'administrativo', 'pacientes:leer'
  UNION ALL SELECT 'administrativo', 'personal:leer'
  UNION ALL SELECT 'administrativo', 'personal:escribir'
  UNION ALL SELECT 'administrativo', 'inventario:leer'
  UNION ALL SELECT 'administrativo', 'inventario:escribir'

  UNION ALL SELECT 'farmacia', 'dashboard:leer'
  UNION ALL SELECT 'farmacia', 'pacientes:leer'
  UNION ALL SELECT 'farmacia', 'inventario:leer'
  UNION ALL SELECT 'farmacia', 'inventario:escribir'
  UNION ALL SELECT 'farmacia', 'tratamientos:leer'

  UNION ALL SELECT 'recepcion', 'dashboard:leer'
  UNION ALL SELECT 'recepcion', 'pacientes:leer'
  UNION ALL SELECT 'recepcion', 'personal:leer'
) p ON p.`rol` = r.`nombre`;
