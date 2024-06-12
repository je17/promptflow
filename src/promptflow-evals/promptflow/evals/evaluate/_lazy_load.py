"""Utility to lazy load modules."""

import importlib
import sys
import types


def lazy_import(fullname):
    """
    This function is used to lazily import modules.  It is used in the following way:
    .. code-block:: python
        from flytekit.lazy_import import lazy_module
        sklearn = lazy_module("sklearn")
        sklearn.svm.SVC()
    :param Text fullname: The full name of the module to import
    """
    if fullname in sys.modules:
        return sys.modules[fullname]
    # https://docs.python.org/3/library/importlib.html#implementing-lazy-imports
    spec = importlib.util.find_spec(fullname)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    loader.exec_module(module)
    return module


class LazyLoader(types.ModuleType):
    """Class for module lazy loading.

    This class helps lazily load modules at package level, which avoids pulling in large
    dependencies like `tensorflow` or `torch`. This class is mirrored from wandb's LazyLoader:
    https://github.com/wandb/wandb/blob/79b2d4b73e3a9e4488e503c3131ff74d151df689/wandb/sdk/lib/lazyloader.py#L9
    """

    def __init__(self, local_name, parent_module_globals, name):
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals

        self._module = None
        super().__init__(str(name))

    def _load(self):
        """Load the module and insert it into the parent's globals."""
        if self._module:
            # If already loaded, return the loaded module.
            return self._module

        # Import the target module and insert it into the parent's namespace
        module = importlib.import_module(self.__name__)
        self._parent_module_globals[self._local_name] = module
        sys.modules[self._local_name] = module

        # Update this object's dict so that if someone keeps a reference to the `LazyLoader`,
        # lookups are efficient (`__getattr__` is only called on lookups that fail).
        self.__dict__.update(module.__dict__)

        return module

    def __getattr__(self, item):
        module = self._load()
        return getattr(module, item)

    def __dir__(self):
        module = self._load()
        return dir(module)

    def __repr__(self):
        if not self._module:
            return f"<module '{self.__name__} (Not loaded yet)'>"
        return repr(self._module)
