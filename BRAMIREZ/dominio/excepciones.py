class ErrorNegocio(ValueError):
    """Una regla del sistema impide completar la operación."""


class Conflicto(ErrorNegocio):
    """Identificador repetido, referencia inválida o historial protegido."""


class NoEncontrado(ErrorNegocio):
    """Entidad inexistente o retirada."""
