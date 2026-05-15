"""Interface web local para o ``converter``.

Sobe um pequeno servidor Flask que reaproveita o
:class:`converter.core.ConversionEngine`, expondo uma página de
upload em ``http://localhost:5000``. Não foi pensada para acesso
público — é uma camada de conveniência para uso local sem terminal.
"""

from .app import create_app

__all__ = ["create_app"]
