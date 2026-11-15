-- ============================================================
-- HAYDEÉN SISTEMA · DATOS DE DEMOSTRACIÓN
-- Ejecutar después de database/schema.sql
--
-- Este archivo es idempotente: puede ejecutarse varias veces sin
-- duplicar personas, pacientes, lotes, horarios ni registros diarios.
-- ============================================================

USE `haydeensistem`;
SET NAMES utf8mb4;

START TRANSACTION;

-- ------------------------------------------------------------
-- 1. PERSONAL Y TURNOS
-- ------------------------------------------------------------

INSERT IGNORE INTO `personal`
  (`nombre`, `apellidos`, `documento`, `fecha_nacimiento`, `telefono`, `email`,
   `rol_id`, `estado`, `fecha_ingreso`, `notas`)
SELECT 'Elena', 'Ríos Vargas', 'MED-001', '1981-04-12', '555-0101',
       'elena.rios@haydeen.local', `id`, 'activo', '2023-02-15',
       'Médica de guardia'
FROM `roles` WHERE `nombre` = 'medico';

INSERT IGNORE INTO `personal`
  (`nombre`, `apellidos`, `documento`, `fecha_nacimiento`, `telefono`, `email`,
   `rol_id`, `estado`, `fecha_ingreso`, `notas`)
SELECT 'Carlos', 'Méndez Salas', 'ENF-001', '1990-09-23', '555-0102',
       'carlos.mendez@haydeen.local', `id`, 'activo', '2024-01-08',
       'Enfermero del turno matutino'
FROM `roles` WHERE `nombre` = 'enfermeria';

INSERT IGNORE INTO `personal`
  (`nombre`, `apellidos`, `documento`, `fecha_nacimiento`, `telefono`, `email`,
   `rol_id`, `estado`, `fecha_ingreso`, `notas`)
SELECT 'Lucía', 'Torres Paredes', 'ENF-002', '1994-11-05', '555-0103',
       'lucia.torres@haydeen.local', `id`, 'libre', '2024-06-17',
       'Enfermera del turno vespertino'
FROM `roles` WHERE `nombre` = 'enfermeria';

INSERT IGNORE INTO `personal`
  (`nombre`, `apellidos`, `documento`, `fecha_nacimiento`, `telefono`, `email`,
   `rol_id`, `estado`, `fecha_ingreso`, `notas`)
SELECT 'Marta', 'Gómez Rivas', 'FAR-001', '1986-07-30', '555-0104',
       'marta.gomez@haydeen.local', `id`, 'activo', '2023-10-02',
       'Responsable de farmacia e inventario'
FROM `roles` WHERE `nombre` = 'farmacia';

INSERT IGNORE INTO `personal`
  (`nombre`, `apellidos`, `documento`, `fecha_nacimiento`, `telefono`, `email`,
   `rol_id`, `estado`, `fecha_ingreso`, `notas`)
SELECT 'José', 'Paredes Luna', 'REC-001', '1988-01-19', '555-0105',
       'jose.paredes@haydeen.local', `id`, 'activo', '2024-03-11',
       'Recepción y atención a familiares'
FROM `roles` WHERE `nombre` = 'recepcion';

SET @pers_elena   = (SELECT `id` FROM `personal` WHERE `documento` = 'MED-001' LIMIT 1);
SET @pers_carlos  = (SELECT `id` FROM `personal` WHERE `documento` = 'ENF-001' LIMIT 1);
SET @pers_lucia   = (SELECT `id` FROM `personal` WHERE `documento` = 'ENF-002' LIMIT 1);
SET @pers_marta   = (SELECT `id` FROM `personal` WHERE `documento` = 'FAR-001' LIMIT 1);
SET @pers_jose    = (SELECT `id` FROM `personal` WHERE `documento` = 'REC-001' LIMIT 1);

INSERT IGNORE INTO `turnos`
  (`personal_id`, `fecha`, `hora_inicio`, `hora_fin`, `tipo`, `estado`, `notas`)
VALUES
  (@pers_carlos, CURDATE(), '07:00:00', '15:00:00', 'matutino',  'en_curso',   'Turno en curso'),
  (@pers_lucia,  CURDATE(), '15:00:00', '23:00:00', 'vespertino', 'programado', 'Cubre medicación de la tarde'),
  (@pers_elena,  CURDATE(), '08:00:00', '20:00:00', 'guardia',    'programado', 'Guardia médica diurna'),
  (@pers_marta,  CURDATE(), '08:00:00', '16:00:00', 'matutino',   'finalizado', 'Surtido de farmacia'),
  (@pers_jose,   CURDATE(), '08:00:00', '16:00:00', 'matutino',   'finalizado', 'Recepción');

-- ------------------------------------------------------------
-- 2. PACIENTES
-- ------------------------------------------------------------

INSERT IGNORE INTO `pacientes`
  (`nombre`, `apellidos`, `documento`, `fecha_nacimiento`, `sexo`,
   `tipo_residencia`, `habitacion`, `cama`, `contacto_familiar`,
   `telefono_contacto`, `alergias`, `diagnostico`, `peso_kg`, `talla_m`,
   `estado`, `fecha_ingreso`)
VALUES
  ('Rosa', 'Martínez López', 'PAC-001', '1942-06-18', 'femenino',
   'residenciado', '101', 'A', 'Ana Martínez', '555-0201', 'Penicilina',
   'Hipertensión arterial y diabetes mellitus tipo 2', 62.50, 1.58,
   'activo', '2025-01-10'),
  ('Manuel', 'Ortega Díaz', 'PAC-002', '1947-02-09', 'masculino',
   'residenciado', '102', 'B', 'Luis Ortega', '555-0202', 'Ninguna',
   'EPOC y limitación funcional', 70.20, 1.70,
   'activo', '2025-03-22'),
  ('Carmen', 'Silva Núñez', 'PAC-003', '1938-10-27', 'femenino',
   'ambulatorio', NULL, NULL, 'María Silva', '555-0203', 'AINEs',
   'Artrosis y control periódico de presión arterial', 55.00, 1.52,
   'activo', '2026-02-14'),
  ('Jorge', 'Ramírez Soto', 'PAC-004', '1950-12-03', 'masculino',
   'ambulatorio', NULL, NULL, 'Paula Ramírez', '555-0204', 'Ninguna',
   'Diabetes mellitus tipo 2 e insulina basal', 80.00, 1.75,
   'activo', '2026-04-05');

SET @pac_rosa    = (SELECT `id` FROM `pacientes` WHERE `documento` = 'PAC-001' LIMIT 1);
SET @pac_manuel  = (SELECT `id` FROM `pacientes` WHERE `documento` = 'PAC-002' LIMIT 1);
SET @pac_carmen  = (SELECT `id` FROM `pacientes` WHERE `documento` = 'PAC-003' LIMIT 1);
SET @pac_jorge   = (SELECT `id` FROM `pacientes` WHERE `documento` = 'PAC-004' LIMIT 1);

-- ------------------------------------------------------------
-- 3. MEDICAMENTOS Y LOTES DE INVENTARIO
-- ------------------------------------------------------------

INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Losartán', 'Losartán potásico', 'Tableta', '50 mg', 'mg', 20, 0, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Losartán' AND `concentracion` = '50 mg'
);

INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Metformina', 'Metformina clorhidrato', 'Tableta', '850 mg', 'mg', 30, 0, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Metformina' AND `concentracion` = '850 mg'
);

INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Insulina glargina', 'Insulina glargina', 'Pluma inyectable', '100 UI/ml', 'UI', 5, 1, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Insulina glargina' AND `concentracion` = '100 UI/ml'
);

INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Salbutamol', 'Salbutamol', 'Inhalador', '100 mcg/dosis', 'mcg', 3, 0, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Salbutamol' AND `concentracion` = '100 mcg/dosis'
);

INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Paracetamol', 'Paracetamol', 'Tableta', '500 mg', 'mg', 25, 0, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Paracetamol' AND `concentracion` = '500 mg'
);

INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Omeprazol', 'Omeprazol', 'Cápsula', '20 mg', 'mg', 15, 0, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Omeprazol' AND `concentracion` = '20 mg'
);

-- Medicamento con stock por debajo del mínimo para demostrar la alerta.
INSERT INTO `medicamentos`
  (`nombre`, `principio_activo`, `presentacion`, `concentracion`, `unidad`,
   `stock_minimo`, `requiere_refrigeracion`, `activo`)
SELECT 'Amoxicilina', 'Amoxicilina trihidrato', 'Cápsula', '500 mg', 'mg', 20, 0, 1
WHERE NOT EXISTS (
  SELECT 1 FROM `medicamentos` WHERE `nombre` = 'Amoxicilina' AND `concentracion` = '500 mg'
);

SET @med_losartan   = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Losartán' AND `concentracion` = '50 mg' LIMIT 1);
SET @med_metformina = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Metformina' AND `concentracion` = '850 mg' LIMIT 1);
SET @med_insulina   = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Insulina glargina' AND `concentracion` = '100 UI/ml' LIMIT 1);
SET @med_salbutamol = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Salbutamol' AND `concentracion` = '100 mcg/dosis' LIMIT 1);
SET @med_paracetamol = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Paracetamol' AND `concentracion` = '500 mg' LIMIT 1);
SET @med_omeprazol  = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Omeprazol' AND `concentracion` = '20 mg' LIMIT 1);
SET @med_amoxicilina = (SELECT `id` FROM `medicamentos` WHERE `nombre` = 'Amoxicilina' AND `concentracion` = '500 mg' LIMIT 1);

INSERT IGNORE INTO `inventario_lotes`
  (`medicamento_id`, `codigo_lote`, `cantidad_inicial`, `cantidad_disponible`,
   `fecha_caducidad`, `fecha_ingreso`, `proveedor`, `costo_unitario`)
VALUES
  (@med_losartan,    'L-2026-001', 120, 110, '2027-06-30', '2026-10-01', 'Farmacéutica Central', 0.85),
  (@med_metformina,  'M-2026-014', 200, 180, '2027-08-31', '2026-10-03', 'Farmacéutica Central', 0.42),
  (@med_insulina,    'I-2026-003',  20,  18, '2027-03-31', '2026-10-05', 'Distribuidora Médica', 12.50),
  (@med_salbutamol,  'S-2026-007',  15,  14, '2028-01-31', '2026-10-08', 'Distribuidora Médica', 8.90),
  (@med_paracetamol, 'P-2026-021', 300, 260, '2027-12-31', '2026-10-10', 'Farmacéutica Central', 0.18),
  (@med_omeprazol,   'O-2026-005', 100,  95, '2027-05-31', '2026-10-12', 'Farmacéutica Central', 0.33),
  (@med_amoxicilina, 'A-2026-002',  10,   8, '2027-02-28', '2026-10-15', 'Distribuidora Médica', 0.55);

SET @lote_losartan    = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_losartan AND `codigo_lote` = 'L-2026-001' LIMIT 1);
SET @lote_metformina  = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_metformina AND `codigo_lote` = 'M-2026-014' LIMIT 1);
SET @lote_insulina    = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_insulina AND `codigo_lote` = 'I-2026-003' LIMIT 1);
SET @lote_salbutamol  = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_salbutamol AND `codigo_lote` = 'S-2026-007' LIMIT 1);
SET @lote_paracetamol = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_paracetamol AND `codigo_lote` = 'P-2026-021' LIMIT 1);
SET @lote_omeprazol   = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_omeprazol AND `codigo_lote` = 'O-2026-005' LIMIT 1);
SET @lote_amoxicilina = (SELECT `id` FROM `inventario_lotes` WHERE `medicamento_id` = @med_amoxicilina AND `codigo_lote` = 'A-2026-002' LIMIT 1);

-- Movimientos que explican la diferencia entre cantidad inicial y disponible.
INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_losartan, 'entrada', 120, 'Compra inicial de lote', @pers_marta, '2026-10-01 09:00:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_losartan AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-01 09:00:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_losartan, 'salida', 10, 'Surtido a pacientes', @pers_marta, '2026-11-09 18:00:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_losartan AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 18:00:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_metformina, 'entrada', 200, 'Compra inicial de lote', @pers_marta, '2026-10-03 09:10:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_metformina AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-03 09:10:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_metformina, 'salida', 20, 'Surtido a pacientes', @pers_marta, '2026-11-09 18:10:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_metformina AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 18:10:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_insulina, 'entrada', 20, 'Compra inicial de lote refrigerado', @pers_marta, '2026-10-05 09:20:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_insulina AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-05 09:20:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_insulina, 'salida', 2, 'Surtido a pacientes', @pers_marta, '2026-11-09 18:20:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_insulina AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 18:20:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_salbutamol, 'entrada', 15, 'Compra inicial de lote', @pers_marta, '2026-10-08 09:30:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_salbutamol AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-08 09:30:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_salbutamol, 'salida', 1, 'Surtido a pacientes', @pers_marta, '2026-11-09 18:30:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_salbutamol AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 18:30:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_paracetamol, 'entrada', 300, 'Compra inicial de lote', @pers_marta, '2026-10-10 09:40:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_paracetamol AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-10 09:40:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_paracetamol, 'salida', 40, 'Surtido a pacientes', @pers_marta, '2026-11-09 18:40:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_paracetamol AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 18:40:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_omeprazol, 'entrada', 100, 'Compra inicial de lote', @pers_marta, '2026-10-12 09:50:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_omeprazol AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-12 09:50:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_omeprazol, 'salida', 5, 'Surtido a pacientes', @pers_marta, '2026-11-09 18:50:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_omeprazol AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 18:50:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_amoxicilina, 'entrada', 10, 'Compra inicial de lote', @pers_marta, '2026-10-15 10:00:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_amoxicilina AND `tipo` = 'entrada' AND `fecha_hora` = '2026-10-15 10:00:00'
);

INSERT INTO `movimientos_inventario`
  (`lote_id`, `tipo`, `cantidad`, `motivo`, `personal_id`, `fecha_hora`)
SELECT @lote_amoxicilina, 'salida', 2, 'Surtido a pacientes', @pers_marta, '2026-11-09 19:00:00'
WHERE NOT EXISTS (
  SELECT 1 FROM `movimientos_inventario`
  WHERE `lote_id` = @lote_amoxicilina AND `tipo` = 'salida' AND `fecha_hora` = '2026-11-09 19:00:00'
);

-- ------------------------------------------------------------
-- 4. TRATAMIENTOS ASIGNADOS A PACIENTES
-- ------------------------------------------------------------

INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_rosa, @med_losartan, 50.00, 'mg', 'oral', 24,
       '2026-11-01 08:00:00', NULL, 'Dra. Elena Ríos',
       'Control de presión arterial', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_rosa AND `medicamento_id` = @med_losartan
    AND `fecha_inicio` = '2026-11-01 08:00:00'
);

INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_rosa, @med_metformina, 850.00, 'mg', 'oral', 12,
       '2026-11-01 08:00:00', NULL, 'Dra. Elena Ríos',
       'Control glucémico', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_rosa AND `medicamento_id` = @med_metformina
    AND `fecha_inicio` = '2026-11-01 08:00:00'
);

INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_manuel, @med_salbutamol, 100.00, 'mcg', 'inhalatoria', 8,
       '2026-11-05 06:00:00', NULL, 'Dra. Elena Ríos',
       'Broncodilatador de rescate y mantenimiento', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_manuel AND `medicamento_id` = @med_salbutamol
    AND `fecha_inicio` = '2026-11-05 06:00:00'
);

INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_carmen, @med_omeprazol, 20.00, 'mg', 'oral', 24,
       '2026-11-03 07:00:00', NULL, 'Dra. Elena Ríos',
       'Protección gástrica', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_carmen AND `medicamento_id` = @med_omeprazol
    AND `fecha_inicio` = '2026-11-03 07:00:00'
);

INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_jorge, @med_insulina, 10.00, 'UI', 'subcutanea', 24,
       '2026-11-04 21:00:00', NULL, 'Dra. Elena Ríos',
       'Insulina basal nocturna', 'activo'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_jorge AND `medicamento_id` = @med_insulina
    AND `fecha_inicio` = '2026-11-04 21:00:00'
);

-- Tratamiento finalizado: conserva su historial y sus horarios.
INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_manuel, @med_paracetamol, 500.00, 'mg', 'oral', 8,
       '2026-10-20 08:00:00', '2026-11-02 20:00:00', 'Dra. Elena Ríos',
       'Analgesia por dolor lumbar', 'finalizado'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_manuel AND `medicamento_id` = @med_paracetamol
    AND `fecha_inicio` = '2026-10-20 08:00:00'
);

-- Tratamiento suspendido: sirve para diferenciar estados clínicos.
INSERT INTO `tratamientos`
  (`paciente_id`, `medicamento_id`, `dosis`, `unidad_dosis`, `via_administracion`,
   `frecuencia_horas`, `fecha_inicio`, `fecha_fin`, `prescrito_por`,
   `indicaciones`, `estado`)
SELECT @pac_manuel, @med_amoxicilina, 500.00, 'mg', 'oral', 12,
       '2026-11-06 08:00:00', NULL, 'Dra. Elena Ríos',
       'Infección respiratoria; suspendido por mejoría clínica', 'suspendido'
WHERE NOT EXISTS (
  SELECT 1 FROM `tratamientos`
  WHERE `paciente_id` = @pac_manuel AND `medicamento_id` = @med_amoxicilina
    AND `fecha_inicio` = '2026-11-06 08:00:00'
);

SET @trat_rosa_losartan   = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_rosa AND `medicamento_id` = @med_losartan AND `fecha_inicio` = '2026-11-01 08:00:00' LIMIT 1);
SET @trat_rosa_metformina = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_rosa AND `medicamento_id` = @med_metformina AND `fecha_inicio` = '2026-11-01 08:00:00' LIMIT 1);
SET @trat_manuel_salbutamol = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_manuel AND `medicamento_id` = @med_salbutamol AND `fecha_inicio` = '2026-11-05 06:00:00' LIMIT 1);
SET @trat_carmen_omeprazol = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_carmen AND `medicamento_id` = @med_omeprazol AND `fecha_inicio` = '2026-11-03 07:00:00' LIMIT 1);
SET @trat_jorge_insulina   = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_jorge AND `medicamento_id` = @med_insulina AND `fecha_inicio` = '2026-11-04 21:00:00' LIMIT 1);
SET @trat_manuel_paracetamol = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_manuel AND `medicamento_id` = @med_paracetamol AND `fecha_inicio` = '2026-10-20 08:00:00' LIMIT 1);
SET @trat_manuel_amoxicilina = (SELECT `id` FROM `tratamientos` WHERE `paciente_id` = @pac_manuel AND `medicamento_id` = @med_amoxicilina AND `fecha_inicio` = '2026-11-06 08:00:00' LIMIT 1);

-- Horarios normalizados por tratamiento.
INSERT IGNORE INTO `tratamiento_horarios` (`tratamiento_id`, `hora`) VALUES
  (@trat_rosa_losartan,       '08:00:00'),
  (@trat_rosa_metformina,     '08:00:00'),
  (@trat_rosa_metformina,     '20:00:00'),
  (@trat_manuel_salbutamol,   '06:00:00'),
  (@trat_manuel_salbutamol,   '14:00:00'),
  (@trat_manuel_salbutamol,   '22:00:00'),
  (@trat_carmen_omeprazol,    '07:00:00'),
  (@trat_jorge_insulina,      '21:00:00'),
  (@trat_manuel_paracetamol,  '08:00:00'),
  (@trat_manuel_paracetamol,  '14:00:00'),
  (@trat_manuel_paracetamol,  '20:00:00'),
  (@trat_manuel_amoxicilina,  '08:00:00'),
  (@trat_manuel_amoxicilina,  '20:00:00');

SET @hor_rosa_losartan_08   = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_rosa_losartan AND `hora` = '08:00:00' LIMIT 1);
SET @hor_rosa_metformina_08 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_rosa_metformina AND `hora` = '08:00:00' LIMIT 1);
SET @hor_rosa_metformina_20 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_rosa_metformina AND `hora` = '20:00:00' LIMIT 1);
SET @hor_manuel_salbutamol_06 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_manuel_salbutamol AND `hora` = '06:00:00' LIMIT 1);
SET @hor_manuel_salbutamol_14 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_manuel_salbutamol AND `hora` = '14:00:00' LIMIT 1);
SET @hor_manuel_salbutamol_22 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_manuel_salbutamol AND `hora` = '22:00:00' LIMIT 1);
SET @hor_carmen_omeprazol_07 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_carmen_omeprazol AND `hora` = '07:00:00' LIMIT 1);
SET @hor_jorge_insulina_21 = (SELECT `id` FROM `tratamiento_horarios` WHERE `tratamiento_id` = @trat_jorge_insulina AND `hora` = '21:00:00' LIMIT 1);

-- ------------------------------------------------------------
-- 5. ADMINISTRACIONES: QUIÉN, A QUIÉN, QUÉ LOTE Y EN QUÉ HORARIO
-- ------------------------------------------------------------

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_rosa_losartan, @hor_rosa_losartan_08, @lote_losartan, @pers_carlos,
       TIMESTAMP(CURDATE(), '08:05:00'), 50.00, 'oral', 'administrado', 'Sin incidencias'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_rosa_losartan
    AND `horario_id` = @hor_rosa_losartan_08
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_rosa_metformina, @hor_rosa_metformina_08, @lote_metformina, @pers_carlos,
       TIMESTAMP(CURDATE(), '08:10:00'), 850.00, 'oral', 'administrado', 'Administrada con desayuno'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_rosa_metformina
    AND `horario_id` = @hor_rosa_metformina_08
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_rosa_metformina, @hor_rosa_metformina_20, NULL, @pers_lucia,
       TIMESTAMP(CURDATE(), '20:00:00'), 0.00, 'oral', 'omitido', 'Paciente rechaza por náuseas'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_rosa_metformina
    AND `horario_id` = @hor_rosa_metformina_20
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_manuel_salbutamol, @hor_manuel_salbutamol_06, @lote_salbutamol, @pers_carlos,
       TIMESTAMP(CURDATE(), '06:05:00'), 100.00, 'inhalatoria', 'administrado', 'Buena respuesta'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_manuel_salbutamol
    AND `horario_id` = @hor_manuel_salbutamol_06
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_manuel_salbutamol, @hor_manuel_salbutamol_14, @lote_salbutamol, @pers_carlos,
       TIMESTAMP(CURDATE(), '14:30:00'), 100.00, 'inhalatoria', 'retrasado', 'Administrado 30 min después por terapia'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_manuel_salbutamol
    AND `horario_id` = @hor_manuel_salbutamol_14
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_manuel_salbutamol, @hor_manuel_salbutamol_22, @lote_salbutamol, @pers_lucia,
       TIMESTAMP(CURDATE(), '22:00:00'), 100.00, 'inhalatoria', 'administrado', 'Turno vespertino'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_manuel_salbutamol
    AND `horario_id` = @hor_manuel_salbutamol_22
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_carmen_omeprazol, @hor_carmen_omeprazol_07, @lote_omeprazol, @pers_carlos,
       TIMESTAMP(CURDATE(), '07:05:00'), 20.00, 'oral', 'administrado', 'Paciente ambulatorio'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_carmen_omeprazol
    AND `horario_id` = @hor_carmen_omeprazol_07
    AND DATE(`fecha_hora`) = CURDATE()
);

INSERT INTO `administraciones_medicamento`
  (`tratamiento_id`, `horario_id`, `lote_id`, `personal_id`, `fecha_hora`,
   `dosis_aplicada`, `via_administracion`, `estado`, `observaciones`)
SELECT @trat_jorge_insulina, @hor_jorge_insulina_21, @lote_insulina, @pers_lucia,
       TIMESTAMP(CURDATE(), '21:05:00'), 10.00, 'subcutanea', 'administrado', 'Insulina basal'
WHERE NOT EXISTS (
  SELECT 1 FROM `administraciones_medicamento`
  WHERE `tratamiento_id` = @trat_jorge_insulina
    AND `horario_id` = @hor_jorge_insulina_21
    AND DATE(`fecha_hora`) = CURDATE()
);

-- ------------------------------------------------------------
-- 6. CONTROL DIARIO: SIGNOS VITALES, DXTX Y PAÑALES
-- ------------------------------------------------------------

INSERT INTO `signos_vitales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `presion_sistolica`,
   `presion_diastolica`, `bpm`, `saturacion_o2`, `frecuencia_respiratoria`,
   `temperatura`, `observaciones`)
SELECT @pac_rosa, @pers_carlos, TIMESTAMP(CURDATE(), '08:15:00'), 130, 85, 78, 96, 18, 36.6,
       'Sin novedades'
WHERE NOT EXISTS (
  SELECT 1 FROM `signos_vitales`
  WHERE `paciente_id` = @pac_rosa AND `fecha_hora` = TIMESTAMP(CURDATE(), '08:15:00')
);

INSERT INTO `signos_vitales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `presion_sistolica`,
   `presion_diastolica`, `bpm`, `saturacion_o2`, `frecuencia_respiratoria`,
   `temperatura`, `observaciones`)
SELECT @pac_rosa, @pers_lucia, TIMESTAMP(CURDATE() - INTERVAL 1 DAY, '20:00:00'), 140, 90, 82, 95, 19, 36.8,
       'Control nocturno'
WHERE NOT EXISTS (
  SELECT 1 FROM `signos_vitales`
  WHERE `paciente_id` = @pac_rosa AND `fecha_hora` = TIMESTAMP(CURDATE() - INTERVAL 1 DAY, '20:00:00')
);

INSERT INTO `signos_vitales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `presion_sistolica`,
   `presion_diastolica`, `bpm`, `saturacion_o2`, `frecuencia_respiratoria`,
   `temperatura`, `observaciones`)
SELECT @pac_manuel, @pers_carlos, TIMESTAMP(CURDATE(), '07:30:00'), 125, 80, 88, 92, 22, 37.0,
       'Disnea leve, requiere inhalador'
WHERE NOT EXISTS (
  SELECT 1 FROM `signos_vitales`
  WHERE `paciente_id` = @pac_manuel AND `fecha_hora` = TIMESTAMP(CURDATE(), '07:30:00')
);

INSERT INTO `signos_vitales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `presion_sistolica`,
   `presion_diastolica`, `bpm`, `saturacion_o2`, `frecuencia_respiratoria`,
   `temperatura`, `observaciones`)
SELECT @pac_carmen, @pers_carlos, TIMESTAMP(CURDATE(), '09:00:00'), 118, 76, 72, 98, 16, 36.5,
       'Control ambulatorio'
WHERE NOT EXISTS (
  SELECT 1 FROM `signos_vitales`
  WHERE `paciente_id` = @pac_carmen AND `fecha_hora` = TIMESTAMP(CURDATE(), '09:00:00')
);

INSERT INTO `signos_vitales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `presion_sistolica`,
   `presion_diastolica`, `bpm`, `saturacion_o2`, `frecuencia_respiratoria`,
   `temperatura`, `observaciones`)
SELECT @pac_jorge, @pers_carlos, TIMESTAMP(CURDATE(), '10:00:00'), 135, 88, 80, 97, 17, 36.7,
       'Control ambulatorio'
WHERE NOT EXISTS (
  SELECT 1 FROM `signos_vitales`
  WHERE `paciente_id` = @pac_jorge AND `fecha_hora` = TIMESTAMP(CURDATE(), '10:00:00')
);

INSERT INTO `dxtx`
  (`paciente_id`, `personal_id`, `fecha_hora`, `valor_mg_dl`, `tipo`,
   `insulina_aplicada`, `observaciones`)
SELECT @pac_rosa, @pers_carlos, TIMESTAMP(CURDATE(), '07:00:00'), 142, 'ayunas', 0.00,
       'Glucosa en ayunas'
WHERE NOT EXISTS (
  SELECT 1 FROM `dxtx`
  WHERE `paciente_id` = @pac_rosa AND `fecha_hora` = TIMESTAMP(CURDATE(), '07:00:00')
);

INSERT INTO `dxtx`
  (`paciente_id`, `personal_id`, `fecha_hora`, `valor_mg_dl`, `tipo`,
   `insulina_aplicada`, `observaciones`)
SELECT @pac_rosa, @pers_carlos, TIMESTAMP(CURDATE(), '13:00:00'), 186, 'postprandial', 0.00,
       'Después del almuerzo'
WHERE NOT EXISTS (
  SELECT 1 FROM `dxtx`
  WHERE `paciente_id` = @pac_rosa AND `fecha_hora` = TIMESTAMP(CURDATE(), '13:00:00')
);

INSERT INTO `dxtx`
  (`paciente_id`, `personal_id`, `fecha_hora`, `valor_mg_dl`, `tipo`,
   `insulina_aplicada`, `observaciones`)
SELECT @pac_manuel, @pers_carlos, TIMESTAMP(CURDATE(), '12:00:00'), 110, 'aleatoria', 0.00,
       'Control aleatorio'
WHERE NOT EXISTS (
  SELECT 1 FROM `dxtx`
  WHERE `paciente_id` = @pac_manuel AND `fecha_hora` = TIMESTAMP(CURDATE(), '12:00:00')
);

INSERT INTO `dxtx`
  (`paciente_id`, `personal_id`, `fecha_hora`, `valor_mg_dl`, `tipo`,
   `insulina_aplicada`, `observaciones`)
SELECT @pac_jorge, @pers_carlos, TIMESTAMP(CURDATE(), '07:30:00'), 165, 'ayunas', 0.00,
       'Glucosa en ayunas'
WHERE NOT EXISTS (
  SELECT 1 FROM `dxtx`
  WHERE `paciente_id` = @pac_jorge AND `fecha_hora` = TIMESTAMP(CURDATE(), '07:30:00')
);

INSERT INTO `dxtx`
  (`paciente_id`, `personal_id`, `fecha_hora`, `valor_mg_dl`, `tipo`,
   `insulina_aplicada`, `observaciones`)
SELECT @pac_jorge, @pers_lucia, TIMESTAMP(CURDATE(), '21:00:00'), 190, 'correccion', 4.00,
       'Corrección antes de insulina basal'
WHERE NOT EXISTS (
  SELECT 1 FROM `dxtx`
  WHERE `paciente_id` = @pac_jorge AND `fecha_hora` = TIMESTAMP(CURDATE(), '21:00:00')
);

INSERT INTO `control_panales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `tipo`, `observaciones`)
SELECT @pac_rosa, @pers_carlos, TIMESTAMP(CURDATE(), '08:30:00'), 'orina', 'Cambio sin incidencias'
WHERE NOT EXISTS (
  SELECT 1 FROM `control_panales`
  WHERE `paciente_id` = @pac_rosa AND `fecha_hora` = TIMESTAMP(CURDATE(), '08:30:00')
);

INSERT INTO `control_panales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `tipo`, `observaciones`)
SELECT @pac_rosa, @pers_carlos, TIMESTAMP(CURDATE(), '12:30:00'), 'mixto', 'Requiere aseo adicional'
WHERE NOT EXISTS (
  SELECT 1 FROM `control_panales`
  WHERE `paciente_id` = @pac_rosa AND `fecha_hora` = TIMESTAMP(CURDATE(), '12:30:00')
);

INSERT INTO `control_panales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `tipo`, `observaciones`)
SELECT @pac_manuel, @pers_carlos, TIMESTAMP(CURDATE(), '09:15:00'), 'heces', 'Sin incidencias'
WHERE NOT EXISTS (
  SELECT 1 FROM `control_panales`
  WHERE `paciente_id` = @pac_manuel AND `fecha_hora` = TIMESTAMP(CURDATE(), '09:15:00')
);

INSERT INTO `control_panales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `tipo`, `observaciones`)
SELECT @pac_carmen, @pers_carlos, TIMESTAMP(CURDATE(), '10:30:00'), 'seco', 'Paciente ambulatorio'
WHERE NOT EXISTS (
  SELECT 1 FROM `control_panales`
  WHERE `paciente_id` = @pac_carmen AND `fecha_hora` = TIMESTAMP(CURDATE(), '10:30:00')
);

INSERT INTO `control_panales`
  (`paciente_id`, `personal_id`, `fecha_hora`, `tipo`, `observaciones`)
SELECT @pac_jorge, @pers_carlos, TIMESTAMP(CURDATE(), '11:00:00'), 'orina', 'Sin incidencias'
WHERE NOT EXISTS (
  SELECT 1 FROM `control_panales`
  WHERE `paciente_id` = @pac_jorge AND `fecha_hora` = TIMESTAMP(CURDATE(), '11:00:00')
);

COMMIT;

-- ============================================================
-- 7. CONSULTAS PARA VER LAS RELACIONES Y ASIGNACIONES
-- ============================================================

-- ¿Qué tratamiento tiene asignado cada paciente?
SELECT
  CONCAT_WS(' ', p.`nombre`, p.`apellidos`) AS paciente,
  p.`tipo_residencia`,
  m.`nombre` AS medicamento,
  CONCAT(t.`dosis`, ' ', t.`unidad_dosis`) AS dosis,
  t.`via_administracion`,
  CONCAT(t.`frecuencia_horas`, ' h') AS frecuencia,
  t.`estado`,
  t.`prescrito_por`
FROM `tratamientos` t
JOIN `pacientes` p ON p.`id` = t.`paciente_id`
JOIN `medicamentos` m ON m.`id` = t.`medicamento_id`
ORDER BY p.`apellidos`, m.`nombre`;

-- ¿Quién administró, a qué paciente y con qué lote?
SELECT
  CONCAT_WS(' ', p.`nombre`, p.`apellidos`) AS paciente,
  m.`nombre` AS medicamento,
  a.`fecha_hora`,
  CONCAT(a.`dosis_aplicada`, ' ', t.`unidad_dosis`) AS dosis_aplicada,
  a.`via_administracion`,
  a.`estado`,
  CONCAT_WS(' ', per.`nombre`, per.`apellidos`) AS administrado_por,
  l.`codigo_lote`
FROM `administraciones_medicamento` a
JOIN `tratamientos` t ON t.`id` = a.`tratamiento_id`
JOIN `pacientes` p ON p.`id` = t.`paciente_id`
JOIN `medicamentos` m ON m.`id` = t.`medicamento_id`
LEFT JOIN `personal` per ON per.`id` = a.`personal_id`
LEFT JOIN `inventario_lotes` l ON l.`id` = a.`lote_id`
ORDER BY a.`fecha_hora` DESC;

-- Turnos del día con rol y estado del personal.
SELECT
  CONCAT_WS(' ', p.`nombre`, p.`apellidos`) AS personal,
  r.`nombre` AS rol,
  t.`hora_inicio`,
  t.`hora_fin`,
  t.`tipo`,
  t.`estado`
FROM `turnos` t
JOIN `personal` p ON p.`id` = t.`personal_id`
JOIN `roles` r ON r.`id` = p.`rol_id`
WHERE t.`fecha` = CURDATE()
ORDER BY t.`hora_inicio`;

-- Stock disponible y alerta por medicamento.
SELECT
  m.`nombre`,
  m.`concentracion`,
  m.`stock_minimo`,
  COALESCE(SUM(l.`cantidad_disponible`), 0) AS disponible,
  CASE
    WHEN COALESCE(SUM(l.`cantidad_disponible`), 0) < m.`stock_minimo` THEN 'BAJO'
    ELSE 'OK'
  END AS alerta
FROM `medicamentos` m
LEFT JOIN `inventario_lotes` l ON l.`medicamento_id` = m.`id`
WHERE m.`activo` = 1
GROUP BY m.`id`, m.`nombre`, m.`concentracion`, m.`stock_minimo`
ORDER BY m.`nombre`;

-- IMC calculado automáticamente por la base de datos.
SELECT
  `nombre`,
  `apellidos`,
  `peso_kg`,
  `talla_m`,
  `imc`
FROM `pacientes`
ORDER BY `apellidos`;

-- ============================================================
-- 8. EJEMPLOS DE ALTAS, BAJAS Y ACTUALIZACIONES
-- Los DELETE están comentados para no borrar la demostración.
-- ============================================================

-- Alta de un paciente nuevo:
-- INSERT INTO pacientes
--   (nombre, apellidos, documento, fecha_nacimiento, sexo, tipo_residencia,
--    peso_kg, talla_m, estado, fecha_ingreso)
-- VALUES
--   ('Nuevo', 'Paciente', 'PAC-005', '1945-01-01', 'masculino',
--    'ambulatorio', 68.00, 1.72, 'activo', CURDATE());

-- Baja lógica recomendada: conserva el historial clínico.
-- UPDATE pacientes SET estado = 'alta' WHERE documento = 'PAC-004';

-- Eliminar un turno: no tiene dependencias.
-- DELETE FROM turnos WHERE id = 1;

-- Eliminar un tratamiento con sus dependencias:
-- START TRANSACTION;
-- DELETE FROM administraciones_medicamento WHERE tratamiento_id = @trat_rosa_losartan;
-- DELETE FROM tratamiento_horarios WHERE tratamiento_id = @trat_rosa_losartan;
-- DELETE FROM tratamientos WHERE id = @trat_rosa_losartan;
-- COMMIT;

-- Un lote con movimientos o administraciones no debe borrarse:
-- DELETE FROM inventario_lotes WHERE id = @lote_losartan;  -- falla por FK
-- Forma correcta: dejar el lote en cero y desactivar el medicamento.
-- UPDATE inventario_lotes SET cantidad_disponible = 0 WHERE id = @lote_losartan;
-- UPDATE medicamentos SET activo = 0 WHERE id = @med_losartan;

-- Eliminar una sesión de usuario (no afecta al historial clínico).
-- DELETE FROM sesiones WHERE usuario_id = 1;

-- Cambiar la asignación de un tratamiento a otro paciente:
-- UPDATE tratamientos SET paciente_id = @pac_carmen WHERE id = @trat_rosa_losartan;

-- Suspender un tratamiento sin borrarlo:
-- UPDATE tratamientos SET estado = 'suspendido' WHERE id = @trat_rosa_losartan;
