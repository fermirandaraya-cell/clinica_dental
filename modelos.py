"""
Modelo de clases - Clínica Dental Sonrisas
==========================================
Evaluación Sumativa N°1 - Programación Orientada a Objeto Seguro (TI3V21)

- Herencia: Persona -> Paciente / Trabajador -> Odontologo / AsistenteDental
            TratamientoDental -> Limpieza / Ortodoncia / Cirugia / Radiografia
- Clases abstractas: Persona, Trabajador, TratamientoDental
- Polimorfismo: calcular_costo() / calcular_duracion() / verificar_permisos()
- Composición: AtencionMedica -> DetalleAtencion
- Asociación: DetalleAtencion -> TratamientoDental, AtencionMedica -> Paciente / Odontologo
- Dependencia: TratamientoDental -> IndicadorExterno (dólar)
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

try:
    import requests
except ImportError:  # el programa avisará en vez de caerse
    requests = None


class IndicadorNoDisponible(Exception):
    """No se pudo obtener el valor del dólar (sin internet, API caída, etc.)."""


# ---------------------------------------------------------------------------
# Persona (abstracta)
# ---------------------------------------------------------------------------
class Persona(ABC):
    """Datos comunes de toda persona que interactúa con la clínica."""

    def __init__(self, rut: str, nombre: str, telefono: str = "", correo: str = ""):
        self._rut = self.normalizar_rut(rut)  # lanza ValueError si es inválido
        self.nombre = nombre
        self.telefono = telefono
        self.correo = correo

    # -- RUT ---------------------------------------------------------------
    @staticmethod
    def normalizar_rut(rut: str) -> str:
        """Devuelve el RUT como 'cuerpo-dv' (sin puntos) o lanza ValueError."""
        if not isinstance(rut, str):
            raise ValueError("El RUT debe ser texto.")
        limpio = rut.strip().upper().replace(".", "").replace(" ", "")
        partes = limpio.split("-")
        if len(partes) != 2:
            raise ValueError("RUT inválido: debe tener guion antes del dígito verificador.")
        cuerpo, dv = partes
        if not cuerpo.isdigit() or not 6 <= len(cuerpo) <= 9:
            raise ValueError("RUT inválido: el cuerpo debe tener entre 6 y 9 dígitos.")
        if len(dv) != 1 or dv not in "0123456789K":
            raise ValueError("RUT inválido: dígito verificador no válido.")
        suma, mult = 0, 2
        for digito in reversed(cuerpo):
            suma += int(digito) * mult
            mult = mult + 1 if mult < 7 else 2
        resto = 11 - (suma % 11)
        esperado = {11: "0", 10: "K"}.get(resto, str(resto))
        if dv != esperado:
            raise ValueError("RUT inválido: el dígito verificador no corresponde.")
        return f"{int(cuerpo)}-{dv}"

    @classmethod
    def validar_rut(cls, rut: str) -> bool:
        try:
            cls.normalizar_rut(rut)
            return True
        except ValueError:
            return False

    @property
    def rut(self) -> str:
        return self._rut

    @property
    def rut_formateado(self) -> str:
        cuerpo, dv = self._rut.split("-")
        return f"{int(cuerpo):,}".replace(",", ".") + "-" + dv

    # -- Datos con validación ------------------------------------------------
    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        valor = (valor or "").strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío.")
        self._nombre = valor

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str):
        self._telefono = self.validar_telefono(valor)

    @staticmethod
    def validar_telefono(valor: str) -> str:
        valor = (valor or "").strip()
        if valor and not all(c.isdigit() or c in "+- " for c in valor):
            raise ValueError("El teléfono solo puede tener números, +, - y espacios.")
        return valor

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str):
        self._correo = self.validar_correo(valor)

    @staticmethod
    def validar_correo(valor: str) -> str:
        valor = (valor or "").strip()
        if valor and "@" not in valor:
            raise ValueError("El correo no es válido (falta '@').")
        return valor

    @property
    @abstractmethod
    def rol(self) -> str:
        """Rol de la persona dentro de la clínica."""

    def __str__(self):
        return f"{self._nombre} (RUT: {self.rut_formateado})"


# ---------------------------------------------------------------------------
# Paciente
# ---------------------------------------------------------------------------
class Paciente(Persona):
    DIAS_DEUDA_LIMITE = 60

    def __init__(self, rut, nombre, telefono="", correo="", historial_medico="",
                 alergias="", alergia_anestesia: Optional[bool] = None,
                 dias_deuda_vencida: int = 0):
        super().__init__(rut, nombre, telefono, correo)
        self.historial_medico = historial_medico
        self.alergias = alergias
        self.alergia_anestesia = alergia_anestesia
        self.dias_deuda_vencida = dias_deuda_vencida

    @property
    def rol(self) -> str:
        return "Paciente"

    @property
    def alergia_anestesia(self) -> Optional[bool]:
        """None = no registrada en la ficha, True = alérgico, False = no alérgico."""
        return self._alergia_anestesia

    @alergia_anestesia.setter
    def alergia_anestesia(self, valor):
        if valor not in (None, True, False):
            raise ValueError("La alergia a la anestesia debe ser Sí, No o sin registrar.")
        self._alergia_anestesia = valor

    @property
    def dias_deuda_vencida(self) -> int:
        return self._dias_deuda_vencida

    @dias_deuda_vencida.setter
    def dias_deuda_vencida(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValueError("Los días de deuda deben ser un entero mayor o igual a 0.")
        self._dias_deuda_vencida = valor

    @property
    def texto_alergia_anestesia(self) -> str:
        return {None: "Sin registrar", True: "Sí", False: "No"}[self._alergia_anestesia]

    def actualizar_historial(self, nueva_info: str):
        if nueva_info.strip():
            self.historial_medico += f" | {nueva_info}" if self.historial_medico else nueva_info

    def verificar_estado_financiero(self) -> str:
        if self._dias_deuda_vencida == 0:
            return "Al día"
        return f"Deuda vencida: {self._dias_deuda_vencida} día(s)"

    def puede_ser_atendido(self) -> bool:
        """Regla de negocio: no se atiende con deuda de más de 60 días."""
        return self._dias_deuda_vencida <= self.DIAS_DEUDA_LIMITE

    def to_dict(self) -> dict:
        return {"rut": self.rut, "nombre": self.nombre, "telefono": self.telefono,
                "correo": self.correo, "historial_medico": self.historial_medico,
                "alergias": self.alergias, "alergia_anestesia": self.alergia_anestesia,
                "dias_deuda_vencida": self.dias_deuda_vencida}

    @classmethod
    def from_dict(cls, d: dict) -> "Paciente":
        return cls(**d)


# ---------------------------------------------------------------------------
# Trabajadores
# ---------------------------------------------------------------------------
class Trabajador(Persona):
    def __init__(self, rut, nombre, telefono, correo, id_trabajador: str, turno: str):
        super().__init__(rut, nombre, telefono, correo)
        self.id_trabajador = id_trabajador
        self.turno = turno

    @abstractmethod
    def verificar_permisos(self, accion: str) -> bool:
        """Indica si el trabajador está autorizado a ejecutar `accion`."""


class Odontologo(Trabajador):
    ACCIONES_PERMITIDAS = {"diagnosticar", "realizar_tratamiento"}

    def __init__(self, rut, nombre, telefono, correo, id_trabajador, turno,
                 especialidad: str, registro_profesional: str):
        super().__init__(rut, nombre, telefono, correo, id_trabajador, turno)
        self.especialidad = especialidad
        self.registro_profesional = registro_profesional

    @property
    def rol(self) -> str:
        return "Odontólogo"

    def diagnosticar(self, paciente: Paciente) -> str:
        return f"{self.nombre} diagnosticó a {paciente.nombre}"

    def realizar_tratamiento(self, tratamiento: "TratamientoDental") -> str:
        return f"{self.nombre} realizó: {tratamiento.descripcion}"

    def verificar_permisos(self, accion: str) -> bool:
        return accion in self.ACCIONES_PERMITIDAS


class AsistenteDental(Trabajador):
    ACCIONES_PERMITIDAS = {"agendar_hora", "preparar_instrumental"}

    def __init__(self, rut, nombre, telefono, correo, id_trabajador, turno, certificacion: str):
        super().__init__(rut, nombre, telefono, correo, id_trabajador, turno)
        self.certificacion = certificacion

    @property
    def rol(self) -> str:
        return "Asistente dental"

    def agendar_hora(self, paciente: Paciente, fecha) -> str:
        return f"Hora agendada para {paciente.nombre} el {fecha}"

    def preparar_instrumental(self, tratamiento: "TratamientoDental") -> str:
        return f"Instrumental preparado para: {tratamiento.descripcion}"

    def verificar_permisos(self, accion: str) -> bool:
        return accion in self.ACCIONES_PERMITIDAS


# ---------------------------------------------------------------------------
# IndicadorExterno (dólar desde mindicador.cl)
# ---------------------------------------------------------------------------
class IndicadorExterno:
    """Consulta el dólar del día. Nunca usa un valor viejo si falla la consulta."""

    URL = "https://mindicador.cl/api/dolar"

    def __init__(self, timeout: float = 5):
        self.timeout = timeout
        self._valor: Optional[float] = None
        self.fecha: Optional[str] = None

    def refrescar(self) -> float:
        """Consulta la API. Si falla, deja el valor en None y lanza IndicadorNoDisponible."""
        self._valor, self.fecha = None, None
        if requests is None:
            raise IndicadorNoDisponible("Falta instalar la librería 'requests'.")
        try:
            resp = requests.get(self.URL, timeout=self.timeout)
            resp.raise_for_status()
            dato = resp.json()["serie"][0]
            valor = float(dato["valor"])
            fecha = str(dato["fecha"])[:10]
        except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as e:
            raise IndicadorNoDisponible(
                "No se pudo obtener el valor del dólar (revisa tu conexión a internet).") from e
        if not math.isfinite(valor) or valor <= 0:
            raise IndicadorNoDisponible("El valor del dólar recibido no es válido.")
        self._valor, self.fecha = valor, fecha
        return valor

    @property
    def valor_dolar(self) -> float:
        if self._valor is None:
            raise IndicadorNoDisponible("No hay un valor del dólar disponible.")
        return self._valor


# ---------------------------------------------------------------------------
# TratamientoDental (abstracta) y subclases
# ---------------------------------------------------------------------------
class TratamientoDental(ABC):
    TIPO = ""
    CAMPOS_EXTRA: tuple = ()

    def __init__(self, id_tratamiento: int, descripcion: str, costo_base: float):
        descripcion = (descripcion or "").strip()
        if not descripcion:
            raise ValueError("La descripción no puede estar vacía.")
        if (isinstance(costo_base, bool) or not isinstance(costo_base, (int, float))
                or not math.isfinite(costo_base) or costo_base < 0):
            raise ValueError("El costo base debe ser un número mayor o igual a 0.")
        self.id_tratamiento = id_tratamiento
        self.descripcion = descripcion
        self.costo_base = costo_base

    @abstractmethod
    def calcular_costo(self, indicador: IndicadorExterno) -> float:
        """Costo en pesos chilenos."""

    @abstractmethod
    def calcular_duracion(self) -> int:
        """Duración estimada en minutos."""

    def to_dict(self) -> dict:
        d = {"tipo": self.TIPO, "id": self.id_tratamiento,
             "descripcion": self.descripcion, "costo_base": self.costo_base}
        d.update({k: getattr(self, k) for k in self.CAMPOS_EXTRA})
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TratamientoDental":
        tipo = TIPOS_TRATAMIENTO[d["tipo"]]
        extra = {k: d[k] for k in tipo.CAMPOS_EXTRA}
        return tipo(d["id"], d["descripcion"], d["costo_base"], **extra)


class Limpieza(TratamientoDental):
    TIPO = "Limpieza"
    CAMPOS_EXTRA = ("tipo_cepillado",)

    def __init__(self, id_tratamiento, descripcion, costo_base, tipo_cepillado: str = "Manual"):
        super().__init__(id_tratamiento, descripcion, costo_base)
        self.tipo_cepillado = tipo_cepillado

    def calcular_costo(self, indicador=None) -> float:
        return self.costo_base  # sin materiales importados

    def calcular_duracion(self) -> int:
        return 30


class Ortodoncia(TratamientoDental):
    """El costo base está en USD (brackets importados) y se convierte con el dólar del día."""
    TIPO = "Ortodoncia"
    CAMPOS_EXTRA = ("tipo_brackets", "cantidad_meses")

    def __init__(self, id_tratamiento, descripcion, costo_base,
                 tipo_brackets: str = "Metálicos", cantidad_meses: int = 18):
        super().__init__(id_tratamiento, descripcion, costo_base)
        if isinstance(cantidad_meses, bool) or not isinstance(cantidad_meses, int) or cantidad_meses < 1:
            raise ValueError("La cantidad de meses debe ser un entero mayor o igual a 1.")
        self.tipo_brackets = tipo_brackets
        self.cantidad_meses = cantidad_meses

    def calcular_costo(self, indicador: IndicadorExterno) -> float:
        return self.costo_base * indicador.valor_dolar  # lanza IndicadorNoDisponible

    def calcular_duracion(self) -> int:
        return 90  # sesión de instalación; luego hay controles mensuales


class Cirugia(TratamientoDental):
    TIPO = "Cirugia"
    CAMPOS_EXTRA = ("requiere_pabellon_especial",)

    def __init__(self, id_tratamiento, descripcion, costo_base,
                 requiere_pabellon_especial: bool = False):
        super().__init__(id_tratamiento, descripcion, costo_base)
        self.requiere_pabellon_especial = bool(requiere_pabellon_especial)

    def calcular_costo(self, indicador=None) -> float:
        return self.costo_base * 1.5  # recargo por complejidad quirúrgica

    def calcular_duracion(self) -> int:
        return 120

    def puede_realizarse(self, pabellon_disponible: bool) -> bool:
        return pabellon_disponible if self.requiere_pabellon_especial else True


class Radiografia(TratamientoDental):
    """Procedimiento complementario que puede ir en la misma ficha que otro tratamiento."""
    TIPO = "Radiografia"

    def calcular_costo(self, indicador=None) -> float:
        return self.costo_base

    def calcular_duracion(self) -> int:
        return 10


TIPOS_TRATAMIENTO = {c.TIPO: c for c in (Limpieza, Ortodoncia, Cirugia, Radiografia)}


# ---------------------------------------------------------------------------
# DetalleAtencion y AtencionMedica (composición)
# ---------------------------------------------------------------------------
class DetalleAtencion:
    """Una línea de la ficha: un tratamiento realizado en la sesión."""

    def __init__(self, id_detalle: int, tratamiento: Optional[TratamientoDental],
                 cantidad: int = 1, precio_unitario: Optional[float] = None,
                 descripcion: Optional[str] = None):
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor o igual a 1.")
        self.id_detalle = id_detalle
        self.tratamiento = tratamiento
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        self.descripcion = descripcion or (tratamiento.descripcion if tratamiento else "")

    def calcular_subtotal(self) -> float:
        if self.precio_unitario is None:
            raise ValueError("El detalle aún no tiene precio calculado.")
        return self.precio_unitario * self.cantidad

    def to_dict(self) -> dict:
        return {"id": self.id_detalle, "descripcion": self.descripcion,
                "cantidad": self.cantidad, "precio_unitario": self.precio_unitario}

    @classmethod
    def from_dict(cls, d: dict) -> "DetalleAtencion":
        return cls(d["id"], None, d["cantidad"], d["precio_unitario"], d["descripcion"])


class AtencionMedica:
    """Ficha de atención: una sesión con uno o más tratamientos."""

    def __init__(self, id_atencion: int, paciente: Optional[Paciente], odontologo: Odontologo,
                 fecha: Optional[date] = None, hora: str = ""):
        self.id_atencion = id_atencion
        self.paciente = paciente
        self.paciente_rut = paciente.rut if paciente else None
        self.paciente_nombre = paciente.nombre if paciente else None
        self.odontologo = odontologo
        self.fecha = fecha or date.today()
        self.hora = hora
        self.estado = "pendiente"
        self.monto_total: Optional[float] = None
        self.valor_dolar_usado: Optional[float] = None
        self.detalles: list[DetalleAtencion] = []

    def agregar_detalle(self, tratamiento: TratamientoDental, cantidad: int = 1):
        self.detalles.append(DetalleAtencion(len(self.detalles) + 1, tratamiento, cantidad))

    def usa_dolar(self) -> bool:
        return any(isinstance(d.tratamiento, Ortodoncia) for d in self.detalles)

    def validar_condiciones(self, pabellon_disponible: bool = True) -> tuple[bool, str]:
        """Reglas de negocio. Devuelve (ok, motivo)."""
        if not self.detalles:
            return False, "La atención no tiene ningún tratamiento."
        if not self.odontologo.verificar_permisos("realizar_tratamiento"):
            return False, "El profesional no tiene permiso para realizar tratamientos."
        if not self.paciente.puede_ser_atendido():
            return False, (f"el paciente tiene una deuda vencida de {self.paciente.dias_deuda_vencida} "
                           f"días (el límite es {Paciente.DIAS_DEUDA_LIMITE}).")
        for d in self.detalles:
            if isinstance(d.tratamiento, Cirugia):
                if self.paciente.alergia_anestesia is None:
                    return False, ("no se puede agendar una cirugía: la ficha del paciente no tiene "
                                   "registrada su alergia a la anestesia. Regístrala en 'Modificar paciente'.")
                if not d.tratamiento.puede_realizarse(pabellon_disponible):
                    return False, "la cirugía requiere pabellón especial y no está disponible."
        return True, ""

    def registrar(self, indicador: IndicadorExterno,
                  pabellon_disponible: bool = True) -> tuple[bool, str]:
        ok, motivo = self.validar_condiciones(pabellon_disponible)
        if not ok:
            self.estado = "rechazada"
            return False, motivo
        precios = [d.tratamiento.calcular_costo(indicador) for d in self.detalles]  # puede lanzar
        for d, precio in zip(self.detalles, precios):
            d.precio_unitario = precio
        self.valor_dolar_usado = indicador.valor_dolar if self.usa_dolar() else None
        self.monto_total = sum(d.calcular_subtotal() for d in self.detalles)
        self.estado = "registrada"
        return True, ""

    def to_dict(self) -> dict:
        return {"id": self.id_atencion, "rut": self.paciente_rut, "nombre": self.paciente_nombre,
                "fecha": self.fecha.isoformat(), "hora": self.hora, "estado": self.estado,
                "monto_total": self.monto_total, "valor_dolar_usado": self.valor_dolar_usado,
                "detalles": [d.to_dict() for d in self.detalles]}

    @classmethod
    def from_dict(cls, d: dict, odontologo: Odontologo) -> "AtencionMedica":
        a = cls(d["id"], None, odontologo, date.fromisoformat(d["fecha"]), d["hora"])
        a.paciente_rut, a.paciente_nombre = d["rut"], d["nombre"]
        a.estado, a.monto_total = d["estado"], d["monto_total"]
        a.valor_dolar_usado = d["valor_dolar_usado"]
        a.detalles = [DetalleAtencion.from_dict(x) for x in d["detalles"]]
        return a


if __name__ == "__main__":
    import main
    try:
        main.menu()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")

