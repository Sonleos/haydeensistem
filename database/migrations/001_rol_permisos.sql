-- ============================================================
-- Migración 001 · Permisos por rol
-- Idempotente. No elimina datos ni recrea tablas existentes.
--
-- Aplica esta migración sobre bases creadas antes de la
-- incorporación de `rol_permisos`.
-- ============================================================

USE `haydeensistem`;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `rol_permisos` (
  `rol_id`     TINYINT UNSIGNED NOT NULL,
  `permiso`    VARCHAR(60)      NOT NULL,
  `created_at` TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rol_id`, `permiso`),
  CONSTRAINT `fk_rol_permisos_rol`
    FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `roles` (`nombre`, `descripcion`) VALUES
  ('administrativo', 'Inventario, personal y gestión administrativa');

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
