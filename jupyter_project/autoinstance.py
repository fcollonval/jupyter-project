"""
Dynamically build instance from dictionary

Reference:
    https://github.com/ipython/traitlets/pull/466#issuecomment-369971116
"""
from traitlets import HasTraits, Instance
from traitlets.config import Configurable


class AutoInstance(Instance):
    """Dynamically build instance from dictionary"""

    def validate(self, obj, value):
        iclass = self.klass

        if (issubclass(iclass, HasTraits) and isinstance(value, dict)):
            if issubclass(iclass, Configurable):
                value = iclass(parent=obj, **value)
            else:
                value = iclass(**value)

        return super().validate(obj, value)
